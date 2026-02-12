let asrClient = null;
let audioContext = null;
let mediaStream = null;
let audioWorkletNode = null;
let isRecording = false;
let audioBuffer = [];
let audioDataCount = 0;

// 音频强度频谱图相关变量
let audioIntensityCanvas = null;
let audioIntensityCtx = null;
let audioIntensityData = [];
let audioIntensityMaxPoints = 100;
let audioIntensityAnimationId = null;

// 音频列表相关变量
let audioList = [];
let audioListCounter = 0;

// 当前播放的音频
let currentPlayingAudio = null;
let currentPlayingElement = null;

function log(message) {
    const logArea = document.getElementById('logArea');
    const time = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.innerHTML = `<span class="log-time">[${time}]</span> ${message}`;
    logArea.appendChild(entry);
    logArea.scrollTop = logArea.scrollHeight;
    
    // 同时输出到浏览器控制台
    console.log(`[${time}] ${message}`);
}

function updateStatus(status) {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    
    statusDot.className = 'status-dot';
    
    switch (status) {
        case 'connected':
            statusDot.classList.add('connected');
            statusText.textContent = '已连接';
            break;
        case 'recognizing':
            statusDot.classList.add('recognizing');
            statusText.textContent = '识别中';
            break;
        default:
            statusText.textContent = '未连接';
    }
}

function updateButtons(connected, recognizing) {
    document.getElementById('connectBtn').disabled = connected;
    document.getElementById('startBtn').disabled = !connected || recognizing;
    document.getElementById('stopBtn').disabled = !recognizing;
    document.getElementById('disconnectBtn').disabled = !connected;
}

