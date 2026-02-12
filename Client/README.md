# ASR 客户端库

本项目提供了 Web 和 Python 两个版本的客户端库，用于连接 ASR 实时语音识别服务。

## 目录结构

```
Client/
├── Web/
│   ├── lib/
│   │   └── AsrClient.js      # Web 客户端库
│   └── demo/
│       └── index.html          # Web 版本 Demo
└── Python/
    ├── lib/
    │   └── AsrClient.py       # Python 客户端库
    └── demo/
        ├── app.py              # Python 版本 Demo 服务
        ├── requirements.txt     # 依赖列表
        └── start.bat           # 启动脚本
```

## Web 客户端库

### 快速开始

1. 引入库文件：
```html
<script src="path/to/AsrClient.js"></script>
```

2. 创建客户端实例：
```javascript
const client = new AsrClient({
    url: 'ws://localhost:8000/ws',
    sampleRate: 16000,
    punctuationPredictionEnabled: true,
    inverseTextNormalizationEnabled: true,
    onConnected: () => console.log('Connected'),
    onDisconnected: () => console.log('Disconnected'),
    onTaskStarted: (message) => console.log('Task started:', message),
    onResultGenerated: (message) => {
        const text = message.payload.output.sentence.text;
        console.log('Result:', text);
    },
    onTaskFinished: (message) => console.log('Task finished:', message),
    onError: (error) => console.error('Error:', error)
});
```

3. 连接并开始识别：
```javascript
await client.connect();
await client.startRecognition();

client.sendAudioData(audioData);

await client.stopRecognition();
client.disconnect();
```

### API 参考

#### 构造函数

```javascript
new AsrClient(options)
```

**参数：**
- `url` (string): WebSocket 服务地址，默认 `ws://localhost:8000/ws`
- `sampleRate` (number): 采样率，默认 `16000`
- `format` (string): 音频格式，默认 `pcm`
- `punctuationPredictionEnabled` (boolean): 是否启用标点预测，默认 `true`
- `inverseTextNormalizationEnabled` (boolean): 是否启用文本归一化，默认 `true`
- `onConnected` (function): 连接成功回调
- `onDisconnected` (function): 连接断开回调
- `onTaskStarted` (function): 任务开始回调
- `onResultGenerated` (function): 识别结果回调
- `onTaskFinished` (function): 任务完成回调
- `onError` (function): 错误回调

#### 方法

- `connect()`: 连接到服务器
- `disconnect()`: 断开连接
- `startRecognition()`: 开始语音识别
- `stopRecognition()`: 停止语音识别
- `sendAudioData(audioData)`: 发送音频数据

#### 属性

- `isConnected`: 是否已连接
- `isRecognizing`: 是否正在识别
- `taskId`: 当前任务 ID

### Demo 使用说明

**重要提示**：Web Demo 必须通过 HTTP 服务器运行，不能直接用浏览器打开 HTML 文件（file:// 协议会导致 CORS 错误）。

#### 启动 Demo 服务器

1. 运行启动脚本：
```bash
cd Client\Web\demo
start.bat
```

2. 或手动启动：
```bash
cd Client\Web\demo
python start_server.py
```

3. 在浏览器中访问：
```
http://localhost:8080/index.html
```

#### Demo 功能

- 实时语音识别
- 可配置采样率（16000 Hz / 8000 Hz）
- 可配置标点预测和文本归一化
- 实时显示识别结果
- 日志记录功能

### 技术实现

#### AudioWorklet

本客户端使用 AudioWorklet 进行音频处理，而不是已废弃的 ScriptProcessorNode。

**audio-processor.js 文件**：
```javascript
class AudioProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
    }

    process(inputs, outputs, parameters) {
        const input = inputs[0];
        
        if (input && input.length > 0) {
            const inputData = input[0];
            
            if (inputData && inputData.length > 0) {
                this.port.postMessage(inputData);
            }
        }
        
        return true;
    }
}

registerProcessor('audio-processor', AudioProcessor);
```

