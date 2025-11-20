# OutpaintingPanel API集成测试文档

## 概述

本文档描述OutpaintingPanel组件与后端Outpainting API的集成测试。

## API端点

**URL**: `/api/outpaint`  
**方法**: POST  
**Content-Type**: application/json

## 请求参数

| 参数名 | 类型 | 必需 | 默认值 | 说明 |
|--------|------|------|--------|------|
| image | string | 是 | - | Base64编码的源图像 |
| prompt | string | 是 | - | 生成内容的描述 |
| negative_prompt | string | 否 | "" | 不想要的内容描述 |
| direction | string | 否 | "all" | 扩展方向：left/right/top/bottom/all |
| extend_pixels | number | 否 | 128 | 扩展的像素数 |
| guidance_scale | number | 否 | 7.5 | 引导强度 |
| num_inference_steps | number | 否 | 20 | 生成步数 |

## 响应格式

### 成功响应

```json
{
  "success": true,
  "image": "data:image/png;base64,..."
}
```

### 错误响应

```json
{
  "success": false,
  "message": "错误描述"
}
```

## 前端实现

### API调用逻辑

```typescript
async function performOutpainting() {
  const response = await fetch('/api/outpaint', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      image: sourceImage,           // Base64图像
      direction: direction,         // 扩展方向
      extend_pixels: pixels,        // 扩展像素数
      prompt: prompt,
      negative_prompt: negativePrompt,
      guidance_scale: guidanceScale,
      num_inference_steps: steps
    })
  });
  
  const data = await response.json();
  
  if (data.success) {
    resultImage = data.image;
    showResult = true;
  }
}
```

### 加载状态显示

- 使用 `loading` 状态变量控制UI
- 按钮显示"扩展中..."文本和加载动画
- 禁用所有交互控件

```svelte
<button
  on:click={performOutpainting}
  disabled={loading || !prompt.trim()}
  class="..."
>
  {#if loading}
    <span class="flex items-center justify-center gap-2">
      <div class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
      扩展中...
    </span>
  {:else}
    开始扩展
  {/if}
</button>
```

### 错误处理

使用统一的错误处理系统（ErrorType）：

1. **验证错误** (VALIDATION)
   - 未上传图像
   - Prompt为空

2. **API错误** (API)
   - HTTP错误状态码
   - 网络连接失败

3. **生成错误** (GENERATION)
   - 后端返回success: false
   - 生成过程失败

```typescript
try {
  // API调用
} catch (e) {
  setError({
    type: ErrorType.API,
    message: 'Outpainting请求失败',
    details: e instanceof Error ? e.message : String(e),
    recoverable: true,
    suggestions: [
      '检查网络连接',
      '确认后端服务正常运行',
      '查看浏览器控制台获取更多信息'
    ]
  });
}
```

## 测试场景

### 1. 基本功能测试

#### 测试步骤：
1. 上传一张512x512的测试图像
2. 输入Prompt: "beautiful landscape, mountains, sky"
3. 选择方向: "all"
4. 设置扩展尺寸: 128px
5. 点击"开始扩展"

#### 预期结果：
- ✅ 显示加载状态
- ✅ 成功返回扩展后的图像
- ✅ 图像尺寸为768x768 (512 + 128*2)
- ✅ 扩展区域与原图自然融合

### 2. 不同方向测试

#### 测试步骤：
分别测试以下方向：
- left (向左扩展)
- right (向右扩展)
- top (向上扩展)
- bottom (向下扩展)
- all (全方向扩展)

#### 预期结果：
- ✅ 每个方向都能正确扩展
- ✅ 预览画布正确显示扩展区域
- ✅ 生成结果符合选择的方向

### 3. 不同扩展尺寸测试

#### 测试步骤：
测试不同的extend_pixels值：
- 64px (最小)
- 128px (默认)
- 256px
- 512px (最大)

#### 预期结果：
- ✅ 所有尺寸都能正常工作
- ✅ 生成时间随尺寸增加而增加
- ✅ 较大尺寸可能需要更多显存

### 4. 参数调整测试

#### 测试步骤：
1. 调整guidance_scale: 1.0 → 20.0
2. 调整steps: 10 → 50
3. 测试不同的Prompt

#### 预期结果：
- ✅ 参数变化影响生成质量
- ✅ 更高的guidance_scale更贴近Prompt
- ✅ 更多steps生成质量更好但速度更慢

### 5. 错误处理测试

#### 测试场景A：未上传图像
- 操作：直接点击"开始扩展"
- 预期：显示错误提示"请先上传图像"

#### 测试场景B：Prompt为空
- 操作：上传图像但不输入Prompt
- 预期：按钮禁用，无法点击

#### 测试场景C：网络错误
- 操作：断开网络连接后尝试扩展
- 预期：显示网络错误提示

#### 测试场景D：后端错误
- 操作：后端服务未启动
- 预期：显示API错误提示

### 6. 结果显示测试

#### 测试步骤：
1. 成功生成一张图像
2. 检查结果显示区域
3. 点击"下载"按钮

#### 预期结果：
- ✅ 结果图像正确显示
- ✅ 图像清晰，无失真
- ✅ 下载功能正常工作
- ✅ 文件名包含时间戳

### 7. 重置功能测试

#### 测试步骤：
1. 完成一次完整的Outpainting流程
2. 点击"重置"按钮

#### 预期结果：
- ✅ 清除源图像
- ✅ 清除结果图像
- ✅ 重置所有参数为默认值
- ✅ 清除错误状态

## 性能测试

### 响应时间

| 场景 | 预期时间 | 备注 |
|------|----------|------|
| 图像上传 | < 1s | 取决于图像大小 |
| API请求 | 2-10s | 取决于参数和硬件 |
| 结果显示 | < 0.5s | 即时显示 |

### 显存使用

| 配置 | 预期显存 | 备注 |
|------|----------|------|
| 512x512 → 768x768 | ~4GB | 标准配置 |
| 512x512 → 1024x1024 | ~6GB | 大尺寸扩展 |

## 已知问题

### 1. 参数名称不匹配（已修复）

**问题**：前端使用`pixels`，后端期望`extend_pixels`

**解决方案**：
```typescript
// 修改前
body: JSON.stringify({
  pixels: pixels,  // ❌ 错误
  ...
})

// 修改后
body: JSON.stringify({
  extend_pixels: pixels,  // ✅ 正确
  ...
})
```

### 2. Base64编码格式

**注意**：确保Base64字符串包含正确的前缀：
```
data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...
```

后端会自动处理带或不带前缀的情况。

## 集成检查清单

- [x] API调用逻辑已实现
- [x] 参数名称与后端匹配
- [x] 加载状态显示已实现
- [x] 错误处理已实现
- [x] 结果显示已实现
- [x] 下载功能已实现
- [x] 重置功能已实现
- [ ] 所有方向测试通过
- [ ] 不同尺寸测试通过
- [ ] 错误场景测试通过
- [ ] 性能测试通过

## 下一步

1. 进行完整的功能测试
2. 测试不同的扩展方向
3. 测试边界情况（极小/极大尺寸）
4. 性能优化（如果需要）
5. 集成到主页面（任务5.3）

## 更新日志

### 2024-11-17
- ✅ 修复参数名称不匹配问题（pixels → extend_pixels）
- ✅ 完成API集成实现
- ✅ 创建测试文档

---

**状态**: API集成已完成，等待测试验证  
**负责人**: AI Assistant  
**最后更新**: 2024-11-17
