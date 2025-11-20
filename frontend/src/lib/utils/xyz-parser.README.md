# XYZ Plot 参数范围解析器

## 概述

`xyz-parser.ts` 提供了强大的参数范围解析功能，用于 XYZ Plot 功能。支持多种输入格式，可以灵活地定义参数值。

## 功能特性

### 1. 多种输入格式支持

#### 逗号分隔的值
```typescript
parseParameterValues('1, 2, 3, 4')
// 结果: [1, 2, 3, 4]

parseParameterValues('5.0, 7.5, 10.0')
// 结果: [5.0, 7.5, 10.0]
```

#### 范围表达式（冒号格式）
```typescript
parseParameterValues('1.0-5.0:1.0')
// 结果: [1.0, 2.0, 3.0, 4.0, 5.0]

parseParameterValues('5.0-10.0:2.5')
// 结果: [5.0, 7.5, 10.0]
```

#### 范围表达式（步长格式）
```typescript
parseParameterValues('1-5, 步长1')
// 结果: [1, 2, 3, 4, 5]

parseParameterValues('0.5-0.9, 步长0.1')
// 结果: [0.5, 0.6, 0.7, 0.8, 0.9]

parseParameterValues('1-10, step 2')
// 结果: [1, 3, 5, 7, 9]
```

#### 混合格式
```typescript
parseParameterValues('1, 2-4:1, 5, 6-8:2')
// 结果: [1, 2, 3, 4, 5, 6, 8]
```

#### 字符串类型
```typescript
parseParameterValues('euler, euler_a, dpm++', 'sampler')
// 结果: ['euler', 'euler_a', 'dpm++']
```

### 2. 自动去重

解析器会自动去除重复的值，保持顺序：

```typescript
parseParameterValues('1, 2, 2, 3, 3, 3')
// 结果: [1, 2, 3]
```

### 3. 智能步长推断

如果范围表达式没有指定步长，解析器会根据范围自动推断合适的步长：

```typescript
parseParameterValues('1-10')
// 自动步长: 1，结果: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

parseParameterValues('1-100')
// 自动步长: 10，结果: [1, 11, 21, 31, 41, 51, 61, 71, 81, 91]
```

### 4. 安全限制

- 单个范围表达式最多生成 100 个值
- 网格总组合数默认限制为 100（可配置）
- 防止浮点精度问题

## API 文档

### parseParameterValues

解析参数值字符串。

```typescript
function parseParameterValues(
  valueString: string,
  parameterType?: string
): ParsedValues
```

**参数:**
- `valueString`: 参数值字符串
- `parameterType`: 参数类型（'numeric', 'steps', 'cfg_scale', 'sampler' 等）

**返回:**
```typescript
interface ParsedValues {
  values: (number | string)[];  // 解析后的值数组
  count: number;                // 值的数量
  isValid: boolean;             // 是否解析成功
  error?: string;               // 错误信息（如果有）
}
```

**示例:**
```typescript
const result = parseParameterValues('5.0-10.0:2.5', 'cfg_scale');
if (result.isValid) {
  console.log(result.values); // [5.0, 7.5, 10.0]
  console.log(result.count);  // 3
} else {
  console.error(result.error);
}
```

### validateGridConfiguration

验证网格配置是否有效。

```typescript
function validateGridConfiguration(
  xAxisValues: string,
  yAxisValues: string,
  zAxisValues?: string | null,
  maxCombinations?: number
): ValidationResult
```

**参数:**
- `xAxisValues`: X轴参数值字符串
- `yAxisValues`: Y轴参数值字符串
- `zAxisValues`: Z轴参数值字符串（可选）
- `maxCombinations`: 最大组合数限制（默认100）

**返回:**
```typescript
interface ValidationResult {
  isValid: boolean;
  error?: string;
  totalCombinations: number;
}
```

**示例:**
```typescript
const result = validateGridConfiguration(
  '20, 30, 40',
  '5.0-10.0:2.5',
  null,
  100
);

if (result.isValid) {
  console.log(`将生成 ${result.totalCombinations} 张图像`);
} else {
  console.error(result.error);
}
```

### calculateParameterCombinations

计算所有参数组合。

```typescript
function calculateParameterCombinations(
  config: GridConfiguration
): ParameterCombination[]
```

