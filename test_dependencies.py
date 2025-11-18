"""测试依赖检查系统"""

import logging
from app.core.dependencies import DependencyChecker

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_dependency_checker():
    """测试依赖检查器"""
    print("\n" + "=" * 60)
    print("测试依赖检查系统")
    print("=" * 60 + "\n")
    
    checker = DependencyChecker()
    
    # 测试不同的加速方式
    for acceleration in ["none", "xformers", "tensorrt"]:
        print(f"\n测试加速方式: {acceleration}")
        print("-" * 60)
        
        result = checker.check_all(acceleration)
        
        print(f"\n检查结果: {'通过 ✓' if result.passed else '失败 ✗'}")
        
        if result.errors:
            print("\n错误:")
            for error in result.errors:
                print(f"  ✗ {error}")
        
        if result.warnings:
            print("\n警告:")
            for warning in result.warnings:
                print(f"  ⚠ {warning}")
        
        print("\n推荐版本:")
        recommended = checker.get_recommended_versions(acceleration)
        for name, version in recommended.items():
            print(f"  - {name}: {version}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    test_dependency_checker()
