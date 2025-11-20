# ControlNetItem 快速开始指南

## 5分钟上手

### 1. 导入组件

```svelte
<script>
  import ControlNetItem from '$lib/components/ControlNetItem.svelte';
</script>
```

### 2. 准备配置数据

```typescript
let config = {
  id: 'cn-1',
  type: 'canny',
  image: '',
  weight: 1.0,
  guidanceStart: 0.0,
  guidanceEnd: 1.0
};
```

### 3. 定义回调函数

```typescript
function handleRemove(id: string) {
  console.log('删除:', id);
}

function handleUpdate(id: string, field: string, value: any) {
  config = { ...config, [field]: value };
}
```

### 4. 使用组件

```svelte
<ControlNetItem
  {config}
  index={0}
  availableTypes={['canny', 'depth', 'pose']}
  onRemove={handleRemove}
  onUpdate={handleUpdate}
/>
```

## 常见用法

### 在列表中使用

```svelte
<script>
  let controlnets = [
    { id: 'cn-1', type: 'canny', image: '', weight: 1.0, guidanceStart: 0.0, guidanceEnd: 1.0 }
  ];
  
  function removeControlNet(id) {
    controlnets = controlnets.filter(cn => cn.id !== id);
  }
  
  function updateControlNet(id, field, value) {
    controlnets = controlnets.map(cn => 
      cn.id === id ? { ...cn, [field]: value } : cn
    );
  }
</script>

{#each controlnets as cn, index (cn.id)}
  <ControlNetItem
    config={cn}
    {index}
    availableTypes={['canny', 'depth', 'pose']}
    onRemove={removeControlNet}
    onUpdate={updateControlNet}
  />
{/each}
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| config | ControlNetConfig | 必需 | ControlNet配置对象 |
| index | number | 必需 | 显示的索引号 |
| availableTypes | string[] | 预设列表 | 可用的类型列表 |
| onRemove | Function | () => {} | 删除回调 |
| onUpdate | Function | () => {} | 更新回调 |

## 配置对象结构

```typescript
interface ControlNetConfig {
  id: string;              // 唯一标识
  type: string;            // 类型
  image: string;           // Base64图像
  weight: number;          // 权重 (0.0-2.0)
  guidanceStart: number;   // 引导开始 (0.0-1.0)
  guidanceEnd: number;     // 引导结束 (0.0-1.0)
}
```

## 常见问题

**Q: 如何获取配置数据？**
A: 配置数据通过 `onUpdate` 回调实时更新到你的状态中。

**Q: 支持哪些图像格式？**
A: 支持所有浏览器支持的图像格式（PNG, JPG, WebP, GIF等）。

**Q: 如何验证配置是否完整？**
A: 检查 `config.image` 是否为空字符串。

---

**查看完整文档**: [ControlNetItem.README.md](./ControlNetItem.README.md)
