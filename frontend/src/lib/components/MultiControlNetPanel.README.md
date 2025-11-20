# MultiControlNetPanel 组件

## 概述

`MultiControlNetPanel` 是一个用于管理多个 ControlNet 配置的 Svelte 组件。它允许用户添加最多 3 个 ControlNet，每个都有独立的配置选项。

## 功能特性

- ✅ 支持添加/删除 ControlNet（最多 3 个）
- ✅ 每个 ControlNet 独立配置
- ✅ 支持多种 ControlNet 类型（canny、depth、pose 等）
- ✅ 图像上传和预览
- ✅ 权重调整（0.0 - 2.0）
- ✅ 引导范围控制（guidance start/end）
- ✅ 完整的错误处理
- ✅ 响应式设计
- ✅ **API集成完成** - 支持调用后端多ControlNet生成API

## 使用方法

### 基础用法

```svelte
<script>
  import MultiControlNetPanel from '$lib/components/MultiControlNetPanel.svelte';
  
  let panel;
  
  function handleGenerate() {
    // 验证配置
    const validation = panel.validate();
    if (!validation.valid) {
      console.error(validation.message);
      return;
    }
    
    // 获取配置
    const controlnets = panel.getControlNets();
    console.log('ControlNet配置:', controlnets);
    
    // 调用API生成图像
    // ...
  }
</script>

<MultiControlNetPanel bind:this={panel} />
<button on:click={handleGenerate}>生成</button>
```

### 高级用法

```svelte
<script>
  import MultiControlNetPanel from '$lib/components/MultiControlNetPanel.svelte';
  
  let panel;
  let loading = false;
  
  async function generateWithMultiControlNet() {
    // 验证
    const validation = panel.validate();
    if (!validation.valid) {
      alert(validation.message);
      return;
    }
    
    // 获取配置
    const controlnets = panel.getControlNets();
    
    if (controlnets.length === 0) {
      alert('请至少添加一个ControlNet');
      return;
    }
    
    loading = true;
    
    try {
      const response = await fetch('/api/multi-controlnet/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: 'your prompt here',
          negative_prompt: 'your negative prompt',
          controlnets: controlnets.map(cn => ({
            type: cn.type,
            image: cn.image,
            weight: cn.weight,
            guidance_start: cn.guidanceStart,
            guidance_end: cn.guidanceEnd
          })),
          steps: 20,
          guidance_scale: 7.5
        })
      });
      
      const data = await response.json();
      console.log('生成结果:', data);
    } catch (error) {
      console.error('生成失败:', error);
    } finally {
      loading = false;
    }
  }
</script>

<MultiControlNetPanel bind:this={panel} />
<button on:click={generateWithMultiControlNet} disabled={loading}>
  {loading ? '生成中...' : '开始生成'}
</button>
```

## API

### 导出方法

#### `getControlNets(): ControlNetConfig[]`

获取所有已配置的 ControlNet（只返回已上传图像的）。

**返回值:**
```typescript
interface ControlNetConfig {
  id: string;              // 唯一标识符
  type: string;            // ControlNet类型
  image: string;           // Base64图像数据
  weight: number;          // 权重 (0.0-2.0)
  guidanceStart: number;   // 引导开始 (0.0-1.0)
  guidanceEnd: number;     // 引导结束 (0.0-1.0)
}
```

**示例:**
```javascript
const controlnets = panel.getControlNets();
console.log(`配置了 ${controlnets.length} 个ControlNet`);
```

#### `validate(): { valid: boolean; message?: string }`

验证当前配置是否有效。

**返回值:**
- `valid`: 配置是否有效
- `message`: 错误消息（如果无效）

**示例:**
```javascript
const validation = panel.validate();
if (!validation.valid) {
  alert(validation.message);
}
```

#### `generate(params): Promise<{ success: boolean; image?: string; message?: string }>` ✨ 新增

直接调用后端API生成图像。

**参数:**
```typescript
interface GenerateParams {
  prompt: string;
  negative_prompt?: string;
  num_inference_steps?: number;  // 默认: 20
  guidance_scale?: number;        // 默认: 7.5
  height?: number;                // 默认: 512
  width?: number;                 // 默认: 512
  seed?: number;                  // 可选
}
```

**返回值:**
```typescript
interface GenerateResult {
  success: boolean;
  image?: string;      // Base64图像数据（如果成功）
  message?: string;    // 错误消息（如果失败）
}
```