**参数:**
```typescript
interface GridConfiguration {
  xAxis: { type: string; values: (number | string)[] };
  yAxis: { type: string; values: (number | string)[] };
  zAxis?: { type: string; values: (number | string)[] };
  totalCombinations: number;
  isValid: boolean;
}
```

**返回:**
```typescript
interface ParameterCombination {
  [key: string]: number | string;
}
```

**示例:**
```typescript
const config = {
  xAxis: { type: 'steps', values: [20, 30] },
  yAxis: { type: 'cfg_scale', values: [5.0, 7.5] },
  totalCombinations: 4,
  isValid: true
};

const combinations = calculateParameterCombinations(config);
// 结果:
// [
//   { steps: 20, cfg_scale: 5.0 },
//   { steps: 30, cfg_scale: 5.0 },
//   { steps: 20, cfg_scale: 7.5 },
//   { steps: 30, cfg_scale: 7.5 }
// ]
```

### getExampleValues

获取参数类型的示例值。

```typescript
function getExampleValues(parameterType: string): string
```

**示例:**
```typescript
getExampleValues('steps')              // "20, 30, 40, 50"
getExampleValues('cfg_scale')          // "5.0-10.0:2.5"
getExampleValues('denoising_strength') // "0.5-0.9, 步长0.1"
```

### formatParameterValues

格式化参数值数组为字符串。

```typescript
function formatParameterValues(values: (number | string)[]): string
```

**示例:**
```typescript
formatParameterValues([1, 2, 3])           // "1, 2, 3"
formatParameterValues(['euler', 'dpm++'])  // "euler, dpm++"
```

## 使用示例

### 在 Svelte 组件中使用

```svelte
<script lang="ts">
  import { parseParameterValues, validateGridConfiguration } from '$lib/utils/xyz-parser';
  
  let xAxisValues = '20, 30, 40';
  let yAxisValues = '5.0-10.0:2.5';
  
  // 响应式解析
  $: xParsed = parseParameterValues(xAxisValues, 'steps');
  $: yParsed = parseParameterValues(yAxisValues, 'cfg_scale');
  
  // 响应式验证
  $: validation = validateGridConfiguration(xAxisValues, yAxisValues);
  
  // 显示解析结果
  $: if (xParsed.isValid) {
    console.log('X轴值:', xParsed.values);
  }
</script>

<div>
  <input bind:value={xAxisValues} />
  {#if xParsed.isValid}
    <span>✓ 已解析 {xParsed.count} 个值</span>
  {:else}
    <span>✗ {xParsed.error}</span>
  {/if}
</div>
```

### 错误处理

```typescript
const result = parseParameterValues('5-1:1'); // 无效：起始值大于结束值

if (!result.isValid) {
  console.error('解析失败:', result.error);
  // 显示错误提示给用户
}
```

## 支持的参数类型

| 参数类型 | 数据类型 | 示例值 |
|---------|---------|--------|
| steps | number | 20, 30, 40, 50 |
| cfg_scale | number | 5.0-10.0:2.5 |
| denoising_strength | number | 0.5-0.9, 步长0.1 |
| seed | number | 42, 123, 456 |
| sampler | string | euler, euler_a, dpm++ |
| scheduler | string | normal, karras, exponential |
| width | number | 512, 768, 1024 |
| height | number | 512, 768, 1024 |

## 限制和注意事项

1. **值数量限制**: 单个范围表达式最多生成 100 个值
2. **组合数限制**: 默认最多 100 个组合（可配置）
3. **浮点精度**: 自动处理浮点精度问题
4. **步长验证**: 步长必须大于 0
5. **范围验证**: 起始值必须小于结束值

## 测试

运行单元测试：

```bash
npm test xyz-parser.test.ts
```

测试覆盖：
- ✅ 逗号分隔的值解析
- ✅ 范围表达式解析（多种格式）
- ✅ 混合格式解析
- ✅ 字符串类型解析
- ✅ 去重功能
- ✅ 错误处理
- ✅ 网格配置验证
- ✅ 参数组合计算

## 更新日志

### v1.0.0 (2025-11-17)
- ✅ 初始版本
- ✅ 支持多种输入格式
- ✅ 自动去重
- ✅ 智能步长推断
- ✅ 完整的错误处理
- ✅ 单元测试覆盖

## 贡献

如需添加新功能或修复bug，请：
1. 添加相应的单元测试
2. 更新文档
3. 确保所有测试通过

## 许可

MIT License
