# ErrorHandler Component

## 概述

统一的错误处理组件，为整个应用提供一致的错误显示和用户反馈机制。

## 功能特性

### ✅ 已实现功能

1. **错误类型分类**
   - 网络错误 (NETWORK)
   - API错误 (API)
   - 验证错误 (VALIDATION)
   - 模型错误 (MODEL)
   - 生成错误 (GENERATION)
   - WebSocket错误 (WEBSOCKET)

2. **智能错误建议**
   - 根据错误类型自动生成解决建议
   - 支持自定义建议
   - 提供可操作的指导

3. **友好的用户界面**
   - 固定在右上角的通知
   - 平滑的滑入动画
   - 类型特定的图标
   - 清晰的错误信息层次
   - 可选的详细信息显示

4. **灵活的交互**
   - 点击关闭按钮
   - 可恢复错误显示"我知道了"按钮
   - 自动状态管理

## 文件结构

```
frontend/src/lib/
├── store.ts                              # 错误状态管理
├── components/
│   ├── ErrorHandler.svelte              # 主组件
│   ├── ErrorHandler.README.md           # 本文档
│   ├── ErrorHandler.test.md             # 测试指南
│   └── ErrorHandler.example.svelte      # 使用示例
```

## 快速开始

### 1. 导入组件

在任何页面中导入ErrorHandler组件：

```svelte
<script>
  import ErrorHandler from '$lib/components/ErrorHandler.svelte';
</script>

<ErrorHandler />
<!-- 你的页面内容 -->
```

### 2. 触发错误

使用 `setError` 函数显示错误：

```typescript
import { setError, ErrorType } from '$lib/store';

// 基本用法
setError({
  type: ErrorType.NETWORK,
  message: '无法连接到服务器',
  recoverable: true
});

// 带详细信息
setError({
  type: ErrorType.API,
  message: 'API请求失败',
  details: 'HTTP 500: Internal Server Error',
  recoverable: true
});

// 自定义建议
setError({
  type: ErrorType.MODEL,
  message: '模型加载失败',
  details: 'CUDA out of memory',
  recoverable: true,
  suggestions: [
    '关闭其他占用显存的程序',
    '尝试使用较小的模型',
    '减少batch size'
  ]
});
```

### 3. 清除错误

```typescript
import { clearError } from '$lib/store';

clearError();
```

## API 参考

### ErrorType 枚举

```typescript
enum ErrorType {
  NETWORK = 'network',      // 网络连接错误
  API = 'api',              // API调用错误
  VALIDATION = 'validation', // 参数验证错误
  MODEL = 'model',          // 模型相关错误
  GENERATION = 'generation', // 图像生成错误
  WEBSOCKET = 'websocket'   // WebSocket连接错误
}
```

### AppError 接口

```typescript
interface AppError {
  type: ErrorType;          // 错误类型
  message: string;          // 错误消息（必填）
  details?: string;         // 详细信息（可选）
  recoverable: boolean;     // 是否可恢复
  suggestions?: string[];   // 自定义建议（可选）
}
```

### 函数

#### setError(error: AppError)

显示错误通知。

**参数:**
- `error`: AppError对象

**示例:**
```typescript
setError({
  type: ErrorType.VALIDATION,
  message: '参数验证失败',
  details: 'steps must be between 1 and 50',
  recoverable: true
});
```

#### clearError()

清除当前显示的错误。

**示例:**
```typescript
clearError();
```

## 使用场景

### 场景1: API调用错误处理

```typescript
async function generateImage() {
  try {
    const response = await fetch('/api/generate', {
      method: 'POST',
      body: JSON.stringify(params)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    return result;
  } catch (error) {
    setError({
      type: ErrorType.API,
      message: '图像生成失败',
      details: error.message,
      recoverable: true
    });
  }
}
```

### 场景2: 模型切换错误

```typescript
async function switchModel(modelName: string) {
  try {
    const response = await fetch('/api/models/switch', {
      method: 'POST',
      body: JSON.stringify({ model_name: modelName })
    });
    
    const result = await response.json();
    
    if (!result.success) {
      setError({
        type: ErrorType.MODEL,
        message: '模型切换失败',
        details: result.message,
        recoverable: true,
        suggestions: [
          '检查模型文件是否存在',
          '确保有足够的显存',
          '尝试重启服务'
        ]
      });
    }
  } catch (error) {
    setError({
      type: ErrorType.NETWORK,
      message: '无法连接到服务器',
      details: error.message,
      recoverable: true
    });
  }
}
```

