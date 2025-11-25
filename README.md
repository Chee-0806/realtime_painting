# ArtFlow - 实时 AI 图像生成应用

基于 StreamDiffusion 的实时 AI 图像生成应用，支持多种生成模式和高级功能。

## ✨ 特性

- 🎨 **多种生成模式**：
  - **Realtime Mode**：实时摄像头图像生成（img2img）
  - **Canvas Mode**：画板绘制图像生成（img2img）
  - **Text Mode**：文本生成图像（txt2img）
- ⚡ **高性能生成**：基于 StreamDiffusion 优化，单帧延迟 < 100ms
- 🚀 **多种加速方式**：支持 xformers、TensorRT 等加速技术
- 🔌 **实时通信**：WebSocket 低延迟双向通信 + HTTP 图像流
- 🎛️ **高级功能**：ControlNet、Inpainting、Outpainting、HiresFix、Upscale 等
- 🖼️ **图像编辑**：内置图像编辑器，支持滤镜、色彩调整等功能
- 🔧 **灵活配置**：YAML 配置文件 + 环境变量支持
- 🐳 **Docker 部署**：一键部署，支持 NVIDIA GPU
- 📱 **现代界面**：SvelteKit + Tailwind CSS 响应式设计

## 🖥️ 系统要求

### 最低要求
- **操作系统**：Linux (Ubuntu 20.04+) / macOS / Windows
- **Python**：3.10+
- **CUDA**：11.8+ 或 12.1+（仅 GPU 加速）
- **GPU**：NVIDIA GPU with 8GB+ VRAM（推荐）
- **内存**：16GB+ RAM
- **磁盘空间**：20GB+

### 推荐配置
- **GPU**：NVIDIA RTX 4070+ with 12GB+ VRAM
- **内存**：32GB+ RAM
- **存储**：SSD with 50GB+ 空间（模型缓存）

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

主要配置文件为 `app/config.yaml`，包含所有设置选项：

```yaml
# 模型配置
model:
  model_id: "stabilityai/sd-turbo"  # Hugging Face 模型 ID
  acceleration: "xformers"         # 加速方式：xformers | tensorrt | none
  use_tiny_vae: true              # 使用 Tiny VAE 提升速度
  use_lcm_lora: true              # 使用 LCM LoRA 减少步数

# Canvas 画板模式配置
canvas_generation:
  width: 512
  height: 512
  steps: 2          # 生成步数（建议 2-4）
  cfg_scale: 2.0    # 引导尺度
  denoise: 0.3      # 去噪强度

# Realtime 实时模式配置
realtime_generation:
  width: 512
  height: 512
  steps: 2
  cfg_scale: 2.0
  denoise: 0.3

# Text 文本生成模式配置
txt2img_generation:
  width: 512
  height: 512
  steps: 4          # txt2img 模式可以更多步数
  cfg_scale: 7.5    # 文本生成通常需要更高的引导尺度
  denoise: 0.0      # txt2img 模式不使用去噪

# 性能优化配置
realtime_performance:
  enable_similar_image_filter: true  # 启用相似图像过滤
  jpeg_quality: 85                  # 图像流质量
  max_fps: 30                       # 最大帧率
```

### 4. 配置环境变量（可选）

创建 `.env` 文件来覆盖默认配置：

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置文件
# 详见下方"配置说明"部分
```

### 5. 启动服务

#### 后端服务
```bash
# 开发模式
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式
python -m app.main
```

#### 前端服务
```bash
cd frontend

# 安装前端依赖
npm install

# 启动开发服务器
npm run dev
```

服务访问地址：
- **后端 API**：http://localhost:8000
- **前端界面**：http://localhost:5173
- **API 文档**：http://localhost:8000/docs

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

## 🎯 功能使用指南

### Realtime Mode（实时模式）
- **用途**：使用摄像头进行实时图像生成
- **操作**：
  1. 允许浏览器访问摄像头
  2. 调整生成参数（提示词、引导尺度等）
  3. 实时查看生成效果
- **适用场景**：实时特效、创意摄影

### Canvas Mode（画板模式）
- **用途**：手绘图像生成
- **操作**：
  1. 在画板上绘制草图
  2. 输入描述性提示词
  3. 生成高质量的图像作品
- **适用场景**：艺术创作、设计原型

### Text Mode（文本模式）
- **用途**：纯文本生成图像
- **操作**：
  1. 输入详细的文本描述
  2. 调整生成参数
  3. 点击生成按钮
- **适用场景**：概念设计、插图创作

### 高级功能

**ControlNet**：
- 支持 Canny、OpenPose、Depth 等多种控制方式
- 可同时使用多个 ControlNet

**图像编辑**：
- 局部重绘（Inpainting）
- 图像外扩（Outpainting）
- 高分辨率修复（HiresFix）
- 图像放大（Upscale）

**其他功能**：
- CLIP 反向提示词生成
- XYZ 参数网格搜索
- 图像滤镜和色彩调整
- 历史记录和撤销操作

## 📡 API 文档

### WebSocket API

**端点**：`ws://localhost:8000/api/ws/{userId}?mode={mode}`