async function connect() {
    const serviceType = document.getElementById('serviceType').value;
    const url = document.getElementById('serverUrl').value;
    const apiKey = document.getElementById('apiKey').value;
    const model = document.getElementById('model').value;
    const sampleRate = parseInt(document.getElementById('sampleRate').value);
    const audioFormat = document.getElementById('audioFormat').value;
    const punctuationEnabled = document.getElementById('punctuationEnabled').checked;
    const normalizationEnabled = document.getElementById('normalizationEnabled').checked;
    const semanticPunctuationEnabled = document.getElementById('semanticPunctuationEnabled').checked;
    const maxSentenceSilence = parseInt(document.getElementById('maxSentenceSilence').value);
    const multiThresholdModeEnabled = document.getElementById('multiThresholdModeEnabled').checked;
    const disfluencyRemovalEnabled = document.getElementById('disfluencyRemovalEnabled').checked;
    const heartbeatEnabled = document.getElementById('heartbeatEnabled').checked;
    const languageHints = document.getElementById('languageHints').value === 'auto' ? [] : [document.getElementById('languageHints').value];
    const vocabularyId = document.getElementById('vocabularyId').value;
    
    // 读取VAD相关配置
    const vadEnabled = document.getElementById('vadEnabled').checked;
    const vadMode = parseInt(document.getElementById('vadMode').value);
    const silenceDuration = parseInt(document.getElementById('silenceDuration').value);
    const silenceThreshold = parseFloat(document.getElementById('silenceThreshold').value);
    const localSampleRate = parseInt(document.getElementById('localSampleRate').value);
    
    log('准备连接到服务器 - 配置参数:');
    log(`  - 服务类型: ${serviceType}`);
    log(`  - 服务器URL: ${url}`);
    log(`  - API密钥: ${apiKey ? '已设置' : '未设置'}`);
    log(`  - 模型: ${model}`);
    log(`  - 采样率: ${sampleRate}`);
    log(`  - 音频格式: ${audioFormat}`);
    log(`  - 标点预测: ${punctuationEnabled}`);
    log(`  - 文本标准化: ${normalizationEnabled}`);
    log(`  - 语义断句: ${semanticPunctuationEnabled}`);
    log(`  - 最大句子静音: ${maxSentenceSilence}ms`);
    log(`  - 多阈值模式: ${multiThresholdModeEnabled}`);
    log(`  - 除冗余: ${disfluencyRemovalEnabled}`);
    log(`  - 心跳: ${heartbeatEnabled}`);
    log(`  - 语言提示: ${JSON.stringify(languageHints)}`);
    log(`  - 词汇表ID: ${vocabularyId}`);
    
    // 输出VAD配置
    log('VAD配置参数:');
    log(`  - 启用VAD: ${vadEnabled}`);
    log(`  - VAD模式: ${vadMode}`);
    log(`  - 静音时长阈值: ${silenceDuration}ms`);
    log(`  - 静音阈值: ${silenceThreshold}`);
    log(`  - 本地采样率: ${localSampleRate}`);
    
    asrClient = new AsrClient({
        serviceType: serviceType,
        url: url,
        apiKey: apiKey,
        model: model,
        sampleRate: sampleRate,
        format: audioFormat,
        punctuationPredictionEnabled: punctuationEnabled,
        inverseTextNormalizationEnabled: normalizationEnabled,
        semanticPunctuationEnabled: semanticPunctuationEnabled,
        maxSentenceSilence: maxSentenceSilence,
        multiThresholdModeEnabled: multiThresholdModeEnabled,
        disfluencyRemovalEnabled: disfluencyRemovalEnabled,
        heartbeatEnabled: heartbeatEnabled,
        languageHints: languageHints,
        vocabularyId: vocabularyId,
        vadEnabled: vadEnabled,
        vadMode: vadMode,
        silenceDurationMs: silenceDuration,
        silenceThreshold: silenceThreshold,
        localSampleRate: localSampleRate,
        onConnected: () => {
            log('✅ WebSocket 连接成功');
            updateStatus('connected');
            updateButtons(true, false);
        },
        onDisconnected: () => {
            log('❌ WebSocket 连接断开');
            updateStatus('disconnected');
            updateButtons(false, false);
            stopRecording();
        },
        onTaskStarted: (message) => {
            log(`🚀 任务开始: ${message.header.task_id}`);
            document.getElementById('taskIdText').textContent = `Task ID: ${message.header.task_id}`;
            updateStatus('recognizing');
            updateButtons(true, true);  // 启用"停止识别"按钮
            startRecording();  // 在收到服务器确认后才开始录音
        },
        onResultGenerated: (message) => {
            const text = message.payload.output.sentence.text;
            if (text) {
                const resultElement = document.getElementById('resultText');
                const resultAreaElement = resultElement.parentElement;
                const currentText = resultElement.textContent;
                
                if (currentText === '等待开始识别...') {
                    resultElement.textContent = text;
                } else {
                    resultElement.textContent = '\n' + text;
                }
                
                // 自动滚动到最新内容
                resultAreaElement.scrollTop = resultAreaElement.scrollHeight;
                
                log(`📝 识别结果: ${text}`);
            }
        },
        onTaskFinished: (message) => {
            log(`✅ 任务完成: ${message.header.task_id}`);
            updateStatus('connected');
            updateButtons(true, false);
            stopRecording();  // 确保在任务完成后停止录音
        },
        onError: (error) => {
            log(`❌ 错误: ${error}`);
            console.error('ASR Client error:', error);
        },
        onAudioSent: (audioData) => {
            // 计算音频时长（假设采样率为16000Hz，每个样本2字节）
            const sampleRate = parseInt(document.getElementById('sampleRate').value);
            const duration = audioData.byteLength / (sampleRate * 2);
            
            // 添加音频到列表
            addAudioToList(audioData, duration);
            
            // 更新音频强度图
            const intensity = calculateAudioIntensity(audioData);
            updateAudioIntensity(intensity);
        }
    });
    
    try {
        log(`尝试连接到: ${url}`);
        await asrClient.connect();
        log('连接过程完成');
    } catch (error) {
        log(`❌ 连接失败: ${error}`);
        console.error('Connection error:', error);
    }
}

