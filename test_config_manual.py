"""手动测试配置管理系统"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from app.config import get_settings, reload_settings


def test_load_from_yaml():
    """测试从 YAML 文件加载配置"""
    print("=" * 60)
    print("测试 1: 从 YAML 文件加载配置")
    print("=" * 60)
    
    settings = get_settings()
    
    print(f"✓ 模型 ID: {settings.model.model_id}")
    print(f"✓ 加速方式: {settings.model.acceleration}")
    print(f"✓ Pipeline 名称: {settings.pipeline.name}")
    print(f"✓ Pipeline 模式: {settings.pipeline.mode}")
    print(f"✓ 图像尺寸: {settings.pipeline.width}x{settings.pipeline.height}")
    print(f"✓ 服务器地址: {settings.server.host}:{settings.server.port}")
    print(f"✓ 日志级别: {settings.logging.level}")
    print()


def test_config_validation():
    """测试配置验证"""
    print("=" * 60)
    print("测试 2: 配置验证")
    print("=" * 60)
    
    settings = get_settings()
    warnings = settings.validate_config()
    
    if warnings:
        print("⚠ 配置警告:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("✓ 配置验证通过，无警告")
    print()


def test_api_settings_response():
    """测试 API 设置响应生成"""
    print("=" * 60)
    print("测试 3: API 设置响应生成")
    print("=" * 60)
    
    settings = get_settings()
    api_response = settings.get_api_settings_response()
    
    print(f"✓ input_params 包含 {len(api_response['input_params']['properties'])} 个参数")
    print(f"✓ 默认输入模式: {api_response['info']['properties']['input_mode']['default']}")
    print(f"✓ 最大队列大小: {api_response['max_queue_size']}")
    print()


def test_to_dict():
    """测试配置转换为字典"""
    print("=" * 60)
    print("测试 4: 配置转换为字典")
    print("=" * 60)
    
    settings = get_settings()
    config_dict = settings.to_dict()
    
    print(f"✓ 配置字典包含 {len(config_dict)} 个顶级键")
    print(f"✓ 顶级键: {', '.join(config_dict.keys())}")
    print()


def test_dimension_validation():
    """测试尺寸验证（必须是 8 的倍数）"""
    print("=" * 60)
    print("测试 5: 尺寸验证")
    print("=" * 60)
    
    from app.config.settings import PipelineConfig
    
    # 测试有效尺寸
    try:
        config = PipelineConfig(width=512, height=512)
        print(f"✓ 有效尺寸 512x512 通过验证")
    except ValueError as e:
        print(f"✗ 意外错误: {e}")
    
    # 测试无效尺寸
    try:
        config = PipelineConfig(width=513, height=512)
        print(f"✗ 无效尺寸 513x512 应该失败但通过了")
    except ValueError as e:
        print(f"✓ 无效尺寸 513x512 正确被拒绝: {e}")
    
    print()


def test_acceleration_validation():
    """测试加速方式验证"""
    print("=" * 60)
    print("测试 6: 加速方式验证")
    print("=" * 60)
    
    from app.config.settings import ModelConfig
    
    # 测试有效加速方式
    for method in ["xformers", "tensorrt", "none"]:
        try:
            config = ModelConfig(acceleration=method)
            print(f"✓ 有效加速方式 '{method}' 通过验证")
        except ValueError as e:
            print(f"✗ 意外错误: {e}")
    
    # 测试无效加速方式
    try:
        config = ModelConfig(acceleration="invalid")
        print(f"✗ 无效加速方式 'invalid' 应该失败但通过了")
    except ValueError as e:
        print(f"✓ 无效加速方式 'invalid' 正确被拒绝")
    
    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("配置管理系统手动测试")
    print("=" * 60 + "\n")
    
    try:
        test_load_from_yaml()
        test_config_validation()
        test_api_settings_response()
        test_to_dict()
        test_dimension_validation()
        test_acceleration_validation()
        
        print("=" * 60)
        print("✓ 所有测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
