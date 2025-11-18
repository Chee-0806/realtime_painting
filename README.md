# StreamDiffusion Backend

基于 StreamDiffusion 的实时图像生成后端服务，为前端提供高性能的 AI 图像生成能力。

## 特性

- ⚡ **实时生成**：基于 StreamDiffusion 优化，单帧延迟 < 100ms
- 🚀 **多种加速**：支持 xformers、TensorRT 等加速方式
- 🎨 **双模式支持**：Image Mode (img2img) 和 Video Mode (txt2img)
- 🔌 **WebSocket 通信**：低延迟的双向实时通信
- 📡 **HTTP 图像流**：通过 multipart/x-mixed-replace 持续推送
- 🔧 **灵活配置**：YAML 配置文件 + 环境变量
- 🐳 **Docker 支持**：一键部署，支持 NVIDIA GPU

## 系统要求

- **操作系统**：Linux (Ubuntu 20.04+)
- **Python**：3.10+
- **CUDA**：11.8+ 或 12.1+
- **GPU**：NVIDIA GPU with 8GB+ VRAM
- **内存**：16GB+ RAM
- **磁盘空间**：20GB+

## 快速开始

### 1. 克隆仓库

```bash
git clone <repository-url>
cd streamdiffusion-backend
```

### 2. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装核心依赖
pip install -r requirements.txt

# 选择加速方式（二选一）
pip install -r requirements-xformers.txt  # 推荐：xformers
# 或
pip install -r requirements-tensorrt.txt  # TensorRT（需要更多配置）
```

### 3. 配置

复制配置文件并根据需要修改：

```bash
cp .env.example .env
```

编辑 `app/config/config.yaml` 配置模型和参数：

```yaml
model:
  model_id: "stabilityai/sd-turbo"
  acceleration: "xformers"  # xformers | tensorrt | none

pipeline:
  name: "img2img"
  mode: "image"  # image | video
  width: 512
  height: 512
```

### 4. 运行服务

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

或使用 Python 直接运行：

```bash
python -m app.main
```

服务将在 `http://localhost:8000` 启动。

## Docker 部署

### 使用 Docker Compose（推荐）

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 使用 Docker

```bash
# 构建镜像
docker build -t streamdiffusion-backend .

# 运行容器
docker run -d \
  --name streamdiffusion-backend \
  --gpus all \
  -p 8000:8000 \
  -v $(pwd)/engines:/app/engines \
  streamdiffusion-backend
```

## API 文档

### WebSocket API

连接到 `/api/ws/{userId}` 进行实时通信。

**协议流程**：

1. 客户端连接 → 服务器发送 `{"status": "connected"}`
2. 服务器发送 `{"status": "send_frame"}`
3. 客户端发送 `{"status": "next_frame"}`
4. 客户端发送参数 JSON：`{"prompt": "...", "guidance_scale": 7.5, ...}`
5. 客户端发送图像数据（仅 image 模式）
6. 重复步骤 2-5

**示例（JavaScript）**：

```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/user123?mode=image');

ws.onmessage = async (event) => {
  const data = JSON.parse(event.data);
  
  if (data.status === 'send_frame') {
    // 发送 next_frame 消息
    ws.send(JSON.stringify({ status: 'next_frame' }));
    
    // 发送参数
    ws.send(JSON.stringify({
      prompt: 'a beautiful landscape',
      guidance_scale: 7.5,
      num_inference_steps: 4
    }));
    
    // 发送图像（如果是 image 模式）
    const imageBlob = await captureImage();
    ws.send(imageBlob);
  }
};
```

### HTTP API

#### GET /api/settings

获取后端配置信息。

**响应**：

```json
{
  "input_params": {
    "properties": {
      "prompt": {
        "default": "",
        "title": "Prompt",
        "type": "string",
        "field": "textarea"
      },
      "guidance_scale": {
        "default": 7.5,
        "title": "Guidance Scale",
        "type": "number",
        "min": 1.0,
        "max": 20.0,
        "field": "range"
      }
    }
  },
  "info": {
    "properties": {
      "title": "StreamDiffusion Backend",
      "input_mode": {
        "default": "image"
      }
    }
  },
  "max_queue_size": 0
}
```

#### GET /api/queue

获取队列状态。

**响应**：

```json
{
  "queue_size": 0
}
```

#### GET /api/stream/{userId}

获取实时图像流（multipart/x-mixed-replace）。

**参数**：
- `quality`: JPEG 质量（1-100），默认 85
- `max_fps`: 最大帧率，默认 30

**示例**：

```html
<img src="http://localhost:8000/api/stream/user123?quality=85&max_fps=30" />
```

## 配置说明

### 模型配置

