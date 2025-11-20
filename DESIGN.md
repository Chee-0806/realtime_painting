# 实时生成与画板功能分离设计文档

## 1. 背景与问题分析

### 1.1 现状
当前系统中，实时生成功能和画板功能共用同一套后端接口：
- WebSocket: `/api/ws/{user_id}`
- 图像流: `/api/stream/{user_id}`
- 共享同一个 Pipeline 实例

### 1.2 问题
1. **接口耦合**：两个功能使用相同接口，难以独立维护和优化
2. **优化策略冲突**：
   - 实时生成需要相似图像过滤和跳帧优化（高帧率、低延迟）
   - 画板需要确保每次绘制都被处理（质量优先、不跳帧）
3. **资源竞争**：共享 Pipeline 实例可能导致资源竞争和性能问题
4. **扩展困难**：未来添加新功能时，难以在不影响其他功能的情况下进行优化

### 1.3 场景差异

#### 实时生成场景
- **输入源**：摄像头视频流（30fps+）
- **特点**：
  - 连续、高频输入
  - 变化渐进（相邻帧相似度高）
  - 需要快速响应
- **优化需求**：
  - 启用相似图像过滤
  - 允许跳帧处理
  - 低延迟优先
  - 高吞吐量

#### 画板场景
- **输入源**：用户绘制画布（事件驱动）
- **特点**：
  - 离散、不连续输入
  - 每次绘制变化显著
  - 用户期望每次绘制都被处理
- **优化需求**：
  - 禁用相似图像过滤
  - 不跳帧，确保每次绘制都被处理
  - 质量优先
  - 响应性优先

## 2. 设计目标

### 2.1 核心目标
1. **接口分离**：实时生成和画板使用独立的 API 接口
2. **优化策略分离**：为不同场景配置最适合的优化策略
3. **资源隔离**：使用独立的 Pipeline 实例，避免相互影响
4. **向后兼容**：确保现有画板功能不受影响

### 2.2 非功能性目标
- **可维护性**：代码结构清晰，职责分明
- **可扩展性**：易于添加新功能和优化策略
- **性能**：各场景使用最优的优化策略
- **稳定性**：两个功能互不影响，独立运行

