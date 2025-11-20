# HiresFixPanel 组件

## 概述

`HiresFixPanel` 是一个用于高分辨率修复（Hires.fix）的 Svelte 组件。它通过两阶段生成过程提升图像质量：先生成低分辨率图像，再放大并细化细节。

## 功能特性

### 核心功能
- ✅ **两阶段生成**: 低分辨率生成 + 高分辨率细化
- ✅ **多种放大算法**: Latent、ESRGAN、LDSR 等
- ✅ **可选源图像**: 支持从头生成或基于现有图像
- ✅ **灵活参数配置**: 步数、放大倍数、降噪强度等
- ✅ **实时预览**: 显示源图像和预期放大倍数
- ✅ **进度显示**: 显示当前生成阶段
- ✅ **结果下载**: 一键下载生成的高分辨率图像

### 参数说明

#### 第一阶段步数 (First Pass Steps)
- **范围**: 10-50
- **推荐值**: 15-25
- **说明**: 低分辨率生成的迭代步数，影响初始图像质量

#### 高分辨率步数 (Hires Steps)
- **范围**: 5-50
- **推荐值**: 10-20
- **说明**: 高分辨率细化的迭代步数，影响最终细节质量

#### 放大算法 (Upscaler)
- **Latent (快速)**: 最快，适合快速预览
- **Latent (最近邻)**: 保持锐利边缘
- **Latent (双三次)**: 平滑放大
- **ESRGAN 4x**: 高质量放大，适合照片
- **R-ESRGAN 4x+**: 增强版 ESRGAN
- **LDSR**: 最高质量，速度较慢

#### 放大倍数 (Upscale By)
- **范围**: 1.0x - 4.0x
- **推荐值**: 2.0x
- **说明**: 图像将被放大到原始尺寸的指定倍数

#### 降噪强度 (Denoising Strength)
- **范围**: 0.0 - 1.0
- **推荐值**: 0.6 - 0.8
- **说明**: 
  - 值越高，高分辨率阶段变化越大
  - 值越低，更接近放大的低分辨率图像
  - 0.7 是平衡质量和一致性的好选择

#### 引导强度 (Guidance Scale)
- **范围**: 1.0 - 20.0
- **推荐值**: 7.5
- **说明**: 控制生成结果与 Prompt 的匹配程度

## 使用方法

### 基本用法

```svelte
<script>
  import HiresFixPanel from '$lib/components/HiresFixPanel.svelte';
</script>

<HiresFixPanel />
```

### 在主页面集成

```svelte
<script>
  import HiresFixPanel from '$lib/components/HiresFixPanel.svelte';
  
  let showHiresFix = false;
</script>

<button on:click={() => showHiresFix = !showHiresFix}>
  🔍 高分辨率修复
</button>

{#if showHiresFix}
  <div class="panel">
    <HiresFixPanel />
  </div>
{/if}
```

## 工作流程

### 从头生成高分辨率图像

1. **输入 Prompt**: 描述想要生成的内容
2. **配置参数**: 设置步数、放大倍数等
3. **选择放大算法**: 根据需求选择速度或质量优先
4. **开始生成**: 点击"开始生成"按钮
5. **等待完成**: 系统会显示当前阶段（第一阶段/第二阶段）
6. **下载结果**: 生成完成后可下载高分辨率图像

### 基于现有图像进行高分辨率修复

1. **上传图像**: 点击"选择图像"上传源图像
2. **输入 Prompt**: 描述图像内容或想要的改进
3. **配置参数**: 调整降噪强度等参数
4. **开始生成**: 系统会放大并细化图像
5. **下载结果**: 获得高分辨率版本

## API 接口

### 请求格式

