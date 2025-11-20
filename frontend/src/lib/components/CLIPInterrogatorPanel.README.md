# CLIPInterrogatorPanel 组件

## 概述

`CLIPInterrogatorPanel` 是一个可复用的 CLIP Prompt 反推组件，用于从图像中提取 Prompt 描述。该组件支持图像上传、多种反推模式，并可以将结果应用到生成参数中。

## 功能特性

- ✅ **图像上传**：支持拖拽或点击上传图像文件
- ✅ **多种模式**：快速模式、经典模式、负面 Prompt 模式
- ✅ **实时预览**：显示上传的图像预览
- ✅ **结果展示**：清晰展示反推的 Prompt 和 Negative Prompt
- ✅ **风格标签**：显示图像的风格特征
- ✅ **一键应用**：将反推结果应用到生成参数
- ✅ **复制功能**：支持单独复制 Prompt 或 Negative Prompt
- ✅ **错误处理**：完善的错误提示和处理机制
- ✅ **事件系统**：支持自定义事件处理

## Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `initialImageUrl` | `string` | `''` | 初始图像 URL（可选） |
| `showCloseButton` | `boolean` | `true` | 是否显示关闭按钮 |
| `autoApplyPrompt` | `boolean` | `false` | 是否自动应用反推结果 |

## Events

组件会触发以下事件：

| 事件名 | 参数 | 说明 |
|--------|------|------|
| `result` | `{ prompt, negative_prompt, flavors, mode }` | 反推完成时触发 |
| `apply` | `{ prompt, negative_prompt, flavors, mode }` | 应用 Prompt 时触发 |
| `copy` | `{ type, text }` | 复制文本时触发 |
| `close` | - | 关闭面板时触发 |

## 使用示例

### 基础使用

```svelte
<script>
  import CLIPInterrogatorPanel from '$lib/components/CLIPInterrogatorPanel.svelte';
</script>

<CLIPInterrogatorPanel />
```

### 带初始图像

```svelte
<script>
  import CLIPInterrogatorPanel from '$lib/components/CLIPInterrogatorPanel.svelte';
  
  let imageUrl = 'https://example.com/image.jpg';
</script>

<CLIPInterrogatorPanel initialImageUrl={imageUrl} />
```

### 自动应用结果

```svelte
<script>
  import CLIPInterrogatorPanel from '$lib/components/CLIPInterrogatorPanel.svelte';
</script>

<CLIPInterrogatorPanel autoApplyPrompt={true} />
```

### 监听事件

```svelte
<script>
  import CLIPInterrogatorPanel from '$lib/components/CLIPInterrogatorPanel.svelte';
  
  function handleResult(event) {
    console.log('反推结果:', event.detail);
  }
  
  function handleApply(event) {
    console.log('应用 Prompt:', event.detail);
  }
  
  function handleClose() {
    console.log('关闭面板');
  }
</script>

<CLIPInterrogatorPanel
  on:result={handleResult}
  on:apply={handleApply}
  on:close={handleClose}
/>
```

### 在弹窗中使用

```svelte
<script>
  import CLIPInterrogatorPanel from '$lib/components/CLIPInterrogatorPanel.svelte';
  
  let showPanel = false;
  
  function handleClose() {
    showPanel = false;
  }
</script>

<button on:click={() => showPanel = true}>
  打开 CLIP 反推
</button>

{#if showPanel}
  <div class="modal">
    <CLIPInterrogatorPanel
      showCloseButton={true}
      on:close={handleClose}
    />
  </div>
{/if}
```

## 反推模式说明

### ⚡ 快速模式 (Fast)
- 使用 BLIP 快速生成图像描述
- 通过 CLIP 进行优化
- 速度快，适合快速预览
- 可能不够详细

### 🎯 经典模式 (Classic)
- 生成更详细和准确的 Prompt 描述
- 处理时间较长
- 适合需要精确描述的场景
- 推荐用于最终生成

### 🚫 负面 Prompt (Negative)
- 专门生成负面提示词
- 用于排除不想要的元素和特征
- 帮助提高生成质量

## API 接口

组件调用后端 `/api/clip/interrogate` 接口：

### 请求格式

```json
{
  "image": "data:image/png;base64,...",
  "mode": "fast" | "classic" | "negative"
}
```

### 响应格式

```json
{
  "success": true,
  "prompt": "a beautiful landscape with mountains",
  "negative_prompt": "blurry, low quality",
  "flavors": ["landscape", "nature", "mountains"],
  "mode": "fast"
}
```

## 样式定制

组件使用 Tailwind CSS 类，可以通过全局样式或 CSS 变量进行定制：

```css
/* 自定义卡片背景 */
.card-compact {
  background: var(--surface-color);
  border-color: var(--border-color);
}

/* 自定义按钮样式 */
.btn-primary {
  background: var(--primary-color);
}
```

## 注意事项

1. **图像大小限制**：上传的图像文件不能超过 10MB
2. **图像格式**：支持 JPG、PNG、WebP 等常见格式
3. **网络连接**：需要后端 CLIP 服务正常运行
4. **处理时间**：经典模式可能需要较长时间处理
5. **显存占用**：CLIP 模型会占用一定显存

## 错误处理

组件会处理以下错误情况：

- ❌ 文件类型不支持
- ❌ 文件大小超限
- ❌ 读取文件失败
- ❌ 网络请求失败
- ❌ 后端服务错误
- ❌ 图像数据无效

所有错误都会显示友好的提示信息和解决建议。

## 性能优化

- 图像预览使用 `max-h-64` 限制高度
- 使用 `disabled` 状态防止重复提交
- 文件读取使用 FileReader API
- 支持 base64 和 URL 两种图像格式

## 可访问性

- 所有交互元素都有 `aria-label`
- 支持键盘导航
- 错误信息清晰可读
- 按钮状态明确

## 浏览器兼容性

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

需要支持以下 Web API：
- FileReader API
- Clipboard API
- Fetch API

## 相关组件

- `ModelManager.svelte` - 模型管理组件
- `PromptTools.svelte` - Prompt 工具组件
- `ErrorHandler.svelte` - 错误处理组件

## 更新日志

### v1.0.0 (2025-11-17)
- ✨ 初始版本
- ✅ 实现图像上传功能
- ✅ 实现三种反推模式
- ✅ 实现结果展示和应用
- ✅ 实现事件系统
- ✅ 完善错误处理

## 许可证

MIT License
