# coding: utf-8
from typing import TypedDict, List, Dict, Any, Literal, Union

class RecodeStates(TypedDict):
    """重编码任务的状态配置"""
    video_state: Dict[str, Any]
    audio_state: Dict[str, Any]
    image_state: Dict[str, Any]
    subtitle_state: Dict[str, Any]
    output_state: Dict[str, Any]

class RecodePayload(TypedDict):
    """重编码任务的 Payload 结构"""
    task_id: str
    type: Literal["Recode"]
    files: List[str]
    states: RecodeStates

class DemuxStates(TypedDict):
    """抽流流任务的状态配置"""
    tracks_state: Dict[str, List[Dict[str, Any]]] # filepath -> list of selected tracks
    option_state: Dict[str, Any]
    output_state: Dict[str, Any]

class DemuxPayload(TypedDict):
    """抽流流任务的 Payload 结构"""
    task_id: str
    type: Literal["Demux"]
    files: List[str]
    states: DemuxStates

# 未来如果加入抽流、混流任务，可以在下方继续定义，并加入到 TaskPayload 联合类型中
# class MuxPayload(TypedDict): ...

# 导出一个通用类型供后续 TaskManager 使用
TaskPayload = Union[RecodePayload, DemuxPayload] 
