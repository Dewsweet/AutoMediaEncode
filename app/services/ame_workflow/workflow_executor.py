from pathlib import Path
from collections import deque
from PySide6.QtCore import QThread, Signal
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
        logger.info('\n' * 10 + '=' * 100 + '\n' + '=' * 100)
        logger.info(f'[AME] 开始执行工作流, {len(self._nodes)} 个节点, {len(self._edges)} 条连线')
        if not self._nodes:
            return
        order = self._topo_sort() # 拓扑排序，确保父节点在子节点前执行
        if order is None:
            self.error_occurred.emit('工作流中存在循环依赖')
            return
        connected = set()
        for fn, fp, tid, tp in self._edges:
            connected.add(fn.id); connected.add(tid)
        order = [n for n in order if n.id in connected]
        logger.info(f'[AME] 拓扑排序: {[n.name() for n in order]}')
        if not order:
            order = [n for n in self._nodes if 'Output' in n.__class__.__name__]
        total = len(order) if order else 1
        self._resolve_temp_dir()
        logger.info(f'[AME] 临时目录: {self._temp_dir}')
        port_data = {}
        for i, node in enumerate(order):
            if self._cancelled: return
            logger.info(f'[AME] 执行节点: {node.name()} ({node.__class__.__name__})')
            self.node_status_changed.emit(node.id, 'running')
            inputs = self._collect(node, port_data)
            logger.info(f'[AME] 输入: {list(inputs.keys())}')
            result = None
            try:
                result = node.execute(inputs, self._temp_dir)
            except Exception as e:
                logger.error(f'[AME] 节点 {node.name()} 执行异常: {e}')
                import traceback
                logger.error(traceback.format_exc())
            if self._cancelled: return
            if result is not None or node.__class__.__name__ == 'OutputNode':
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
                logger.error(f'[AME] 节点 {node.name()} 返回 None, 执行失败')
                self.node_status_changed.emit(node.id, 'error')
                self.error_occurred.emit(f'节点 {node.name()} 执行失败')
                return
            self.progress_updated.emit(int((i + 1) / total * 100))
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
        ids = {n.id for n in self._nodes}
        adj = {i: [] for i in ids}
        deg = {i: 0 for i in ids}
        for fn, fp, tid, tp in self._edges:
            if fn.id != tid:
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

    def _resolve_temp_dir(self):
        # 优先: 工作区节点
        for n in self._nodes:
            if 'Workspace' in n.__class__.__name__:
                wd = n.property('workspace', '')
                wd = Path(wd) if wd else None
                if wd and wd.is_dir():
                    self._temp_dir = wd / 'temp'
                    self._temp_dir.mkdir(exist_ok=True)
                    return
        # 其次: 输出节点目录
        for n in self._nodes:
            if 'Output' in n.__class__.__name__:
                op = n.property('output', '')
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
            if 'Input' in n.__class__.__name__:
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
