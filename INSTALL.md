# StreamDiffusion Backend 安装指南

本文档提供在新环境中安装 StreamDiffusion Backend 的完整步骤。

## 前置要求

- Python 3.10+
- CUDA 11.8+ 或 12.1+（推荐 12.1+）
- Conda 或 Python 虚拟环境
- 至少 20GB 可用磁盘空间（用于模型和缓存）

## 安装步骤

### 1. 创建 Conda 环境

```bash
# 创建 Python 3.10 环境
conda create -n rp python=3.10 -y
conda activate rp
```

### 2. 配置环境变量（可选，推荐）

将缓存和虚拟环境指向数据盘，避免占用系统盘空间：

```bash
# 运行环境配置脚本
./setup_env.sh

# 激活缓存环境变量
source /root/autodl-tmp/activate_cache.sh
```

**注意**：如果使用其他路径，请修改 `setup_env.sh` 中的 `DATA_DISK_ROOT` 变量。

### 3. 安装 PyTorch（严格按照 StreamDiffusion 的版本）

**重要**：StreamDiffusion 使用 PyTorch 2.1.0，必须使用相同版本：

```bash
# CUDA 12.1
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121

# CUDA 11.8
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu118
```

### 4. 安装基础依赖

```bash
# 安装核心依赖
pip install -r requirements.txt
```

**重要说明**：
- `requirements.txt` 中已包含所有基础依赖，版本严格按照 StreamDiffusion
- 关键版本已固定以避免冲突：
  - `torch==2.1.0` - StreamDiffusion 要求
  - `torchvision==0.16.0` - StreamDiffusion 要求
  - `numpy>=1.24.0,<2.0` - 避免与 onnxruntime 不兼容
  - `huggingface_hub<0.20.0` - diffusers 0.24.0 需要
  - `diffusers==0.24.0` - StreamDiffusion 要求
- 如果仍遇到版本冲突，请查看 `INSTALL.md` 的"常见问题"部分

### 5. 安装 TensorRT 依赖（如果使用 TensorRT 加速）

**重要**：TensorRT 需要通过 NVIDIA PyPI 安装，严格按照 StreamDiffusion 的版本：

```bash
# 方法 1：使用 StreamDiffusion 的安装脚本（推荐）
python -m streamdiffusion.tools.install-tensorrt

# 方法 2：手动安装（根据 CUDA 版本选择）
       # CUDA 12.x:
       pip install "nvidia-cudnn-cu12==8.9.4.25" --no-cache-dir  # StreamDiffusion install-tensorrt.py 要求
       pip install --pre --extra-index-url https://pypi.nvidia.com tensorrt==9.0.1.post12.dev4 --no-cache-dir

       # CUDA 11.x:
       pip install "nvidia-cudnn-cu11==8.9.4.25" --no-cache-dir
       pip install --pre --extra-index-url https://pypi.nvidia.com tensorrt==9.0.1.post11.dev4 --no-cache-dir

# 然后安装其他 TensorRT 依赖
pip install -r requirements-tensorrt.txt
```

       **依赖说明**（严格按照 StreamDiffusion 的版本）：
       - `tensorrt==9.0.1.post12.dev4` - TensorRT 核心库（CUDA 12，必须从 NVIDIA PyPI 安装）
       - `nvidia-cudnn-cu12==8.9.4.25` - cuDNN（StreamDiffusion install-tensorrt.py 要求）
       - `cuda-python>=12.0.0` - CUDA Python 绑定（已修复 API 导入问题）
       - `onnx==1.15.0` - ONNX 模型格式（StreamDiffusion setup.py 要求）
       - `onnxruntime==1.16.3` - ONNX Runtime（StreamDiffusion setup.py 要求）
       - `protobuf==3.20.2` - Protobuf（StreamDiffusion setup.py 要求）
       - `polygraphy==0.47.1` - TensorRT 工具链（StreamDiffusion 要求）
       - `onnx-graphsurgeon==0.3.26` - ONNX 图操作工具（StreamDiffusion 要求）
       - **注意**：PyTorch 2.1.0 不需要 `onnxscript`（只有 PyTorch 2.9+ 需要）

       **注意**：所有版本必须严格按照 StreamDiffusion 的要求，不能使用其他版本。

### 6. 验证安装

```bash
# 验证 Python 环境
python --version  # 应该显示 Python 3.10.x

# 验证关键依赖
python -c "import torch; print('PyTorch:', torch.__version__)"
python -c "import diffusers; print('Diffusers:', diffusers.__version__)"

# 如果安装了 TensorRT，验证 TensorRT 依赖
python -c "import tensorrt; print('TensorRT:', tensorrt.__version__)"
python -c "import onnx; print('ONNX:', onnx.__version__)"
python -c "import onnxruntime; print('ONNX Runtime:', onnxruntime.__version__)"
python -c "import cuda.bindings.runtime as cudart; print('CUDA Python: OK')"
```

### 7. 启动服务

```bash
# 确保配置文件存在
ls app/config/config.yaml

# 启动服务
./start.sh
```

## 常见问题

### Q1: 安装时提示 "No space left on device"

**解决方案**：
1. 运行 `./setup_env.sh` 配置缓存路径到数据盘
2. 激活缓存环境变量：`source /root/autodl-tmp/activate_cache.sh`
3. 重新安装依赖

### Q2: 导入错误 "cannot import name 'cudart' from 'cuda'"

**原因**：`cuda-python` 13.0.3 改变了 API 结构