```typescript
POST /api/hires-fix

{
  prompt: string;                    // 必需
  negative_prompt: string;           // 可选
  first_pass_steps: number;          // 第一阶段步数
  hires_steps: number;               // 高分辨率步数
  upscaler: string;                  // 放大算法
  upscale_by: number;                // 放大倍数
  denoising_strength: number;        // 降噪强度
  guidance_scale: number;            // 引导强度
  image?: string;                    // 可选，Base64 编码的源图像
}
```

### 响应格式

```typescript
{
  success: boolean;
  image: string;                     // Base64 编码的结果图像
  message?: string;                  // 错误信息（如果失败）
}
```

## 错误处理

组件集成了统一的错误处理系统，会在以下情况显示友好的错误提示：

- ❌ **未输入 Prompt**: 提示用户输入描述
- ❌ **图像加载失败**: 提示选择有效的图像文件
- ❌ **API 请求失败**: 显示网络错误和解决建议
- ❌ **生成失败**: 显示后端错误信息和调整建议

## 性能优化建议

### 快速预览
- 使用 Latent 放大算法
- 第一阶段步数: 15
- 高分辨率步数: 10
- 放大倍数: 2.0x

### 高质量输出
- 使用 ESRGAN 或 LDSR 放大算法
- 第一阶段步数: 25
- 高分辨率步数: 20
- 放大倍数: 2.0-3.0x
- 降噪强度: 0.7

### 极致质量
- 使用 LDSR 放大算法
- 第一阶段步数: 30
- 高分辨率步数: 25
- 放大倍数: 4.0x
- 降噪强度: 0.75

## 技术细节

### 组件结构

```
HiresFixPanel.svelte
├── 状态管理
│   ├── 图像状态 (sourceImage, resultImage)
│   ├── 参数配置 (steps, upscaler, etc.)
│   └── UI 状态 (loading, progress)
├── 图像处理
│   ├── 文件上传
│   ├── Canvas 预览
│   └── 图像缩放
├── API 调用
│   ├── 请求构建
│   ├── 错误处理
│   └── 结果处理
└── UI 组件
    ├── 参数输入
    ├── 进度显示
    └── 结果展示
```

### 依赖项

- `svelte`: 核心框架
- `$lib/store`: 错误状态管理
- Canvas API: 图像预览

## 样式定制

组件使用 Tailwind CSS 类名，支持以下 CSS 变量定制：

```css
--surface: 背景色
--surface-elevated: 提升背景色
--border: 边框色
--text-primary: 主文本色
--text-secondary: 次要文本色
--primary: 主题色
--success: 成功色
--info: 信息色
```

## 最佳实践

### Prompt 编写
- 详细描述想要的内容和风格
- 包含质量关键词：`high quality`, `detailed`, `sharp`
- 指定艺术风格：`photorealistic`, `anime style`, `oil painting`

### 参数调整
- 从默认参数开始测试
- 逐步调整单个参数观察效果
- 记录好的参数组合以便复用

### 性能考虑
- 大放大倍数（3x-4x）需要更多显存和时间
- LDSR 算法质量最高但速度最慢
- 建议先用 Latent 快速预览，满意后再用 ESRGAN/LDSR

## 故障排除

### 问题：生成失败
- 检查 Prompt 是否为空
- 确认后端服务正常运行
- 查看浏览器控制台错误信息

### 问题：结果质量不佳
- 增加第一阶段步数
- 增加高分辨率步数
- 尝试不同的放大算法
- 调整降噪强度

### 问题：生成速度慢
- 减少步数
- 使用 Latent 放大算法
- 降低放大倍数

## 版本历史

- **v1.0.0** (2025-11-17)
  - ✅ 初始版本
  - ✅ 支持两阶段生成
  - ✅ 多种放大算法
  - ✅ 完整的参数配置
  - ✅ 错误处理和进度显示

## 相关组件

- `InpaintingPanel`: 局部重绘
- `OutpaintingPanel`: 画布扩展
- `UpscalePanel`: 独立图像放大
- `ModelManager`: 模型管理

## 许可证

MIT License
