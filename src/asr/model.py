import logging
import os
from funasr import AutoModel
from typing import Dict, Any, Optional
import numpy as np


logger = logging.getLogger(__name__)


class ASRModel:
    
    def __init__(self, model_path: str = "paraformer-zh-streaming", model_revision: str = "v2.0.4", device: str = "cpu", semantic_punctuation_enabled: bool = True, max_sentence_silence: int = 800, model_dir: str = "models", enable_punctuation_model: bool = False, default_response_mode: str = "fast"):
        self.model_path = model_path
        self.model_revision = model_revision
        self.device = device
        self.semantic_punctuation_enabled = semantic_punctuation_enabled
        self.max_sentence_silence = max_sentence_silence
        self.model_dir = model_dir
        self.enable_punctuation_model = enable_punctuation_model
        self.default_response_mode = default_response_mode
        self.model = None
        self._load_model()
    
    def _load_model(self):
        try:
            logger.info(f"Loading ASR model: {self.model_path} (revision: {self.model_revision})")
            logger.info(f"Semantic punctuation: {self.semantic_punctuation_enabled}")
            logger.info(f"Max sentence silence: {self.max_sentence_silence}ms")
            logger.info(f"Punctuation model: {self.enable_punctuation_model}")
            logger.info(f"Default response mode: {self.default_response_mode}")
            
            # 正确加载模型，包含标点模型
            # 确保model_dir是绝对路径
            if not os.path.isabs(self.model_dir):
                model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), self.model_dir)
            else:
                model_dir = self.model_dir
            
            # 确保模型目录存在
            os.makedirs(model_dir, exist_ok=True)
            logger.info(f"Using model directory: {model_dir}")
            
            # 设置环境变量，确保modelscope使用我们指定的目录
            os.environ['MODELSCOPE_CACHE'] = model_dir
            logger.info(f"Set MODELSCOPE_CACHE to: {os.environ.get('MODELSCOPE_CACHE')}")
            
            # 正确加载模型，包含标点模型
            # 尝试使用具体的模型路径
            if self.model_path == "paraformer-zh-streaming":
                # 使用完整的模型路径
                model_path = "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online"
                logger.info(f"Using full model path: {model_path}")
            else:
                model_path = self.model_path
            
            # 根据配置决定是否加载标点模型
            if self.enable_punctuation_model:
                self.model = AutoModel(
                    model=model_path,
                    model_revision=self.model_revision,
                    device=self.device,
                    punc_model="ct-punc",
                    disable_update=True,
                    trust_remote_code=False
                )
                logger.info("ASR model loaded successfully with punctuation model")
            else:
                self.model = AutoModel(
                    model=model_path,
                    model_revision=self.model_revision,
                    device=self.device,
                    disable_update=True,
                    trust_remote_code=False
                )
                logger.info("ASR model loaded successfully without punctuation model (optimized for speed)")
        except Exception as e:
            logger.error(f"Failed to load ASR model: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def recognize(self, audio_data: np.ndarray, cache: Optional[Dict[str, Any]] = None, is_final: bool = False, 
                  enable_punctuation: bool = True, response_mode: str = "balanced") -> Dict[str, Any]:
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        if cache is None:
            cache = {}
        
        try:
            logger.debug(f"Recognizing audio: shape={audio_data.shape}, dtype={audio_data.dtype}, is_final={is_final}, response_mode={response_mode}")
            
            # 根据响应模式选择不同的chunk_size
            if response_mode == "fast":
                chunk_size = [0, 3, 1]  # 180ms出字，60ms前瞻
                logger.debug("Using fast response mode: chunk_size=[0, 3, 1]")
            elif response_mode == "accurate":
                chunk_size = [0, 8, 4]  # 480ms出字，240ms前瞻
                logger.debug("Using accurate response mode: chunk_size=[0, 8, 4]")
            else:  # balanced
                chunk_size = [0, 5, 2]  # 300ms出字，120ms前瞻
                logger.debug("Using balanced response mode: chunk_size=[0, 5, 2]")
            
            # 正确的 FunASR 流式推理参数
            logger.debug(f"Calling model.generate with chunk_size={chunk_size}, max_sentence_silence={self.max_sentence_silence}, semantic_punctuation_enabled={self.semantic_punctuation_enabled}")
            result = self.model.generate(
                input=audio_data,
                cache=cache,
                is_final=is_final,
                chunk_size=chunk_size,
                vad_kwargs={
                    "max_end_silence_time": self.max_sentence_silence,
                    "max_single_segment_time": 60000
                },
                semantic_punctuation_enabled=self.semantic_punctuation_enabled,
                disable_pbar=True
            )
            
            logger.debug(f"Model result: {result}")
            
            if result and len(result) > 0:
                text = result[0].get("text", "")
                logger.debug(f"Recognized text: '{text}'")
                
                # 检查是否为最终结果
                is_final_result = result[0].get("is_final", is_final)
                
                logger.debug(f"Recognition completed: text='{text}', is_final={is_final_result}")
                return {
                    "text": text,
                    "cache": cache,
                    "timestamp": result[0].get("timestamp", []),
                    "sentence_info": result[0].get("sentence_info", []),
                    "is_partial": not is_final_result,
                    "is_final": is_final_result
                }
            else:
                logger.debug("No result from model")
                return {
                    "text": "",
                    "cache": cache,
                    "timestamp": [],
                    "sentence_info": [],
                    "is_partial": not is_final,
                    "is_final": is_final
                }
        except Exception as e:
            logger.error(f"Recognition error: {e}", exc_info=True)
            return {
                "text": "",
                "cache": cache,
                "timestamp": [],
                "sentence_info": [],
                "is_partial": not is_final,
                "is_final": is_final
            }
    
    def finalize(self, cache: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        if cache is None:
            cache = {}
        
        try:
            result = self.model.generate(
                input=np.array([]),
                cache=cache,
                is_final=True,
                chunk_size=[0, 10, 5],  # [chunk_size, chunk_stride, encoder_chunk_look_back]
                vad_kwargs={
                    "max_end_silence_time": self.max_sentence_silence,
                    "max_single_segment_time": 60000
                },
                semantic_punctuation_enabled=self.semantic_punctuation_enabled,
                disable_pbar=True
            )
            
            if result and len(result) > 0:
                text = result[0].get("text", "")
                is_final_result = result[0].get("is_final", True)
                return {
                    "text": text,
                    "cache": cache,
                    "timestamp": result[0].get("timestamp", []),
                    "sentence_info": result[0].get("sentence_info", []),
                    "is_partial": not is_final_result,
                    "is_final": is_final_result
                }
            else:
                return {
                    "text": "",
                    "cache": cache,
                    "timestamp": [],
                    "sentence_info": [],
                    "is_partial": False,
                    "is_final": True
                }
        except Exception as e:
            logger.error(f"Finalization error: {e}")
            return {
                "text": "",
                "cache": cache,
                "timestamp": [],
                "sentence_info": [],
                "is_partial": False,
                "is_final": True
            }
