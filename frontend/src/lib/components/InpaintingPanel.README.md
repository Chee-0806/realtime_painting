# InpaintingPanel 组件使用说明

## 概述

InpaintingPanel 是一个完整的局部重绘（Inpainting）功能组件，允许用户上传图像、绘制蒙版并使用AI重绘指定区域。

## 功能特性

### ✅ 已实现的功能

1. **图像上传**
   - 支持所有常见图像格式（PNG, JPG, WebP等）
   - 自动调整图像大小（最大512x512，保持宽高比）
   - 实时预览

2. **蒙版绘制Canvas**
   - 双层Canvas架构（源图像 + 蒙版层）
   - 实时绘制反馈
   - 红色半透明蒙版显示

3. **画笔工具**
   - 画笔模式：绘制需要重绘的区域
   - 橡皮擦模式：擦除蒙版
   - 可调节画笔大小（5-100px）
   - 可调节画笔硬度（10-100%）
   - 清除蒙版功能

4. **参数配置**
   - Prompt输入（必填）
   - Negative Prompt输入（可选）
   - 重绘强度（strength: 0.0-1.0）
   - 引导强度（guidance_scale: 1.0-20.0）
   - 生成步数（steps: 10-50）

5. **错误处理**
   - 集成统一错误处理系统
   - 详细的错误提示和建议
   - 输入验证

6. **结果展示**
   - 生成结果预览
   - 下载功能
   - 重置功能

## 使用方法

### 基本用法

```svelte
<script>
  import InpaintingPanel from '$lib/components/InpaintingPanel.svelte';
</script>

<InpaintingPanel />
```

### 集成到页面

```svelte
<!-- 在主页面或工具页面中 -->
<script>
  import InpaintingPanel from '$lib/components/InpaintingPanel.svelte';
  
  let showInpainting = false;
</script>

<button on:click={() => showInpainting = !showInpainting}>
  {showInpainting ? '隐藏' : '显示'} Inpainting
</button>

{#if showInpainting}
  <div class="card">
    <InpaintingPanel />
  </div>
{/if}
```

## API要求

组件需要后端提供以下API端点：

### POST /api/inpaint

**请求体：**
```json
{
  "image": "data:image/png;base64,...",
  "mask": "data:image/png;base64,...",
  "prompt": "a beautiful flower",
  "negative_prompt": "blurry, low quality",
  "strength": 0.6,
  "guidance_scale": 7.5,
  "steps": 20
}
```

**响应：**
```json
{
  "success": true,
  "image": "data:image/png;base64,...",
  "message": "Inpainting完成"
}
```

**错误响应：**
```json
{
  "success": false,
  "message": "错误描述"
}
```

## 用户操作流程

1. **上传图像**
   - 点击"选择图像"按钮
   - 选择要编辑的图像文件
   - 图像自动加载到画布

2. **绘制蒙版**
   - 选择画笔工具
   - 调整画笔大小和硬度
   - 在图像上绘制红色区域标记需要重绘的部分
   - 使用橡皮擦修正蒙版
   - 可随时清除蒙版重新绘制

3. **配置参数**
   - 输入Prompt描述想要生成的内容
   - （可选）输入Negative Prompt
   - 调整重绘强度、引导强度和生成步数

4. **生成结果**
   - 点击"开始重绘"按钮
   - 等待生成完成
   - 查看结果并下载

5. **重置**
   - 点击"重置"按钮清除所有内容
   - 开始新的Inpainting任务

## 技术细节

### Canvas架构

组件使用双层Canvas架构：

1. **源图像Canvas（sourceCanvas）**
   - 显示原始图像
   - 不可交互（pointer-events: none）
   - 作为背景层

2. **蒙版Canvas（maskCanvas）**
   - 覆盖在源图像上方
   - 可交互（接收鼠标事件）
   - 使用mix-blend-mode显示红色半透明效果

### 画笔实现

- 使用Canvas的`arc()`方法绘制圆形画笔
- 使用径向渐变实现画笔硬度效果
- 橡皮擦使用`globalCompositeOperation = 'destination-out'`

### 状态管理

- 使用Svelte的响应式变量管理组件状态
- 集成全局错误状态（errorState store）
- 独立的组件状态，不依赖外部store

## 样式定制

组件使用Tailwind CSS类，可以通过修改类名来定制样式：

```svelte
<!-- 修改主容器样式 -->
<div class="space-y-4 p-6 bg-custom-bg">
  <!-- ... -->
</div>

<!-- 修改按钮样式 -->
<button class="custom-button-class">
  开始重绘
</button>
```

## 性能考虑

1. **图像大小限制**
   - 自动缩放到最大512x512
   - 保持宽高比
   - 减少内存占用和处理时间

2. **Canvas优化**
   - 使用`image-rendering: crisp-edges`保持清晰度
   - 避免不必要的重绘

3. **错误处理**
   - 完善的输入验证
   - 友好的错误提示
   - 自动清理错误状态

## 已知限制

1. 仅支持鼠标操作，暂不支持触摸屏
2. 蒙版绘制不支持撤销/重做（可以使用橡皮擦或清除）
3. 图像大小限制为512x512

## 未来改进

- [ ] 添加触摸屏支持
- [ ] 实现蒙版撤销/重做
- [ ] 支持更大的图像尺寸
- [ ] 添加预设蒙版形状（矩形、圆形等）
- [ ] 实现蒙版反转功能
- [ ] 添加蒙版羽化效果

## 相关需求

- 需求 1.2: 前端组件缺失 - Inpainting功能
- 需求 5.1: P1功能前端界面缺失 - Inpainting界面

## 版本历史

- v1.0.0 (2025-11-17): 初始版本，实现所有核心功能