**解决方案**：
- 确保使用 `cuda-python>=12.0.0`
- 代码中已修复为 `import cuda.bindings.runtime as cudart`

### Q3: 导入错误 "cannot import name 'opset23' from 'onnxscript.onnx_opset'"

**原因**：`onnxscript` 版本太旧，不支持 PyTorch 2.9 需要的 `opset23`

**解决方案**：
- 升级 `onnxscript` 到 `>=0.2.0`（推荐 `0.5.6`）
- 运行：`pip install "onnxscript>=0.2.0"`

### Q4: NumPy 版本冲突

**原因**：NumPy 2.x 与某些模块（如 `onnxruntime`）不兼容

**解决方案**：
- ✅ **已解决**：`requirements.txt` 中已固定 `numpy>=1.24.0,<2.0`
- 如果仍遇到问题，运行：`pip install "numpy>=1.24.0,<2.0" --force-reinstall`

### Q5: ONNX 版本不匹配

**原因**：使用了错误的 PyTorch 版本导致 ONNX 版本不匹配

**解决方案**：
- ✅ **已解决**：使用 PyTorch 2.1.0（StreamDiffusion 原始版本），ONNX 使用 `1.15.0`（StreamDiffusion setup.py 要求）
- 不要使用 PyTorch 2.9，会导致 ONNX 导出问题

### Q6: TensorRT 无法初始化 CUDA（错误码 35: cudaErrorInsufficientDriver）

**原因**：TensorRT 版本不正确，使用了不兼容的版本（如 TensorRT 10.x 需要 CUDA 13）

**解决方案**：
- ✅ **已解决**：严格按照 StreamDiffusion 的 `install-tensorrt.py` 安装 TensorRT 9.0.1
- 使用正确的安装命令：
  ```bash
  # CUDA 12.x
  pip install --pre --extra-index-url https://pypi.nvidia.com tensorrt==9.0.1.post12.dev4 --no-cache-dir
  
  # CUDA 11.x
  pip install --pre --extra-index-url https://pypi.nvidia.com tensorrt==9.0.1.post11.dev4 --no-cache-dir
  ```
- 或使用 StreamDiffusion 的安装脚本：
  ```bash
  python -m streamdiffusion.tools.install-tensorrt
  ```

**注意**：不要使用 `pip install tensorrt`，这会安装不兼容的版本。必须使用 NVIDIA PyPI 安装指定版本。

## 版本兼容性说明

### PyTorch 版本

- **必须**：PyTorch 2.1.0（StreamDiffusion 原始版本）
- **不要使用**：PyTorch 2.9+（会导致 ONNX 导出和 TensorRT 编译问题）

### CUDA 版本

- **推荐**：CUDA 12.1+（与 TensorRT 9.0+ 兼容性最好）
- **支持**：CUDA 11.8+

### TensorRT 版本

- **推荐**：TensorRT 9.0.0+
- 首次运行时会自动编译 TensorRT 引擎（需要一些时间）

## 依赖安装顺序（重要）

为了避免版本冲突，建议按以下顺序安装：

1. **基础 Python 环境**：Python 3.10 + Conda
2. **环境配置**：运行 `setup_env.sh`（可选）
3. **基础依赖**：`pip install -r requirements.txt`
4. **TensorRT 依赖**：`pip install -r requirements-tensorrt.txt`（如果使用 TensorRT）

## 快速安装脚本

如果你想要一键安装所有依赖，可以创建一个安装脚本：

```bash
#!/bin/bash
# install_all.sh

set -e

echo "=========================================="
echo "StreamDiffusion Backend 完整安装脚本"
echo "=========================================="

# 1. 创建环境（如果不存在）
if ! conda env list | grep -q "^rp "; then
    echo "创建 Conda 环境..."
    conda create -n rp python=3.10 -y
fi

# 2. 激活环境
echo "激活 Conda 环境..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate rp

# 3. 配置缓存（可选）
if [ -f "./setup_env.sh" ]; then
    echo "配置缓存路径..."
    ./setup_env.sh
    source /root/autodl-tmp/activate_cache.sh 2>/dev/null || true
fi

# 4. 安装基础依赖
echo "安装基础依赖..."
pip install -r requirements.txt

# 5. 安装 TensorRT 依赖
echo "安装 TensorRT 依赖..."
pip install -r requirements-tensorrt.txt

# 6. 验证安装
echo "验证安装..."
python -c "import torch; print('✓ PyTorch:', torch.__version__)"
python -c "import diffusers; print('✓ Diffusers:', diffusers.__version__)"
python -c "import tensorrt; print('✓ TensorRT:', tensorrt.__version__)" 2>/dev/null || echo "⚠ TensorRT 未安装（如果不需要 TensorRT 加速可以忽略）"

echo ""
echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 检查配置文件: app/config/config.yaml"
echo "2. 启动服务: ./start.sh"
```

保存为 `install_all.sh`，然后运行：

```bash
chmod +x install_all.sh
./install_all.sh
```

## 总结

**最小安装步骤**（不使用 TensorRT）：
```bash
conda create -n rp python=3.10 -y
conda activate rp
pip install -r requirements.txt
./start.sh
```

**完整安装步骤**（使用 TensorRT）：
```bash
conda create -n rp python=3.10 -y
conda activate rp
./setup_env.sh  # 可选，配置缓存路径
source /root/autodl-tmp/activate_cache.sh  # 如果运行了 setup_env.sh
pip install -r requirements.txt
pip install -r requirements-tensorrt.txt
./start.sh
```

