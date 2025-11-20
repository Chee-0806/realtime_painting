# UpscalePanel 组件文档

## 概述

`UpscalePanel` 是一个独立的图像放大面板组件，使用 AI 算法（Real-ESRGAN）或传统插值算法提升图像分辨率。

## 功能特性

### 核心功能
- ✅ 图像上传和预览
- ✅ 多种放大算法选择（Real-ESRGAN、Lanczos、Bicubic）
- ✅ 可调节放大倍数（1.0x - 4.0x）
- ✅ 实时预览原始和目标尺寸
- ✅ 进度显示和加载状态
- ✅ 结果下载功能
- ✅ 完整的错误处理

### 放大算法

#### Real-ESRGAN（推荐）
- **特点**: AI 增强，最高质量
- **适用**: 照片、艺术作品、需要高质量的场景
- **速度**: 较慢（取决于图像大小）
- **效果**: 保留细节，减少模糊和锯齿

#### Lanczos
- **特点**: 传统算法，速度快
- **适用**: 快速预览、实时处理
- **速度**: 快
- **效果**: 较好的质量，但不如 AI 算法

#### Bicubic
- **特点**: 标准插值算法
- **适用**: 一般用途
- **速度**: 中等
- **效果**: 平衡质量和速度

## 使用方法

### 基本使用

```svelte
<script>
  import UpscalePanel from '$lib/components/UpscalePanel.svelte';
</script>

<UpscalePanel />
```

### 在主页面集成

```svelte
<script>
  import UpscalePanel from '$lib/components/UpscalePanel.svelte';
  let showUpscalePanel = false;
</script>

<button on:click={() => showUpscalePanel = !showUpscalePanel}>
  图像放大
</button>

{#if showUpscalePanel}
  <div class="card">
    <UpscalePanel />
  </div>
{/if}
```

## API 集成

### 后端端点

```
POST /api/upscale
```

### 请求格式

```typescript
{
  image: string;        // Base64 编码的图像
  scale: number;        // 放大倍数 (1.0 - 4.0)
  upscaler: string;     // "real-esrgan" | "lanczos" | "bicubic"
}
```

### 响应格式

```typescript
{
  success: boolean;
  image?: string;       // Base64 编码的放大后图像
  message?: string;     // 错误消息（如果失败）
}
```

## 组件状态

### 主要状态变量

```typescript
let sourceImage: string = '';              // 源图像 Base64
let sourceImageElement: HTMLImageElement;  // 图像元素
let upscaler: string = 'real-esrgan';     // 当前选择的算法
let scale: number = 2.0;                   // 放大倍数
let loading: boolean = false;              // 加载状态
let resultImage: string = '';              // 结果图像
let showResult: boolean = false;           // 是否显示结果
let progress: number = 0;                  // 进度百分比
```

## 用户流程

1. **上传图像**
   - 点击"选择图像"按钮
   - 选择要放大的图像文件
   - 预览显示原始图像和尺寸信息

2. **配置参数**
   - 选择放大算法（Real-ESRGAN、Lanczos、Bicubic）
   - 调整放大倍数（1.0x - 4.0x）
   - 查看目标尺寸预览

3. **执行放大**
   - 点击"开始放大"按钮
   - 等待处理完成（显示进度条）
   - 查看放大结果

4. **下载结果**
   - 点击"下载"按钮
   - 保存放大后的图像

## 错误处理

### 常见错误

#### 1. 图像加载失败
```
错误: 图像加载失败
建议: 
- 选择一个有效的图像文件
- 确保文件格式正确（PNG、JPG、WebP）
```

#### 2. Pipeline 未初始化
```
错误: Upscale Pipeline 可能未初始化
建议:
- 检查后端配置
- 查看后端启动日志
- 确认 upscale_pipeline 已正确加载
```

#### 3. 网络错误
```
错误: 无法连接到服务器
建议:
- 检查网络连接
- 确认后端服务正常运行
- 检查防火墙设置
```

## 性能优化

### 图像尺寸限制
- 预览图像最大尺寸: 512px（保持宽高比）
- 建议原始图像不超过 2048px（避免处理时间过长）

### 放大倍数建议
- **2.0x**: 最常用，平衡质量和速度
- **3.0x - 4.0x**: 高倍放大，处理时间较长
- **1.0x - 1.5x**: 轻微放大，快速处理

### 算法选择建议
- **快速预览**: 使用 Lanczos
- **最终输出**: 使用 Real-ESRGAN
- **平衡选择**: 使用 Bicubic

## 样式定制

### CSS 变量

```css
--surface-elevated: 背景色
--border: 边框色
--text-primary: 主文本色
--text-secondary: 次要文本色
--primary: 主题色
--success: 成功色
```

### 自定义样式

```svelte
<UpscalePanel />

<style>
  :global(.upscale-panel) {
    /* 自定义样式 */
  }
</style>
```

## 依赖项

### 前端依赖
- Svelte
- TypeScript
- `$lib/store` (错误处理)

### 后端依赖
- FastAPI
- PIL (Pillow)
- Real-ESRGAN (可选)
- BasicSR (可选)

## 测试

参见 `UpscalePanel.TEST.md` 获取详细的测试指南。

## 示例

参见 `UpscalePanel.example.svelte` 获取完整的使用示例。

## 常见问题

### Q: Real-ESRGAN 不可用怎么办？
A: 组件会自动降级到 Lanczos 算法。检查后端日志确认 Real-ESRGAN 是否正确安装。

### Q: 放大速度很慢？
A: 
- 尝试使用较小的放大倍数
- 使用 Lanczos 或 Bicubic 算法
- 减小原始图像尺寸

### Q: 放大后图像质量不理想？
A: 
- 使用 Real-ESRGAN 算法
- 确保原始图像质量足够好
- 避免过大的放大倍数（建议 ≤ 2.0x）

## 更新日志

### v1.0.0 (2025-11-17)
- ✅ 初始版本
- ✅ 支持三种放大算法
- ✅ 完整的 UI 和错误处理
- ✅ 进度显示和结果下载

## 相关组件

- `HiresFixPanel.svelte` - 高分辨率修复（包含放大功能）
- `InpaintingPanel.svelte` - 局部重绘
- `OutpaintingPanel.svelte` - 画布扩展

## 维护者

AI Assistant

## 许可证

与项目主许可证相同
