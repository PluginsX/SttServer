import logging
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from typing import Optional
import numpy as np

from ..protocol.parser import ProtocolParser
from ..protocol.formatter import ProtocolFormatter
from ..protocol.types import RunTaskCommand, FinishTaskCommand
from ..audio.processor import AudioProcessor
from ..asr.model import ASRModel
from ..state.session import SessionManager, SessionState


logger = logging.getLogger(__name__)


class WebSocketHandler:
    
    def __init__(self, asr_model: ASRModel, session_manager: SessionManager):
        self.asr_model = asr_model
        self.session_manager = session_manager
        self.parser = ProtocolParser()
        self.formatter = ProtocolFormatter()
    
    async def handle_connection(self, websocket: WebSocket):
        await websocket.accept()
        client_info = f"{websocket.client.host}:{websocket.client.port}"
        logger.info(f"WebSocket connection established: {client_info}")
        
        session: Optional[SessionState] = None
        audio_processor: Optional[AudioProcessor] = None
        protocol: str = "aliyun"  # 默认使用阿里云协议
        
        try:
            logger.info(f"Starting WebSocket message loop for client: {client_info}")
            while True:
                message = await websocket.receive()
                logger.debug(f"Received message from {client_info}: {list(message.keys())}")
                
                if "text" in message:
                    logger.debug(f"Processing text message: {message['text'][:100]}...")  # 只记录前100字符
                    command = self.parser.parse_command(message["text"])
                    logger.debug(f"Parsed command type: {type(command).__name__}")
                    
                    if isinstance(command, RunTaskCommand):
                        # 处理旧版run-task命令
                        logger.info(f"Handling legacy run-task command for client: {client_info}")
                        session = await self._handle_run_task(websocket, command)
                        if session:
                            audio_processor = AudioProcessor(session.sample_rate)
                            await websocket.send_text(self.formatter.create_task_started_event(
                                command.header.task_id, 
                                protocol="legacy"
                            ))
                            logger.info(f"Sent task-started event for legacy protocol, task: {command.header.task_id}")
                            protocol = "legacy"
                    
                    elif isinstance(command, FinishTaskCommand):
                        # 处理旧版finish-task命令
                        logger.info(f"Handling legacy finish-task command for client: {client_info}, task: {command.header.task_id}")
                        if session:
                            await self._handle_finish_task(websocket, command, session, audio_processor, protocol="legacy")
                            session = None
                            audio_processor = None
                            logger.info(f"Legacy task completed, task: {command.header.task_id}")
                        # 不跳出循环，继续等待客户端的下一条消息
                    
                    elif isinstance(command, dict) and command.get("type") == "StartTranscription":
                        # 处理阿里云StartTranscription命令
                        logger.info(f"Handling aliyun StartTranscription command for client: {client_info}, task: {command['task_id']}")
                        session = await self._handle_start_transcription(websocket, command)
                        if session:
                            audio_processor = AudioProcessor(session.sample_rate)
                            await websocket.send_text(self.formatter.create_task_started_event(
                                command["task_id"], 
                                protocol="aliyun"
                            ))
                            logger.info(f"Sent TranscriptionStarted event for aliyun protocol, task: {command['task_id']}")
                            protocol = "aliyun"
                    
                    elif isinstance(command, dict) and command.get("type") == "StopTranscription":
                        # 处理阿里云StopTranscription命令
                        logger.info(f"Handling aliyun StopTranscription command for client: {client_info}, task: {command['task_id']}")
                        if session:
                            await self._handle_stop_transcription(websocket, command, session, audio_processor, protocol="aliyun")
                            session = None
                            audio_processor = None
                            logger.info(f"Aliyun transcription stopped, task: {command['task_id']}")
                        # 不主动关闭WebSocket连接，让客户端决定何时关闭
                        # 不跳出循环，继续等待客户端的下一条消息
                    
                    else:
                        logger.warning(f"Unknown command type from {client_info}: {type(command)}, command: {command}")
                
                elif "bytes" in message:
                    if session and audio_processor:
                        logger.debug(f"Processing audio data: {len(message['bytes'])} bytes for task: {session.task_id}")
                        await self.handle_audio_data(websocket, message["bytes"], session, audio_processor, protocol)
                    else:
                        logger.warning(f"Ignoring audio data from {client_info}: no active session")
        
        except WebSocketDisconnect as e:
            logger.info(f"WebSocket disconnected: {client_info}, reason: {e.code} - {e.reason}")
        except RuntimeError as e:
            if "Cannot call 'receive' once a disconnect message has been received" in str(e):
                logger.info(f"WebSocket already disconnected: {client_info}")
            else:
                logger.error(f"WebSocket error for {client_info}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"WebSocket error for {client_info}: {e}", exc_info=True)
        finally:
            if session:
                task_id = session.task_id
                logger.info(f"Cleaning up session for {client_info}, task: {task_id}")
                self.session_manager.remove_session(task_id)
            logger.info(f"WebSocket connection closed for {client_info}")
    
    async def _handle_run_task(self, websocket: WebSocket, command: RunTaskCommand) -> Optional[SessionState]:
        task_id = command.header.task_id
        parameters = command.payload.parameters
        
        if not self.parser.validate_task_id(task_id):
            logger.warning(f"Invalid task_id: {task_id}")
            return None
        
        session = self.session_manager.create_session(
            task_id,
            sample_rate=parameters.sample_rate,
            punctuation_enabled=parameters.punctuation_prediction_enabled,
            response_mode=parameters.response_mode
        )
        session.start()
        
        logger.info(f"Task started: {task_id}, punctuation_enabled={parameters.punctuation_prediction_enabled}, response_mode={parameters.response_mode}")
        
        return session
    
    async def _handle_start_transcription(self, websocket: WebSocket, command: dict) -> Optional[SessionState]:
        task_id = command["task_id"]
        payload = command.get("payload", {})
        
        logger.info(f"Processing StartTranscription command for task: {task_id}")
        logger.info(f"Request payload: {payload}")
        
        if not self.parser.validate_task_id(task_id):
            logger.warning(f"Invalid task_id: {task_id}")
            return None
        
        sample_rate = payload.get("sample_rate", 16000)
        enable_punctuation_prediction = payload.get("enable_punctuation_prediction", False)
        enable_inverse_text_normalization = payload.get("enable_inverse_text_normalization", False)
        enable_disfluency_removal = payload.get("enable_disfluency_removal", False)
        max_sentence_silence = payload.get("max_sentence_silence", 200)
        enable_semantic_sentence_detection = payload.get("enable_semantic_sentence_detection", False)
        response_mode = payload.get("response_mode", "fast")  # 默认使用fast模式以获得最快响应
        
        logger.info(f"Creating session with parameters: "
                   f"sample_rate={sample_rate}, "
                   f"punctuation_enabled={enable_punctuation_prediction}, "
                   f"inverse_text_normalization_enabled={enable_inverse_text_normalization}, "
                   f"disfluency_removal_enabled={enable_disfluency_removal}, "
                   f"max_sentence_silence={max_sentence_silence}, "
                   f"semantic_sentence_detection={enable_semantic_sentence_detection}, "
                   f"response_mode={response_mode}")
        
        session = self.session_manager.create_session(
            task_id,
            sample_rate=sample_rate,
            punctuation_enabled=enable_punctuation_prediction,
            response_mode=response_mode
        )
        session.start()
        
        logger.info(f"Transcription started successfully: {task_id}")
        
        return session
    
    async def _handle_finish_task(
        self, 
        websocket: WebSocket, 
        command: FinishTaskCommand, 
        session: SessionState,
        audio_processor: Optional[AudioProcessor],
        protocol: str = "legacy"
    ):
        task_id = command.header.task_id
        
        if session is None:
            logger.warning(f"No session found for task: {task_id}")
            return
        
        session.finish()
        
        # 先发送task-finished事件，符合阿里云规范，确保客户端能立即收到停止响应
        await websocket.send_text(self.formatter.create_task_finished_event(task_id, protocol=protocol))
        
        # 然后异步处理最终的音频数据和结果
        async def process_final_audio():
            if audio_processor:
                audio_data = audio_processor.get_buffered_audio()
                if len(audio_data) > 0:
                    try:
                        result = self.asr_model.finalize(session.cache)
                        if result["text"]:
                            # 注意：按照阿里云规范，任务结束后不应该再发送结果事件
                            # 这里我们只记录日志，不发送额外的结果
                            logger.info(f"Final result for task {task_id}: {result['text']}")
                    except Exception as e:
                        logger.error(f"Error processing final audio: {e}")
            
            self.session_manager.remove_session(task_id)
            logger.info(f"Task finished: {task_id}")
        
        # 异步执行，不阻塞WebSocket连接
        asyncio.create_task(process_final_audio())
    
    async def _handle_stop_transcription(
        self, 
        websocket: WebSocket, 
        command: dict, 
        session: SessionState,
        audio_processor: Optional[AudioProcessor],
        protocol: str = "aliyun"
    ):
        task_id = command["task_id"]
        
        if session is None:
            logger.warning(f"No session found for task: {task_id}")
            return
        
        session.finish()
        
        # 先发送TranscriptionCompleted事件，符合阿里云规范，确保客户端能立即收到停止响应
        await websocket.send_text(self.formatter.create_task_finished_event(task_id, protocol=protocol))
        
        # 立即删除会话，避免后续访问
        self.session_manager.remove_session(task_id)
        logger.info(f"Transcription stopped: {task_id}")
        
        # 同步处理最终的音频数据和结果，避免异步任务导致的阻塞
        if audio_processor:
            audio_data = audio_processor.get_buffered_audio()
            if len(audio_data) > 0:
                try:
                    result = self.asr_model.finalize(session.cache)
                    if result["text"]:
                        # 注意：按照阿里云规范，任务结束后不应该再发送结果事件
                        # 这里我们只记录日志，不发送额外的结果
                        logger.info(f"Final result for task {task_id}: {result['text']}")
                except Exception as e:
                    logger.error(f"Error processing final audio: {e}")
        
        logger.info(f"Final audio processing completed for task {task_id}")
    
    async def handle_audio_data(
        self, 
        websocket: WebSocket, 
        audio_data: bytes, 
        session: SessionState,
        audio_processor: AudioProcessor,
        protocol: str = "aliyun"
    ):
        if not session.is_running():
            logger.warning(f"Session not running for task {session.task_id}, ignoring audio data")
            return
        
        logger.debug(f"Received audio data: {len(audio_data)} bytes for task {session.task_id}")
        audio_processor.add_audio(audio_data)
        
        # 使用模型内置的 VAD 和智能缓冲
        chunk_audio = audio_processor.get_chunk_audio()
        if len(chunk_audio) == 0:
            logger.debug(f"No audio chunk ready for processing, task: {session.task_id}")
            return
        
        logger.debug(f"Processing audio chunk: {len(chunk_audio)} samples for task: {session.task_id}")
        result = self.asr_model.recognize(
            chunk_audio, 
            session.cache, 
            is_final=False,
            enable_punctuation=session.punctuation_enabled,
            response_mode=session.response_mode
        )
        
        logger.debug(f"Recognition result for task {session.task_id}: text='{result['text']}', is_final={result.get('is_final', False)}")
        
        if result["text"] and result["text"] != session.last_text:
            logger.info(f"New recognition result for task {session.task_id}: '{result['text']}' (is_final: {result.get('is_final', False)})")
            session.update_result(result["text"], result["timestamp"])
            
            logger.debug(f"Sending result generated event for task: {session.task_id}")
            await websocket.send_text(
                self.formatter.create_result_generated_event(
                    task_id=session.task_id,
                    text=result["text"],
                    begin_time=0,
                    end_time=session.get_duration_ms(),
                    sentence_end=result.get("is_final", False),
                    is_final=result.get("is_final", False),
                    protocol=protocol,
                    sentence_index=session.sentence_count
                )
            )
            logger.debug(f"Sent result generated event for task: {session.task_id}")
