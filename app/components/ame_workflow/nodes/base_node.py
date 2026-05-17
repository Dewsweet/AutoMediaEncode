import json
from pathlib import Path
from typing import Optional


class BaseNodeData:
    NODE_TYPE = ""
    NODE_NAME = ""
    CATEGORY = ""
    COLOR = "#607D8B"
    INPUT_PORTS = []
    OUTPUT_PORTS = []
    DEFAULT_PARAMS = {}

    def __init__(self, node_id: str = "", x: float = 0, y: float = 0):
        self.node_id = node_id
        self.x = x
        self.y = y
        self.params = dict(self.DEFAULT_PARAMS)

    def to_dict(self):
        return {
            "id": self.node_id,
            "type": self.NODE_TYPE,
            "name": self.NODE_NAME,
            "category": self.CATEGORY,
            "color": self.COLOR,
            "x": self.x,
            "y": self.y,
            "params": self.params,
            "input_ports": self.INPUT_PORTS,
            "output_ports": self.OUTPUT_PORTS,
        }

    @classmethod
    def from_dict(cls, d: dict):
        inst = cls(
            node_id=d.get('id', ''),
            x=d.get('x', 0),
            y=d.get('y', 0)
        )
        inst.params = d.get('params', dict(cls.DEFAULT_PARAMS))
        return inst

    @classmethod
    def get_meta(cls):
        return {
            "type": cls.NODE_TYPE,
            "name": cls.NODE_NAME,
            "category": cls.CATEGORY,
            "color": cls.COLOR,
            "input_ports": cls.INPUT_PORTS,
            "output_ports": cls.OUTPUT_PORTS,
            "params": dict(cls.DEFAULT_PARAMS),
        }
