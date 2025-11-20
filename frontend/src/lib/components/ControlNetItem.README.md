# ControlNetItem 组件文档

## 概述

`ControlNetItem.svelte` 是一个可复用的 Svelte 组件，用于配置单个 ControlNet 的参数。它是 `MultiControlNetPanel` 组件的子组件，提供了完整的 ControlNet 配置界面。

## 功能特性

- ✅ **类型选择**: 支持多种 ControlNet 类型（canny、depth、pose 等）
- ✅ **图像上传**: 支持拖拽或点击上传控制图像
- ✅ **权重控制**: 0.0-2.0 范围的权重滑块
- ✅ **引导范围**: 独立配置引导开始和结束位置
- ✅ **实时预览**: 上传后立即显示图像预览
- ✅ **错误处理**: 完善的文件验证和错误提示
- ✅ **响应式设计**: 适配桌面和移动设备

## 接口定义

### Props

```typescript
interface ControlNetConfig {
  id: string;              // 唯一标识符
  type: string;            // ControlNet类型
  image: string;           // Base64图像数据
  weight: number;          // 权重 (0.0-2.0)
  guidanceStart: number;   // 引导开始 (0.0-1.0)
  guidanceEnd: number;     // 引导结束 (0.0-1.0)
}

// 组件Props
export let config: ControlNetConfig;
export let index: number;
export let availableTypes: string[];
export let onRemove: (id: string) => void;
export let onUpdate: (id: string, field: keyof ControlNetConfig, value: any) => void;
```

### 事件

- `onRemove(id)`: 删除此 ControlNet 时触发
- `onUpdate(id, field, value)`: 任何配置更新时触发

## 使用方法

### 基础用法

```svelte
<script>
  import ControlNetItem from '$lib/components/ControlNetItem.svelte';
  
  let config = {
    id: 'cn-1',
    type: 'canny',
    image: '',
    weight: 1.0,
    guidanceStart: 0.0,
    guidanceEnd: 1.0
  };
  
  const availableTypes = ['canny', 'depth', 'pose', 'scribble'];
  
  function handleRemove(id) {
    console.log('删除:', id);
  }
  
  function handleUpdate(id, field, value) {
    config = { ...config, [field]: value };
  }
</script>

<ControlNetItem
  {config}
  index={0}
  {availableTypes}
  onRemove={handleRemove}
  onUpdate={handleUpdate}
/>
```

### 在列表中使用

```svelte
<script>
  import ControlNetItem from '$lib/components/ControlNetItem.svelte';
  
  let controlnets = [
    { id: 'cn-1', type: 'canny', image: '', weight: 1.0, guidanceStart: 0.0, guidanceEnd: 1.0 },
    { id: 'cn-2', type: 'depth', image: '', weight: 0.8, guidanceStart: 0.0, guidanceEnd: 1.0 }
  ];
  
  function removeControlNet(id) {
    controlnets = controlnets.filter(cn => cn.id !== id);
  }
  
  function updateControlNet(id, field, value) {
    controlnets = controlnets.map(cn => 
      cn.id === id ? { ...cn, [field]: value } : cn
    );
  }
</script>

<div class="space-y-4">
  {#each controlnets as cn, index (cn.id)}
    <ControlNetItem
      config={cn}
      {index}
      availableTypes={['canny', 'depth', 'pose']}
      onRemove={removeControlNet}
      onUpdate={updateControlNet}
    />
  {/each}
</div>
```

## 配置参数说明

### ControlNet 类型

支持的 ControlNet 类型：

- `canny`: 边缘检测
- `depth`: 深度图
- `pose`: 姿态检测
- `scribble`: 涂鸦
- `lineart`: 线稿
- `normal`: 法线图
- `semantic`: 语义分割

### 权重 (Weight)

- **范围**: 0.0 - 2.0
- **默认值**: 1.0
- **说明**: 控制 ControlNet 对生成结果的影响强度
  - 0.0: 无影响
  - 1.0: 标准影响
  - 2.0: 最大影响

### 引导范围 (Guidance Range)

- **引导开始 (Guidance Start)**
  - 范围: 0.0 - 1.0
  - 默认值: 0.0
  - 说明: ControlNet 开始生效的步数比例

- **引导结束 (Guidance End)**
  - 范围: 0.0 - 1.0
  - 默认值: 1.0
  - 说明: ControlNet 停止生效的步数比例

## 样式定制

组件使用 CSS 变量进行样式定制：

```css
:root {
  --color-surface: #1a1a1a;
  --color-background: #0d0d0d;
  --color-border: #333333;
  --color-text-primary: #ffffff;
  --color-text-secondary: #999999;
  --color-primary: #3b82f6;
  --color-error: #ef4444;
}
```

### 自定义样式

```svelte
<ControlNetItem
  {config}
  {index}
  {availableTypes}
  onRemove={handleRemove}
  onUpdate={handleUpdate}
  --controlnet-bg="var(--custom-bg)"
  --controlnet-border="var(--custom-border)"
/>
```

## 错误处理

组件内置了完善的错误处理机制：

### 文件验证

- 只接受图像文件（PNG, JPG, WebP 等）
- 自动显示错误提示
- 提供解决建议

### 错误示例

```typescript
// 非图像文件
setError({
  type: ErrorType.VALIDATION,
  message: '请选择图像文件',
  details: '只支持图像格式（PNG, JPG, WebP等）',
  recoverable: true,
  suggestions: ['选择一个有效的图像文件']
});

// 文件读取失败
setError({
  type: ErrorType.VALIDATION,
  message: '图像加载失败',
  details: '无法读取选择的文件',
  recoverable: true,
  suggestions: ['尝试选择其他图像文件']
});
```

## 性能优化

### 图像处理

- 使用 FileReader API 异步读取文件
- Base64 编码后存储，避免重复读取
- 图像预览自动限制最大高度（8rem）

### 事件处理

- 使用回调函数而非事件派发，减少开销
- 滑块使用 `input` 事件实现实时更新
- 避免不必要的重渲染

## 可访问性

- ✅ 所有表单元素都有对应的 label
- ✅ 按钮有明确的 title 属性
- ✅ 支持键盘导航
- ✅ 滑块支持键盘调整（方向键）

## 浏览器兼容性

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## 相关组件

- `MultiControlNetPanel.svelte`: 父组件，管理多个 ControlNet
- `ErrorHandler.svelte`: 错误处理组件

## 更新日志

### v1.0.0 (2025-11-17)

- ✅ 初始版本发布
- ✅ 实现基础配置功能
- ✅ 添加图像上传和预览
- ✅ 实现权重和引导范围控制
- ✅ 完善错误处理

## 许可证

MIT License

## 维护者

AI Assistant

---

**最后更新**: 2025-11-17
