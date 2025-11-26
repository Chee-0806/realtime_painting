# LoRA 集成使用说明

## 概述

ArtFlow 现已支持预制 LoRA 模型的自动下载和管理功能。用户可以在下拉菜单中直接选择预制 LoRA 模型，系统会自动下载并集成到实时绘画流程中。

## 功能特性

### ✅ 已实现功能

1. **预制 LoRA 选项**
   - 在 LoRA 下拉菜单中显示可用的预制模型
   - 支持 LCM 加速 LoRA 和各种风格化 LoRA
   - 使用国内镜像源（HF Mirror、ModelScope）

2. **自动下载功能**
   - 选择预制 LoRA 后自动开始下载
   - 实时下载进度显示
   - 支持断点续传和下载取消

3. **智能管理**
   - 自动检测已下载的 LoRA 文件
   - 文件完整性验证
   - 下载历史记录和统计

4. **用户友好界面**
   - 直观的 LoRA 管理器界面
   - 实时进度条和状态显示
   - 分类展示加速类和风格类 LoRA

## 快速开始

### 1. 安装依赖

```bash
# 进入项目目录
cd /Users/xuqi/Codes/realtime_painting

# 安装依赖（包含 LoRA 下载功能）
pip install -r requirements.txt

# 或添加缺失的依赖
pip install aiohttp>=3.8.0
```

### 2. 启动服务

```bash
# 启动后端服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 启动前端服务
cd frontend
npm run dev
```

### 3. 使用 LoRA 功能

#### 方法一：通过参数面板
1. 打开 ArtFlow 界面
2. 在参数配置中找到 "LoRA Selection" 下拉菜单
3. 选择带有 "📥" 前缀的预制 LoRA 模型
4. 系统会自动开始下载
5. 下载完成后即可使用

#### 方法二：通过 LoRA 管理器
1. 在 LoRA Selection 下方点击 "📦 LoRA 管理器" 按钮
2. 浏览可用的 LoRA 模型
3. 点击 "📥 下载" 按钮下载需要的模型
4. 下载完成后返回主界面使用

## 可用的预制 LoRA 模型

### ⚡ 加速类 LoRA

| 模型名称 | 描述 | 大小 | 适用模型 |
|---------|------|------|----------|
| LCM LoRA (SD 1.5) | Latent Consistency Model - 大幅加速生成 | 180MB | SD 1.5, SD-Turbo |
| LCM LoRA (SDXL) | Stable Diffusion XL LCM - 高质量高速生成 | 340MB | SDXL |

### 🎨 风格类 LoRA

| 模型名称 | 描述 | 大小 | 适用模型 |
|---------|------|------|----------|
| 动漫风格 LoRA | 日本动漫风格 - 适合角色和场景生成 | 45MB | SD 1.5, SD-Turbo |
| 写实风格 LoRA | 摄影写实风格 - 生成逼真的照片效果 | 38MB | SD 1.5, SD-Turbo |
| 油画风格 LoRA | 油画艺术风格 - 经典绘画效果 | 52MB | SD 1.5, SD-Turbo |
| 赛博朋克 LoRA | 未来科幻风格 - 赛博朋克美学 | 41MB | SD 1.5, SD-Turbo |

## API 接口

### 获取所有 LoRA 预设
```http
GET /api/lora/presets
```

### 获取下载状态
```http
GET /api/lora/download/status
```

### 开始下载
```http
POST /api/lora/download/{preset_id}
Content-Type: application/json

{
  "preset_id": "lcm-sdv1-5",
  "mirror_index": 0
}
```

### 取消下载
```http
POST /api/lora/download/{preset_id}/cancel
```

### 删除 LoRA 文件
```http
DELETE /api/lora/presets/{preset_id}
```

### 实时进度 (WebSocket)
```javascript
const ws = new WebSocket('ws://localhost:8000/api/lora/ws/progress');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'progress_update') {
    console.log('下载进度:', data.tasks);
  }
};
```

## 配置文件

### 预设配置文件位置
```
app/pipelines/presets.yaml
```

### LoRA 存储目录
```
app/lib/StreamDiffusion/models/LoRA/
```

### 下载统计信息
```
app/lib/StreamDiffusion/models/LoRA/.download_stats.json
```

## 手动添加 LoRA 模型

### 方法一：直接复制文件
```bash
# 将 LoRA 文件复制到指定目录
cp your_lora_model.safetensors /Users/xuqi/Codes/realtime_painting/app/lib/StreamDiffusion/models/LoRA/
```

### 方法二：添加到预设配置
编辑 `app/pipelines/presets.yaml`：

```yaml
presets:
  - id: "your-custom-lora"
    name: "自定义 LoRA"
    description: "你的自定义 LoRA 模型"
    mirrors:
      - url: "https://your-mirror-url.com/lora.safetensors"
        name: "镜像源"
    filename: "custom_lora.safetensors"
    size: "50MB"
    model_type: "style"
    compatible_models: ["runwayml/stable-diffusion-v1-5"]
    tags: ["custom", "style"]
```

## 性能建议

1. **推荐优先下载 LCM LoRA**
   - 可以显著提升生成速度（5-10倍）
   - 支持实时绘画的低延迟需求

2. **存储空间管理**
   - LoRA 文件大小从 30MB 到 340MB 不等
   - 建议定期清理不需要的 LoRA 文件

3. **网络优化**
   - 系统自动选择国内镜像源，下载速度较快
   - 支持断点续传，网络中断后可恢复下载

## 故障排除

### 常见问题

1. **下载失败**
   - 检查网络连接
   - 尝试切换镜像源
   - 查看错误信息了解具体原因

2. **LoRA 选择后无效果**
   - 确认 LoRA 文件已完整下载
   - 检查 LoRA 与当前基础模型的兼容性

3. **性能问题**
   - 使用 LCM LoRA 可以大幅提升速度
   - 关闭不需要的 LoRA 以节省内存

### 日志查看

```bash
# 查看后端日志
tail -f logs/app.log

# 查看特定错误
grep "LoRA" logs/app.log
```

## 开发者信息

### 核心文件结构
```
app/
├── pipelines/
│   ├── lora_downloader.py    # LoRA 下载管理器
│   ├── lora_utils.py         # LoRA 工具函数
│   ├── presets.yaml          # 预设配置
│   └── streamdiffusion_base.py  # 基础管道
├── api/
│   └── lora.py               # LoRA API 路由
└── main.py                   # 主应用（包含路由注册）

frontend/src/lib/components/
└── LoRADownloader.svelte     # 前端 LoRA 管理组件
```

### 扩展开发
- 添加新的预制 LoRA：编辑 `presets.yaml`
- 自定义下载逻辑：修改 `lora_downloader.py`
- 扩展前端功能：修改 `LoRADownloader.svelte`

## 更新日志

- **v1.0** (2025-11-26)
  - ✨ 新增预制 LoRA 下载功能
  - ✨ 支持国内镜像源
  - ✨ 实时下载进度显示
  - ✨ WebSocket 实时通信
  - 🔧 集成到现有参数面板
  - 📚 完整的 API 文档