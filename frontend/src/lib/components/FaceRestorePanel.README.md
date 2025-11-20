# FaceRestorePanel 组件文档

## 概述

`FaceRestorePanel` 是一个用于面部修复和增强的 Svelte 组件。它使用 AI 技术（CodeFormer 或 GFPGAN）来修复和改善人脸图像的质量。

## 功能特性

### 核心功能
- ✅ 图像上传和预览
- ✅ 多模型支持（CodeFormer、GFPGAN）
- ✅ 可调节的修复强度
- ✅ 前后对比视图
- ✅ 实时进度显示
- ✅ 结果下载

### 用户体验
- 🎨 直观的参数配置界面
- 📊 实时进度反馈
- 🔄 交互式前后对比滑块
- 💾 一键下载修复结果
- ⚠️ 完善的错误处理和提示

## 使用方法

### 基本用法

```svelte
<script>
  import FaceRestorePanel from '$lib/components/FaceRestorePanel.svelte';
</script>

<FaceRestorePanel />
```

### 在主页面集成

```svelte
<script>
  import FaceRestorePanel from '$lib/components/FaceRestorePanel.svelte';
  
  let showFaceRestore = false;
</script>

<button on:click={() => showFaceRestore = !showFaceRestore}>
  面部修复
</button>

{#if showFaceRestore}
  <div class="panel">
    <FaceRestorePanel />
  </div>
{/if}
```

## API 接口

### 后端 API 端点

**POST /api/face-restore**

请求体：
```json
{
  "image": "data:image/png;base64,...",
  "model": "codeformer",
  "strength": 0.8
}
```

响应：
```json
{
  "success": true,
  "image": "data:image/png;base64,...",
  "message": "面部修复成功"
}
```

### 参数说明

| 参数 | 类型 | 范围 | 默认值 | 说明 |
|------|------|------|--------|------|
| `image` | string | - | - | Base64 编码的源图像 |
| `model` | string | codeformer, gfpgan | codeformer | 修复模型 |
| `strength` | number | 0.0-1.0 | 0.8 | 修复强度 |

## 模型说明

### CodeFormer（推荐）
- **优点**：最新技术，效果最佳，细节保留好
- **适用场景**：高质量修复，专业用途
- **速度**：较慢
- **推荐强度**：0.7-0.9

### GFPGAN
- **优点**：经典模型，速度快，稳定性好
- **适用场景**：快速修复，批量处理
- **速度**：较快
- **推荐强度**：0.6-0.8

## 修复强度指南

| 强度范围 | 效果 | 适用场景 |
|---------|------|---------|
| 0.0-0.3 | 轻微修复 | 保留原始特征，轻微增强 |
| 0.3-0.7 | 平衡修复 | 推荐设置，平衡质量和保真度 |
| 0.7-1.0 | 强力修复 | 最大化修复效果，可能改变特征 |

## 前后对比功能

组件提供交互式的前后对比视图：

1. **滑块控制**：拖动滑块查看修复前后的差异
2. **标签显示**：清晰标注"原始"和"修复后"
3. **切换显示**：可以隐藏对比视图，仅显示结果

## 错误处理

组件会处理以下错误情况：

### 文件上传错误
- 非图像文件
- 文件读取失败
- 图像加载失败

### API 错误
- 网络连接失败
- 后端服务错误
- 模型未加载
- 无法检测到人脸

### 错误提示示例

```typescript
{
  type: ErrorType.API,
  message: '面部修复失败',
  details: '无法检测到人脸',
  recoverable: true,
  suggestions: [
    '确保图像中包含清晰的人脸',
    '尝试使用不同的模型',
    '调整修复强度参数'
  ]
}
```

## 性能优化

### 图像预览
- 自动缩放到最大 512px
- 保持原始宽高比
- Canvas 渲染优化

### 进度反馈
- 实时进度条显示
- 阶段性状态提示
- 平滑动画过渡

### 内存管理
- 及时清理 Canvas 资源
- 优化图像数据存储
- 避免内存泄漏

## 样式定制

组件使用 CSS 变量，可以轻松定制：

```css
:root {
  --surface: #1a1a1a;
  --surface-elevated: #2a2a2a;
  --border: #3a3a3a;
  --text-primary: #ffffff;
  --text-secondary: #a0a0a0;
  --primary: #3b82f6;
  --success: #10b981;
  --info: #06b6d4;
}
```

## 最佳实践

### 图像选择
1. 选择包含清晰人脸的图像
2. 避免过度模糊或损坏的图像
3. 推荐分辨率：512x512 到 2048x2048

### 参数调整
1. 从默认参数开始（CodeFormer, 0.8）
2. 根据结果逐步调整强度
3. 对比不同模型的效果

### 工作流程
1. 上传图像
2. 选择合适的模型
3. 调整修复强度
4. 点击"开始修复"
5. 使用对比视图查看效果
6. 下载满意的结果

## 故障排除

### 问题：修复效果不理想
**解决方案**：
- 尝试调整修复强度
- 切换到不同的模型
- 确保源图像质量足够

### 问题：无法检测到人脸
**解决方案**：
- 确保图像中有清晰可见的人脸
- 尝试裁剪图像，突出人脸区域
- 检查图像是否过度模糊

### 问题：处理速度慢
**解决方案**：
- 使用 GFPGAN 模型（速度更快）
- 降低源图像分辨率
- 检查后端资源使用情况

## 技术细节

### 依赖项
- Svelte 4.x
- TypeScript
- Canvas API
- Fetch API

### 浏览器兼容性
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### 文件大小
- 组件代码：~15KB
- 样式：~2KB
- 总计：~17KB（未压缩）

## 更新日志

### v1.0.0 (2025-11-17)
- ✨ 初始版本发布
- ✅ 支持 CodeFormer 和 GFPGAN
- ✅ 实现前后对比功能
- ✅ 完善错误处理
- ✅ 添加进度显示

## 相关组件

- `UpscalePanel` - 图像放大
- `HiresFixPanel` - 高分辨率修复
- `InpaintingPanel` - 局部重绘
- `ErrorHandler` - 错误处理

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题或建议，请通过以下方式联系：
- GitHub Issues
- 项目文档
- 开发团队

---

**最后更新**：2025-11-17  
**版本**：1.0.0  
**维护者**：StreamDiffusion Team
