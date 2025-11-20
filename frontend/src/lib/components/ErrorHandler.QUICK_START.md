# ErrorHandler Quick Start Guide

## 30秒快速开始

### 1. 导入组件 (在任何页面)

```svelte
<script>
  import ErrorHandler from '$lib/components/ErrorHandler.svelte';
</script>

<ErrorHandler />
```

### 2. 显示错误

```typescript
import { setError, ErrorType } from '$lib/store';

setError({
  type: ErrorType.NETWORK,
  message: '无法连接到服务器',
  recoverable: true
});
```

### 3. 清除错误

```typescript
import { clearError } from '$lib/store';

clearError();
```

---

## 常用代码片段

### API调用错误处理

```typescript
try {
  const response = await fetch('/api/endpoint');
  if (!response.ok) throw new Error(response.statusText);
  return await response.json();
} catch (error) {
  setError({
    type: ErrorType.API,
    message: 'API调用失败',
    details: error.message,
    recoverable: true
  });
}
```

### 参数验证

```typescript
if (steps < 1 || steps > 50) {
  setError({
    type: ErrorType.VALIDATION,
    message: '参数超出范围',
    details: `steps必须在1-50之间，当前: ${steps}`,
    recoverable: true
  });
  return;
}
```

### WebSocket错误

```typescript
ws.onerror = () => {
  setError({
    type: ErrorType.WEBSOCKET,
    message: 'WebSocket连接失败',
    recoverable: true
  });
};
```

---

## 错误类型速查

| 类型 | 使用场景 | 图标 |
|------|---------|------|
| `ErrorType.NETWORK` | 网络连接问题 | 🌐 |
| `ErrorType.API` | API调用失败 | ⚙️ |
| `ErrorType.VALIDATION` | 参数验证失败 | ✏️ |
| `ErrorType.MODEL` | 模型加载/切换失败 | 🎨 |
| `ErrorType.GENERATION` | 图像生成失败 | 🖼️ |
| `ErrorType.WEBSOCKET` | WebSocket连接问题 | 🔌 |

---

## 完整示例

```svelte
<script lang="ts">
  import ErrorHandler from '$lib/components/ErrorHandler.svelte';
  import { setError, clearError, ErrorType } from '$lib/store';
  
  async function handleGenerate() {
    try {
      // 验证参数
      if (!prompt) {
        setError({
          type: ErrorType.VALIDATION,
          message: 'Prompt不能为空',
          recoverable: true
        });
        return;
      }
      
      // API调用
      const response = await fetch('/api/generate', {
        method: 'POST',
        body: JSON.stringify({ prompt })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const result = await response.json();
      
      // 成功后清除之前的错误
      clearError();
      
      return result;
      
    } catch (error) {
      setError({
        type: ErrorType.API,
        message: '生成失败',
        details: error.message,
        recoverable: true,
        suggestions: [
          '检查网络连接',
          '确认后端服务运行正常',
          '尝试调整参数后重试'
        ]
      });
    }
  }
</script>

<ErrorHandler />

<button on:click={handleGenerate}>
  生成图像
</button>
```

---

## 自定义建议

```typescript
setError({
  type: ErrorType.MODEL,
  message: '显存不足',
  details: 'CUDA out of memory (2.5 GB needed)',
  recoverable: true,
  suggestions: [
    '关闭其他占用显存的程序',
    '使用较小的模型',
    '减小batch size',
    '降低图像分辨率'
  ]
});
```

---

## 非可恢复错误

```typescript
setError({
  type: ErrorType.MODEL,
  message: '模型文件损坏',
  details: 'Checksum verification failed',
  recoverable: false  // 不显示"我知道了"按钮
});
```

---

## 调试技巧

### 浏览器控制台测试

```javascript
// 打开控制台，执行:
import { setError, ErrorType } from './frontend/src/lib/store.ts';

setError({
  type: ErrorType.NETWORK,
  message: '测试错误',
  recoverable: true
});
```

### 查看当前错误状态

```typescript
import { errorState } from '$lib/store';

errorState.subscribe(state => {
  console.log('Error state:', state);
});
```

---

## 最佳实践

✅ **DO**
- 使用正确的错误类型
- 提供清晰的错误消息
- 包含有用的详细信息
- 提供可操作的建议
- 在catch块中处理错误

❌ **DON'T**
- 使用模糊的错误消息
- 忘记设置recoverable标志
- 在错误中包含敏感信息
- 忽略错误处理

---

## 更多信息

- 📖 完整文档: `ErrorHandler.README.md`
- 🧪 测试指南: `ErrorHandler.test.md`
- 🎨 视觉指南: `ErrorHandler.VISUAL_GUIDE.md`
- 📝 实现总结: `TASK_3.1_IMPLEMENTATION_SUMMARY.md`

---

**快速开始完成！** 🎉

现在你可以在整个应用中使用统一的错误处理了。
