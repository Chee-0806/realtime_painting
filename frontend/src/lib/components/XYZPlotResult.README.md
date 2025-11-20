# XYZPlotResult 组件

XYZ Plot 结果展示组件，用于以网格形式展示参数对比生成的图像结果。

## 功能特性

### ✅ 核心功能
- **网格布局展示**: 以表格形式展示所有参数组合的生成结果
- **参数标签显示**: 清晰显示X轴、Y轴和Z轴的参数类型和值
- **图像点击放大**: 点击任意图像可放大预览，显示对应的参数信息
- **批量下载功能**: 一键下载所有生成的图像，文件名自动包含参数信息
- **3D网格支持**: 支持Z轴参数，可通过选择器切换不同的Z值
- **键盘快捷键**: 按ESC键快速关闭预览窗口

### 🎨 用户体验
- 响应式网格布局，自动适应不同屏幕尺寸
- 图像悬停效果，提供视觉反馈
- 平滑的动画过渡
- 清晰的参数标签和统计信息

## 使用方法

### 基本用法

```svelte
<script>
  import XYZPlotResult from '$lib/components/XYZPlotResult.svelte';
  
  let results = {
    images: [
      'data:image/png;base64,...',
      'data:image/png;base64,...',
      // 更多图像...
    ],
    xAxis: {
      type: 'steps',
      values: [20, 30, 40, 50]
    },
    yAxis: {
      type: 'cfg_scale',
      values: [5.0, 7.5, 10.0]
    }
  };
</script>

<XYZPlotResult {results} />
```

### 带Z轴的3D网格

```svelte
<script>
  import XYZPlotResult from '$lib/components/XYZPlotResult.svelte';
  
  let results = {
    images: [...], // 图像数组
    xAxis: {
      type: 'steps',
      values: [20, 30, 40]
    },
    yAxis: {
      type: 'cfg_scale',
      values: [5.0, 7.5, 10.0]
    },
    zAxis: {
      type: 'seed',
      values: [42, 123, 456]
    }
  };
</script>

<XYZPlotResult {results} />
```

### 空状态

```svelte
<script>
  import XYZPlotResult from '$lib/components/XYZPlotResult.svelte';
  
  let results = null; // 显示空状态
</script>

<XYZPlotResult {results} />
```

## Props

### `results`
- **类型**: `Object | null`
- **必需**: 是
- **默认值**: `null`

结果数据对象，包含以下字段：

```typescript
{
  images: string[];  // Base64编码的图像数组
  xAxis: {
    type: string;              // 参数类型
    values: (number | string)[] // 参数值数组
  };
  yAxis: {
    type: string;
    values: (number | string)[]
  };
  zAxis?: {  // 可选
    type: string;
    values: (number | string)[]
  };
}
```

#### 图像数组顺序
图像数组按照 **Z → Y → X** 的顺序排列：
- 对于2D网格（无Z轴）：`[Y0X0, Y0X1, Y0X2, Y1X0, Y1X1, Y1X2, ...]`
- 对于3D网格（有Z轴）：`[Z0Y0X0, Z0Y0X1, Z0Y1X0, Z0Y1X1, Z1Y0X0, Z1Y0X1, ...]`

#### 支持的参数类型
- `steps`: 步数
- `cfg_scale`: CFG引导强度
- `denoising_strength`: 降噪强度
- `seed`: 随机种子
- `sampler`: 采样器
- `scheduler`: 调度器
- `width`: 宽度
- `height`: 高度

## 功能说明

### 网格布局
- 使用HTML表格实现网格布局
- X轴参数显示在表头
- Y轴参数显示在左侧列
- 每个单元格显示对应参数组合的生成图像

### 图像预览
- 点击任意图像打开全屏预览
- 预览窗口显示：
  - 放大的图像
  - 对应的参数信息（X、Y、Z值）
  - 下载按钮
  - 关闭按钮
- 支持键盘快捷键（ESC关闭）

### 批量下载
- 点击"批量下载"按钮下载所有图像
- 文件名格式：
  - 2D网格: `xy_{xType}_{xValue}_{yType}_{yValue}.png`
  - 3D网格: `xyz_{xType}_{xValue}_{yType}_{yValue}_{zType}_{zValue}.png`
- 自动延迟下载，避免浏览器阻止
- 显示下载进度状态

### Z轴支持
- 当提供Z轴数据时，显示Z轴选择器
- 点击Z值按钮可滚动到对应的网格
- 每个Z值显示独立的2D网格

## 示例

查看 `XYZPlotResult.example.svelte` 文件获取完整的使用示例。

## 样式定制

组件使用Tailwind CSS类，可以通过修改类名来定制样式：

```svelte
<!-- 修改网格单元格大小 -->
<th class="p-2 min-w-[120px]">  <!-- 改为 min-w-[200px] -->

<!-- 修改预览窗口大小 -->
<div class="max-w-4xl">  <!-- 改为 max-w-6xl -->
```

## 注意事项

1. **图像格式**: 图像必须是Base64编码的Data URL格式
2. **数组顺序**: 确保图像数组按照正确的顺序排列（Z → Y → X）
3. **性能**: 大量图像可能影响性能，建议限制网格大小
4. **浏览器兼容**: 批量下载功能可能在某些浏览器中受限

## 集成示例

### 与XYZPlotPanel集成

```svelte
<script>
  import XYZPlotPanel from '$lib/components/XYZPlotPanel.svelte';
  import XYZPlotResult from '$lib/components/XYZPlotResult.svelte';
  
  let results = null;
  
  async function handleGenerate(config) {
    // 调用API生成图像
    const response = await fetch('/api/xyz-plot', {
      method: 'POST',
      body: JSON.stringify(config)
    });
    
    const data = await response.json();
    results = data.results;
  }
</script>

<div class="grid grid-cols-2 gap-4">
  <div>
    <XYZPlotPanel on:generate={handleGenerate} />
  </div>
  <div>
    <XYZPlotResult {results} />
  </div>
</div>
```

## 相关组件

- `XYZPlotPanel.svelte`: XYZ Plot 参数配置面板
- `xyz-parser.ts`: 参数解析工具

## 更新日志

### v1.0.0 (2024-11-17)
- ✅ 初始版本
- ✅ 实现网格布局
- ✅ 实现参数标签显示
- ✅ 实现图像点击放大
- ✅ 实现批量下载功能
- ✅ 支持Z轴3D网格