```yaml
model:
  model_id: "stabilityai/sd-turbo"  # Hugging Face 模型 ID
  acceleration: "xformers"  # 加速方式
  engine_dir: "engines"  # TensorRT 引擎缓存目录
  use_cuda_graph: false  # CUDA Graph 优化
```

### Pipeline 配置

```yaml
pipeline:
  name: "img2img"  # Pipeline 类型
  mode: "image"  # 输入模式
  width: 512  # 图像宽度（必须是 8 的倍数）
  height: 512  # 图像高度（必须是 8 的倍数）
  use_tiny_vae: true  # 使用 Tiny VAE
  use_lcm_lora: true  # 使用 LCM LoRA
  warmup: 10  # Warmup 步骤数
```

### 性能配置

```yaml
performance:
  enable_similar_image_filter: false  # 相似图像过滤
  similar_image_filter_threshold: 0.98  # 相似度阈值
  similar_image_filter_max_skip_frame: 10  # 最大跳帧数
  jpeg_quality: 85  # 图像流 JPEG 质量
```

### 环境变量

可以通过环境变量覆盖配置：

```bash
export STREAMDIFFUSION_MODEL__MODEL_ID="stabilityai/sd-turbo"
export STREAMDIFFUSION_MODEL__ACCELERATION="xformers"
export STREAMDIFFUSION_PIPELINE__WIDTH=512
export STREAMDIFFUSION_PIPELINE__HEIGHT=512
```

## 加速方式

### xformers（推荐）

最简单的加速方式，显著降低显存占用。

```bash
pip install -r requirements-xformers.txt
```

配置：

```yaml
model:
  acceleration: "xformers"
```

### TensorRT

最高性能，但首次运行需要编译引擎（5-10 分钟）。

```bash
pip install -r requirements-tensorrt.txt
```

配置：

```yaml
model:
  acceleration: "tensorrt"
  engine_dir: "engines"
  use_cuda_graph: true  # 可选，进一步优化
```

**注意**：
- 引擎会缓存在 `engine_dir` 目录
- 更改模型、尺寸或 batch_size 需要重新编译
- prompt 等运行时参数可以动态更新

### 无加速

使用默认 PyTorch 实现。

```yaml
model:
  acceleration: "none"
```

## 故障排除

### CUDA 内存不足

- 降低图像尺寸（width/height）
- 使用 Tiny VAE
- 启用 xformers

### TensorRT 编译失败

- 检查 CUDA 版本兼容性
- 确保安装了正确的 TensorRT 版本
- 查看日志获取详细错误信息

### 依赖版本冲突

运行依赖检查：

```python
from app.core.dependencies import DependencyChecker

checker = DependencyChecker()
is_valid, errors = checker.check_all("xformers")

if not is_valid:
    for error in errors:
        print(error)
    
    recommended = checker.get_recommended_versions("xformers")
    print("推荐版本:", recommended)
```

## 性能优化

### 相似图像过滤

跳过相似度过高的帧以节省计算：

```yaml
performance:
  enable_similar_image_filter: true
  similar_image_filter_threshold: 0.98
  similar_image_filter_max_skip_frame: 10
```

### GPU 内存管理

系统会自动清理 GPU 内存，也可以手动触发：

```python
from app.utils.performance import PerformanceOptimizer

PerformanceOptimizer.cleanup_gpu_memory()
PerformanceOptimizer.log_gpu_memory_info()
```

## 开发

### 项目结构

```
app/
├── main.py                 # FastAPI 应用入口
├── config/                 # 配置管理
│   ├── settings.py
│   └── config.yaml
├── core/                   # 核心组件
│   ├── engine.py          # StreamDiffusion 引擎
│   ├── session.py         # 会话管理
│   └── dependencies.py    # 依赖检查
├── api/                    # API 层
│   ├── websocket.py       # WebSocket 处理
│   ├── http.py            # HTTP API
│   └── stream.py          # 图像流
├── pipelines/              # Pipeline 实现
│   ├── base.py
│   ├── img2img.py
│   └── txt2img.py
└── utils/                  # 工具函数
    ├── image.py
    ├── performance.py
    └── logger.py
```

### 添加新 Pipeline

1. 在 `app/pipelines/` 创建新文件
2. 继承 `BasePipeline` 并实现所有抽象方法
3. 类名必须为 `Pipeline`
4. 在配置中指定 Pipeline 名称

示例：

```python
from app.pipelines.base import BasePipeline

class Pipeline(BasePipeline):
    # 实现所有抽象方法
    pass
```

## 许可证

[添加许可证信息]

## 致谢

- [StreamDiffusion](https://github.com/cumulo-autumn/StreamDiffusion)
- [Stable Diffusion](https://github.com/Stability-AI/stablediffusion)
- [FastAPI](https://fastapi.tiangolo.com/)
