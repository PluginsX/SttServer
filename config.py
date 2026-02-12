from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """ASR 服务配置类
    
    本配置类使用 Pydantic V2 语法，通过 BaseSettings 实现配置管理
    支持从环境变量和 .env 文件加载配置
    """
    
    # 服务器配置
    host: str = "0.0.0.0"  # 服务器监听地址，0.0.0.0 表示监听所有网络接口
    port: int = 8000  # 服务器监听端口
    
    # 模型配置
    model_path: str = "paraformer-zh-streaming"  # 模型路径，支持本地路径或 ModelScope 模型名称
    model_revision: str = "v2.0.4"  # 模型版本号，对应 ModelScope 上的模型版本
    device: str = "cuda:0"  # 模型运行设备，可选值："cpu" 或 "cuda:0"（使用 GPU）
    model_dir: str = "models"  # 模型缓存目录
    
    # 模型内置功能配置（性能优化配置）
    semantic_punctuation_enabled: bool = False  # 是否启用语义标点预测（关闭以提升速度）
    max_sentence_silence: int = 200  # 句子最大静音时长（毫秒），最小值200ms以获得最快响应
    enable_punctuation_model: bool = False  # 是否启用标点模型（关闭以大幅提升速度）
    default_response_mode: str = "fast"  # 默认响应模式：fast（最快）、balanced（平衡）、accurate（准确）
    
    # 音频配置
    default_sample_rate: int = 16000  # 默认音频采样率（Hz），推荐值：16000
    default_format: str = "pcm"  # 默认音频格式，支持："pcm"（推荐）、"wav" 等
    chunk_size: int = 3200  # 音频缓冲区大小（字节），16000Hz 采样率下对应 100ms 音频
    
    # 连接配置
    max_connections: int = 10  # 最大并发连接数
    connection_timeout: int = 300  # 连接超时时间（秒），超过此时间无活动将被断开
    
    # 性能优化配置
    torch_threads: int = 4  # PyTorch线程数，建议设置为CPU核心数
    torch_num_workers: int = 2  # PyTorch数据加载工作线程数
    enable_cuda_optimization: bool = True  # 启用CUDA优化
    enable_tf32: bool = True  # 启用TensorFloat-32（Ampere及以上GPU）
    enable_cudnn_benchmark: bool = False  # 启用cuDNN benchmark（固定输入尺寸时启用）
    enable_cudnn_deterministic: bool = False  # 启用cuDNN确定性算法（影响性能但保证可重复性）
    memory_fraction: float = 0.9  # GPU内存分配比例（0.0-1.0）
    
    class Config:
        env_file = ".env"  # 环境变量文件路径
        case_sensitive = False  # 环境变量大小写不敏感


# 创建配置实例
settings = Settings()
"""全局配置实例

使用示例：
    from config import settings
    print(settings.host)
    print(settings.port)
"""

