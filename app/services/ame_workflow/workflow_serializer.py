"""工作流文件校验、原子写入与可撤销的画布替换。"""
import copy
import json
import math
import os
import tempfile
from pathlib import Path

from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QUndoStack


def _invalid(detail):
    return ValueError(QCoreApplication.translate(
        'WorkflowSerializer', '无效的工作流文件: {detail}').format(detail=detail))


def _node_types(graph=None):
    if graph is not None:
        return graph.node_factory.nodes
    from app.components.ame_workflow.nodes import TYPE_NAME_MAP
    from NodeGraphQt.nodes.backdrop_node import BackdropNode
    return {**TYPE_NAME_MAP, BackdropNode.type_: BackdropNode}


def validate_workflow(data, graph=None):
    """校验引用和端口，兼容出厂预设的旧端口名；不构建或修改画布。"""
    if not isinstance(data, dict) or not isinstance(data.get('nodes'), dict):
        raise _invalid('nodes')
    data = copy.deepcopy(data)
    settings = data.get('graph', {})
    if not isinstance(settings, dict):
        raise _invalid('graph')
    for key in ('accept_connection_types', 'reject_connection_types'):
        if key in settings:
            try:
                constraints = json.loads(settings[key])
                def check_constraints(value):
                    if isinstance(value, dict):
                        return all(check_constraints(v) for v in value.values())
                    return isinstance(value, list) and all(isinstance(v, str) for v in value)
                if not isinstance(constraints, dict) or not check_constraints(constraints):
                    raise ValueError(key)
            except (ValueError, TypeError):
                raise _invalid(key) from None
    for key, choices in (('layout_direction', (0, 1)), ('pipe_style', (0, 1, 2))):
        if key in settings and settings[key] not in choices:
            raise _invalid(key)
    for key in ('acyclic', 'pipe_collision', 'pipe_slicing'):
        if key in settings and not isinstance(settings[key], bool):
            raise _invalid(key)

    types = _node_types(graph)
    ports = {}
    for nid, node in data['nodes'].items():
        if not isinstance(nid, str) or not isinstance(node, dict):
            raise _invalid('node')
        kind = node.get('type_')
        if not isinstance(kind, str) or kind not in types:
            raise _invalid(f'type_: {kind}')
        if not isinstance(node.get('custom', {}), dict):
            raise _invalid(f'{nid}: custom')
        if 'name' in node and not isinstance(node['name'], str):
            raise _invalid(f'{nid}: name')
        for key in ('pos', 'color', 'border_color', 'text_color'):
            if key not in node:
                continue
            value = node[key]
            lengths = (2,) if key == 'pos' else (3, 4)
            if (not isinstance(value, list) or len(value) not in lengths
                    or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in value)):
                raise _invalid(f'{nid}: {key}')
        for key in ('width', 'height'):
            if key in node and (not isinstance(node[key], (int, float))
                               or not math.isfinite(node[key]) or node[key] <= 0):
                raise _invalid(f'{nid}: {key}')
        cls = types[kind]
        ports[nid] = {}
        for direction, attr in (('in', 'INPUTS'), ('out', 'OUTPUTS')):
            names = {p[0] for p in getattr(cls, attr, [])}
            if node.get('port_deletion_allowed'):
                entries = node.get('input_ports' if direction == 'in' else 'output_ports')
                if not isinstance(entries, list):
                    raise _invalid(f'{nid}: {direction} ports')
                names = set()
                for entry in entries:
                    if not isinstance(entry, dict) or not isinstance(entry.get('name'), str):
                        raise _invalid(f'{nid}: port')
                    if entry['name'] in names:
                        raise _invalid(f'{nid}: duplicate port')
                    names.add(entry['name'])
            ports[nid][direction] = names

    connections = data.get('connections', [])
    if not isinstance(connections, list):
        raise _invalid('connections')
    for conn in connections:
        if not isinstance(conn, dict):
            raise _invalid('connection')
        # 先检查两端引用，再解析兼容名称。
        for direction in ('out', 'in'):
            endpoint = conn.get(direction)
            if (not isinstance(endpoint, list) or len(endpoint) != 2
                    or not all(isinstance(v, str) for v in endpoint)
                    or endpoint[0] not in ports):
                raise _invalid(f'connection: {direction}')
        for direction in ('out', 'in'):
            endpoint = conn[direction]
            nid, name = endpoint
            names = ports[nid][direction]
            if name not in names:
                if name in ('path', 'input', 'output') and len(names) == 1:
                    name = next(iter(names))
                elif name == 'input' and direction == 'in' and names == {'file', 'pipe'}:
                    source = data['nodes'][conn['out'][0]]['type_']
                    name = 'pipe' if source == 'ame.VSPipeNode' else 'file'
                elif (direction == 'out' and name == 'video'
                      and data['nodes'][nid]['type_'] == 'ame.VSPipeNode'):
                    name = 'pipe'
                if name not in names:
                    raise _invalid(f'{nid}: {direction}.{endpoint[1]}')
                endpoint[1] = name
    return data