**支持的模式**：
- `realtime` - 实时模式
- `canvas` - 画板模式

**协议流程**：

1. 客户端连接 → 服务器发送 `{"status": "connected"}`
2. 服务器发送 `{"status": "send_frame"}`
3. 客户端发送 `{"status": "next_frame"}`
4. 客户端发送参数 JSON
5. 客户端发送图像数据（仅 img2img 模式）
6. 重复步骤 2-5

**示例（JavaScript）**：

```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/user123?mode=realtime');

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

    // 发送图像（如果是 img2img 模式）
    const imageBlob = await captureImage();
    ws.send(imageBlob);
  }
};
```

### HTTP API

#### GET /api/realtime/settings
#### GET /api/canvas/settings

获取指定模式的配置信息。

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
      "cfg_scale": {
        "default": 2.0,
        "title": "CFG Scale",
        "type": "number",
        "min": 1.0,
        "max": 20.0,
        "field": "range"
      },
      "steps": {
        "default": 2,
        "title": "Steps",
        "type": "integer",
        "min": 1,
        "max": 50,
        "field": "range"
      }
    }
  },
  "info": {
    "properties": {
      "title": "ArtFlow",
      "input_mode": {
        "default": "image"
      }
    }
  },
  "max_queue_size": 0,
  "page_content": ""
}
```

#### GET /api/realtime/queue
#### GET /api/canvas/queue

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

#### GET /api/health

健康检查端点。

**响应**：

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET /docs

自动生成的 OpenAPI 文档（Swagger UI）。

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

## 🏗️ 项目架构

### 后端架构

```
app/
├── main.py                     # FastAPI 应用入口
├── config.py                   # 配置管理系统
├── config.yaml                 # 配置文件
├── api/                        # API 路由层
│   ├── __init__.py
│   ├── websocket.py           # WebSocket 连接处理
│   ├── canvas.py              # Canvas 模式 API
│   ├── realtime.py            # Realtime 模式 API
│   ├── models.py              # API 数据模型
│   └── session_base.py        # 会话基类
├── core/                       # 核心组件
│   ├── __init__.py
│   ├── engine.py              # StreamDiffusion 引擎封装
│   ├── session.py             # 会话管理
│   └── dependencies.py        # 依赖检查工具
├── pipelines/                  # 生成管道
│   ├── __init__.py
│   ├── base.py                # 管道基类
│   ├── canvas.py              # Canvas 画板管道
│   ├── realtime.py            # Realtime 实时管道
│   ├── txt2img.py             # Txt2Img 文本生成管道
│   ├── streamdiffusion_base.py # StreamDiffusion 基础管道
│   └── lora_utils.py          # LoRA 工具
├── services/                   # 业务服务
│   ├── session_service.py     # 会话服务
│   ├── resource_monitor.py    # 资源监控
│   └── runtime.py             # 运行时管理
├── utils/                      # 工具函数
│   ├── __init__.py
│   ├── image.py               # 图像处理工具
│   ├── performance.py         # 性能优化工具
│   └── logger.py              # 日志配置
└── tests/                      # 测试文件
    ├── __init__.py
    ├── test_dependencies.py   # 依赖检查测试
    └── test_pipeline_base.py  # 管道基类测试
```

### 前端架构

```
frontend/
├── src/
│   ├── lib/
│   │   ├── components/        # UI 组件
│   │   │   ├── ImagePlayer.svelte       # 图像播放器
│   │   │   ├── VideoInput.svelte        # 摄像头输入
│   │   │   ├── PipelineOptions.svelte   # 参数控制
│   │   │   ├── ModelManager.svelte      # 模型管理
│   │   │   ├── InpaintingPanel.svelte   # 局部重绘面板
│   │   │   ├── OutpaintingPanel.svelte  # 外扩绘画面板
│   │   │   ├── ControlNet*.svelte       # ControlNet 相关
│   │   │   └── ...                      # 其他高级功能组件
│   │   ├── utils/              # 工具函数
│   │   │   ├── websocket.ts     # WebSocket 管理器
│   │   │   ├── image.ts         # 图像处理
│   │   │   └── keyboard.ts      # 键盘快捷键
│   │   ├── store.ts            # 状态管理
│   │   └── types.ts            # TypeScript 类型定义
│   └── routes/                 # 页面路由
│       ├── +page.svelte        # Realtime 模式主页面
│       └── canvas/+page.svelte # Canvas 模式页面
├── package.json
└── vite.config.ts
```

### 技术栈

**后端**：
- **Web 框架**：FastAPI + uvicorn
- **AI 引擎**：StreamDiffusion + diffusers + transformers
- **深度学习**：PyTorch + CUDA
- **图像处理**：Pillow + OpenCV
- **配置管理**：Pydantic + python-dotenv

**前端**：
- **框架**：SvelteKit + TypeScript
- **样式**：Tailwind CSS
- **状态管理**：Svelte stores
- **构建工具**：Vite

**部署**：
- **容器化**：Docker + Docker Compose
- **GPU 支持**：NVIDIA Container Toolkit
- **代理**：Nginx（生产环境）

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
