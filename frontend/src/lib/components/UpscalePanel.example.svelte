<script lang="ts">
  /**
   * UpscalePanel 使用示例
   * 
   * 本文件展示了如何在不同场景下使用 UpscalePanel 组件
   */
  
  import UpscalePanel from './UpscalePanel.svelte';
  
  // 示例 1: 基本使用
  let showBasicExample = true;
  
  // 示例 2: 在模态框中使用
  let showModalExample = false;
  
  // 示例 3: 在标签页中使用
  let activeTab = 'upscale';
  
  // 示例 4: 与其他功能集成
  let showIntegratedExample = false;
</script>

<div class="examples-container">
  <h1 class="text-2xl font-bold mb-6">UpscalePanel 使用示例</h1>
  
  <!-- 示例导航 -->
  <div class="mb-8 flex gap-2">
    <button 
      on:click={() => showBasicExample = !showBasicExample}
      class="px-4 py-2 bg-primary text-white rounded-lg"
    >
      示例 1: 基本使用
    </button>
    <button 
      on:click={() => showModalExample = !showModalExample}
      class="px-4 py-2 bg-primary text-white rounded-lg"
    >
      示例 2: 模态框
    </button>
    <button 
      on:click={() => activeTab = 'upscale'}
      class="px-4 py-2 bg-primary text-white rounded-lg"
    >
      示例 3: 标签页
    </button>
    <button 
      on:click={() => showIntegratedExample = !showIntegratedExample}
      class="px-4 py-2 bg-primary text-white rounded-lg"
    >
      示例 4: 集成使用
    </button>
  </div>
  
  <!-- 示例 1: 基本使用 -->
  {#if showBasicExample}
    <section class="example-section">
      <h2 class="text-xl font-semibold mb-4">示例 1: 基本使用</h2>
      <p class="text-sm text-text-secondary mb-4">
        最简单的使用方式，直接在页面中嵌入组件。
      </p>
      
      <div class="card p-6">
        <UpscalePanel />
      </div>
      
      <details class="mt-4">
        <summary class="cursor-pointer text-primary font-medium">查看代码</summary>
        <pre class="mt-2 p-4 bg-surface-elevated rounded-lg overflow-x-auto"><code>{`<script>
  import UpscalePanel from '$lib/components/UpscalePanel.svelte';
</script>

<div class="card">
  <UpscalePanel />
</div>`}</code></pre>
      </details>
    </section>
  {/if}
  
  <!-- 示例 2: 在模态框中使用 -->
  {#if showModalExample}
    <section class="example-section">
      <h2 class="text-xl font-semibold mb-4">示例 2: 在模态框中使用</h2>
      <p class="text-sm text-text-secondary mb-4">
        将组件放在模态框中，提供更好的用户体验。
      </p>
      
      <button 
        on:click={() => showModalExample = true}
        class="px-4 py-2 bg-success text-white rounded-lg"
      >
        打开图像放大工具
      </button>
      
      <!-- 模态框 -->
      <div class="modal-overlay">
        <div class="modal-content">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-semibold">图像放大</h3>
            <button 
              on:click={() => showModalExample = false}
              class="text-2xl text-text-secondary hover:text-text-primary"
            >
              ×
            </button>
          </div>
          
          <UpscalePanel />
        </div>
      </div>
      
      <details class="mt-4">
        <summary class="cursor-pointer text-primary font-medium">查看代码</summary>
        <pre class="mt-2 p-4 bg-surface-elevated rounded-lg overflow-x-auto"><code>{`<script>
  import UpscalePanel from '$lib/components/UpscalePanel.svelte';
  let showModal = false;
</script>

<button on:click={() => showModal = true}>
  打开图像放大工具
</button>

{#if showModal}
  <div class="modal-overlay">
    <div class="modal-content">
      <div class="flex justify-between items-center mb-4">
        <h3>图像放大</h3>
        <button on:click={() => showModal = false}>×</button>
      </div>
      <UpscalePanel />
    </div>
  </div>
{/if}`}</code></pre>
      </details>
    </section>
  {/if}
  
  <!-- 示例 3: 在标签页中使用 -->
  <section class="example-section">
    <h2 class="text-xl font-semibold mb-4">示例 3: 在标签页中使用</h2>
    <p class="text-sm text-text-secondary mb-4">
      与其他图像处理功能放在同一个标签页界面中。
    </p>
    
    <div class="card p-6">
      <!-- 标签页导航 -->
      <div class="flex gap-2 mb-6 border-b border-border">
        <button 
          on:click={() => activeTab = 'upscale'}
          class="px-4 py-2 {activeTab === 'upscale' ? 'border-b-2 border-primary text-primary' : 'text-text-secondary'}"
        >
          图像放大
        </button>
        <button 
          on:click={() => activeTab = 'inpaint'}
          class="px-4 py-2 {activeTab === 'inpaint' ? 'border-b-2 border-primary text-primary' : 'text-text-secondary'}"
        >
          局部重绘
        </button>
        <button 
          on:click={() => activeTab = 'outpaint'}
          class="px-4 py-2 {activeTab === 'outpaint' ? 'border-b-2 border-primary text-primary' : 'text-text-secondary'}"
        >
          画布扩展
        </button>
      </div>
      
      <!-- 标签页内容 -->
      {#if activeTab === 'upscale'}
        <UpscalePanel />
      {:else if activeTab === 'inpaint'}
        <div class="text-center text-text-secondary py-8">
          局部重绘功能（示例）
        </div>
      {:else if activeTab === 'outpaint'}
        <div class="text-center text-text-secondary py-8">
          画布扩展功能（示例）
        </div>
      {/if}
    </div>
    
    <details class="mt-4">
      <summary class="cursor-pointer text-primary font-medium">查看代码</summary>
      <pre class="mt-2 p-4 bg-surface-elevated rounded-lg overflow-x-auto"><code>{`<script>
  import UpscalePanel from '$lib/components/UpscalePanel.svelte';
  let activeTab = 'upscale';
</script>

<div class="tabs">
  <button on:click={() => activeTab = 'upscale'}>
    图像放大
  </button>
  <button on:click={() => activeTab = 'inpaint'}>
    局部重绘
  </button>
  <button on:click={() => activeTab = 'outpaint'}>
    画布扩展
  </button>
</div>

{#if activeTab === 'upscale'}
  <UpscalePanel />
{:else if activeTab === 'inpaint'}
  <!-- InpaintingPanel -->
{:else if activeTab === 'outpaint'}
  <!-- OutpaintingPanel -->
{/if}`}</code></pre>
    </details>
  </section>
  
  <!-- 示例 4: 与其他功能集成 -->
  {#if showIntegratedExample}
    <section class="example-section">
      <h2 class="text-xl font-semibold mb-4">示例 4: 与其他功能集成</h2>
      <p class="text-sm text-text-secondary mb-4">
        在主页面中集成，与生成功能配合使用。
      </p>
      
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- 左侧：生成区域（示例） -->
        <div class="card p-6">
          <h3 class="text-lg font-semibold mb-4">图像生成</h3>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-2">Prompt</label>
              <textarea 
                class="w-full px-3 py-2 bg-surface-elevated border border-border rounded-lg"
                rows="3"
                placeholder="描述你想要生成的图像..."
              ></textarea>
            </div>
            
            <button class="w-full px-4 py-3 bg-primary text-white rounded-lg">
              生成图像
            </button>
            
            <div class="border border-border rounded-lg p-4 bg-surface-elevated">
              <p class="text-center text-text-secondary">生成结果将显示在这里</p>
            </div>
            
            <button class="w-full px-4 py-2 bg-success text-white rounded-lg">
              放大生成结果 →
            </button>
          </div>
        </div>
        
        <!-- 右侧：放大区域 -->
        <div class="card p-6">
          <UpscalePanel />
        </div>
      </div>
      
      <details class="mt-4">
        <summary class="cursor-pointer text-primary font-medium">查看代码</summary>
        <pre class="mt-2 p-4 bg-surface-elevated rounded-lg overflow-x-auto"><code>{`<script>
  import UpscalePanel from '$lib/components/UpscalePanel.svelte';
  
  let generatedImage = '';
  
  async function generateImage() {
    // 生成图像逻辑
    const response = await fetch('/api/generate', {
      method: 'POST',
      body: JSON.stringify({ prompt: '...' })
    });
    const data = await response.json();
    generatedImage = data.image;
  }
  
  function upscaleGenerated() {
    // 将生成的图像传递给 UpscalePanel
    // 可以通过事件或状态管理实现
  }
</script>

<div class="grid grid-cols-2 gap-6">
  <div class="card">
    <h3>图像生成</h3>
    <textarea bind:value={prompt}></textarea>
    <button on:click={generateImage}>生成图像</button>
    {#if generatedImage}
      <img src={generatedImage} alt="生成结果" />
      <button on:click={upscaleGenerated}>放大生成结果</button>
    {/if}
  </div>
  
  <div class="card">
    <UpscalePanel />
  </div>
</div>`}</code></pre>
      </details>
    </section>
  {/if}
  
  <!-- 使用技巧 -->
  <section class="example-section mt-8">
    <h2 class="text-xl font-semibold mb-4">💡 使用技巧</h2>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="card p-4">
        <h3 class="font-semibold mb-2">🎯 选择合适的算法</h3>
        <ul class="text-sm text-text-secondary space-y-1">
          <li>• <strong>Real-ESRGAN</strong>: 照片、艺术作品</li>
          <li>• <strong>Lanczos</strong>: 快速预览</li>
          <li>• <strong>Bicubic</strong>: 一般用途</li>
        </ul>
      </div>
      
      <div class="card p-4">
        <h3 class="font-semibold mb-2">📏 放大倍数建议</h3>
        <ul class="text-sm text-text-secondary space-y-1">
          <li>• <strong>2.0x</strong>: 最常用，效果好</li>
          <li>• <strong>3.0x-4.0x</strong>: 高倍放大，耗时长</li>
          <li>• <strong>1.0x-1.5x</strong>: 轻微放大，快速</li>
        </ul>
      </div>
      
      <div class="card p-4">
        <h3 class="font-semibold mb-2">⚡ 性能优化</h3>
        <ul class="text-sm text-text-secondary space-y-1">
          <li>• 原始图像不要太大（≤ 2048px）</li>
          <li>• 预览时使用 Lanczos</li>
          <li>• 最终输出使用 Real-ESRGAN</li>
        </ul>
      </div>
      
      <div class="card p-4">
        <h3 class="font-semibold mb-2">🔧 故障排除</h3>
        <ul class="text-sm text-text-secondary space-y-1">
          <li>• 检查后端服务是否运行</li>
          <li>• 确认 upscale_pipeline 已加载</li>
          <li>• 查看浏览器控制台错误</li>
        </ul>
      </div>
    </div>
  </section>
</div>

<style>
  .examples-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  .example-section {
    margin-bottom: 3rem;
  }
  
  .card {
    background: var(--surface, #1a1a1a);
    border: 1px solid var(--border, #333);
    border-radius: 0.5rem;
  }
  
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  
  .modal-content {
    background: var(--surface, #1a1a1a);
    border: 1px solid var(--border, #333);
    border-radius: 0.5rem;
    padding: 2rem;
    max-width: 600px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;
  }
  
  pre {
    font-size: 0.875rem;
    line-height: 1.5;
  }
  
  code {
    font-family: 'Courier New', monospace;
  }
</style>
