1. 本项目的架构图表存储在 `docs/framwork.mermaid` 文件中，所有涉及架构调整的新修改要实时更新该文件。
2. 项目对外服务统一的通信协议 F:\Project\Python\AsrServer\docs\项目通信协议.md
3. 本项目通信协议参考阿里云DashScope WebSocket协议，详细定义请参考 F:\Project\Python\AsrServer\docs\Paraformer实时语音识别WebSocket API.md
4. 项目所有python脚本必须使用专用虚拟环境运行 F:\Project\Python\AsrServer\venv\Scripts\python.exe
5. 下载大型文件可使用aria2c工具下载文件 E:\Program Files\aria2\aria2c.exe
6. 根据开发计划进行项目开发，遇到实施问题必须及时纠正更新相关文档。
7. 所有临时测试文件必须存储在 tests/ 目录下，不允许提交到版本控制中。
8. 程序绑定端口被占用时，不要修改端口重试！而是查找占用端口的进程，结束进程后重试。
9. 阿里云ASR服务信息
   - 服务地址：wss://dashscope.aliyuncs.com/api-ws/v1/inference
   - 服务密钥：sk-a7558f9302974d1891906107f6033939
   - 服务模型：paraformer-realtime-v2
10. GPU优先使用，CPU次之
11. pip安装新包优先查找本地缓存 F:\Project\Python\PipLib