# CLIPInterrogatorPanel 快速开始

## 5 分钟快速上手

### 1. 导入组件

```svelte
<script>
  import CLIPInterrogatorPanel from '$lib/components/CLIPInterrogatorPanel.svelte';
</script>
```

### 2. 使用组件

```svelte
<CLIPInterrogatorPanel />
```

就这么简单！🎉

---

## 常见用法

### 基础使用

```svelte
<CLIPInterrogatorPanel />
```

### 带初始图像

```svelte
<CLIPInterrogatorPanel initialImageUrl="https://example.com/image.jpg" />
```

### 自动应用结果

```svelte
<CLIPInterrogatorPanel autoApplyPrompt={true} />
```

### 监听事件

```svelte
<script>
  function handleResult(event) {
    console.log('反推结果:', event.detail);
  }
</script>

<CLIPInterrogatorPanel on:result={handleResult} />
```

---

## Props 速查

| Props | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| `initialImageUrl` | string | `''` | 初始图像 URL |
| `showCloseButton` | boolean | `true` | 显示关闭按钮 |
| `autoApplyPrompt` | boolean | `false` | 自动应用结果 |

---

## 事件速查

| 事件 | 参数 | 说明 |
|------|------|------|
| `on:result` | `{ prompt, negative_prompt, flavors, mode }` | 反推完成 |
| `on:apply` | `{ prompt, negative_prompt, flavors, mode }` | 应用 Prompt |
| `on:copy` | `{ type, text }` | 复制文本 |
| `on:close` | - | 关闭面板 |

---

## 反推模式

- **⚡ 快速模式**: 速度快，适合预览
- **🎯 经典模式**: 详细准确，推荐使用
- **🚫 负面模式**: 生成负面提示词

---

## 完整示例

```svelte
<script lang="ts">
  import CLIPInterrogatorPanel from '$lib/components/CLIPInterrogatorPanel.svelte';
  
  let showPanel = false;
  
  function handleResult(event: CustomEvent) {
    console.log('反推结果:', event.detail);
    alert('反推完成！');
  }
  
  function handleApply(event: CustomEvent) {
    console.log('应用 Prompt:', event.detail);
    alert('Prompt 已应用！');
  }
  
  function handleClose() {
    showPanel = false;
  }
</script>

<button on:click={() => showPanel = true}>
  打开 CLIP 反推
</button>

{#if showPanel}
  <div class="modal">
    <CLIPInterrogatorPanel
      on:result={handleResult}
      on:apply={handleApply}
      on:close={handleClose}
    />
  </div>
{/if}
```

---

## 注意事项

⚠️ **图像大小**: 最大 10MB  
⚠️ **图像格式**: JPG、PNG、WebP  
⚠️ **处理时间**: 经典模式可能需要 10-30 秒  
⚠️ **网络连接**: 需要后端 CLIP 服务运行  

---

## 下一步

- 📖 查看 [完整文档](./CLIPInterrogatorPanel.README.md)
- 🧪 查看 [测试指南](./CLIPInterrogatorPanel.TEST.md)
- 💡 查看 [示例代码](./CLIPInterrogatorPanel.example.svelte)

---

**快速开始完成！** 🚀

现在你已经掌握了 CLIPInterrogatorPanel 组件的基本使用方法。
