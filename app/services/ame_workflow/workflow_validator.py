from collections import deque

from app.components.ame_workflow.node_item import AMENodeItem
from app.components.ame_workflow.node_edge import AMEEdge
from app.components.ame_workflow import PortDirection


class WorkflowValidator:
    def __init__(self):
        self.errors = []

    def validate(self, nodes: list, edges: list) -> bool:
        self.errors.clear()

        if not nodes:
            self.errors.append("工作流中没有节点")
            return False

        node_ids = {n.node_id() for n in nodes}

        output_nodes = [n for n in nodes if n.node_type() == 'output']
        if not output_nodes:
            self.errors.append("缺少输出节点")
            return False

        for output_node in output_nodes:
            connected = False
            for e in edges:
                if e.source_port() and e.source_port().node().node_id() == output_node.node_id():
                    connected = True
                    break
                if e.target_port() and e.target_port().node().node_id() == output_node.node_id():
                    connected = True
                    break
            if not connected:
                self.errors.append("输出节点未连接到任何工作流")

        if self._has_cycle(nodes, edges, node_ids):
            self.errors.append("工作流中存在循环依赖")
            return False

        return len(self.errors) == 0

    def _has_cycle(self, nodes, edges, node_ids) -> bool:
        adj = {nid: [] for nid in node_ids}
        in_degree = {nid: 0 for nid in node_ids}

        for e in edges:
            sp = e.source_port()
            tp = e.target_port()
            if sp is None or tp is None:
                continue
            from_id = sp.node().node_id()
            to_id = tp.node().node_id()
            if from_id != to_id:
                adj[from_id].append(to_id)
                in_degree[to_id] = in_degree.get(to_id, 0) + 1

        queue = deque([nid for nid in node_ids if in_degree.get(nid, 0) == 0])
        visited = 0

        while queue:
            u = queue.popleft()
            visited += 1
            for v in adj.get(u, []):
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        return visited != len(node_ids)

    def get_topological_order(self, nodes: list, edges: list) -> list:
        node_list = list(nodes)
        node_ids = {n.node_id() for n in node_list}
        node_map = {n.node_id(): n for n in node_list}

        adj = {nid: [] for nid in node_ids}
        in_degree = {nid: 0 for nid in node_ids}

        for e in edges:
            sp = e.source_port()
            tp = e.target_port()
            if sp is None or tp is None:
                continue
            from_id = sp.node().node_id()
            to_id = tp.node().node_id()
            if from_id != to_id:
                adj[from_id].append(to_id)
                in_degree[to_id] = in_degree.get(to_id, 0) + 1

        queue = deque([nid for nid in node_ids if in_degree.get(nid, 0) == 0])
        order = []

        while queue:
            u = queue.popleft()
            order.append(node_map[u])
            for v in adj.get(u, []):
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        return order
