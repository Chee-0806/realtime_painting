"""测试环境变量覆盖配置"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))


def test_env_override():
    """测试环境变量覆盖 YAML 配置"""
    print("=" * 60)
    print("测试环境变量覆盖")
    print("=" * 60)
    
    # 设置环境变量
    os.environ["STREAMDIFFUSION_MODEL__MODEL_ID"] = "test/model"
    os.environ["STREAMDIFFUSION_MODEL__ACCELERATION"] = "tensorrt"
    os.environ["STREAMDIFFUSION_SERVER__PORT"] = "9000"
    os.environ["STREAMDIFFUSION_PIPELINE__WIDTH"] = "768"
    os.environ["STREAMDIFFUSION_PIPELINE__HEIGHT"] = "768"
    os.environ["STREAMDIFFUSION_LOGGING__LEVEL"] = "DEBUG"
    
    # 重新导入以应用环境变量
    from app.config import reload_settings
    
    settings = reload_settings()
    
    # 验证环境变量覆盖
    assert settings.model.model_id == "test/model", f"Expected 'test/model', got '{settings.model.model_id}'"
    print(f"✓ 模型 ID 被环境变量覆盖: {settings.model.model_id}")
    
    assert settings.model.acceleration == "tensorrt", f"Expected 'tensorrt', got '{settings.model.acceleration}'"
    print(f"✓ 加速方式被环境变量覆盖: {settings.model.acceleration}")
    
    assert settings.server.port == 9000, f"Expected 9000, got {settings.server.port}"
    print(f"✓ 服务器端口被环境变量覆盖: {settings.server.port}")
    
    assert settings.pipeline.width == 768, f"Expected 768, got {settings.pipeline.width}"
    print(f"✓ Pipeline 宽度被环境变量覆盖: {settings.pipeline.width}")
    
    assert settings.pipeline.height == 768, f"Expected 768, got {settings.pipeline.height}"
    print(f"✓ Pipeline 高度被环境变量覆盖: {settings.pipeline.height}")
    
    assert settings.logging.level == "DEBUG", f"Expected 'DEBUG', got '{settings.logging.level}'"
    print(f"✓ 日志级别被环境变量覆盖: {settings.logging.level}")
    
    # 验证未被覆盖的值仍然来自 YAML
    assert settings.pipeline.name == "img2img", f"Expected 'img2img', got '{settings.pipeline.name}'"
    print(f"✓ 未覆盖的值保持 YAML 配置: pipeline.name = {settings.pipeline.name}")
    
    print("\n✓ 所有环境变量覆盖测试通过")
    
    # 清理环境变量
    for key in list(os.environ.keys()):
        if key.startswith("STREAMDIFFUSION_"):
            del os.environ[key]


if __name__ == "__main__":
    try:
        test_env_override()
        print("\n" + "=" * 60)
        print("✓ 测试完成")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 意外错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
