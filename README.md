# ArtFlow - 实时AI图像生成应用

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![SvelteKit](https://img.shields.io/badge/SvelteKit-latest-orange.svg)](https://kit.svelte.dev)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)

ArtFlow 是一个基于 StreamDiffusion 的实时 AI 图像生成应用，提供高性能的实时图像生成能力，支持多种生成模式和先进的AI功能。

## ✨ 主要特性

### 🎨 三种生成模式
- **实时模式 (Realtime)**: 使用摄像头输入进行实时图像到图像生成
- **画布模式 (Canvas)**: 基于手绘/素描进行图像生成
- **文本模式 (Text)**: 纯文本到图像生成

### 🚀 高性能优化
- **超低延迟**: < 100ms 实时生成延迟
- **多种加速**: 支持 xformers 内存优化
- **GPU 优化**: 智能内存管理和资源调度
- **流式传输**: WebSocket + HTTP 流媒体技术

### 🛠️ 高级功能
- **图像编辑**: 修复、扩展、超分辨率、高分辨率修复
- **LoRA 支持**: 动态加载和管理 LoRA 模型
- **图像编辑器**: 滤镜、色彩调整、变换工具
- **CLIP 集成**: 自动图像提示生成

### 💻 现代化界面
- **响应式设计**: 适配各种屏幕尺寸
- **实时预览**: 流畅的图像生成体验
- **键盘快捷键**: 高效的操作体验
- **暗色主题**: 护眼的用户界面

## 🏗️ 技术架构

### 后端架构
- **框架**: Python FastAPI + StreamDiffusion
- **通信**: WebSocket 实时双向通信
- **流媒体**: HTTP multipart/x-mixed-replace
- **配置系统**: YAML 配置 + 环境变量
- **模块化**: 管道模式支持功能扩展

### 前端架构
- **框架**: SvelteKit + TypeScript
- **样式**: Tailwind CSS
- **状态管理**: Svelte stores
- **实时通信**: WebSocket 客户端
- **构建工具**: Vite

## 🚀 快速开始

### 环境要求
- Python 3.10+
- CUDA 11.8+ 或 12.1+ (GPU加速)
- Node.js 16+ (前端开发)
- Docker 20.10+ (容器化部署)
- Docker Compose 2.0+ (容器化部署)
- 8GB+ VRAM (推荐 12GB+)

## 🐳 Docker 容器化部署 (推荐)

这是最简单和推荐的部署方式，支持一键启动！

### 快速启动

```bash
# 1. 克隆项目
git clone https://github.com/your-username/realtime_painting.git
cd realtime_painting

# 2. 一键启动
./quick-start.sh

# 或使用完整部署脚本
./deploy.sh

# 访问应用
# 🌐 API服务: http://localhost:8000
# 📚 API文档: http://localhost:8000/docs
```

### 完整功能部署

```bash
# 启动所有服务 (数据库、缓存、监控)
./deploy.sh --monitor --db --cache

# 开发环境 (包含前端热重载)
./deploy.sh -p dev -b

# 查看帮助
./deploy.sh --help
```

### Docker 部署特性
- ✅ 一键部署，自动配置
- ✅ GPU/CPU 自适应
- ✅ 多环境支持 (dev/prod)
- ✅ 完整监控体系
- ✅ 数据持久化
- ✅ 健康检查
- ✅ 自动扩缩容

## 💻 手动部署

### 后端设置

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装 xformers 加速 (推荐)
pip install -r requirements-xformers.txt

# 4. 配置环境变量
cp .env.docker .env
# 编辑 .env 文件配置模型路径等参数

# 5. 启动后端服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端设置

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev

# 4. 构建生产版本
npm run build
npm run preview
```

## 📖 API 文档

启动后端服务后，访问以下地址：

- **API 文档**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/api/health

### 主要 API 端点

- `WebSocket: /api/ws/{userId}?mode={mode}` - 实时生成连接
- `GET /api/settings` - 获取配置信息
- `GET /api/queue` - 查询队列状态
- `GET /api/stream/{userId}` - 图像流传输

## 🎯 使用指南

### 实时模式
1. 打开浏览器访问 http://localhost:5173
2. 允许摄像头权限
3. 调整生成参数 (提示词、引导强度等)
4. 实时查看生成效果

### 画布模式
1. 切换到 Canvas 标签页
2. 使用画笔绘制草图
3. 添加文本提示
4. 生成精美图像

### 高级功能
- **ControlNet**: 在控制面板中添加控制网络
- **LoRA 管理**: 在模型管理器中加载 LoRA 模型
- **图像编辑**: 使用内置编辑器进行后处理

## 🔧 配置说明

### 主要配置文件: `app/config.yaml`

```yaml
model:
  model_id: "stabilityai/sd-turbo"
  acceleration: "xformers"  # xformers | none

pipeline:
  name: "realtime"
  mode: "image"
  width: 512
  height: 512
  use_tiny_vae: true
  use_lcm_lora: true

performance:
  enable_similar_image_filter: false
  jpeg_quality: 85

server:
  host: "0.0.0.0"
  port: 8000
  max_queue_size: 0
```

### 环境变量

```bash
# 模型配置
STREAMDIFFUSION_MODEL_ID="stabilityai/sd-turbo"
STREAMDIFFUSION_ACCELERATION="xformers"  # 推荐使用 xformers

# 服务器配置
STREAMDIFFUSION_HOST="0.0.0.0"
STREAMDIFFUSION_PORT="8000"

# 安全配置
STREAMDIFFUSION_CORS_ORIGINS="http://localhost:5173"
```

## 🧪 测试

### 后端测试

```bash
# 运行依赖检查
python -m app.tests.test_dependencies

# 运行管道基础测试
python -m app.tests.test_pipeline_base

# 运行所有测试
pytest app/tests/
```

### 前端测试

```bash
cd frontend

# 运行组件测试
npm run test

# 类型检查
npm run check

# 代码检查
npm run lint
```

## 📊 性能指标

在 **GPU: RTX 4090**, **CPU: Core i9-13900K**, **OS: Ubuntu 22.04** 环境下的测试结果：

| 模式 | 分辨率 | 生成步骤 | FPS | 延迟 |
|------|--------|----------|-----|------|
| 实时模式 | 512x512 | 1 | 90+ | < 50ms |
| 画布模式 | 512x512 | 4 | 25+ | < 100ms |
| 文本模式 | 512x512 | 4 | 20+ | < 120ms |

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 开发流程
1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 代码规范
- 后端: 遵循 PEP 8，使用 black 格式化
- 前端: 使用 ESLint + Prettier 格式化
- 提交信息: 遵循 Conventional Commits

## 📝 更新日志

### v1.0.0 (2024-01-26)
- ✨ 添加 LoRA 管理功能
- ✨ 增强管道选项配置
- ✨ 更新环境配置系统
- 🛠️ 修复内存和GPU显存泄漏问题
- 🚀 优化资源管理和性能
- ✨ 添加全屏预览功能
- ✨ 优化会话处理和画布清理

### v0.9.0 (2024-01-20)
- 🎨 初始版本发布
- ✨ 支持三种生成模式
- ✨ 实现 WebSocket 实时通信
- ✨ 集成 StreamDiffusion 引擎

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [StreamDiffusion](https://github.com/cumulo-autumn/StreamDiffusion) - 核心生成引擎
- [FastAPI](https://fastapi.tiangolo.com/) - 后端 Web 框架
- [SvelteKit](https://kit.svelte.dev/) - 前端框架
- [Stability AI](https://stability.ai/) - 模型支持

## 📞 支持

- 📧 邮箱: support@artflow.dev
- 💬 讨论: [GitHub Discussions](https://github.com/your-username/realtime_painting/discussions)
- 🐛 问题: [GitHub Issues](https://github.com/your-username/realtime_painting/issues)
- 📖 文档: [项目 Wiki](https://github.com/your-username/realtime_painting/wiki)

---

<div align="center">
  <p>如果这个项目对您有帮助，请给我们一个 ⭐️</p>
  <p>Made with ❤️ by ArtFlow Team</p>
</div>