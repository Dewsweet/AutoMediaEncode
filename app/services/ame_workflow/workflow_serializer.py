import json
from pathlib import Path

from app.components.ame_workflow.node_item import AMENodeItem
from app.components.ame_workflow.node_edge import AMEEdge


def save_workflow(nodes: list, edges: list, filepath: str):
    nodes_data = []
    for n in nodes:
        if isinstance(n, AMENodeItem):
            nodes_data.append(n.get_state())

    edges_data = []
    for e in edges:
        if isinstance(e, AMEEdge):
            sp = e.source_port()
            tp = e.target_port()
            if sp and tp:
                edges_data.append({
                    "id": f"{sp.node().node_id()}_{sp.port_name()}_to_{tp.node().node_id()}_{tp.port_name()}",
                    "from_node": sp.node().node_id(),
                    "from_port": sp.port_name(),
                    "to_node": tp.node().node_id(),
                    "to_port": tp.port_name(),
                })

    workflow = {
        "version": "1.0",
        "nodes": nodes_data,
        "edges": edges_data,
    }
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, ensure_ascii=False, indent=2)


def load_workflow(filepath: str):
    with open(filepath, 'r', encoding='utf-8') as f:
        workflow = json.load(f)
    return workflow.get('nodes', []), workflow.get('edges', [])