**示例:**
```javascript
const result = await panel.generate({
  prompt: 'a beautiful landscape',
  negative_prompt: 'ugly, blurry',
  num_inference_steps: 20,
  guidance_scale: 7.5,
  height: 512,
  width: 512
});

if (result.success) {
  console.log('生成成功！');
  displayImage(result.image);
} else {
  console.error('生成失败:', result.message);
}
```

## ControlNet 配置说明

### 类型 (Type)

支持的 ControlNet 类型：
- `canny`: 边缘检测
- `depth`: 深度图
- `pose`: 姿态检测
- `scribble`: 涂鸦
- `lineart`: 线稿
- `normal`: 法线贴图
- `semantic`: 语义分割

### 权重 (Weight)

控制 ControlNet 的影响强度：
- 范围: 0.0 - 2.0
- 默认: 1.0
- 建议: 0.5 - 1.5

### 引导范围 (Guidance Range)

控制 ControlNet 在生成过程中的作用时机：
- `guidanceStart`: 开始时机 (0.0 - 1.0)
- `guidanceEnd`: 结束时机 (0.0 - 1.0)
- 默认: 0.0 - 1.0（全程作用）

**示例:**
- `0.0 - 0.5`: 只在前半段作用
- `0.5 - 1.0`: 只在后半段作用
- `0.0 - 1.0`: 全程作用

## 错误处理

组件使用统一的错误处理机制：

```javascript
import { setError, ErrorType } from '$lib/store';

// 验证错误
setError({
  type: ErrorType.VALIDATION,
  message: '配置验证失败',
  details: '请检查ControlNet配置',
  recoverable: true
});
```

## 样式定制

组件使用 CSS 变量，可以通过覆盖这些变量来定制样式：

```css
:root {
  --color-background: #ffffff;
  --color-surface: #f5f5f5;
  --color-border: #e0e0e0;
  --color-text-primary: #000000;
  --color-text-secondary: #666666;
  --color-primary: #3b82f6;
  --color-error: #ef4444;
}
```

## 最佳实践

### 1. 图像尺寸

建议使用与生成目标相同尺寸的控制图像：
- 标准: 512x512
- 高清: 768x768 或 1024x1024

### 2. 权重调整

- 从默认值 1.0 开始
- 如果效果太强，降低到 0.5-0.8
- 如果效果太弱，提高到 1.2-1.5

### 3. 类型组合

推荐的 ControlNet 组合：
- Canny + Depth: 精确控制结构和深度
- Pose + Lineart: 控制姿态和线条
- Depth + Normal: 增强 3D 感

### 4. 性能优化

- 避免同时使用 3 个高权重的 ControlNet
- 使用较小的图像尺寸可以提高速度
- 考虑使用引导范围来减少计算量

## 故障排除

### 问题: 无法添加 ControlNet

**原因:** 已达到最大数量（3个）

**解决:** 删除现有的 ControlNet 后再添加

### 问题: 图像上传失败

**原因:** 文件格式不支持或文件损坏

**解决:** 
- 确保使用支持的图像格式（PNG、JPG、WebP）
- 尝试使用其他图像文件

### 问题: 生成效果不理想

**原因:** ControlNet 配置不当

**解决:**
- 调整权重值
- 尝试不同的 ControlNet 类型
- 调整引导范围

## 示例场景

### 场景 1: 精确重绘

```javascript
// 使用 Canny 边缘检测保持结构
{
  type: 'canny',
  weight: 1.2,
  guidanceStart: 0.0,
  guidanceEnd: 1.0
}
```

### 场景 2: 风格转换

```javascript
// 使用 Depth 保持深度，Lineart 保持线条
[
  { type: 'depth', weight: 0.8, guidanceStart: 0.0, guidanceEnd: 0.7 },
  { type: 'lineart', weight: 0.6, guidanceStart: 0.0, guidanceEnd: 1.0 }
]
```

### 场景 3: 姿态控制

```javascript
// 使用 Pose 控制人物姿态
{
  type: 'pose',
  weight: 1.0,
  guidanceStart: 0.0,
  guidanceEnd: 0.8
}
```

## 相关组件

- `InpaintingPanel`: 局部重绘
- `OutpaintingPanel`: 画布扩展
- `HiresFixPanel`: 高分辨率修复

## 更新日志

### v1.0.0 (2025-11-17)
- ✅ 初始版本
- ✅ 支持最多 3 个 ControlNet
- ✅ 完整的配置选项
- ✅ 错误处理和验证

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