function disconnect() {
    log('断开服务器连接');
    if (asrClient) {
        asrClient.disconnect();
        asrClient = null;
        log('✅ 已断开与服务器的连接');
    } else {
        log('⚠️ 当前没有活跃的连接');
    }
    
    // 停止当前播放的音频
    if (currentPlayingAudio) {
        currentPlayingAudio.pause();
        currentPlayingAudio = null;
        if (currentPlayingElement) {
            currentPlayingElement.classList.remove('playing');
        }
        currentPlayingElement = null;
    }
}

async function startRecognition() {
    try {
        // 获取当前配置参数并记录
        const serviceType = document.getElementById('serviceType').value;
        const url = document.getElementById('serverUrl').value;
        const apiKey = document.getElementById('apiKey').value;
        const model = document.getElementById('model').value;
        const sampleRate = parseInt(document.getElementById('sampleRate').value);
        const audioFormat = document.getElementById('audioFormat').value;
        const punctuationEnabled = document.getElementById('punctuationEnabled').checked;
        const normalizationEnabled = document.getElementById('normalizationEnabled').checked;
        const semanticPunctuationEnabled = document.getElementById('semanticPunctuationEnabled').checked;
        const maxSentenceSilence = parseInt(document.getElementById('maxSentenceSilence').value);
        const multiThresholdModeEnabled = document.getElementById('multiThresholdModeEnabled').checked;
        const disfluencyRemovalEnabled = document.getElementById('disfluencyRemovalEnabled').checked;
        const heartbeatEnabled = document.getElementById('heartbeatEnabled').checked;
        const languageHints = document.getElementById('languageHints').value === 'auto' ? [] : [document.getElementById('languageHints').value];
        const vocabularyId = document.getElementById('vocabularyId').value;
        const vadEnabled = document.getElementById('vadEnabled').checked;
        const vadMode = parseInt(document.getElementById('vadMode').value);
        const silenceDuration = parseInt(document.getElementById('silenceDuration').value);
        
        // 记录即将使用的API调用参数
        log('开始语音识别 - 当前配置参数:');
        log(`  - 服务类型: ${serviceType}`);
        log(`  - 服务器URL: ${url}`);
        log(`  - 模型: ${model}`);
        log(`  - 采样率: ${sampleRate}`);
        log(`  - 音频格式: ${audioFormat}`);
        log(`  - 标点预测: ${punctuationEnabled}`);
        log(`  - 文本标准化: ${normalizationEnabled}`);
        log(`  - 语义断句: ${semanticPunctuationEnabled}`);
        log(`  - 最大句子静音: ${maxSentenceSilence}ms`);
        log(`  - 多阈值模式: ${multiThresholdModeEnabled}`);
        log(`  - 除冗余: ${disfluencyRemovalEnabled}`);
        log(`  - 心跳: ${heartbeatEnabled}`);
        log(`  - 语言提示: ${JSON.stringify(languageHints)}`);
        log(`  - 词汇表ID: ${vocabularyId}`);
        log(`  - VAD启用: ${vadEnabled}`);
        log(`  - VAD模式: ${vadMode}`);
        log(`  - 静音持续时间: ${silenceDuration}ms`);
        
        // 重置音频列表和音频强度图
        audioList = [];
        audioListCounter = 0;
        audioIntensityData = new Array(audioIntensityMaxPoints).fill(0);
        document.getElementById('audioList').innerHTML = '';
        drawAudioIntensity();
        
        // 重置结果文本框
        document.getElementById('resultText').textContent = '';
        
        // 发起识别请求，但不立即开始录音
        asrClient.startRecognition();
        log('已向服务器发起语音识别请求');
        updateStatus('connecting');  // 更新状态为正在连接服务器
        updateButtons(true, false);  // 保持"停止识别"按钮为禁用状态，直到服务器确认开始
    } catch (error) {
        log(`启动识别失败: ${error}`);
        console.error('Start recognition error:', error);
    }
}

