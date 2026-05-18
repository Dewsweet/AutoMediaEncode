from collections import deque


class WorkflowValidator:
    def __init__(self):
        self.errors = []

    def validate(self, nodes: list, edges: list) -> bool:
        self.errors.clear()
        if not nodes:
            self.errors.append("工作流中没有节点")
            return False

        node_ids = {n.id for n in nodes}
        output_nodes = [n for n in nodes if 'OutputNode' in n.type_]
        if not output_nodes:
            self.errors.append("缺少输出节点")
            return False

        if self._has_cycle(nodes, edges, node_ids):
            self.errors.append("工作流中存在循环依赖")
            return False
        return len(self.errors) == 0

    def _has_cycle(self, nodes, edges, node_ids) -> bool:
        adj = {nid: [] for nid in node_ids}
        in_degree = {nid: 0 for nid in node_ids}

        for from_node, from_port, to_id, to_port in edges:
            if from_node.id != to_id:
                adj[from_node.id].append(to_id)
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
        node_ids = {n.id for n in node_list}
        node_map = {n.id: n for n in node_list}
        adj = {nid: [] for nid in node_ids}
        in_degree = {nid: 0 for nid in node_ids}

        for from_node, from_port, to_id, to_port in edges:
            if from_node.id != to_id:
                adj[from_node.id].append(to_id)
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
