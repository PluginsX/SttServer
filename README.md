# ASR Server

实时语音识别服务，兼容阿里云 DashScope WebSocket API 协议。

## 功能特性

- 支持中文普通话实时语音识别
- 100% 兼容阿里云 DashScope WebSocket API 协议
- 基于 FunASR paraformer-zh-streaming 模型
- FastAPI + WebSocket 架构
- 支持流式音频输入
- 实时返回识别结果

## 环境要求

- Python 3.12+
- Windows 10+

## 快速开始

### 1. 安装依赖

```bash
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. 启动服务

```bash
.\venv\Scripts\python.exe main.py
```

或使用启动脚本：

```bash
start_server.bat
```

服务将在 `http://0.0.0.0:8000` 启动。

### 3. 测试服务

```bash
.\venv\Scripts\python.exe test_client.py
```

## API 文档

服务启动后，访问 `http://localhost:8000/docs` 查看 Swagger API 文档。

## WebSocket 连接

### 连接地址

```
ws://localhost:8000/ws
```

### 协议格式

详见 [项目通信协议.md](Documents/项目通信协议.md)

### 示例

#### 1. 发送 run-task 命令

```json
{
  "header": {
    "action": "run-task",
    "task_id": "your-task-id",
    "streaming": "duplex"
  },
  "payload": {
    "task_group": "audio",
    "task": "asr",
    "function": "recognition",
    "model": "paraformer-realtime-v2",
    "parameters": {
      "format": "pcm",
      "sample_rate": 16000,
      "language_hints": null,
      "punctuation_prediction_enabled": true,
      "inverse_text_normalization_enabled": true
    },
    "input": {}
  }
}
```

#### 2. 发送音频数据

发送 PCM 格式的音频数据（16kHz, 16bit, 单声道）。

#### 3. 发送 finish-task 命令

```json
{
  "header": {
    "action": "finish-task",
    "task_id": "your-task-id",
    "streaming": "duplex"
  },
  "payload": {
    "input": {}
  }
}
```

## 客户端库

项目提供了 Web 和 Python 两个版本的客户端库，详见 [Client/README.md](Client/README.md)。

### Web 客户端

- **库文件**: `Client/Web/lib/AsrClient.js`
- **Demo**: `Client/Web/demo/index.html`

### Python 客户端

- **库文件**: `Client/Python/lib/AsrClient.py`
- **Demo**: `Client/Python/demo/app.py`

## 项目结构

```
AsrServer/
├── src/
│   ├── protocol/      # 协议相关
│   ├── websocket/     # WebSocket 处理
│   ├── audio/        # 音频处理
│   ├── asr/          # ASR 模型
│   └── state/        # 状态管理
├── Client/           # 客户端库和 Demo
│   ├── Web/          # Web 客户端
│   └── Python/       # Python 客户端
├── Documents/        # 文档
├── venv/            # 虚拟环境
├── main.py          # 主程序
├── config.py        # 配置文件
├── test_client.py   # 测试客户端
└── requirements.txt # 依赖列表
```

## 配置

编辑 `config.py` 修改服务配置：

```python
class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    model_path: str = "paraformer-zh-streaming"
    model_revision: str = "v2.0.4"
    device: str = "cpu"
    # ...
```

## 许可证

MIT License