## 3. 架构设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI Application                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────┐      ┌──────────────────────┐     │
│  │  实时生成 API 模块    │      │    画板 API 模块      │     │
│  │  /api/realtime/*     │      │   /api/canvas/*      │     │
│  └──────────┬───────────┘      └──────────┬──────────┘     │
│             │                               │                │
│             ▼                               ▼                │
│  ┌──────────────────────┐      ┌──────────────────────┐     │
│  │  Realtime Pipeline   │      │   Canvas Pipeline    │     │
│  │  (相似过滤: 启用)     │      │  (相似过滤: 禁用)    │     │
│  │  (跳帧: 允许)         │      │  (跳帧: 禁用)         │     │
│  └──────────┬───────────┘      └──────────┬──────────┘     │
│             │                               │                │
│             └───────────────┬───────────────┘                │
│                             ▼                                 │
│                  ┌──────────────────────┐                     │
│                  │  StreamDiffusion     │                     │
│                  │  Engine (共享)       │                     │
│                  └──────────────────────┘                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 模块划分

#### 3.2.1 API 层
- **`app/api/realtime.py`**：实时生成专用 API
  - WebSocket: `/api/realtime/ws/{user_id}`
  - 图像流: `/api/realtime/stream/{user_id}`
  - 设置: `/api/realtime/settings`

- **`app/api/canvas.py`**：画板专用 API
  - WebSocket: `/api/canvas/ws/{user_id}`
  - 图像流: `/api/canvas/stream/{user_id}`
  - 设置: `/api/canvas/settings`

#### 3.2.2 Pipeline 层
- **`app/pipelines/realtime_pipeline.py`**：实时生成专用 Pipeline
  - 启用相似图像过滤
  - 允许跳帧
  - 优化低延迟

- **`app/pipelines/canvas_pipeline.py`**：画板专用 Pipeline
  - 禁用相似图像过滤
  - 不跳帧
  - 优化质量

#### 3.2.3 配置层
- **`app/config/config.yaml`**：分离的配置
  - `realtime.performance.*`：实时生成优化配置
  - `canvas.performance.*`：画板优化配置

## 4. 接口设计

### 4.1 实时生成接口

#### 4.1.1 WebSocket 连接
```
WS /api/realtime/ws/{user_id}
```

**协议流程**：
1. 客户端连接 WebSocket
2. 服务器发送 `{"status": "connected"}`
3. 服务器发送 `{"status": "send_frame"}`
4. 客户端发送二进制消息：
   - 格式: `[4字节JSON长度] + [JSON数据] + [图像数据]`
   - JSON: `{"status": "next_frame", "prompt": "...", ...}`
5. 服务器处理并返回 `{"status": "send_frame"}` 继续循环

#### 4.1.2 图像流
```
GET /api/realtime/stream/{user_id}
Content-Type: multipart/x-mixed-replace; boundary=frame
```

**响应格式**：
```
--frame
Content-Type: image/jpeg
Content-Length: {size}

{JPEG数据}
--frame
...
```

#### 4.1.3 设置接口
```
GET /api/realtime/settings
```

**响应**：
```json
{
  "info": {...},
  "input_params": {...},
  "performance": {
    "enable_similar_image_filter": true,
    "similar_image_filter_threshold": 0.98,
    "similar_image_filter_max_skip_frame": 10,
    "max_fps": 30
  }
}
```

### 4.2 画板接口

#### 4.2.1 WebSocket 连接
```
WS /api/canvas/ws/{user_id}
```

**协议流程**：与实时生成相同，但使用不同的 Pipeline 实例

#### 4.2.2 图像流
```
GET /api/canvas/stream/{user_id}
Content-Type: multipart/x-mixed-replace; boundary=frame
```

#### 4.2.3 设置接口
```
GET /api/canvas/settings
```

**响应**：
```json
{
  "info": {...},
  "input_params": {...},
  "performance": {
    "enable_similar_image_filter": false,
    "max_fps": 0
  }
}
```

## 5. 优化策略设计

### 5.1 实时生成优化策略

#### 5.1.1 相似图像过滤
```python
# 配置
enable_similar_image_filter: true
similar_image_filter_threshold: 0.98  # 相似度阈值
similar_image_filter_max_skip_frame: 10  # 最大跳帧数
```

**原理**：
- 计算当前帧与上一帧的相似度
- 如果相似度 > 阈值，跳过当前帧
- 如果连续跳帧数 > 最大跳帧数，强制处理

**优势**：
- 减少不必要的推理计算
- 降低延迟
- 提高吞吐量

#### 5.1.2 帧率控制
```python
max_fps: 30  # 最大帧率限制
```

**实现**：
- 在图像流生成器中限制帧率
- 使用 `asyncio.sleep()` 控制帧间隔

#### 5.1.3 队列优化
```python
# 只处理最新帧，丢弃旧帧
async def get_latest_data(user_id):
    latest_data = None
    while not queue.empty():
        latest_data = queue.get_nowait()
    return latest_data
```

### 5.2 画板优化策略

#### 5.2.1 禁用相似图像过滤
```python
enable_similar_image_filter: false
```

**原因**：
- 用户每次绘制都是有意行为
- 需要确保每次绘制都被处理
- 质量优先于性能

#### 5.2.2 无帧率限制
```python
max_fps: 0  # 0 表示无限制
```

**原因**：
- 画板输入是事件驱动的，不是连续流
- 不需要限制帧率

#### 5.2.3 确保处理所有帧
```python
# 处理队列中的所有帧（不丢弃）
async def process_all_frames(user_id):
    while not queue.empty():
        frame = queue.get()
        process_frame(frame)
```

## 6. 配置设计

### 6.1 配置文件结构

```yaml
# app/config/config.yaml

# 模型配置（共享）
model:
  model_id: "stabilityai/sd-turbo"
  acceleration: "xformers"
  engine_dir: "engines"

# Pipeline 配置（共享）
pipeline:
  name: "img2img"
  mode: "image"
  width: 512
  height: 512
  use_tiny_vae: true

# 实时生成专用配置
realtime:
  performance:
    enable_similar_image_filter: true
    similar_image_filter_threshold: 0.98
    similar_image_filter_max_skip_frame: 10
    max_fps: 30
    priority: "latency"  # latency | quality
    jpeg_quality: 85

# 画板专用配置
canvas:
  performance:
    enable_similar_image_filter: false
    max_fps: 0  # 0 表示无限制
    priority: "quality"  # latency | quality
    jpeg_quality: 95  # 更高质量

# 服务器配置（共享）
server:
  host: "0.0.0.0"
  port: 8000
  max_queue_size: 0
  timeout: 0
```

### 6.2 配置加载

```python
# app/config/settings.py

class RealtimePerformanceConfig(BaseModel):
    enable_similar_image_filter: bool = True
    similar_image_filter_threshold: float = 0.98
    similar_image_filter_max_skip_frame: int = 10
    max_fps: int = 30
    priority: Literal["latency", "quality"] = "latency"
    jpeg_quality: int = 85

class CanvasPerformanceConfig(BaseModel):
    enable_similar_image_filter: bool = False
    max_fps: int = 0
    priority: Literal["latency", "quality"] = "quality"
    jpeg_quality: int = 95

class Settings(BaseModel):
    model: ModelConfig
    pipeline: PipelineConfig
    realtime: RealtimePerformanceConfig
    canvas: CanvasPerformanceConfig
    server: ServerConfig
    ...
```

## 7. 实施计划

### 7.1 阶段一：配置分离（1-2天）
1. 修改 `config.yaml`，添加 `realtime` 和 `canvas` 配置节
2. 更新 `settings.py`，添加对应的配置类
3. 验证配置加载正确

### 7.2 阶段二：Pipeline 分离（2-3天）
1. 创建 `app/pipelines/realtime_pipeline.py`
   - 继承或复用现有 Pipeline
   - 启用相似图像过滤
   - 配置跳帧参数
2. 创建 `app/pipelines/canvas_pipeline.py`
   - 继承或复用现有 Pipeline
   - 禁用相似图像过滤
   - 确保不跳帧
3. 在 `main.py` 中初始化两个独立的 Pipeline 实例

### 7.3 阶段三：API 分离（3-4天）
1. 创建 `app/api/realtime.py`
   - 实现 WebSocket 处理
   - 实现图像流处理
   - 使用 `realtime_pipeline`
2. 创建 `app/api/canvas.py`
   - 实现 WebSocket 处理
   - 实现图像流处理
   - 使用 `canvas_pipeline`
3. 在 `main.py` 中注册新路由

### 7.4 阶段四：前端适配（2-3天）
1. 修改 `frontend/src/lib/lcmLive.ts`
   - 更新 WebSocket URL: `/api/realtime/ws/{user_id}`
   - 更新图像流 URL: `/api/realtime/stream/{user_id}`
2. 修改 `frontend/src/routes/canvas/+page.svelte`
   - 更新 WebSocket URL: `/api/canvas/ws/{user_id}`
   - 更新图像流 URL: `/api/canvas/stream/{user_id}`
3. 测试两个功能是否正常工作

### 7.5 阶段五：测试与优化（2-3天）
1. 功能测试
   - 实时生成功能测试
   - 画板功能测试
   - 两个功能同时运行测试
2. 性能测试
   - 实时生成延迟测试
   - 画板响应性测试
   - 资源使用测试
3. 优化调整
   - 根据测试结果调整优化参数
   - 优化代码性能

## 8. 文件结构

### 8.1 新增文件

```
app/
├── api/
│   ├── realtime.py          # 新建：实时生成API
│   ├── canvas.py             # 新建：画板API
│   └── ...
├── pipelines/
│   ├── realtime_pipeline.py  # 新建：实时生成Pipeline
│   ├── canvas_pipeline.py    # 新建：画板Pipeline
│   └── ...
├── config/
│   ├── config.yaml           # 修改：添加分离配置
│   └── settings.py            # 修改：添加配置类
└── main.py                    # 修改：初始化两个Pipeline
```

### 8.2 修改文件

```
frontend/
├── src/
│   ├── lib/
│   │   └── lcmLive.ts         # 修改：更新URL
│   └── routes/
│       ├── +page.svelte       # 修改：更新URL
│       └── canvas/
│           └── +page.svelte   # 修改：更新URL
```

## 9. 风险评估

### 9.1 技术风险

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|----------|
| Pipeline 初始化失败 | 高 | 低 | 添加错误处理和回退机制 |
| 内存占用增加 | 中 | 中 | 监控内存使用，必要时优化 |
| 配置加载错误 | 中 | 低 | 添加配置验证和默认值 |
| 前端适配问题 | 低 | 中 | 充分测试，保持向后兼容 |

### 9.2 业务风险

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|----------|
| 画板功能受影响 | 高 | 低 | 充分测试，保持现有逻辑 |
| 实时生成功能不可用 | 高 | 低 | 修复现有问题，充分测试 |
| 性能下降 | 中 | 低 | 性能测试，优化调整 |

## 10. 测试计划

### 10.1 单元测试
- Pipeline 初始化测试
- 配置加载测试
- API 路由测试

### 10.2 集成测试
- 实时生成端到端测试
- 画板端到端测试
- 两个功能同时运行测试

### 10.3 性能测试
- 实时生成延迟测试
- 画板响应性测试
- 资源使用测试（CPU、GPU、内存）

### 10.4 兼容性测试
- 浏览器兼容性测试
- 不同设备测试

## 11. 后续优化方向

### 11.1 性能优化
- 动态调整优化参数
- 根据负载自动调整策略
- GPU 资源调度优化

### 11.2 功能扩展
- 支持更多输入源（视频文件、图片序列等）
- 支持更多输出格式
- 支持批量处理

### 11.3 监控与日志
- 添加性能监控
- 添加错误追踪
- 添加使用统计

## 12. 总结

本设计文档详细说明了如何将实时生成和画板功能分离，包括：

1. **接口分离**：使用不同的 API 路径，避免耦合
2. **优化策略分离**：为不同场景配置最适合的优化策略
3. **资源隔离**：使用独立的 Pipeline 实例，避免相互影响
4. **向后兼容**：确保现有功能不受影响

通过实施本方案，可以实现：
- 更好的可维护性
- 更好的性能优化
- 更好的扩展性
- 更好的稳定性

---

**文档版本**：v1.0  
**创建日期**：2024-01-XX  
**最后更新**：2024-01-XX  
**作者**：AI Assistant

