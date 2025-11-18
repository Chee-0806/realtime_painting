# 依赖检查系统使用说明

## 概述

依赖检查系统用于在应用启动时验证所有必需的依赖项是否正确安装和配置。

## 功能特性

1. **Python 版本检查**：确保 Python >= 3.10
2. **PyTorch 和 CUDA 检查**：验证 PyTorch >= 2.0 和 CUDA >= 11.8 或 12.1+
3. **加速方式验证**：
   - xformers: 检查 xformers >= 0.0.22
   - TensorRT: 检查完整的 TensorRT 依赖栈
4. **详细错误报告**：提供当前版本、推荐版本和安装命令
5. **严格验证**：失败时不降级，确保配置正确

## 使用方法

### 基本用法

```python
from app.core.dependencies import DependencyChecker

# 创建检查器
checker = DependencyChecker()

# 检查所有依赖（根据加速方式）
result = checker.check_all("xformers")  # 或 "tensorrt" 或 "none"

# 检查结果
if result.passed:
    print("所有依赖检查通过 ✓")
else:
    print("依赖检查失败 ✗")
    for error in result.errors:
        print(f"  - {error}")
```

### 在应用启动时使用

```python
from app.core.dependencies import DependencyChecker
from app.config.settings import get_settings
import sys

def check_dependencies():
    """启动时检查依赖"""
    settings = get_settings()
    checker = DependencyChecker()
    
    # 根据配置的加速方式检查
    result = checker.check_all(settings.model.acceleration)
    
    if not result.passed:
        logger.error("依赖检查失败，无法启动应用")
        for error in result.errors:
            logger.error(error)
        sys.exit(1)
    
    logger.info("依赖检查通过")
```

### 获取推荐版本

```python
checker = DependencyChecker()
versions = checker.get_recommended_versions("tensorrt")

print("推荐版本:")
for name, version in versions.items():
    print(f"  {name}: {version}")
```

## 检查项说明

### Python 版本检查

- **要求**：Python 3.10+
- **原因**：使用了 Python 3.10 的新特性（如类型注解语法）

### PyTorch 和 CUDA 检查

- **PyTorch 要求**：>= 2.0.0
- **CUDA 要求**：11.8+ 或 12.1+
- **原因**：StreamDiffusion 需要较新的 PyTorch 和 CUDA 版本

### xformers 检查

- **要求**：>= 0.0.22
- **检查内容**：
  - xformers 包是否安装
  - 版本是否满足要求
  - 核心功能是否可导入

### TensorRT 检查

检查以下依赖：

- **tensorrt**: >= 9.0.0
- **cuda-python**: >= 12.0.0
- **onnx**: == 1.15.0
- **onnxruntime**: == 1.16.3
- **protobuf**: == 3.20.2
- **polygraphy**: >= 0.47.0

## 错误处理

### 错误类型

1. **版本不兼容**：当前版本低于要求版本
2. **依赖缺失**：必需的包未安装
3. **CUDA 不可用**：没有可用的 NVIDIA GPU 或 CUDA 驱动

### 错误消息格式

```
xformers 加速方式初始化失败: xformers 未安装
推荐版本: 0.0.22+
安装命令: pip install xformers>=0.0.22+
```

## 版本信息记录

检查通过后，系统会记录所有依赖的版本信息：

```
============================================================
依赖版本信息:
============================================================
✓ Python: 3.10.0 (要求: 3.10+)
✓ PyTorch: 2.1.0 (要求: 2.0.0+)
✓ CUDA: 12.1 (要求: 11.8+ or 12.1+)
✓ xformers: 0.0.22 (要求: 0.0.22+)
============================================================
```

## 设计原则

1. **严格验证**：不进行降级，确保环境完全符合要求
2. **清晰反馈**：提供详细的错误信息和解决方案
3. **早期失败**：在启动时就发现问题，避免运行时错误
4. **可扩展性**：易于添加新的依赖检查

## 相关需求

- 需求 12.1: 检查 Python、PyTorch、CUDA 版本
- 需求 12.2: 验证 TensorRT 版本与 StreamDiffusion 的兼容性
- 需求 12.3: 验证 xformers 版本与 PyTorch 版本的兼容性
- 需求 12.6: 记录所有关键依赖的版本信息
- 需求 12.7: 依赖检查失败时终止启动
