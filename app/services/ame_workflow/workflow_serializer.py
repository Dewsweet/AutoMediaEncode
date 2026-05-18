import json


def save_workflow(graph, filepath: str):
    graph.save_session(filepath)


def load_workflow(graph, filepath: str):
    graph.load_session(filepath)
