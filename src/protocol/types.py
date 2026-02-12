from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# 阿里云WebSocket API规范的指令类型
class StartTranscriptionHeader(BaseModel):
    message_id: str
    task_id: str
    namespace: str = Field(default="SpeechTranscriber")
    name: str = Field(default="StartTranscription")
    appkey: Optional[str] = Field(default=None)


class StartTranscriptionPayload(BaseModel):
    format: str = Field(default="pcm")
    sample_rate: int = Field(default=16000)
    enable_intermediate_result: bool = Field(default=False)
    enable_punctuation_prediction: bool = Field(default=False)
    enable_inverse_text_normalization: bool = Field(default=False)
    customization_id: Optional[str] = Field(default=None)
    vocabulary_id: Optional[str] = Field(default=None)
    max_sentence_silence: int = Field(default=800)
    enable_words: bool = Field(default=False)
    disfluency: bool = Field(default=False)
    speech_noise_threshold: Optional[float] = Field(default=None)
    enable_semantic_sentence_detection: bool = Field(default=False)


class StartTranscriptionCommand(BaseModel):
    header: StartTranscriptionHeader
    payload: StartTranscriptionPayload


class StopTranscriptionHeader(BaseModel):
    message_id: str
    task_id: str
    namespace: str = Field(default="SpeechTranscriber")
    name: str = Field(default="StopTranscription")
    appkey: Optional[str] = Field(default=None)


class StopTranscriptionPayload(BaseModel):
    pass


class StopTranscriptionCommand(BaseModel):
    header: StopTranscriptionHeader
    payload: Optional[StopTranscriptionPayload] = Field(default=None)


# 阿里云WebSocket API规范的事件类型
class TranscriptionStartedHeader(BaseModel):
    message_id: str
    task_id: str
    namespace: str = Field(default="SpeechTranscriber")
    name: str = Field(default="TranscriptionStarted")
    status: int = Field(default=20000000)
    status_message: str = Field(default="GATEWAY|SUCCESS|Success.")


class TranscriptionStartedPayload(BaseModel):
    session_id: str


class TranscriptionStartedEvent(BaseModel):
    header: TranscriptionStartedHeader
    payload: TranscriptionStartedPayload


class TranscriptionResultChangedHeader(BaseModel):
    message_id: str
    task_id: str
    namespace: str = Field(default="SpeechTranscriber")
    name: str = Field(default="TranscriptionResultChanged")
    status: int = Field(default=20000000)
    status_message: str = Field(default="GATEWAY|SUCCESS|Success.")


class WordInfo(BaseModel):
    text: str
    startTime: int
    endTime: int


class TranscriptionResultChangedPayload(BaseModel):
    index: int
    time: int
    result: str
    words: Optional[List[WordInfo]] = Field(default=None)


class TranscriptionResultChangedEvent(BaseModel):
    header: TranscriptionResultChangedHeader
    payload: TranscriptionResultChangedPayload


class SentenceEndHeader(BaseModel):
    message_id: str
    task_id: str
    namespace: str = Field(default="SpeechTranscriber")
    name: str = Field(default="SentenceEnd")
    status: int = Field(default=20000000)
    status_message: str = Field(default="GATEWAY|SUCCESS|Success.")


class StashResult(BaseModel):
    sentenceId: int
    beginTime: int
    text: str
    currentTime: int


class SentenceEndPayload(BaseModel):
    index: int
    time: int
    begin_time: int
    result: str
    confidence: Optional[float] = Field(default=None)
    words: Optional[List[WordInfo]] = Field(default=None)
    status: Optional[int] = Field(default=20000000)
    stash_result: Optional[StashResult] = Field(default=None)


class SentenceEndEvent(BaseModel):
    header: SentenceEndHeader
    payload: SentenceEndPayload


class TranscriptionCompletedHeader(BaseModel):
    message_id: str
    task_id: str
    namespace: str = Field(default="SpeechTranscriber")
    name: str = Field(default="TranscriptionCompleted")
    status: int = Field(default=20000000)
    status_message: str = Field(default="GATEWAY|SUCCESS|Success.")


class TranscriptionCompletedPayload(BaseModel):
    pass


class TranscriptionCompletedEvent(BaseModel):
    header: TranscriptionCompletedHeader
    payload: Optional[TranscriptionCompletedPayload] = Field(default=None)


# 兼容旧版本的类型定义（用于向后兼容）
class RunTaskHeader(BaseModel):
    action: str = Field(default="run-task")
    task_id: str
    streaming: str = Field(default="duplex")


class RunTaskParameters(BaseModel):
    format: str = Field(default="pcm")
    sample_rate: int = Field(default=16000)
    language_hints: Optional[List[str]] = Field(default=None)
    punctuation_prediction_enabled: bool = Field(default=True)
    inverse_text_normalization_enabled: bool = Field(default=True)
    response_mode: str = Field(default="balanced")


class RunTaskPayload(BaseModel):
    task_group: str = Field(default="audio")
    task: str = Field(default="asr")
    function: str = Field(default="recognition")
    model: str = Field(default="paraformer-realtime-v2")
    parameters: RunTaskParameters
    input: Dict[str, Any] = Field(default_factory=dict)


class RunTaskCommand(BaseModel):
    header: RunTaskHeader
    payload: RunTaskPayload


class FinishTaskHeader(BaseModel):
    action: str = Field(default="finish-task")
    task_id: str
    streaming: str = Field(default="duplex")


class FinishTaskPayload(BaseModel):
    input: Dict[str, Any] = Field(default_factory=dict)


class FinishTaskCommand(BaseModel):
    header: FinishTaskHeader
    payload: FinishTaskPayload


class TaskStartedHeader(BaseModel):
    task_id: str
    event: str = Field(default="task-started")
    attributes: Dict[str, Any] = Field(default_factory=dict)


class TaskStartedEvent(BaseModel):
    header: TaskStartedHeader
    payload: Dict[str, Any] = Field(default_factory=dict)


class LegacyWordInfo(BaseModel):
    begin_time: int
    end_time: int
    text: str
    punctuation: str = Field(default="")


class SentenceInfo(BaseModel):
    begin_time: int
    end_time: Optional[int]
    text: str
    sentence_end: bool
    is_final: bool = Field(default=False)
    words: Optional[List[LegacyWordInfo]] = Field(default=None)


class UsageInfo(BaseModel):
    duration: int


class ResultGeneratedHeader(BaseModel):
    task_id: str
    event: str = Field(default="result-generated")
    attributes: Dict[str, Any] = Field(default_factory=dict)


class OutputInfo(BaseModel):
    sentence: SentenceInfo


class ResultGeneratedPayload(BaseModel):
    output: OutputInfo
    usage: Optional[UsageInfo] = Field(default=None)


class ResultGeneratedEvent(BaseModel):
    header: ResultGeneratedHeader
    payload: ResultGeneratedPayload


class TaskFinishedHeader(BaseModel):
    task_id: str
    event: str = Field(default="task-finished")
    attributes: Dict[str, Any] = Field(default_factory=dict)


class TaskFinishedEvent(BaseModel):
    header: TaskFinishedHeader
    payload: Dict[str, Any] = Field(default_factory=dict)
