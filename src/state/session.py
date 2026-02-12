import time
import logging
from typing import Optional, Dict, Any
from enum import Enum


class SessionStateEnum(Enum):
    IDLE = "idle"
    RUNNING = "running"
    FINISHED = "finished"


logger = logging.getLogger(__name__)


class SessionState:
    
    def __init__(self, task_id: str, sample_rate: int = 16000, punctuation_enabled: bool = True, response_mode: str = "balanced"):
        self.task_id = task_id
        self.state = SessionStateEnum.IDLE
        self.sample_rate = sample_rate
        self.punctuation_enabled = punctuation_enabled
        self.response_mode = response_mode
        self.cache = {}
        self.last_text = ""
        self.last_timestamp = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.total_duration_ms = 0
        self.sentence_count = 0
    
    def start(self):
        self.state = SessionStateEnum.RUNNING
        self.start_time = time.time()
        logger.info(f"Session started: {self.task_id}, sample_rate={self.sample_rate}, punctuation_enabled={self.punctuation_enabled}, response_mode={self.response_mode}")
    
    def finish(self):
        self.state = SessionStateEnum.FINISHED
        self.end_time = time.time()
        duration = self.get_duration_ms()
        logger.info(f"Session finished: {self.task_id}, total_duration={duration}ms, sentences_processed={self.sentence_count}")
    
    def is_running(self) -> bool:
        return self.state == SessionStateEnum.RUNNING
    
    def is_finished(self) -> bool:
        return self.state == SessionStateEnum.FINISHED
    
    def update_result(self, text: str, timestamp: list):
        if text != self.last_text:
            self.last_text = text
            self.last_timestamp = timestamp
            self.sentence_count += 1
    
    def get_duration_ms(self) -> int:
        if self.start_time is None:
            return 0
        end = self.end_time or time.time()
        return int((end - self.start_time) * 1000)
    
    def reset(self):
        self.state = SessionStateEnum.IDLE
        self.cache = {}
        self.last_text = ""
        self.last_timestamp = []
        self.start_time = None
        self.end_time = None
        self.total_duration_ms = 0
        self.sentence_count = 0


class SessionManager:
    
    def __init__(self):
        self.sessions: Dict[str, SessionState] = {}
    
    def create_session(self, task_id: str, sample_rate: int = 16000, punctuation_enabled: bool = True, response_mode: str = "balanced") -> SessionState:
        if task_id in self.sessions:
            logger.warning(f"Session {task_id} already exists, replacing. Previous session state: {self.sessions[task_id].state}")
        
        session = SessionState(task_id, sample_rate, punctuation_enabled, response_mode)
        self.sessions[task_id] = session
        logger.info(f"Created new session: {task_id}, sample_rate={sample_rate}, punctuation_enabled={punctuation_enabled}, response_mode={response_mode}")
        logger.info(f"Active sessions count: {len(self.sessions)}")
        return session
    
    def get_session(self, task_id: str) -> Optional[SessionState]:
        return self.sessions.get(task_id)
    
    def remove_session(self, task_id: str) -> bool:
        if task_id in self.sessions:
            session = self.sessions[task_id]
            del self.sessions[task_id]
            logger.info(f"Removed session: {task_id}, final_state={session.state.value}, total_duration={session.get_duration_ms()}ms")
            logger.info(f"Remaining active sessions count: {len(self.sessions)}")
            return True
        else:
            logger.warning(f"Attempted to remove non-existent session: {task_id}")
            return False
    
    def get_all_sessions(self) -> Dict[str, SessionState]:
        return self.sessions.copy()
    
    def get_active_sessions(self) -> Dict[str, SessionState]:
        return {
            task_id: session 
            for task_id, session in self.sessions.items() 
            if session.is_running()
        }
