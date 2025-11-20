# MaskEditor 组件文档

## 概述

MaskEditor 是一个独立的蒙版编辑器组件，用于在图像上绘制和编辑蒙版。它提供了完整的绘图工具集，包括画笔、橡皮擦、填充工具，以及蒙版预览和反转功能。

## 功能特性

### ✅ 已实现功能

1. **画笔工具** - 在画布上绘制白色蒙版区域
2. **橡皮擦工具** - 擦除已绘制的蒙版
3. **填充工具** - 使用洪水填充算法填充连续区域
4. **蒙版预览** - 叠加显示源图像和蒙版
5. **蒙版反转** - 反转蒙版的白色和黑色区域
6. **清除蒙版** - 一键清除所有蒙版内容
7. **画笔参数调整** - 可调节画笔大小和硬度
8. **键盘快捷键** - 支持快捷键操作
9. **触摸支持** - 支持触摸屏设备
10. **事件通知** - 蒙版变化时触发事件

## 使用方法

### 基本用法

```svelte
<script>
  import MaskEditor from '$lib/components/MaskEditor.svelte';
  
  let maskEditor;
  let sourceImage = 'data:image/png;base64,...';
  
  function handleMaskChange(event) {
    const { dataURL, imageData } = event.detail;
    console.log('蒙版已更新:', dataURL);
  }
  
  function getMask() {
    const maskDataURL = maskEditor.getMaskDataURL();
    console.log('获取蒙版:', maskDataURL);
  }
</script>

<MaskEditor
  bind:this={maskEditor}
  width={512}
  height={512}
  sourceImage={sourceImage}
  on:change={handleMaskChange}
/>

<button on:click={getMask}>获取蒙版</button>
```

### 在 InpaintingPanel 中集成

```svelte
<script>
  import MaskEditor from '$lib/components/MaskEditor.svelte';
  
  let maskEditor;
  let sourceImage = '';
  
  async function performInpainting() {
    const maskDataURL = maskEditor.getMaskDataURL();
    
    const response = await fetch('/api/inpaint', {
      method: 'POST',
      body: JSON.stringify({
        image: sourceImage,
        mask: maskDataURL,
        prompt: prompt,
        // ... 其他参数
      })
    });
  }
</script>

<MaskEditor
  bind:this={maskEditor}
  width={canvasWidth}
  height={canvasHeight}
  sourceImage={sourceImage}
/>
```

## Props

| 属性 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `width` | `number` | `512` | 画布宽度（像素） |
| `height` | `number` | `512` | 画布高度（像素） |
| `sourceImage` | `string` | `''` | 源图像的 Data URL |
| `tool` | `'brush' \| 'eraser' \| 'fill'` | `'brush'` | 当前选中的工具 |
| `brushSize` | `number` | `30` | 画笔大小（5-100） |
| `brushHardness` | `number` | `0.8` | 画笔硬度（0.1-1.0） |

## 公开方法

### `clearMask()`
清除所有蒙版内容。

```javascript
maskEditor.clearMask();
```

### `invertMaskData()`
反转蒙版的颜色。

```javascript
maskEditor.invertMaskData();
```

### `getMaskDataURL(): string`
获取蒙版的 Data URL（PNG 格式）。

```javascript
const maskDataURL = maskEditor.getMaskDataURL();
```

### `getMaskImageData(): ImageData | null`
获取蒙版的 ImageData 对象。

```javascript
const imageData = maskEditor.getMaskImageData();
```

### `setMaskFromDataURL(dataURL: string)`
从 Data URL 加载蒙版。

```javascript
maskEditor.setMaskFromDataURL('data:image/png;base64,...');
```

## 事件

### `change`
当蒙版内容发生变化时触发。

```svelte
<MaskEditor on:change={handleChange} />

<script>
  function handleChange(event) {
    const { dataURL, imageData } = event.detail;
    // dataURL: 蒙版的 Data URL
    // imageData: 蒙版的 ImageData 对象
  }
</script>
```

