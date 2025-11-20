# RESTful API 设计规范

## 接口设计原则

1. **使用资源名词**：使用复数形式表示资源集合
2. **使用 HTTP 方法**：GET（查询）、POST（创建）、PUT（更新）、DELETE（删除）
3. **层次清晰**：资源嵌套合理，子资源表示相关操作
4. **语义明确**：接口路径清晰表达资源关系

## 实时生成 API

### 会话管理
- `POST /api/realtime/sessions` - 创建会话（可选，返回 session_id）
- `GET /api/realtime/sessions/{session_id}` - 获取会话信息
- `DELETE /api/realtime/sessions/{session_id}` - 删除会话
- `GET /api/realtime/sessions` - 获取所有会话列表（可选）

### WebSocket 连接
- `WS /api/realtime/sessions/{session_id}/ws` - WebSocket 连接

### 图像流
- `GET /api/realtime/sessions/{session_id}/stream` - 获取图像流

### 队列状态
- `GET /api/realtime/sessions/{session_id}/queue` - 获取会话队列状态
- `GET /api/realtime/queue` - 获取全局队列状态

### 配置
- `GET /api/realtime/settings` - 获取实时生成配置

## 画板 API

### 会话管理
- `POST /api/canvas/sessions` - 创建会话（可选，返回 session_id）
- `GET /api/canvas/sessions/{session_id}` - 获取会话信息
- `DELETE /api/canvas/sessions/{session_id}` - 删除会话
- `GET /api/canvas/sessions` - 获取所有会话列表（可选）

### WebSocket 连接
- `WS /api/canvas/sessions/{session_id}/ws` - WebSocket 连接

### 图像流
- `GET /api/canvas/sessions/{session_id}/stream` - 获取图像流

### 队列状态
- `GET /api/canvas/sessions/{session_id}/queue` - 获取会话队列状态
- `GET /api/canvas/queue` - 获取全局队列状态

### 配置
- `GET /api/canvas/settings` - 获取画板配置

## 通用 API（保持不变）

- `GET /api/models` - 获取模型列表
- `POST /api/models/switch` - 切换模型
- `GET /api/vaes` - 获取 VAE 列表
- `POST /api/vae/switch` - 切换 VAE
- `GET /api/schedulers` - 获取采样器列表
- `POST /api/scheduler/set` - 设置采样器
- `GET /api/health` - 健康检查
- `GET /api/acceleration` - 获取加速信息

## 接口对比

### 旧接口（不符合 RESTful）
```
WS /api/realtime/ws/{user_id}
GET /api/realtime/stream/{user_id}
GET /api/realtime/settings
GET /api/realtime/queue
```

### 新接口（符合 RESTful）
```
POST /api/realtime/sessions                    # 创建会话
WS /api/realtime/sessions/{session_id}/ws      # WebSocket 连接
GET /api/realtime/sessions/{session_id}/stream # 图像流
GET /api/realtime/sessions/{session_id}        # 会话信息
GET /api/realtime/sessions/{session_id}/queue  # 会话队列
DELETE /api/realtime/sessions/{session_id}     # 删除会话
GET /api/realtime/settings                     # 配置
GET /api/realtime/queue                        # 全局队列
```

## 实施说明

1. **向后兼容**：保持旧接口可用，但标记为 deprecated
2. **渐进迁移**：前端逐步迁移到新接口
3. **文档更新**：更新 API 文档，说明新接口规范

