# MultiControlNetPanel 快速开始

## 5 分钟上手指南

### 1. 导入组件

```svelte
<script>
  import MultiControlNetPanel from '$lib/components/MultiControlNetPanel.svelte';
  
  let panel;
</script>
```

### 2. 添加到页面

```svelte
<MultiControlNetPanel bind:this={panel} />
```

### 3. 获取配置

```javascript
// 验证配置
const validation = panel.validate();
if (!validation.valid) {
  alert(validation.message);
  return;
}

// 获取 ControlNet 配置
const controlnets = panel.getControlNets();
console.log('配置:', controlnets);
```

### 4. 调用 API

```javascript
const response = await fetch('/api/multi-controlnet/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    prompt: 'your prompt',
    controlnets: controlnets.map(cn => ({
      type: cn.type,
      image: cn.image,
      weight: cn.weight,
      guidance_start: cn.guidanceStart,
      guidance_end: cn.guidanceEnd
    }))
  })
});
```

## 完整示例

```svelte
<script lang="ts">
  import MultiControlNetPanel from '$lib/components/MultiControlNetPanel.svelte';
  
  let panel;
  let loading = false;
  let result = '';
  
  async function generate() {
    // 验证
    const validation = panel.validate();
    if (!validation.valid) {
      alert(validation.message);
      return;
    }
    
    // 获取配置
    const controlnets = panel.getControlNets();
    if (controlnets.length === 0) {
      alert('请至少添加一个 ControlNet');
      return;
    }
    
    loading = true;
    
    try {
      const response = await fetch('/api/multi-controlnet/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: 'a beautiful landscape',
          negative_prompt: 'ugly, blurry',
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
      if (data.success) {
        result = data.image;
      }
    } catch (error) {
      console.error('生成失败:', error);
      alert('生成失败，请重试');
    } finally {
      loading = false;
    }
  }
</script>

<div class="container">
  <MultiControlNetPanel bind:this={panel} />
  
  <button on:click={generate} disabled={loading}>
    {loading ? '生成中...' : '开始生成'}
  </button>
  
  {#if result}
    <img src={result} alt="生成结果" />
  {/if}
</div>
```

## 常见用法

### 添加 ControlNet

用户点击"+ 添加ControlNet"按钮即可添加，最多 3 个。

### 配置 ControlNet

每个 ControlNet 可以独立配置：
- **类型**: 选择 ControlNet 类型（canny、depth、pose 等）
- **图像**: 上传控制图像
- **权重**: 调整影响强度（0.0 - 2.0）
- **引导范围**: 控制作用时机（0.0 - 1.0）

### 删除 ControlNet

点击每个 ControlNet 右上角的 ✕ 按钮即可删除。

## 推荐配置

### 精确重绘
```javascript
{
  type: 'canny',
  weight: 1.2,
  guidanceStart: 0.0,
  guidanceEnd: 1.0
}
```

### 风格转换
```javascript
[
  { type: 'depth', weight: 0.8 },
  { type: 'lineart', weight: 0.6 }
]
```

### 姿态控制
```javascript
{
  type: 'pose',
  weight: 1.0,
  guidanceStart: 0.0,
  guidanceEnd: 0.8
}
```

## 故障排除

### 无法添加 ControlNet
- 检查是否已达到最大数量（3个）
- 删除现有的 ControlNet 后再添加

### 图像上传失败
- 确保文件格式正确（PNG、JPG、WebP）
- 检查文件大小是否过大

### 生成效果不理想
- 调整权重值（建议 0.5 - 1.5）
- 尝试不同的 ControlNet 类型
- 调整引导范围

## 下一步

- 查看 [完整文档](./MultiControlNetPanel.README.md)
- 查看 [测试指南](./MultiControlNetPanel.TEST.md)
- 查看 [示例代码](./MultiControlNetPanel.example.svelte)

## 需要帮助？

如果遇到问题，请：
1. 查看浏览器控制台的错误信息
2. 检查后端日志
3. 参考完整文档
4. 提交 Issue
