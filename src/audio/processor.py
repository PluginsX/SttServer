import numpy as np
import logging
from typing import Optional


logger = logging.getLogger(__name__)


class AudioProcessor:
    
    def __init__(self, sample_rate: int = 16000, chunk_size_ms: int = 100):
        self.sample_rate = sample_rate
        self.chunk_size_ms = chunk_size_ms
        self.chunk_size = int(sample_rate * chunk_size_ms / 1000)
        self.buffer = []
        self.total_samples = 0
    
    def add_audio(self, audio_data: bytes) -> np.ndarray:
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            self.buffer.append(audio_array)
            self.total_samples += len(audio_array)
            return audio_array
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return np.array([])
    
    def get_buffered_audio(self) -> np.ndarray:
        if not self.buffer:
            return np.array([])
        
        result = np.concatenate(self.buffer)
        self.buffer = []
        return result
    
    def get_chunk_audio(self) -> np.ndarray:
        if not self.buffer:
            return np.array([])
        
        result = np.concatenate(self.buffer)
        
        # 只有当累积的音频数据达到指定大小时才返回处理块
        # 这样可以避免过于频繁的模型调用
        if len(result) >= self.chunk_size:
            chunk = result[:self.chunk_size]
            self.buffer = [result[self.chunk_size:]]
            return chunk
        else:
            # 如果累积的数据不足一个块大小，则不返回任何数据
            # 等待更多音频数据到达
            return np.array([])
    
    def clear_buffer(self):
        self.buffer = []
        self.total_samples = 0
    
    def get_duration_ms(self) -> int:
        return int(self.total_samples * 1000 / self.sample_rate)
