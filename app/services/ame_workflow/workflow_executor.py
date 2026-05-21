import os, uuid
from collections import deque
from PySide6.QtCore import QThread, Signal
from app.services.tool_service import ToolService
from app.common.logger import logger


class AMEWorkflowExecutor(QThread):
    progress_updated = Signal(int)
    node_status_changed = Signal(str, str)
    error_occurred = Signal(str)

    def __init__(self, nodes: list, edges: list, parent=None):
        super().__init__(parent)
        self._nodes = list(nodes)
        self._edges = list(edges)
        self._cancelled = False
        self._node_map = {n.id: n for n in self._nodes}
        self._temp_dir = ''

    def cancel(self):
        self._cancelled = True

    def run(self):
        if not self._nodes:
            return
        order = self._topo_sort()
        if order is None:
            self.error_occurred.emit('工作流中存在循环依赖')
            return
        connected = set()
        for fn, fp, tid, tp in self._edges:
            connected.add(fn.id); connected.add(tid)
        order = [n for n in order if n.id in connected]
        if not order:
            order = [n for n in self._nodes if 'Output' in n.__class__.__name__]
        total = len(order) if order else 1
        self._resolve_temp_dir()
        port_data = {}
        for i, node in enumerate(order):
            if self._cancelled: return
            self.node_status_changed.emit(node.id, 'running')
            inputs = self._collect(node, port_data)
            result = None
            try:
                result = node.execute(inputs, self._temp_dir)
            except Exception as e:
                logger.error(f'{node.name()} failed: {e}')
            if self._cancelled: return
            if result is not None or node.__class__.__name__ == 'OutputNode':
                if result:
                    for pn, files in result.items():
                        port_data[(node.id, pn)] = files
                self.node_status_changed.emit(node.id, 'done')
            else:
                self.node_status_changed.emit(node.id, 'error')
                self.error_occurred.emit(f'节点 {node.name()} 执行失败')
                return
            self.progress_updated.emit(int((i + 1) / total * 100))

    def _collect(self, node, port_data):
        inp = {}
        for fn, fp, tid, tp in self._edges:
            if tid == node.id:
                key = (fn.id, fp)
                if key in port_data:
                    inp.setdefault(tp, []).extend(port_data[key])
        return inp

    def _topo_sort(self):
        ids = {n.id for n in self._nodes}
        adj = {i: [] for i in ids}; deg = {i: 0 for i in ids}
        for fn, fp, tid, tp in self._edges:
            if fn.id != tid:
                adj[fn.id].append(tid); deg[tid] = deg.get(tid, 0) + 1
        q = deque(i for i in ids if deg[i] == 0)
        order = []
        while q:
            u = q.popleft(); order.append(self._node_map[u])
            for v in adj.get(u, []):
                deg[v] -= 1
                if deg[v] == 0: q.append(v)
        return order if len(order) == len(ids) else None

    def _resolve_temp_dir(self):
        for n in self._nodes:
            if 'Workspace' in n.__class__.__name__:
                wd = n.property('work_dir', '')
                if wd and os.path.isdir(wd):
                    self._temp_dir = os.path.join(wd, 'temp')
                    os.makedirs(self._temp_dir, exist_ok=True)
                    return
        for n in self._nodes:
            if 'Output' in n.__class__.__name__:
                op = n.property('output_path', '')
                if op:
                    od = os.path.dirname(op) or '.'
                    self._temp_dir = os.path.join(od, 'temp')
                    os.makedirs(self._temp_dir, exist_ok=True)
                    return
        for n in self._nodes:
            if 'Input' in n.__class__.__name__:
                fp = n.property('file_path', '')
                if fp and os.path.isfile(fp):
                    sd = os.path.dirname(fp) or '.'
                    self._temp_dir = os.path.join(sd, 'temp')
                    os.makedirs(self._temp_dir, exist_ok=True)
                    return
        self._temp_dir = os.path.join(os.path.abspath('.'), 'temp')
        os.makedirs(self._temp_dir, exist_ok=True)