## 键盘快捷键

| 快捷键 | 功能 |
|--------|------|
| `B` | 切换到画笔工具 |
| `E` | 切换到橡皮擦工具 |
| `F` | 切换到填充工具 |
| `C` | 清除蒙版 |
| `I` | 反转蒙版 |
| `[` | 减小画笔大小 |
| `]` | 增大画笔大小 |

## 工具说明

### 🖌️ 画笔工具
- 在画布上绘制白色蒙版区域
- 可调节画笔大小和硬度
- 支持连续绘制，避免断点

### 🧹 橡皮擦工具
- 擦除已绘制的蒙版
- 使用与画笔相同的大小参数
- 完全透明擦除

### 🪣 填充工具
- 使用洪水填充算法
- 点击区域即可填充连续的相同颜色区域
- 支持透明度填充

### 👁️ 预览功能
- 叠加显示源图像和蒙版
- 帮助用户更好地定位蒙版区域
- 可随时切换显示/隐藏

### 🔄 反转功能
- 反转蒙版的白色和黑色区域
- 用于快速创建反向蒙版
- 保持透明度信息

## 技术实现

### 画笔绘制
使用 Canvas 2D API 的 `lineTo` 和 `stroke` 方法实现连续绘制，避免快速移动时出现断点。

```javascript
maskCtx.beginPath();
maskCtx.moveTo(lastX, lastY);
maskCtx.lineTo(currentX, currentY);
maskCtx.stroke();
```

### 洪水填充
实现了基于栈的洪水填充算法，支持大面积填充而不会导致栈溢出。

```javascript
const stack = [{ x: startX, y: startY }];
while (stack.length > 0) {
  const { x, y } = stack.pop();
  // 填充逻辑
  // 添加相邻像素到栈
}
```

### 触摸支持
通过监听 `touchstart`、`touchmove`、`touchend` 事件，支持触摸屏设备。

```javascript
function getMousePos(event: MouseEvent | TouchEvent) {
  if (event instanceof MouseEvent) {
    return { x: event.clientX, y: event.clientY };
  } else {
    return { 
      x: event.touches[0].clientX, 
      y: event.touches[0].clientY 
    };
  }
}
```

## 样式定制

组件使用 Tailwind CSS 类名，可以通过修改类名来定制样式：

```svelte
<!-- 修改工具按钮样式 -->
<button
  class="custom-button-class"
>
  画笔
</button>
```

## 性能优化

1. **Canvas 上下文配置** - 使用 `willReadFrequently: true` 优化频繁读取
2. **事件防抖** - 蒙版变化事件在绘制结束时才触发
3. **高效填充** - 使用访问集合避免重复处理像素
4. **图像缓存** - 源图像加载后缓存，避免重复加载

## 浏览器兼容性

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ 移动端浏览器（支持触摸）

## 已知限制

1. 填充工具在处理超大图像时可能较慢
2. 画笔硬度在某些浏览器上可能显示略有差异
3. 触摸设备上的画笔大小可能需要调整以适应手指操作

## 未来改进

- [ ] 添加撤销/重做功能
- [ ] 支持多层蒙版
- [ ] 添加魔棒选择工具
- [ ] 支持蒙版羽化
- [ ] 添加蒙版保存/加载功能
- [ ] 优化大图像性能

## 相关组件

- `InpaintingPanel.svelte` - 使用 MaskEditor 的局部重绘面板
- `OutpaintingPanel.svelte` - 可能使用 MaskEditor 的画布扩展面板

## 版本历史

### v1.0.0 (2025-11-17)
- ✅ 初始版本
- ✅ 实现画笔、橡皮擦、填充工具
- ✅ 实现蒙版预览和反转功能
- ✅ 添加键盘快捷键支持
- ✅ 添加触摸屏支持

## 许可证

MIT License