function stopRecognition() {
    log('停止语音识别请求');
    if (asrClient) {
        asrClient.stopRecognition();
        log('✅ 已向服务器发送停止识别命令');
    }
    stopRecording();
    
    // 停止当前播放的音频
    if (currentPlayingAudio) {
        currentPlayingAudio.pause();
        currentPlayingAudio = null;
        if (currentPlayingElement) {
            currentPlayingElement.classList.remove('playing');
        }
        currentPlayingElement = null;
    }
}

async function startRecording() {
    try {
        const vadEnabled = document.getElementById('vadEnabled').checked;
        const vadMode = parseInt(document.getElementById('vadMode').value);
        const silenceDuration = parseInt(document.getElementById('silenceDuration').value);
        
        log(`准备启动录音 - VAD配置:`);
        log(`  - VAD启用: ${vadEnabled}`);
        log(`  - VAD模式: ${vadMode}`);
        log(`  - 静音持续时间: ${silenceDuration}ms`);
        
        // 更新AsrClient的VAD配置
        asrClient.updateAudioProcessorConfig({
            vadEnabled: vadEnabled,
            vadMode: vadMode,
            silenceDurationMs: silenceDuration
        });
        
        // 使用AsrClient的startRecording方法
        log('正在启动录音...');
        await asrClient.startRecording();
        
        if (vadEnabled) {
            log(`🎧 VAD 已启用: 模式 ${vadMode}, 静音阈值 ${silenceDuration}ms`);
        } else {
            log('📡 VAD 未启用，发送原始音频流');
        }
        
        isRecording = true;
        log('✅ 开始录音');
    } catch (error) {
        log(`❌ 录音启动失败: ${error}`);
        console.error('Start recording error:', error);
        throw error;
    }
}

function stopRecording() {
    log('停止录音');
    // 使用AsrClient的stopRecording方法
    if (asrClient) {
        asrClient.stopRecording();
    }
    
    // 重置本地变量
    audioWorkletNode = null;
    audioContext = null;
    mediaStream = null;
    isRecording = false;
    log('✅ 录音已停止');
}

async function testConnection() {
    const serviceType = document.getElementById('serviceType').value;
    const url = document.getElementById('serverUrl').value;
    const apiKey = document.getElementById('apiKey').value;
    
    log(`开始测试与服务器的连接: ${url}`);
    
    try {
        if (serviceType === 'aliyun') {
                // 对于阿里云服务，尝试使用XMLHttpRequest来测试连接
                // 因为标准WebSocket API不支持直接添加headers
                log('测试阿里云服务连接...');
                
                // 首先测试API Key是否已设置
                if (!apiKey) {
                    log('错误: API Key未设置，请输入有效的API Key');
                    return;
                }
                
                // 使用fetch API测试API Key是否有效
                log('验证API Key...');
                
                // 注意：这里只是测试网络连接，不是真正的API调用
                // 阿里云DashScope API可能需要特定的端点来验证API Key
                
                // 尝试在URL中添加API Key作为参数
                let wsUrl = url;
                if (apiKey) {
                    if (wsUrl.includes('?')) {
                        wsUrl += `&api_key=${encodeURIComponent(apiKey)}`;
                    } else {
                        wsUrl += `?api_key=${encodeURIComponent(apiKey)}`;
                    }
                }
                log(`尝试连接: ${wsUrl}`);
                
                // 尝试WebSocket连接
                const ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {
                log('连接测试成功: 服务器响应正常');
                ws.close();
            };
            
            ws.onerror = (error) => {
                log(`连接测试失败: ${error.message || '未知错误'}`);
                log('注意: 在浏览器环境中，标准WebSocket API不支持直接添加headers');
                log('这可能是导致连接失败的原因');
                ws.close();
            };
            
            ws.onclose = (event) => {
                if (event.code !== 1000) {
                    log(`连接关闭: 代码 ${event.code}, 原因: ${event.reason || '无'}`);
                    
                    switch (event.code) {
                        case 1006:
                            log('错误代码1006: 连接被意外关闭');
                            log('可能原因:');
                            log('1. API Key未正确设置');
                            log('2. 网络连接问题');
                            log('3. 浏览器安全限制（无法添加headers）');
                            break;
                        case 40000002:
                            log('错误代码40000002: 无效的消息');
                            log('可能原因: message_id或task_id格式错误');
                            break;
                        default:
                            log('请检查网络连接和API Key设置');
                    }
                }
            };
            
            // 设置5秒超时
            setTimeout(() => {
                if (ws.readyState === WebSocket.CONNECTING) {
                    log('连接测试超时: 服务器无响应');
                    ws.close();
                }
            }, 5000);
        } else {
            // 对于本地服务，使用标准WebSocket连接
            const ws = new WebSocket(url);
            
            ws.onopen = () => {
                log('连接测试成功: 服务器响应正常');
                ws.close();
            };
            
            ws.onerror = (error) => {
                log(`连接测试失败: ${error.message || '未知错误'}`);
                ws.close();
            };
            
            ws.onclose = (event) => {
                if (event.code !== 1000) {
                    log(`连接关闭: 代码 ${event.code}, 原因: ${event.reason || '无'}`);
                }
            };
            
            // 设置5秒超时
            setTimeout(() => {
                if (ws.readyState === WebSocket.CONNECTING) {
                    log('连接测试超时: 服务器无响应');
                    ws.close();
                }
            }, 5000);
        }
        
    } catch (error) {
        log(`连接测试异常: ${error.message || '未知异常'}`);
        log(`异常详情: ${JSON.stringify(error)}`);
    }
}

