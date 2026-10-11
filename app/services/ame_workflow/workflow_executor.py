from pathlib import Path
from collections import deque
from PySide6.QtCore import QThread, Signal
from app.common.logger import logger
from .process_runner import ProcessControl, ProcessCancelled, process_scope


class AMEWorkflowExecutor(QThread):
    progress_updated = Signal(int)
    node_status_changed = Signal(str, str)
    error_occurred = Signal(str)

    def __init__(self, nodes: list, edges: list, parent=None):
        super().__init__(parent)
        self._nodes = list(nodes)
        self._edges = list(edges)
        self._cancelled = False
        self._paused = False
        self._node_map = {n.id: n for n in self._nodes}
        self._temp_dir = ''
        self._control = ProcessControl()
        self.succeeded = False

    def cancel(self):
        self._cancelled = True
        self._paused = False
        self._control.cancel()

    def pause(self):
        self._paused = True
        self._control.paused.set()

    def resume(self):
        self._paused = False
        self._control.paused.clear()

    def run(self):
        try:
            with process_scope(self._control):
                self._execute()
        except ProcessCancelled:
            pass
        except Exception as error:
            logger.exception('[AME] 工作流执行异常')
            if not self._cancelled:
                self.error_occurred.emit(str(error))
        finally:
            self._control.close()

    def _execute(self):
        logger.info('\n' * 10 + '=' * 100 + '\n' + '=' * 100)
        logger.info(f'[AME] 开始执行工作流, {len(self._nodes)} 个节点, {len(self._edges)} 条连线')
        if not self._nodes:
            return
        from app.components.ame_workflow.nodes.io.output_node import OutputNode
        output_nodes = [node for node in self._nodes if isinstance(node, OutputNode)]
        if len(output_nodes) > 1:
            self.error_occurred.emit(self.tr('工作流仅支持一个输出节点，请仅保留一个输出节点'))
            return
        if any(self._is_disabled(node) for node in output_nodes):
            self.error_occurred.emit(self.tr('输出节点已禁用，请启用输出节点后再开始任务'))
            return
        # 禁用不代表旁路：编码、分离等节点的输入输出格式可能不同。
        # 在任何文件操作之前检查禁用节点仍连向启用节点的情况。
        for source, _, target_id, _ in self._edges:
            target = self._node_map[target_id]
            if self._is_disabled(source) and not self._is_disabled(target):
                self.error_occurred.emit(self.tr("节点 '{target}' 仍依赖已禁用节点 '{source}'，请启用上游节点或调整连线").format(
                    target=getattr(target, 'display_name', target.name)(),
                    source=getattr(source, 'display_name', source.name)()))
                return
        for node in self._nodes:
            if self._is_disabled(node):
                self.node_status_changed.emit(node.id, 'skipped')
        order = self._topo_sort()
        if order is None:
            self.error_occurred.emit(self.tr('工作流中存在循环依赖'))
            return
        connected = set()
        for fn, fp, tid, tp in self._edges:
            connected.add(fn.id); connected.add(tid)
        order = [n for n in order if n.id in connected]
        logger.info(f'[AME] 拓扑排序: {[n.name() for n in order]}')
        if not order:
            order = [n for n in self._nodes if 'Output' in n.__class__.__name__ and not self._is_disabled(n)]
        if output_nodes:
            # 唯一输出节点最后执行，包括未连线的输出节点（由其报告缺少输入）。
            order = [node for node in order if node not in output_nodes] + output_nodes
        total = len(order) if order else 1
        self._resolve_temp_dir()
        logger.info(f'[AME] 临时目录: {self._temp_dir}')
        port_data = {}

        for i, node in enumerate(order):
            if self._cancelled:
                return
            self._control.checkpoint()

            logger.info(f'[AME] 执行节点: {node.name()} ({node.__class__.__name__})')
            self.node_status_changed.emit(node.id, 'running')
            node._ame_cancelled = lambda: self._cancelled
            node._ame_paused = lambda: self._paused

            inputs = self._collect(node, port_data)
            logger.info(f'[AME] 输入: {list(inputs.keys())}')
            result = None
            node._last_error = ''
            try:
                result = node.execute(inputs, self._temp_dir)
            except ProcessCancelled:
                self.node_status_changed.emit(node.id, 'cancelled')
                return
            except Exception as e:
                node._last_error = str(e)
                logger.error(f'[AME] 节点 {node.name()} 执行异常: {e}')
                import traceback
                logger.error(traceback.format_exc())

            if self._cancelled:
                self.node_status_changed.emit(node.id, 'cancelled')
                return

            if isinstance(result, dict):
                if result:
                    logger.info(f'[AME] 输出: {list(result.keys())}')
                    for pn, files in result.items():
                        if files:
                            logger.info(f'[AME]   {pn}: {files[0]}')
                        port_data[(node.id, pn)] = files
                else:
                    logger.info(f'[AME] 输出: 空')
                self.node_status_changed.emit(node.id, 'done')
            else:
                logger.error(f'[AME] 节点 {node.name()} 未返回有效结果, 执行失败')
                self.node_status_changed.emit(node.id, 'error')
                detail = getattr(node, '_last_error', '')
                msg = self.tr("节点 '{name}' 执行失败").format(name=getattr(node, 'display_name', node.name)())
                if detail:
                    msg += f"\n{detail[:200]}"
                self.error_occurred.emit(msg)
                return
            self.progress_updated.emit(int((i + 1) / total * 100))

        self._control.checkpoint()
        self.succeeded = True
        logger.info(f'[AME] 工作流执行完成')

    def _collect(self, node, port_data):
        inp = {}
        for fn, fp, tid, tp in self._edges:
            if tid == node.id:
                key = (fn.id, fp)
                if key in port_data:
                    inp.setdefault(tp, []).extend(port_data[key])
        return inp

    def _topo_sort(self):
        ids = {n.id for n in self._nodes if not self._is_disabled(n)}
        adj = {i: [] for i in ids}
        deg = {i: 0 for i in ids}
        for fn, fp, tid, tp in self._edges:
            if fn.id in ids and tid in ids and fn.id != tid:
                adj[fn.id].append(tid)
                deg[tid] = deg.get(tid, 0) + 1
        q = deque(i for i in ids if deg[i] == 0)
        order = []
        while q:
            u = q.popleft()
            order.append(self._node_map[u])
            for v in adj.get(u, []):
                deg[v] -= 1
                if deg[v] == 0:
                    q.append(v)
        return order if len(order) == len(ids) else None

    @staticmethod
    def _is_disabled(node):
        return bool(getattr(node, 'disabled', lambda: False)())

    def _resolve_temp_dir(self):
        # 优先: 工作区节点
        for n in self._nodes:
            if not self._is_disabled(n) and 'Workspace' in n.__class__.__name__:
                wd = n.property('workspace', '')
                wd = Path(wd) if wd else None
                if wd and wd.is_dir():
                    self._temp_dir = wd / 'temp'
                    self._temp_dir.mkdir(exist_ok=True)
                    return
        # 其次: 输出节点目录
        for n in self._nodes:
            if not self._is_disabled(n) and 'Output' in n.__class__.__name__:
                op = n.property('output', '')
                if not op:
                    continue
                if Path(op).is_dir():
                    self._temp_dir = Path(op) / 'temp'
                    self._temp_dir.mkdir(exist_ok=True)
                    return
                elif Path(op).is_file(): 
                    od = Path(op).parent
                    if od.is_dir():
                        self._temp_dir = od / 'temp'
                        self._temp_dir.mkdir(exist_ok=True)
                        return
        # 最后: 输入文件目录
        for n in self._nodes:
            if not self._is_disabled(n) and 'Input' in n.__class__.__name__:
                for prop in ['input_file', 'input_multi']:
                    fp = n.property(prop, '')
                    if fp:
                        f = fp.split('\n')[0].strip()
                        f = Path(f)
                        if f.is_file():
                            sd = f.parent
                            self._temp_dir = sd / 'temp'
                            self._temp_dir.mkdir(exist_ok=True)
                            return
