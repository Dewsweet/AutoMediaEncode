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
    PortType.VIDEO: (0xFF, 0x6B, 0x6B),
    PortType.AUDIO: (0x4E, 0xCD, 0xC4),
    PortType.SUBTITLE: (0xFF, 0xD9, 0x3D),
    PortType.CHAPTER: (0xC7, 0x92, 0xEA),
    PortType.ATTACHMENT: (0xFF, 0x8A, 0x65),
    PortType.SCRIPT: (0x6C, 0x5C, 0xE7),
    PortType.ANY: (0x95, 0xA5, 0xA6),
}

CATEGORY_COLORS = {
    "系统": "#607D8B",
    "输入": "#4CAF50",
    "处理": "#FF9800",
    "编码": "#F44336",
    "封装": "#9C27B0",
    "输出": "#2196F3",
}

PORT_COMPATIBILITY = {
    PortType.VIDEO: {PortType.VIDEO, PortType.ANY},
    PortType.AUDIO: {PortType.AUDIO, PortType.ANY},
    PortType.SUBTITLE: {PortType.SUBTITLE, PortType.ANY},
    PortType.CHAPTER: {PortType.CHAPTER, PortType.ANY},
    PortType.ATTACHMENT: {PortType.ATTACHMENT, PortType.ANY},
    PortType.SCRIPT: {PortType.VIDEO},
    PortType.ANY: {PortType.VIDEO, PortType.AUDIO, PortType.SUBTITLE, PortType.CHAPTER, PortType.ATTACHMENT, PortType.SCRIPT, PortType.ANY},
}

NODE_PORT_RADIUS = 5
NODE_HEADER_HEIGHT = 28
NODE_PORT_SPACING = 22
NODE_PADDING_H = 14
NODE_PADDING_V = 6
NODE_MIN_WIDTH = 160
NODE_DEFAULT_WIDTH = 180
NODE_CORNER_RADIUS = 8