**在 HTML 中使用**：
```javascript
await audioContext.audioWorklet.addModule('audio-processor.js');
const audioWorkletNode = new AudioWorkletNode(audioContext, 'audio-processor');

audioWorkletNode.port.onmessage = (event) => {
    const inputData = event.data;
    const pcmData = new Int16Array(inputData.length);
    
    for (let i = 0; i < inputData.length; i++) {
        pcmData[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7FFF;
    }
    
    client.sendAudioData(pcmData.buffer);
};
```

## Python 客户端库

### 快速开始

1. 安装依赖：
```bash
pip install websockets
```

2. 使用异步客户端：
```python
import asyncio
from AsrClient import AsrClient

async def main():
    client = AsrClient(
        url='ws://localhost:8000/ws',
        sample_rate=16000,
        punctuation_prediction_enabled=True,
        inverse_text_normalization_enabled=True
    )
    
    await client.connect()
    await client.start_recognition()
    
    with open('audio.pcm', 'rb') as f:
        while True:
            data = f.read(4096)
            if not data:
                break
            await client.send_audio_data(data)
    
    await client.stop_recognition()
    await client.disconnect()

asyncio.run(main())
```

3. 使用同步客户端：
```python
from AsrClient import AsrClientSync

client = AsrClientSync(
    url='ws://localhost:8000/ws',
    sample_rate=16000
)

client.connect()
client.start_recognition()

with open('audio.pcm', 'rb') as f:
    while True:
        data = f.read(4096)
        if not data:
            break
        client.send_audio_data(data)

client.stop_recognition()
client.disconnect()
```

### API 参考

#### 构造函数

```python
AsrClient(url, sample_rate, format, punctuation_prediction_enabled, inverse_text_normalization_enabled)
AsrClientSync(url, sample_rate, format, punctuation_prediction_enabled, inverse_text_normalization_enabled)
```

**参数：**
- `url` (str): WebSocket 服务地址，默认 `ws://localhost:8000/ws`
- `sample_rate` (int): 采样率，默认 `16000`
- `format` (str): 音频格式，默认 `pcm`
- `punctuation_prediction_enabled` (bool): 是否启用标点预测，默认 `True`
- `inverse_text_normalization_enabled` (bool): 是否启用文本归一化，默认 `True`

#### 异步方法 (AsrClient)

- `async connect()`: 连接到服务器
- `async disconnect()`: 断开连接
- `async start_recognition()`: 开始语音识别
- `async stop_recognition()`: 停止语音识别
- `async send_audio_data(audio_data)`: 发送音频数据

#### 同步方法 (AsrClientSync)

- `connect()`: 连接到服务器
- `disconnect()`: 断开连接
- `start_recognition()`: 开始语音识别
- `stop_recognition()`: 停止语音识别
- `send_audio_data(audio_data)`: 发送音频数据

#### 回调函数

- `on_connected`: 连接成功回调
- `on_disconnected`: 连接断开回调
- `on_task_started`: 任务开始回调
- `on_result_generated`: 识别结果回调
- `on_task_finished`: 任务完成回调
- `on_error`: 错误回调

#### 属性

- `is_connected()`: 是否已连接
- `is_recognizing()`: 是否正在识别
- `get_task_id()`: 获取当前任务 ID

### Demo

运行 `Client/Python/demo/start.bat` 启动 Python 版本 Demo 服务，然后访问 `http://localhost:5000`。

## 音频格式要求

- 格式：PCM
- 采样率：16000 Hz 或 8000 Hz
- 位深度：16 bit
- 声道：单声道

## 注意事项

1. 确保服务器已启动并运行在指定地址
2. 音频数据必须是 PCM 格式
3. 建议使用 16000 Hz 采样率以获得最佳识别效果
4. WebSocket 连接断开后需要重新连接才能继续使用

## 许可证

MIT License