// 初始化音频强度频谱图
function initAudioIntensityCanvas() {
    audioIntensityCanvas = document.getElementById('audioIntensityCanvas');
    if (audioIntensityCanvas) {
        audioIntensityCtx = audioIntensityCanvas.getContext('2d');
        
        // 设置canvas尺寸
        const container = audioIntensityCanvas.parentElement;
        audioIntensityCanvas.width = container.clientWidth;
        audioIntensityCanvas.height = container.clientHeight;
        
        // 初始化数据数组
        audioIntensityData = new Array(audioIntensityMaxPoints).fill(0);
        
        // 监听窗口大小变化
        window.addEventListener('resize', () => {
            if (audioIntensityCanvas) {
                audioIntensityCanvas.width = container.clientWidth;
                audioIntensityCanvas.height = container.clientHeight;
            }
        });
    }
}

// 更新音频强度数据
function updateAudioIntensity(intensity) {
    if (!audioIntensityCtx) return;
    
    // 添加新数据点
    audioIntensityData.push(intensity);
    
    // 保持数据长度固定
    if (audioIntensityData.length > audioIntensityMaxPoints) {
        audioIntensityData.shift();
    }
    
    // 绘制频谱图
    drawAudioIntensity();
}

// 绘制音频强度频谱图
function drawAudioIntensity() {
    if (!audioIntensityCtx || !audioIntensityCanvas) return;
    
    const width = audioIntensityCanvas.width;
    const height = audioIntensityCanvas.height;
    const padding = { top: 20, right: 10, bottom: 30, left: 50 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    // 清空画布
    audioIntensityCtx.clearRect(0, 0, width, height);
    
    // 绘制背景网格
    audioIntensityCtx.strokeStyle = '#e0e0e0';
    audioIntensityCtx.lineWidth = 1;
    
    // 绘制水平网格线和Y轴标签（能量值）
    const energyLevels = [0.1, 0.08, 0.06, 0.04, 0.02, 0];
    for (let i = 0; i < energyLevels.length; i++) {
        const energy = energyLevels[i];
        const y = padding.top + (1 - energy / 0.1) * chartHeight;
        
        // 绘制水平网格线
        audioIntensityCtx.beginPath();
        audioIntensityCtx.moveTo(padding.left, y);
        audioIntensityCtx.lineTo(width - padding.right, y);
        audioIntensityCtx.stroke();
        
        // 绘制Y轴标签
        audioIntensityCtx.fillStyle = '#666';
        audioIntensityCtx.font = '10px Arial';
        audioIntensityCtx.textAlign = 'right';
        audioIntensityCtx.textBaseline = 'middle';
        audioIntensityCtx.fillText(energy.toFixed(3), padding.left - 5, y);
    }
    
    // 绘制垂直网格线和X轴标签（时间）
    const timeLabels = ['1.0s', '0.8s', '0.6s', '0.4s', '0.2s', '0.0s'];
    for (let i = 0; i <= 5; i++) {
        const x = padding.left + (chartWidth / 5) * i;
        
        // 绘制垂直网格线
        audioIntensityCtx.beginPath();
        audioIntensityCtx.moveTo(x, padding.top);
        audioIntensityCtx.lineTo(x, height - padding.bottom);
        audioIntensityCtx.stroke();
        
        // 绘制X轴标签
        audioIntensityCtx.fillStyle = '#666';
        audioIntensityCtx.font = '10px Arial';
        audioIntensityCtx.textAlign = 'center';
        audioIntensityCtx.textBaseline = 'top';
        audioIntensityCtx.fillText(timeLabels[i], x, height - padding.bottom + 5);
    }
    
    // 绘制Y轴标题
    audioIntensityCtx.save();
    audioIntensityCtx.translate(15, height / 2);
    audioIntensityCtx.rotate(-Math.PI / 2);
    audioIntensityCtx.fillStyle = '#333';
    audioIntensityCtx.font = 'bold 11px Arial';
    audioIntensityCtx.textAlign = 'center';
    audioIntensityCtx.fillText('能量值', 0, 0);
    audioIntensityCtx.restore();
    
    // 绘制X轴标题
    audioIntensityCtx.fillStyle = '#333';
    audioIntensityCtx.font = 'bold 11px Arial';
    audioIntensityCtx.textAlign = 'center';
    audioIntensityCtx.fillText('时间（最近1秒）', padding.left + chartWidth / 2, height - 5);
    
    // 绘制音频强度曲线
    audioIntensityCtx.beginPath();
    audioIntensityCtx.strokeStyle = '#2196F3';
    audioIntensityCtx.lineWidth = 2;
    
    for (let i = 0; i < audioIntensityData.length; i++) {
        const x = padding.left + (chartWidth / (audioIntensityMaxPoints - 1)) * i;
        const y = padding.top + chartHeight - (audioIntensityData[i] / 0.1) * chartHeight;
        
        if (i === 0) {
            audioIntensityCtx.moveTo(x, y);
        } else {
            audioIntensityCtx.lineTo(x, y);
        }
    }
    
    audioIntensityCtx.stroke();
    
    // 填充曲线下方区域
    audioIntensityCtx.lineTo(padding.left + chartWidth, padding.top + chartHeight);
    audioIntensityCtx.lineTo(padding.left, padding.top + chartHeight);
    audioIntensityCtx.closePath();
    
    const gradient = audioIntensityCtx.createLinearGradient(0, padding.top, 0, padding.top + chartHeight);
    gradient.addColorStop(0, 'rgba(33, 150, 243, 0.3)');
    gradient.addColorStop(1, 'rgba(33, 150, 243, 0.05)');
    audioIntensityCtx.fillStyle = gradient;
    audioIntensityCtx.fill();
}

// 添加音频到列表
function addAudioToList(audioData, duration) {
    const audioListElement = document.getElementById('audioList');
    if (!audioListElement) return;
    
    audioListCounter++;
    const audioId = `audio-${audioListCounter}`;
    const audioBlob = new Blob([audioData], { type: 'audio/wav' });
    const audioUrl = URL.createObjectURL(audioBlob);
    
    const time = new Date().toLocaleTimeString();
    
    // 创建音频项元素
    const audioItem = document.createElement('div');
    audioItem.className = 'audio-item';
    audioItem.id = audioId;
    audioItem.onclick = () => toggleAudioPlay(audioId, audioUrl);
    
    audioItem.innerHTML = `
        <div class="audio-icon">🎤</div>
        <div class="audio-bubble">音频片段 #${audioListCounter}</div>
        <div class="audio-info">
            <span class="audio-duration">${duration.toFixed(2)}s</span>
            <span class="audio-time">${time}</span>
        </div>
    `;
    
    // 添加到列表顶部
    audioListElement.insertBefore(audioItem, audioListElement.firstChild);
    
    // 保存音频数据
    audioList.push({
        id: audioId,
        url: audioUrl,
        data: audioData,
        duration: duration,
        time: time
    });
    
    // 自动滚动到顶部
    audioListElement.scrollTop = 0;
    
    log(`📤 添加音频到列表: 片段 #${audioListCounter}, 时长: ${duration.toFixed(2)}s`);
}

// 切换音频播放状态
function toggleAudioPlay(audioId, audioUrl) {
    const audioItem = document.getElementById(audioId);
    if (!audioItem) return;
    
    // 如果正在播放当前音频，则暂停
    if (currentPlayingAudio && currentPlayingElement === audioItem) {
        currentPlayingAudio.pause();
        currentPlayingAudio = null;
        currentPlayingElement = null;
        audioItem.classList.remove('playing');
        log(`⏸️ 暂停播放音频: ${audioId}`);
        return;
    }
    
    // 如果正在播放其他音频，则停止
    if (currentPlayingAudio) {
        currentPlayingAudio.pause();
        currentPlayingAudio = null;
        if (currentPlayingElement) {
            currentPlayingElement.classList.remove('playing');
        }
    }
    
    // 播放新音频
    const audio = new Audio(audioUrl);
    audio.onended = () => {
        currentPlayingAudio = null;
        currentPlayingElement = null;
        audioItem.classList.remove('playing');
        log(`✅ 音频播放完成: ${audioId}`);
    };
    
    audio.onerror = (error) => {
        console.error('音频播放错误:', error);
        log(`❌ 音频播放失败: ${audioId}`);
        audioItem.classList.remove('playing');
        currentPlayingAudio = null;
        currentPlayingElement = null;
    };
    
    // 尝试播放音频
    const playPromise = audio.play();
    
    if (playPromise !== undefined) {
        playPromise.then(() => {
            currentPlayingAudio = audio;
            currentPlayingElement = audioItem;
            audioItem.classList.add('playing');
            log(`▶️ 开始播放音频: ${audioId}`);
        }).catch(error => {
            console.error('音频播放被阻止:', error);
            if (error.name === 'NotAllowedError') {
                log(`⚠️ 浏览器阻止了自动播放，请先与页面交互`);
            } else {
                log(`❌ 音频播放失败: ${error.message}`);
            }
            audioItem.classList.remove('playing');
            currentPlayingAudio = null;
            currentPlayingElement = null;
        });
    } else {
        // 旧版浏览器，直接播放
        currentPlayingAudio = audio;
        currentPlayingElement = audioItem;
        audioItem.classList.add('playing');
        log(`▶️ 开始播放音频: ${audioId}`);
    }
}

// 计算音频强度
function calculateAudioIntensity(audioData) {
    if (!audioData || audioData.length === 0) return 0;
    
    let sum = 0;
    const data = new Int16Array(audioData);
    
    for (let i = 0; i < data.length; i++) {
        sum += data[i] * data[i];
    }
    
    const average = sum / data.length;
    const energy = Math.sqrt(average);
    
    // 归一化到0-0.1范围，与VAD静音阈值单位一致
    const normalized = energy / 32768;
    
    return Math.min(0.1, Math.max(0, normalized));
}

// 页面加载完成后初始化
window.onload = function() {
    initAudioIntensityCanvas();
};