# OutpaintingPanel 组件文档

## 概述

OutpaintingPanel 是一个用于画布扩展（Outpainting）的 Svelte 组件。它允许用户上传图像，选择扩展方向和尺寸，然后使用 AI 生成扩展区域的内容。

## 功能特性

### ✅ 已实现功能

1. **图像上传和预览**
   - 支持常见图像格式（PNG, JPG, WebP等）
   - 自动调整预览尺寸（最大512px）
   - 实时预览扩展区域

2. **扩展方向选择**
   - 向左扩展（←）
   - 向右扩展（→）
   - 向上扩展（↑）
   - 向下扩展（↓）
   - 全方向扩展（⊕）

3. **扩展尺寸配置**
   - 滑块控制：64px - 512px
   - 步长：64px（建议使用64的倍数）
   - 实时预览扩展效果

4. **参数配置**
   - Prompt输入（必填）
   - Negative Prompt输入（可选）
   - 引导强度（Guidance Scale）：1.0 - 20.0
   - 生成步数（Steps）：10 - 50

5. **错误处理**
   - 文件类型验证
   - 图像加载错误处理
   - API请求错误处理
   - 用户友好的错误提示和建议

6. **结果展示**
   - 生成结果预览
   - 下载功能
   - 重置功能

## 使用方法

### 基本用法

```svelte
<script>
  import OutpaintingPanel from '$lib/components/OutpaintingPanel.svelte';
</script>

<OutpaintingPanel />
```

### 在主页面集成

```svelte
<!-- frontend/src/routes/+page.svelte -->
<script>
  import OutpaintingPanel from '$lib/components/OutpaintingPanel.svelte';
  let showOutpainting = false;
</script>

{#if showOutpainting}
  <div class="card">
    <OutpaintingPanel />
  </div>
{/if}

<button on:click={() => showOutpainting = !showOutpainting}>
  {showOutpainting ? '隐藏' : '显示'} Outpainting
</button>
```

## API 接口

组件调用后端 `/api/outpaint` 端点：

### 请求格式

```typescript
POST /api/outpaint
Content-Type: application/json

{
  image: string;              // Base64编码的源图像
  direction: 'left' | 'right' | 'top' | 'bottom' | 'all';
  pixels: number;             // 扩展像素数（64-512）
  prompt: string;             // 生成提示词
  negative_prompt: string;    // 负面提示词
  guidance_scale: number;     // 引导强度（1.0-20.0）
  num_inference_steps: number; // 生成步数（10-50）
}
```

### 响应格式

```typescript
{
  success: boolean;
  image?: string;             // Base64编码的结果图像
  message?: string;           // 错误消息（如果失败）
}
```

## 组件状态

### 主要状态变量

- `sourceImage`: 源图像的Base64数据
- `direction`: 扩展方向
- `pixels`: 扩展像素数
- `prompt`: 生成提示词
- `negativePrompt`: 负面提示词
- `guidanceScale`: 引导强度
- `steps`: 生成步数
- `loading`: 加载状态
- `resultImage`: 生成结果
- `showResult`: 是否显示结果

## 预览功能

组件提供实时预览功能：

1. **灰色区域**：表示将要扩展的空白区域
2. **蓝色虚线框**：标记扩展边界
3. **原始图像**：保持在中心位置
4. **自动更新**：当改变方向或尺寸时自动更新预览

## 错误处理

组件集成了统一的错误处理系统：

### 验证错误
- 文件类型不正确
- 未上传图像
- 未输入Prompt

### API错误
- 网络连接失败
- 后端服务不可用
- HTTP错误

### 生成错误
- Outpainting失败
- 参数配置错误

每个错误都会提供：
- 清晰的错误消息
- 详细的错误信息
- 可操作的解决建议

## 样式说明

组件使用 Tailwind CSS 类名，遵循项目的设计系统：

- **主色调**：`bg-primary`, `text-primary`
- **成功色**：`bg-success`
- **表面色**：`bg-surface`, `bg-surface-elevated`
- **边框色**：`border-border`
- **文本色**：`text-text-primary`, `text-text-secondary`

## 性能优化

1. **图像缩放**：自动将大图像缩放到合理尺寸
2. **Canvas优化**：使用pixelated渲染模式
3. **响应式预览**：根据扩展参数动态更新
4. **防抖处理**：避免频繁的预览更新

## 依赖项

- `svelte`: 核心框架
- `$lib/store`: 错误状态管理
- Tailwind CSS: 样式系统

## 浏览器兼容性

- Chrome/Edge: ✅ 完全支持
- Firefox: ✅ 完全支持
- Safari: ✅ 完全支持
- 移动浏览器: ✅ 支持（需要触摸优化）

## 已知限制

1. **扩展尺寸**：建议使用64的倍数以获得更好的效果
2. **图像大小**：预览限制在512px以内
3. **方向限制**：一次只能选择一个扩展方向
4. **后端依赖**：需要后端实现 `/api/outpaint` 端点

## 未来改进

- [ ] 支持批量扩展
- [ ] 添加扩展历史记录
- [ ] 支持自定义扩展比例
- [ ] 添加预设配置
- [ ] 支持拖拽上传

## 相关组件

- `InpaintingPanel.svelte`: 局部重绘组件
- `ErrorHandler.svelte`: 错误处理组件
- `MaskEditor.svelte`: 蒙版编辑器

## 需求覆盖

本组件满足以下需求：

- ✅ 需求 1.3: 前端组件缺失 - Outpainting功能
- ✅ 需求 5.1: P1功能前端界面缺失 - Outpainting界面

## 版本历史

- **v1.0.0** (2025-11-17): 初始版本
  - 实现基本的Outpainting功能
  - 支持5种扩展方向
  - 集成错误处理
  - 实时预览功能

## 维护者

AI Assistant

## 许可证

与项目主许可证相同