### 场景3: 参数验证

```typescript
function validateParameters(params: any) {
  if (params.steps < 1 || params.steps > 50) {
    setError({
      type: ErrorType.VALIDATION,
      message: '参数验证失败',
      details: `steps必须在1-50之间，当前值: ${params.steps}`,
      recoverable: true,
      suggestions: [
        '调整steps参数到有效范围',
        '参考文档了解参数限制'
      ]
    });
    return false;
  }
  return true;
}
```

### 场景4: WebSocket连接错误

```typescript
function setupWebSocket() {
  const ws = new WebSocket('ws://localhost:7860/ws');
  
  ws.onerror = (error) => {
    setError({
      type: ErrorType.WEBSOCKET,
      message: 'WebSocket连接失败',
      details: '无法建立实时连接',
      recoverable: true,
      suggestions: [
        '检查网络连接',
        '确认后端服务正在运行',
        '刷新页面重试'
      ]
    });
  };
  
  ws.onclose = () => {
    setError({
      type: ErrorType.WEBSOCKET,
      message: 'WebSocket连接断开',
      recoverable: true
    });
  };
}
```

## 样式定制

ErrorHandler使用Tailwind CSS类，可以通过修改组件来定制样式：

```svelte
<!-- 修改背景色 -->
<div class="bg-red-50 border-l-4 border-red-500">

<!-- 修改位置 -->
<div class="fixed top-4 right-4 z-50">

<!-- 修改最大宽度 -->
<div class="max-w-md">
```

## 最佳实践

1. **始终提供有意义的错误消息**
   ```typescript
   // ❌ 不好
   setError({
     type: ErrorType.API,
     message: '错误',
     recoverable: true
   });
   
   // ✅ 好
   setError({
     type: ErrorType.API,
     message: '无法加载模型列表',
     details: 'API返回404错误',
     recoverable: true
   });
   ```

2. **选择正确的错误类型**
   - 网络问题 → NETWORK
   - 后端API错误 → API
   - 用户输入错误 → VALIDATION
   - 模型相关 → MODEL
   - 生成过程错误 → GENERATION
   - WebSocket问题 → WEBSOCKET

3. **提供可操作的建议**
   ```typescript
   // ❌ 不好
   suggestions: ['出错了', '请重试']
   
   // ✅ 好
   suggestions: [
     '检查模型文件是否存在于 models/ 目录',
     '确认模型名称拼写正确',
     '尝试重新下载模型'
   ]
   ```

4. **合理使用recoverable标志**
   ```typescript
   // 用户可以重试的错误
   recoverable: true
   
   // 严重错误，需要重启或人工干预
   recoverable: false
   ```

5. **在catch块中处理错误**
   ```typescript
   try {
     await riskyOperation();
   } catch (error) {
     setError({
       type: ErrorType.API,
       message: '操作失败',
       details: error.message,
       recoverable: true
     });
   }
   ```

## 测试

参见 `ErrorHandler.test.md` 获取完整的测试指南。

快速测试：

```javascript
// 在浏览器控制台
import { setError, ErrorType } from '$lib/store';

setError({
  type: ErrorType.NETWORK,
  message: '测试错误',
  recoverable: true
});
```

## 性能考虑

- ✅ 组件仅在有错误时渲染
- ✅ 使用CSS动画（GPU加速）
- ✅ 最小化重渲染
- ✅ 无内存泄漏

## 浏览器兼容性

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 未来改进

- [ ] 支持多个错误同时显示（队列）
- [ ] 添加错误日志记录
- [ ] 支持错误上报到后端
- [ ] 添加声音提示（可选）
- [ ] 支持自定义主题
- [ ] 添加错误统计

## 相关需求

本组件满足以下需求：

- ✅ 需求 8.1: 模型加载失败时显示具体错误原因和解决建议
- ✅ 需求 8.2: WebSocket连接断开时显示连接状态
- ✅ 需求 8.3: 生成失败时显示错误信息并保留用户输入
- ✅ 需求 8.4: 参数配置错误时提示用户
- ✅ 需求 8.5: 系统资源不足时显示优化建议

## 贡献

如需改进此组件，请：

1. 阅读设计文档 `.kiro/specs/feature-completion/design.md`
2. 遵循现有代码风格
3. 添加测试用例
4. 更新文档

## 许可

与项目主许可证相同。
