<script lang="ts">
  import CLIPInterrogatorPanel from './CLIPInterrogatorPanel.svelte';
  
  // 示例配置
  let showPanel1 = true;
  let showPanel2 = false;
  let showPanel3 = false;
  
  // 示例图像 URL
  let exampleImageUrl = '';
  
  // 事件处理
  function handleResult(event: CustomEvent) {
    console.log('反推结果:', event.detail);
    alert(`反推完成！\n\nPrompt: ${event.detail.prompt}\n\nNegative: ${event.detail.negative_prompt}`);
  }
  
  function handleApply(event: CustomEvent) {
    console.log('应用 Prompt:', event.detail);
    alert('Prompt 已应用到生成参数！');
  }
  
  function handleCopy(event: CustomEvent) {
    console.log('复制:', event.detail);
    alert(`已复制 ${event.detail.type === 'prompt' ? 'Prompt' : 'Negative Prompt'}`);
  }
  
  function handleClose() {
    console.log('关闭面板');
    showPanel2 = false;
  }
</script>

<div class="container mx-auto p-8 space-y-8">
  <div class="text-center mb-8">
    <h1 class="text-4xl font-bold mb-4">CLIPInterrogatorPanel 组件示例</h1>
    <p class="text-text-secondary">
      展示 CLIP Prompt 反推组件的各种使用方式
    </p>
  </div>
  
  <!-- 示例 1: 基础使用 -->
  <section class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-semibold">示例 1: 基础使用</h2>
      <button
        on:click={() => showPanel1 = !showPanel1}
        class="btn-secondary"
      >
        {showPanel1 ? '隐藏' : '显示'}
      </button>
    </div>
    
    {#if showPanel1}
      <div class="max-w-2xl mx-auto">
        <CLIPInterrogatorPanel />
      </div>
      
      <div class="bg-surface/50 p-4 rounded-xl border border-border">
        <h3 class="font-semibold mb-2">代码示例：</h3>
        <pre class="bg-black/20 p-4 rounded-lg overflow-x-auto"><code>{`<script>
  import CLIPInterrogatorPanel from '$lib/components/CLIPInterrogatorPanel.svelte';
</script>

<CLIPInterrogatorPanel />`}</code></pre>
      </div>
    {/if}
  </section>
  
  <!-- 示例 2: 带事件监听 -->
  <section class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-semibold">示例 2: 带事件监听</h2>
      <button
        on:click={() => showPanel2 = !showPanel2}
        class="btn-secondary"
      >
        {showPanel2 ? '隐藏' : '显示'}
      </button>
    </div>
    
    {#if showPanel2}
      <div class="max-w-2xl mx-auto">
        <CLIPInterrogatorPanel
          on:result={handleResult}
          on:apply={handleApply}
          on:copy={handleCopy}
          on:close={handleClose}
        />
      </div>
      
      <div class="bg-surface/50 p-4 rounded-xl border border-border">
        <h3 class="font-semibold mb-2">代码示例：</h3>
        <pre class="bg-black/20 p-4 rounded-lg overflow-x-auto"><code>{`<script>
  import CLIPInterrogatorPanel from '$lib/components/CLIPInterrogatorPanel.svelte';
  
  function handleResult(event) {
    console.log('反推结果:', event.detail);
  }
  
  function handleApply(event) {
    console.log('应用 Prompt:', event.detail);
  }
  
  function handleCopy(event) {
    console.log('复制:', event.detail);
  }
  
  function handleClose() {
    console.log('关闭面板');
  }
</script>

<CLIPInterrogatorPanel
  on:result={handleResult}
  on:apply={handleApply}
  on:copy={handleCopy}
  on:close={handleClose}
/>`}</code></pre>
      </div>
    {/if}
  </section>
  
  <!-- 示例 3: 带初始图像和自动应用 -->
  <section class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-semibold">示例 3: 带初始图像和自动应用</h2>
      <button
        on:click={() => showPanel3 = !showPanel3}
        class="btn-secondary"
      >
        {showPanel3 ? '隐藏' : '显示'}
      </button>
    </div>
    
    {#if showPanel3}
      <div class="max-w-2xl mx-auto space-y-4">
        <div class="bg-surface/50 p-4 rounded-xl border border-border">
          <label class="label">图像 URL（可选）</label>
          <input
            type="text"
            bind:value={exampleImageUrl}
            placeholder="输入图像 URL，例如: https://example.com/image.jpg"
            class="input"
          />
          <p class="text-xs text-text-tertiary mt-2">
            提示：可以使用任何公开的图像 URL，或者直接上传本地图像
          </p>
        </div>
        
        <CLIPInterrogatorPanel
          initialImageUrl={exampleImageUrl}
          autoApplyPrompt={true}
          showCloseButton={false}
        />
      </div>
      
      <div class="bg-surface/50 p-4 rounded-xl border border-border">
        <h3 class="font-semibold mb-2">代码示例：</h3>
        <pre class="bg-black/20 p-4 rounded-lg overflow-x-auto"><code>{`<script>
  import CLIPInterrogatorPanel from '$lib/components/CLIPInterrogatorPanel.svelte';
  
  let imageUrl = 'https://example.com/image.jpg';
</script>

<CLIPInterrogatorPanel
  initialImageUrl={imageUrl}
  autoApplyPrompt={true}
  showCloseButton={false}
/>`}</code></pre>
      </div>
    {/if}
  </section>
  
  <!-- 功能说明 -->
  <section class="space-y-4">
    <h2 class="text-2xl font-semibold">功能说明</h2>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- 反推模式 -->
      <div class="bg-surface/50 p-6 rounded-xl border border-border">
        <h3 class="font-semibold mb-3 flex items-center gap-2">
          <span>🎯</span>
          <span>反推模式</span>
        </h3>
        <ul class="space-y-2 text-sm">
          <li class="flex items-start gap-2">
            <span class="text-primary">⚡</span>
            <div>
              <strong>快速模式：</strong>使用 BLIP 快速生成描述，速度快但可能不够详细
            </div>
          </li>
          <li class="flex items-start gap-2">
            <span class="text-success">🎯</span>
            <div>
              <strong>经典模式：</strong>生成更详细准确的描述，处理时间较长
            </div>
          </li>
          <li class="flex items-start gap-2">
            <span class="text-danger">🚫</span>
            <div>
              <strong>负面模式：</strong>专门生成负面提示词，排除不想要的元素
            </div>
          </li>
        </ul>
      </div>
      
      <!-- 主要功能 -->
      <div class="bg-surface/50 p-6 rounded-xl border border-border">
        <h3 class="font-semibold mb-3 flex items-center gap-2">
          <span>✨</span>
          <span>主要功能</span>
        </h3>
        <ul class="space-y-2 text-sm">
          <li class="flex items-center gap-2">
            <span class="text-primary">✓</span>
            <span>图像上传和预览</span>
          </li>
          <li class="flex items-center gap-2">
            <span class="text-primary">✓</span>
            <span>多种反推模式选择</span>
          </li>
          <li class="flex items-center gap-2">
            <span class="text-primary">✓</span>
            <span>Prompt 和 Negative Prompt 生成</span>
          </li>
          <li class="flex items-center gap-2">
            <span class="text-primary">✓</span>
            <span>风格标签识别</span>
          </li>
          <li class="flex items-center gap-2">
            <span class="text-primary">✓</span>
            <span>一键应用到生成参数</span>
          </li>
          <li class="flex items-center gap-2">
            <span class="text-primary">✓</span>
            <span>复制功能</span>
          </li>
        </ul>
      </div>
      
      <!-- Props -->
      <div class="bg-surface/50 p-6 rounded-xl border border-border">
        <h3 class="font-semibold mb-3 flex items-center gap-2">
          <span>⚙️</span>
          <span>Props 配置</span>
        </h3>
        <ul class="space-y-2 text-sm">
          <li>
            <code class="bg-black/20 px-2 py-1 rounded">initialImageUrl</code>
            <span class="text-text-secondary ml-2">初始图像 URL</span>
          </li>
          <li>
            <code class="bg-black/20 px-2 py-1 rounded">showCloseButton</code>
            <span class="text-text-secondary ml-2">显示关闭按钮</span>
          </li>
          <li>
            <code class="bg-black/20 px-2 py-1 rounded">autoApplyPrompt</code>
            <span class="text-text-secondary ml-2">自动应用结果</span>
          </li>
        </ul>
      </div>
      
      <!-- Events -->
      <div class="bg-surface/50 p-6 rounded-xl border border-border">
        <h3 class="font-semibold mb-3 flex items-center gap-2">
          <span>📡</span>
          <span>事件系统</span>
        </h3>
        <ul class="space-y-2 text-sm">
          <li>
            <code class="bg-black/20 px-2 py-1 rounded">on:result</code>
            <span class="text-text-secondary ml-2">反推完成</span>
          </li>
          <li>
            <code class="bg-black/20 px-2 py-1 rounded">on:apply</code>
            <span class="text-text-secondary ml-2">应用 Prompt</span>
          </li>
          <li>
            <code class="bg-black/20 px-2 py-1 rounded">on:copy</code>
            <span class="text-text-secondary ml-2">复制文本</span>
          </li>
          <li>
            <code class="bg-black/20 px-2 py-1 rounded">on:close</code>
            <span class="text-text-secondary ml-2">关闭面板</span>
          </li>
        </ul>
      </div>
    </div>
  </section>
  
  <!-- 使用提示 -->
  <section class="bg-primary/10 border border-primary/30 p-6 rounded-xl">
    <h3 class="font-semibold mb-3 flex items-center gap-2">
      <span>💡</span>
      <span>使用提示</span>
    </h3>
    <ul class="space-y-2 text-sm">
      <li>• 上传的图像文件不能超过 10MB</li>
      <li>• 支持 JPG、PNG、WebP 等常见图像格式</li>
      <li>• 经典模式处理时间较长，请耐心等待</li>
      <li>• 可以通过事件系统自定义处理逻辑</li>
      <li>• 组件会自动更新 pipelineValues store</li>
    </ul>
  </section>
</div>

<style>
  code {
    font-family: 'Courier New', monospace;
    font-size: 0.875rem;
  }
  
  pre {
    font-family: 'Courier New', monospace;
    font-size: 0.875rem;
    line-height: 1.5;
  }
</style>
