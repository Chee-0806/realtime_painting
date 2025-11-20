# ImageEditor 组件文档

## 概述

ImageEditor 是一个基础的图像编辑器组件，提供图像加载、预览和Canvas编辑功能。这是任务8.1的实现，为后续的图像编辑工具（裁剪、旋转、颜色调整等）奠定基础。

## 功能特性

### ✅ 已实现功能

1. **图像加载**
   - 支持通过文件选择器上传图像
   - 支持常见图像格式（PNG, JPG, WebP等）
   - 自动缩放以适应画布（最大800x600px）
   - 保持原始宽高比

2. **Canvas编辑器**
   - 基于HTML5 Canvas实现
   - 高质量图像渲染
   - 响应式画布尺寸

3. **编辑历史**
   - 撤销/重做功能（最多20步）
   - 自动保存编辑状态
   - 历史记录管理

4. **图像操作**
   - 重置到原始图像
   - 下载编辑后的图像
   - 清空画布

5. **导出API**
   - `getImageDataURL()`: 导出Base64图像数据
   - `getCanvas()`: 获取Canvas元素引用

6. **错误处理**
   - 集成统一错误处理系统
   - 友好的错误提示和建议

### 🚧 待实现功能（后续任务）

以下功能将在任务8.2-8.5中实现：

- **任务8.2**: 裁剪/旋转/缩放工具
- **任务8.3**: 颜色调整（亮度、对比度、饱和度）
- **任务8.4**: 滤镜效果（模糊、锐化、灰度）
- **任务8.5**: 前后对比视图

## 使用方法

### 基础使用

```svelte
<script>
  import ImageEditor from '$lib/components/ImageEditor.svelte';
</script>

<ImageEditor />
```

### 使用导出API

```svelte
<script>
  import ImageEditor from '$lib/components/ImageEditor.svelte';
  
  let imageEditor: ImageEditor;
  
  function exportImage() {
    // 获取Base64图像数据
    const dataURL = imageEditor.getImageDataURL();
    console.log('图像数据:', dataURL);
  }
  
  function getCanvasInfo() {
    // 获取Canvas元素
    const canvas = imageEditor.getCanvas();
    console.log('Canvas尺寸:', canvas.width, 'x', canvas.height);
  }
</script>

<ImageEditor bind:this={imageEditor} />

<button on:click={exportImage}>导出图像</button>
<button on:click={getCanvasInfo}>获取Canvas信息</button>
```

### 集成到其他组件

ImageEditor可以作为其他图像处理功能的基础组件：

```svelte
<script>
  import ImageEditor from '$lib/components/ImageEditor.svelte';
  
  let editor: ImageEditor;
  
  async function processImage() {
    // 获取当前图像
    const imageData = editor.getImageDataURL();
    
    // 发送到后端处理
    const response = await fetch('/api/process', {
      method: 'POST',
      body: JSON.stringify({ image: imageData })
    });
    
    // 处理结果...
  }
</script>

<ImageEditor bind:this={editor} />
<button on:click={processImage}>处理图像</button>
```

## API参考

### 导出方法

#### `getImageDataURL(): string`

导出当前Canvas内容为Base64编码的Data URL。

**返回值**: 
- `string` - Base64编码的图像数据（PNG格式）

**示例**:
```typescript
const dataURL = imageEditor.getImageDataURL();
// 返回: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
```

#### `getCanvas(): HTMLCanvasElement`

获取Canvas元素的引用，可用于高级操作。

**返回值**:
- `HTMLCanvasElement` - Canvas DOM元素

**示例**:
```typescript
const canvas = imageEditor.getCanvas();
const ctx = canvas.getContext('2d');
// 可以直接操作Canvas...
```

## 组件状态

### 内部状态

- `sourceImage`: 原始图像的Base64数据
- `sourceImageElement`: 图像元素引用
- `canvas`: Canvas元素引用
- `ctx`: Canvas 2D渲染上下文
- `editHistory`: 编辑历史记录数组
- `historyIndex`: 当前历史位置
- `loading`: 加载状态
- `imageLoaded`: 图像是否已加载

### 配置常量

- `MAX_HISTORY`: 最大历史记录数（20）
- `maxWidth`: 最大画布宽度（800px）
- `maxHeight`: 最大画布高度（600px）

## 用户交互

### 按钮操作

1. **选择图像** - 打开文件选择器上传图像
2. **撤销** - 撤销上一步操作（Ctrl+Z）
3. **重做** - 重做下一步操作（Ctrl+Shift+Z）
4. **重置** - 恢复到原始图像
5. **下载** - 下载当前编辑结果
6. **清空** - 清空画布并重新开始

### 键盘快捷键

目前组件支持以下快捷键（通过按钮提示）：

- `Ctrl+Z` - 撤销
- `Ctrl+Shift+Z` - 重做

注：实际快捷键功能将在后续任务中实现。

## 错误处理

组件集成了统一的错误处理系统，会在以下情况显示错误：

1. **文件类型错误** - 选择了非图像文件
2. **文件读取失败** - 无法读取选择的文件
3. **图像加载失败** - 图像数据损坏或格式不支持
4. **下载失败** - Canvas导出失败

所有错误都会通过`ErrorHandler`组件显示，并提供解决建议。

## 样式定制

组件使用Tailwind CSS类名，可以通过以下方式定制：

```svelte
<ImageEditor class="custom-class" />
```

主要样式类：
- `.space-y-4` - 垂直间距
- `.bg-surface-elevated` - 背景色
- `.border-border` - 边框色
- `.text-text-primary` - 主文本色
- `.text-text-secondary` - 次要文本色

## 性能考虑

1. **图像缩放**: 大图像会自动缩放到800x600px以内，避免性能问题
2. **历史记录限制**: 最多保存20步历史，防止内存溢出
3. **Canvas优化**: 使用`willReadFrequently`选项优化频繁读取操作

## 浏览器兼容性

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

需要支持：
- HTML5 Canvas
- FileReader API
- ES6+ JavaScript

## 测试

查看 `ImageEditor.example.svelte` 文件获取完整的使用示例和测试场景。

运行示例：
```bash
cd frontend
npm run dev
# 访问示例页面
```

## 相关任务

- ✅ **任务8.1**: 创建ImageEditor组件（当前任务）
- ⏳ **任务8.2**: 实现基础编辑工具（裁剪/旋转/缩放）
- ⏳ **任务8.3**: 实现颜色调整工具
- ⏳ **任务8.4**: 实现滤镜效果
- ⏳ **任务8.5**: 实现前后对比视图
- ⏳ **任务8.6**: 集成到主页面

## 需求映射

本组件满足以下需求：

- **需求5.4**: 图像编辑工具
  - ✅ 图像加载和预览
  - ✅ Canvas编辑器
  - ⏳ 裁剪/旋转/缩放（待实现）
  - ⏳ 颜色调整（待实现）
  - ⏳ 滤镜效果（待实现）

## 更新日志

### v1.0.0 (2025-11-17)
- ✅ 初始实现
- ✅ 图像加载和预览功能
- ✅ Canvas编辑器基础功能
- ✅ 撤销/重做系统
- ✅ 图像下载功能
- ✅ 导出API
- ✅ 错误处理集成

## 贡献指南

如需扩展此组件，请遵循以下原则：

1. 保持与现有组件的一致性
2. 使用统一的错误处理系统
3. 添加适当的类型定义
4. 更新文档和示例
5. 考虑性能影响
6. 保持向后兼容

## 许可证

与项目主许可证相同。

---

**维护者**: AI Assistant  
**创建日期**: 2025-11-17  
**最后更新**: 2025-11-17
