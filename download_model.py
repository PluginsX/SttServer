from funasr import AutoModel

print("开始下载 paraformer-zh-streaming 模型...")
print("模型较大，请耐心等待...")

try:
    model = AutoModel(
        model="paraformer-zh-streaming",
        model_revision="v2.0.4",
        device="cpu"
    )
    print("模型下载成功！")
    print(f"模型已保存到: {model.model_dir}")
except Exception as e:
    print(f"模型下载失败: {e}")
    print("\n提示：")
    print("1. 请检查网络连接")
    print("2. 如果下载速度慢，可以尝试使用 aria2c 工具")
    print("3. 模型文件较大（约 1-2GB），请确保有足够的磁盘空间")
