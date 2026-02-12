#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型预加载脚本
用于提前下载和缓存模型，减少服务启动时间
"""

import logging
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import settings
from src.asr.model import ASRModel


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def preload_model():
    """
    预加载模型
    """
    logger.info("Starting model preload process...")
    logger.info(f"Model path: {settings.model_path}")
    logger.info(f"Model revision: {settings.model_revision}")
    logger.info(f"Model directory: {settings.model_dir}")
    
    try:
        # 初始化ASRModel，触发模型下载
        asr_model = ASRModel(
            model_path=settings.model_path,
            model_revision=settings.model_revision,
            device=settings.device,
            semantic_punctuation_enabled=settings.semantic_punctuation_enabled,
            max_sentence_silence=settings.max_sentence_silence,
            model_dir=settings.model_dir
        )
        
        logger.info("Model preload completed successfully!")
        logger.info("Models are now cached locally, service startup will be faster.")
        
    except Exception as e:
        logger.error(f"Failed to preload model: {e}")
        sys.exit(1)


if __name__ == "__main__":
    preload_model()
