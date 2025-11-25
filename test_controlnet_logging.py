#!/usr/bin/env python3
"""
ControlNet 日志测试脚本

用于验证 ControlNet 是否正常工作，以及详细的日志输出。
"""

import logging
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志级别为 DEBUG 以显示所有日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('controlnet_test.log')
    ]
)

logger = logging.getLogger(__name__)

def test_controlnet_imports():
    """测试 ControlNet 相关导入"""
    logger.info("🧪 测试 ControlNet 导入...")

    try:
        from controlnet_aux import (
            CannyDetector,
            OpenposeDetector,
            MidasDetector,
            HEDdetector,
            MLSDdetector,
            LineartDetector,
            NormalBaeDetector,
            PidiNetDetector,
            SamDetector,
        )
        logger.info("✅ controlnet-aux 导入成功")

        detectors = {
            "canny": CannyDetector,
            "pose": OpenposeDetector,
            "depth": MidasDetector,
            "hed": HEDdetector,
            "mlsd": MLSDdetector,
            "lineart": LineartDetector,
            "normal": NormalBaeDetector,
            "scribble": PidiNetDetector,
            "semantic": SamDetector,
        }

        logger.info(f"📋 可用的检测器: {list(detectors.keys())}")
        return detectors, True

    except ImportError as e:
        logger.error(f"❌ controlnet-aux 导入失败: {e}")
        return {}, False

def test_controlnet_initialization(detectors):
    """测试 ControlNet 检测器初始化"""
    logger.info("🧪 测试 ControlNet 检测器初始化...")

    initialized = {}

    for name, detector_class in detectors.items():
        try:
            logger.info(f"🔧 初始化 {name} 检测器...")
            detector = detector_class()
            initialized[name] = detector
            logger.info(f"✅ {name} 检测器初始化成功")
        except Exception as e:
            logger.error(f"❌ {name} 检测器初始化失败: {e}")

    logger.info(f"🎉 成功初始化 {len(initialized)} 个检测器")
    logger.info(f"📋 成功的检测器: {list(initialized.keys())}")

    return initialized

def test_pipeline_import():
    """测试 Pipeline 导入"""
    logger.info("🧪 测试 Canvas Pipeline 导入...")

    try:
        from app.pipelines.canvas import Pipeline
        logger.info("✅ Canvas Pipeline 导入成功")

        # 获取输入参数模式
        schema = Pipeline.get_input_params_schema()
        logger.info(f"📋 Pipeline 输入参数模式: {list(schema['properties'].keys())}")

        return Pipeline

    except Exception as e:
        logger.error(f"❌ Canvas Pipeline 导入失败: {e}")
        return None

def test_image_processing(detectors):
    """测试图像处理"""
    logger.info("🧪 测试图像处理...")

    try:
        from PIL import Image
        import numpy as np

        # 创建一个测试图像
        test_image = Image.new('RGB', (512, 512), color='red')
        logger.info(f"📏 创建测试图像: {test_image.size}, 模式: {test_image.mode}")

        # 测试 Canny 检测
        if "canny" in detectors:
            logger.info("🔍 测试 Canny 边缘检测...")
            canny_detector = detectors["canny"]
            canny_result = canny_detector(test_image)
            logger.info(f"✅ Canny 检测完成，结果类型: {type(canny_result)}")

            if isinstance(canny_result, np.ndarray):
                logger.info(f"📏 Canny 结果形状: {canny_result.shape}")
                edge_pixels = np.sum(canny_result > 0)
                total_pixels = canny_result.size
                edge_ratio = edge_pixels / total_pixels * 100
                logger.info(f"📊 Canny 边缘统计: {edge_pixels}/{total_pixels} ({edge_ratio:.2f}%)")
            else:
                logger.info(f"📏 Canny 结果尺寸: {getattr(canny_result, 'size', 'unknown')}")

        # 测试其他检测器
        for name, detector in detectors.items():
            if name == "canny":
                continue  # 已经测试过了

            try:
                logger.info(f"🔍 测试 {name} 检测...")
                result = detector(test_image)
                logger.info(f"✅ {name} 检测完成，结果类型: {type(result)}")

                if isinstance(result, np.ndarray):
                    logger.info(f"📏 {name} 结果形状: {result.shape}")
                elif hasattr(result, 'size'):
                    logger.info(f"📏 {name} 结果尺寸: {result.size}")

            except Exception as e:
                logger.error(f"❌ {name} 检测失败: {e}")

        return True

    except Exception as e:
        logger.error(f"❌ 图像处理测试失败: {e}")
        return False

def test_pipeline_creation():
    """测试 Pipeline 创建"""
    logger.info("🧪 测试 Pipeline 创建...")

    try:
        import torch
        from app.pipelines.canvas import Pipeline

        device = torch.device("cpu")  # 使用 CPU 避免内存问题
        torch_dtype = torch.float32   # 使用 float32 在 CPU 上更稳定

        logger.info(f"🔧 使用设备: {device}, 数据类型: {torch_dtype}")

        # 创建模拟参数
        args = {}

        logger.info("🔧 创建 Pipeline 实例...")
        pipeline = Pipeline(args, device, torch_dtype)

        logger.info("✅ Pipeline 创建成功!")

        # 获取初始参数
        initial_params = pipeline._get_initial_params()
        logger.info(f"📋 初始参数:")
        logger.info(f"   ControlNet 启用: {initial_params.controlnet_enabled}")
        logger.info(f"   ControlNet 类型: {initial_params.controlnet_model}")
        logger.info(f"   ControlNet 强度: {initial_params.controlnet_strength}")

        return pipeline

    except Exception as e:
        logger.error(f"❌ Pipeline 创建失败: {e}")
        return None

def main():
    """主测试函数"""
    logger.info("🚀 开始 ControlNet 功能测试...")

    # 测试导入
    detectors, import_success = test_controlnet_imports()

    if not import_success:
        logger.error("❌ ControlNet 导入失败，无法继续测试")
        return False

    # 测试初始化
    initialized_detectors = test_controlnet_initialization(detectors)

    if not initialized_detectors:
        logger.error("❌ 没有检测器初始化成功，无法继续测试")
        return False

    # 测试图像处理
    image_test_success = test_image_processing(initialized_detectors)

    # 测试 Pipeline 导入
    pipeline_class = test_pipeline_import()

    # 测试 Pipeline 创建（可选，可能会消耗较多资源）
    pipeline = None
    if pipeline_class:
        try:
            pipeline = test_pipeline_creation()
        except Exception as e:
            logger.warning(f"⚠️ Pipeline 创建跳过（可能是资源限制）: {e}")

    # 总结
    logger.info("🎯 测试总结:")
    logger.info(f"   ControlNet 导入: {'✅ 成功' if import_success else '❌ 失败'}")
    logger.info(f"   检测器初始化: {'✅ 成功' if initialized_detectors else '❌ 失败'} ({len(initialized_detectors)} 个)")
    logger.info(f"   图像处理: {'✅ 成功' if image_test_success else '❌ 失败'}")
    logger.info(f"   Pipeline 导入: {'✅ 成功' if pipeline_class else '❌ 失败'}")
    logger.info(f"   Pipeline 创建: {'✅ 成功' if pipeline else '❌ 失败'}")

    success = import_success and bool(initialized_detectors) and image_test_success

    if success:
        logger.info("🎉 ControlNet 功能测试通过！")
        logger.info("📝 详细日志已保存到 controlnet_test.log")
    else:
        logger.error("❌ ControlNet 功能测试失败")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)