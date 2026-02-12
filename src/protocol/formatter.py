import json
import logging
import uuid
from typing import Optional
from .types import (
    TaskStartedEvent,
    ResultGeneratedEvent,
    TaskFinishedEvent,
    SentenceInfo,
    OutputInfo,
    ResultGeneratedPayload,
    TranscriptionStartedEvent,
    TranscriptionResultChangedEvent,
    SentenceEndEvent,
    TranscriptionCompletedEvent,
    WordInfo,
)


logger = logging.getLogger(__name__)


class ProtocolFormatter:
    
    @staticmethod
    def generate_message_id() -> str:
        """生成唯一的消息ID
        
        Returns:
            32位的消息ID
        """
        return uuid.uuid4().hex
    
    @staticmethod
    def create_task_started_event(task_id: str, protocol: str = "aliyun") -> str:
        """创建任务开始事件
        
        Args:
            task_id: 任务ID
            protocol: 协议类型，可选值："aliyun" 或 "legacy"
            
        Returns:
            JSON格式的事件消息
        """
        logger.debug(f"Creating task started event for task: {task_id}, protocol: {protocol}")
        
        if protocol == "aliyun":
            # 生成符合阿里云规范的事件
            event = TranscriptionStartedEvent(
                header={
                    "message_id": ProtocolFormatter.generate_message_id(),
                    "task_id": task_id,
                    "namespace": "SpeechTranscriber",
                    "name": "TranscriptionStarted",
                    "status": 20000000,
                    "status_message": "GATEWAY|SUCCESS|Success."
                },
                payload={
                    "session_id": ProtocolFormatter.generate_message_id()
                }
            )
            logger.debug(f"Created TranscriptionStarted event for task: {task_id}")
        else:
            # 生成符合旧版规范的事件
            event = TaskStartedEvent(
                header={
                    "task_id": task_id,
                    "event": "task-started",
                    "attributes": {}
                },
                payload={}
            )
            logger.debug(f"Created legacy TaskStarted event for task: {task_id}")
        
        result = event.model_dump_json(exclude_none=True)
        logger.debug(f"Serialized task started event for task: {task_id}")
        return result
    
    @staticmethod
    def create_result_generated_event(
        task_id: str,
        text: str,
        begin_time: int,
        end_time: Optional[int] = None,
        sentence_end: bool = False,
        words: Optional[list] = None,
        duration: Optional[int] = None,
        is_final: bool = False,  # 添加此字段
        protocol: str = "aliyun",
        sentence_index: int = 1
    ) -> str:
        """创建结果生成事件
        
        Args:
            task_id: 任务ID
            text: 识别结果文本
            begin_time: 开始时间
            end_time: 结束时间
            sentence_end: 是否句子结束
            words: 词信息列表
            duration: 音频时长
            is_final: 是否最终结果
            protocol: 协议类型，可选值："aliyun" 或 "legacy"
            sentence_index: 句子索引
            
        Returns:
            JSON格式的事件消息
        """
        logger.debug(f"Creating result generated event for task: {task_id}, text: '{text}', protocol: {protocol}")
        
        if protocol == "aliyun":
            # 生成符合阿里云规范的事件
            if not sentence_end:
                # 中间结果
                event = TranscriptionResultChangedEvent(
                    header={
                        "message_id": ProtocolFormatter.generate_message_id(),
                        "task_id": task_id,
                        "namespace": "SpeechTranscriber",
                        "name": "TranscriptionResultChanged",
                        "status": 20000000,
                        "status_message": "GATEWAY|SUCCESS|Success."
                    },
                    payload={
                        "index": sentence_index,
                        "time": duration or 0,
                        "result": text,
                        "words": [
                            {
                                "text": w["text"],
                                "startTime": w["begin_time"],
                                "endTime": w["end_time"]
                            }
                            for w in words
                        ] if words else None
                    }
                )
                logger.debug(f"Created TranscriptionResultChanged event for task: {task_id}")
            else:
                # 句子结束事件
                event = SentenceEndEvent(
                    header={
                        "message_id": ProtocolFormatter.generate_message_id(),
                        "task_id": task_id,
                        "namespace": "SpeechTranscriber",
                        "name": "SentenceEnd",
                        "status": 20000000,
                        "status_message": "GATEWAY|SUCCESS|Success."
                    },
                    payload={
                        "index": sentence_index,
                        "time": duration or 0,
                        "begin_time": begin_time,
                        "result": text,
                        "words": [
                            {
                                "text": w["text"],
                                "startTime": w["begin_time"],
                                "endTime": w["end_time"]
                            }
                            for w in words
                        ] if words else None
                    }
                )
                logger.debug(f"Created SentenceEnd event for task: {task_id}")
        else:
            # 生成符合旧版规范的事件
            sentence_info = SentenceInfo(
                begin_time=begin_time,
                end_time=end_time,
                text=text,
                sentence_end=sentence_end,
                is_final=is_final,
                words=[
                    {
                        "begin_time": w["begin_time"],
                        "end_time": w["end_time"],
                        "text": w["text"]
                    }
                    for w in words
                ] if words else None
            )
            
            output_info = OutputInfo(sentence=sentence_info)
            
            payload_data = {"output": output_info.model_dump(exclude_none=True)}
            if duration is not None:
                payload_data["usage"] = {"duration": duration}
            
            payload = ResultGeneratedPayload(**payload_data)
            
            event = ResultGeneratedEvent(
                header={
                    "task_id": task_id,
                    "event": "result-generated",
                    "attributes": {}
                },
                payload=payload
            )
            logger.debug(f"Created legacy ResultGenerated event for task: {task_id}")
        
        result = event.model_dump_json(exclude_none=True)
        logger.debug(f"Serialized result generated event for task: {task_id}")
        return result
    
    @staticmethod
    def create_task_finished_event(task_id: str, protocol: str = "aliyun") -> str:
        """创建任务完成事件
        
        Args:
            task_id: 任务ID
            protocol: 协议类型，可选值："aliyun" 或 "legacy"
            
        Returns:
            JSON格式的事件消息
        """
        logger.debug(f"Creating task finished event for task: {task_id}, protocol: {protocol}")
        
        if protocol == "aliyun":
            # 生成符合阿里云规范的事件
            event = TranscriptionCompletedEvent(
                header={
                    "message_id": ProtocolFormatter.generate_message_id(),
                    "task_id": task_id,
                    "namespace": "SpeechTranscriber",
                    "name": "TranscriptionCompleted",
                    "status": 20000000,
                    "status_message": "GATEWAY|SUCCESS|Success."
                },
                payload={}
            )
            logger.debug(f"Created TranscriptionCompleted event for task: {task_id}")
        else:
            # 生成符合旧版规范的事件
            event = TaskFinishedEvent(
                header={
                    "task_id": task_id,
                    "event": "task-finished",
                    "attributes": {}
                },
                payload={}
            )
            logger.debug(f"Created legacy TaskFinished event for task: {task_id}")
        
        result = event.model_dump_json(exclude_none=True)
        logger.debug(f"Serialized task finished event for task: {task_id}")
        return result
