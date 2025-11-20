# 环境配置说明

## 概述

为了避免占用系统盘空间，所有缓存和虚拟环境都配置到 `/root/autodl-tmp` 数据盘。

## 快速开始

### 1. 运行环境配置脚本

```bash
cd /root/realtime_painting
./setup_env.sh
```

这个脚本会：
- 在数据盘创建所有缓存目录
- 配置环境变量
- 创建符号链接
- 生成激活脚本

### 2. 激活缓存环境（可选）

如果需要在当前 shell 中手动激活：

```bash
source /root/autodl-tmp/activate_cache.sh
```

**注意**：`start.sh` 启动脚本会自动加载缓存环境，通常不需要手动激活。

### 3. 启动服务

```bash
./start.sh
```

## 缓存目录结构

所有缓存存储在 `/root/autodl-tmp`：

```
/root/autodl-tmp/
├── cache/
│   ├── pip/              # pip 包缓存
│   ├── huggingface/      # Hugging Face 模型缓存
│   ├── transformers/     # Transformers 缓存
│   ├── torch/            # PyTorch 缓存
│   └── xdg/              # XDG 缓存
└── conda-envs/           # Conda 环境（如果使用）
```

## 环境变量

配置脚本会设置以下环境变量：

- `PIP_CACHE_DIR`: pip 缓存目录
- `HF_HOME`: Hugging Face 主目录
- `TRANSFORMERS_CACHE`: Transformers 缓存
- `HF_DATASETS_CACHE`: Hugging Face 数据集缓存
- `TORCH_HOME`: PyTorch 缓存
- `CONDA_ENVS_PATH`: Conda 环境路径

## 验证配置

检查缓存路径：

```bash
# 检查 pip 缓存
echo $PIP_CACHE_DIR

# 检查 Hugging Face 缓存
echo $HF_HOME

# 检查 PyTorch 缓存
echo $TORCH_HOME
```

## 清理缓存

如果需要清理缓存释放空间：

```bash
# 清理 pip 缓存
rm -rf /root/autodl-tmp/cache/pip/*

# 清理 Hugging Face 缓存（注意：会删除已下载的模型）
rm -rf /root/autodl-tmp/cache/huggingface/*

# 清理所有缓存
rm -rf /root/autodl-tmp/cache/*
```

## 注意事项

1. **首次运行**：首次运行 `setup_env.sh` 后，建议重启终端或运行 `source activate_cache.sh` 使环境变量生效。

2. **模型下载**：首次下载模型时，会保存到 `/root/autodl-tmp/cache/huggingface/`，不会占用系统盘。

3. **Conda 环境**：如果使用 Conda，环境会创建在 `/root/autodl-tmp/conda-envs/`。

4. **符号链接**：脚本会创建符号链接，确保兼容性。如果遇到问题，可以删除符号链接重新运行脚本。

## 故障排除

### 问题：环境变量未生效

**解决**：
```bash
source /root/autodl-tmp/activate_cache.sh
```

### 问题：缓存仍然在系统盘

**解决**：
1. 检查环境变量是否正确设置
2. 删除系统盘的缓存目录
3. 重新运行 `setup_env.sh`

### 问题：权限错误

**解决**：
```bash
chmod +x setup_env.sh
sudo ./setup_env.sh  # 如果需要
```

