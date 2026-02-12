import json
import logging
from typing import Union, Optional
from .types import (
    RunTaskCommand,
    FinishTaskCommand,
    StartTranscriptionCommand,
    StopTranscriptionCommand,
)


logger = logging.getLogger(__name__)


class ProtocolParser:
    
    @staticmethod
    def parse_command(message: str) -> Optional[Union[RunTaskCommand, FinishTaskCommand, dict]]:
        try:
            data = json.loads(message)
            
            # 检查是否为阿里云WebSocket API规范的指令
            header = data.get("header", {})
            namespace = header.get("namespace", "")
            name = header.get("name", "")
            
            if namespace == "SpeechTranscriber":
                if name == "StartTranscription":
                    # 解析阿里云StartTranscription指令
                    try:
                        command = StartTranscriptionCommand(**data)
                        # 返回字典格式，包含所有必要的信息
                        return {
                            "type": "StartTranscription",
                            "header": command.header.model_dump(),
                            "payload": command.payload.model_dump(),
                            "task_id": command.header.task_id,
                            "message_id": command.header.message_id,
                            "appkey": command.header.appkey,
                        }
                    except Exception as e:
                        logger.error(f"Failed to parse StartTranscription command: {e}")
                        return None
                elif name == "StopTranscription":
                    # 解析阿里云StopTranscription指令
                    try:
                        command = StopTranscriptionCommand(**data)
                        # 返回字典格式，包含所有必要的信息
                        return {
                            "type": "StopTranscription",
                            "header": command.header.model_dump(),
                            "payload": command.payload.model_dump() if command.payload else {},
                            "task_id": command.header.task_id,
                            "message_id": command.header.message_id,
                        }
                    except Exception as e:
                        logger.error(f"Failed to parse StopTranscription command: {e}")
                        return None
            
            # 检查是否为旧版指令
            action = header.get("action", "")
            if action == "run-task":
                return RunTaskCommand(**data)
            elif action == "finish-task":
                return FinishTaskCommand(**data)
            else:
                logger.warning(f"Unknown action: {action}")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return None
        except Exception as e:
            logger.error(f"Parse command error: {e}")
            return None
    
    @staticmethod
    def validate_task_id(task_id: str) -> bool:
        if not task_id:
            return False
        if len(task_id) < 32:
            return False
        return True