def read_workflow(filepath, graph=None):
    with Path(filepath).open('r', encoding='utf-8-sig') as stream:
        data = json.load(stream)
    return validate_workflow(data, graph)


def write_workflow(data, filepath, *, overwrite=True):
    """先完整序列化再写入同目录临时文件；失败不损坏原文件。"""
    target = Path(filepath)
    content = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False,
                         default=lambda value: list(value) if isinstance(value, set) else value)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n',
                                         prefix='.ame-workflow-', suffix='.tmp',
                                         dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if overwrite:
            os.replace(temporary, target)
        else:
            # Windows rename 不覆盖目标，保护首次保存和导入时的同名竞态。
            os.rename(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return target


def save_workflow(graph, filepath, *, overwrite=True, update_session=True):
    target = write_workflow(graph.serialize_session(), filepath, overwrite=overwrite)
    if update_session:
        graph.model.session = str(target)
    return target


def load_workflow(graph, filepath):
    """先添加候选节点；恢复成功后才移除旧节点，异常时撤销整个替换。"""
    data = read_workflow(filepath, graph)
    old_nodes = graph.all_nodes()
    old_ids = {node.id for node in old_nodes}
    old_settings = copy.deepcopy(graph.serialize_session()['graph'])
    old_selection = {node.id: node.selected() for node in old_nodes}
    old_directions = {node.id: node.model.layout_direction for node in old_nodes}
    old_session = graph.current_session()
    original_stack = graph.undo_stack()
    # 候选恢复使用独立撤销栈，失败时不丢失用户原有的重做分支。
    stack = QUndoStack(graph)
    graph._undo_stack = stack
    stack.beginMacro(QCoreApplication.translate('WorkflowSerializer', '加载工作流'))
    try:
        created = list(graph._deserialize(data, adjust_graph_style=False))
        if len(created) != len(data['nodes']):
            raise _invalid('node restoration')
        mapping = dict(zip(data['nodes'], created))
        for conn in data.get('connections', []):
            out_id, out_name = conn['out']
            in_id, in_name = conn['in']
            out_port = mapping[out_id].outputs().get(out_name)
            in_port = mapping[in_id].inputs().get(in_name)
            if not out_port or not in_port or in_port not in out_port.connected_ports():
                raise _invalid('connection restoration')
        graph.delete_nodes(old_nodes)
        for node, saved in zip(created, data['nodes'].values()):
            node.set_property('name', saved.get('name', node.NODE_NAME))
        graph._deserialize({'graph': data.get('graph', {})})
        graph.clear_selection()
    except Exception:
        stack.endMacro()
        stack.undo()
        graph._deserialize({'graph': old_settings})
        for node in old_nodes:
            node.set_layout_direction(old_directions[node.id])
            # QGraphicsScene 移除图元时会清除选择，NodesRemovedCmd.undo 不恢复它。
            node.view.selected = old_selection[node.id]
            # 同步 NodeGraphQt 用于序列化的图元属性缓存。
            _ = node.view.selected
            node.model.set_property('selected', old_selection[node.id])
        graph.model.session = old_session
        if {node.id for node in graph.all_nodes()} != old_ids:
            raise RuntimeError(QCoreApplication.translate('WorkflowSerializer', '无法恢复原工作流画布'))
        raise
    else:
        stack.endMacro()
        original_stack.clear()
        graph.model.session = str(filepath)
    finally:
        graph._undo_stack = original_stack
        stack.clear()
        stack.deleteLater()
    graph.session_changed.emit(str(filepath))
    return True
