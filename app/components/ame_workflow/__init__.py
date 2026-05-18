from enum import Enum


class PortType:
    VIDEO = "video"
    AUDIO = "audio"
    SUBTITLE = "subtitle"
    CHAPTER = "chapter"
    ATTACHMENT = "attachment"
    SCRIPT = "script"
    ANY = "any"


class PortDirection:
    INPUT = "input"
    OUTPUT = "output"


PORT_COLORS = {
    PortType.VIDEO: (255, 107, 107),
    PortType.AUDIO: (78, 205, 196),
    PortType.SUBTITLE: (255, 217, 61),
    PortType.CHAPTER: (199, 146, 234),
    PortType.ATTACHMENT: (255, 138, 101),
    PortType.SCRIPT: (108, 92, 231),
    PortType.ANY: (149, 165, 166),
}

CATEGORY_COLORS = {
    "系统": "#607D8B",
    "输入": "#4CAF50",
    "处理": "#FF9800",
    "编码": "#F44336",
    "封装": "#9C27B0",
    "输出": "#2196F3",
}

NODE_PORT_RADIUS = 5
NODE_HEADER_HEIGHT = 28
NODE_PORT_SPACING = 22
NODE_PADDING_H = 14
NODE_PADDING_V = 6
NODE_MIN_WIDTH = 160
NODE_DEFAULT_WIDTH = 180
NODE_CORNER_RADIUS = 8
