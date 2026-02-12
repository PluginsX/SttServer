import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from src.asr.model import ASRModel
from src.state.session import SessionManager
from src.websocket.handler import WebSocketHandler


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def optimize_pytorch_performance():
    """优化PyTorch性能配置"""
    try:
        import torch
        
        # 设置PyTorch线程数
        torch.set_num_threads(settings.torch_threads)
        logger.info(f"Set PyTorch threads to: {settings.torch_threads}")
        
        # 设置PyTorch工作线程数
        if hasattr(torch, 'set_num_interop_threads'):
            torch.set_num_interop_threads(settings.torch_num_workers)
            logger.info(f"Set PyTorch interop threads to: {settings.torch_num_workers}")
        
        # CUDA优化
        if torch.cuda.is_available() and settings.enable_cuda_optimization:
            logger.info("CUDA is available, applying optimizations...")
            
            # 启用TensorFloat-32（Ampere及以上GPU）
            if settings.enable_tf32:
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
                logger.info("Enabled TensorFloat-32 for faster computation")
            
            # 启用cuDNN benchmark（固定输入尺寸时启用）
            if settings.enable_cudnn_benchmark:
                torch.backends.cudnn.benchmark = True
                logger.info("Enabled cuDNN benchmark mode")
            
            # 启用cuDNN确定性算法
            if settings.enable_cudnn_deterministic:
                torch.backends.cudnn.deterministic = True
                logger.info("Enabled cuDNN deterministic mode")
            
            # 设置GPU内存分配比例
            if 0.0 < settings.memory_fraction <= 1.0:
                torch.cuda.set_per_process_memory_fraction(settings.memory_fraction)
                logger.info(f"Set GPU memory fraction to: {settings.memory_fraction}")
            
            # 显示CUDA设备信息
            device_count = torch.cuda.device_count()
            current_device = torch.cuda.current_device()
            device_name = torch.cuda.get_device_name(current_device)
            logger.info(f"CUDA devices: {device_count}, current: {device_name}")
            
            # 显示GPU内存信息
            total_memory = torch.cuda.get_device_properties(current_device).total_memory / (1024**3)
            logger.info(f"Total GPU memory: {total_memory:.2f} GB")
        else:
            logger.info("CUDA is not available or optimization is disabled")
            
    except ImportError:
        logger.warning("PyTorch not available, skipping performance optimization")
    except Exception as e:
        logger.warning(f"Failed to apply PyTorch optimizations: {e}")


asr_model = None
session_manager = None
ws_handler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global asr_model, session_manager, ws_handler
    
    logger.info("Starting ASR Server...")
    
    # 应用PyTorch性能优化
    optimize_pytorch_performance()
    
    try:
        asr_model = ASRModel(
            model_path=settings.model_path,
            model_revision=settings.model_revision,
            device=settings.device,
            semantic_punctuation_enabled=settings.semantic_punctuation_enabled,
            max_sentence_silence=settings.max_sentence_silence,
            model_dir=settings.model_dir,
            enable_punctuation_model=settings.enable_punctuation_model,
            default_response_mode=settings.default_response_mode
        )
        logger.info("ASR model loaded successfully with performance optimizations")
    except Exception as e:
        logger.error(f"Failed to load ASR model: {e}")
        raise
    
    session_manager = SessionManager()
    ws_handler = WebSocketHandler(asr_model, session_manager)
    
    logger.info("ASR Server started successfully")
    
    yield
    
    logger.info("Shutting down ASR Server...")


app = FastAPI(
    title="ASR Server",
    description="Real-time Speech Recognition Server compatible with Alibaba Cloud DashScope WebSocket API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "service": "ASR Server",
        "version": "1.0.0",
        "status": "running",
        "model": settings.model_path
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_handler.handle_connection(websocket)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn_config = {
        "host": settings.host,
        "port": settings.port,
        "reload": True,
        "workers": 1,  # 使用单个worker，因为模型是单例的
        "log_level": "info",
        "access_log": True,
        "timeout_keep_alive": 300,
        "timeout_graceful_shutdown": 30,
        "limit_concurrency": 20,  # 提高并发限制
        "limit_max_requests": 10000,  # 每个worker处理的最大请求数
        "backlog": 2048,  # 增加backlog队列大小
    }
    
    logger.info(f"Starting ASR Server with optimized configuration: {uvicorn_config}")
    uvicorn.run("main:app", **uvicorn_config)
