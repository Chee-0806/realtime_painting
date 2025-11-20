<script lang="ts">
  import OutpaintingPanel from './OutpaintingPanel.svelte';
  
  // 示例：在主页面中使用 OutpaintingPanel
  let showPanel = false;
</script>

<div class="container mx-auto p-6 space-y-6">
  <div class="text-center">
    <h1 class="text-3xl font-bold text-text-primary mb-4">
      OutpaintingPanel 使用示例
    </h1>
    <p class="text-text-secondary mb-6">
      演示如何在应用中集成和使用 Outpainting 组件
    </p>
  </div>
  
  <!-- 切换按钮 -->
  <div class="flex justify-center">
    <button
      on:click={() => showPanel = !showPanel}
      class="px-6 py-3 bg-primary hover:bg-primary/90 text-white rounded-lg font-medium transition-colors"
    >
      {showPanel ? '隐藏' : '显示'} Outpainting 面板
    </button>
  </div>
  
  <!-- Outpainting 面板 -->
  {#if showPanel}
    <div class="max-w-2xl mx-auto">
      <div class="card p-6 bg-surface border border-border rounded-xl shadow-lg">
        <OutpaintingPanel />
      </div>
    </div>
  {/if}
  
  <!-- 使用说明 -->
  <div class="max-w-4xl mx-auto mt-12">
    <div class="card p-6 bg-surface-elevated border border-border rounded-xl">
      <h2 class="text-xl font-semibold text-text-primary mb-4">📖 使用说明</h2>
      
      <div class="space-y-4 text-text-secondary">
        <div>
          <h3 class="font-semibold text-text-primary mb-2">1️⃣ 上传图像</h3>
          <p>点击"选择图像"按钮，上传你想要扩展的图像。支持 PNG、JPG、WebP 等常见格式。</p>
        </div>
        
        <div>
          <h3 class="font-semibold text-text-primary mb-2">2️⃣ 选择扩展方向</h3>
          <p>选择你想要扩展的方向：</p>
          <ul class="list-disc list-inside ml-4 mt-2">
            <li><strong>← 左</strong>: 向左侧扩展画布</li>
            <li><strong>→ 右</strong>: 向右侧扩展画布</li>
            <li><strong>↑ 上</strong>: 向上方扩展画布</li>
            <li><strong>↓ 下</strong>: 向下方扩展画布</li>
            <li><strong>⊕ 全部</strong>: 向所有方向扩展画布</li>
          </ul>
        </div>
        
        <div>
          <h3 class="font-semibold text-text-primary mb-2">3️⃣ 调整扩展尺寸</h3>
          <p>使用滑块调整扩展的像素数（64-512px）。建议使用64的倍数以获得更好的效果。</p>
        </div>
        
        <div>
          <h3 class="font-semibold text-text-primary mb-2">4️⃣ 输入 Prompt</h3>
          <p>描述你想要在扩展区域生成的内容。例如：</p>
          <ul class="list-disc list-inside ml-4 mt-2">
            <li>"beautiful mountain landscape, blue sky, clouds"</li>
            <li>"ocean waves, sandy beach, sunset"</li>
            <li>"forest trees, green grass, natural lighting"</li>
          </ul>
        </div>
        
        <div>
          <h3 class="font-semibold text-text-primary mb-2">5️⃣ 配置参数（可选）</h3>
          <p>调整生成参数以获得更好的效果：</p>
          <ul class="list-disc list-inside ml-4 mt-2">
            <li><strong>引导强度</strong>: 控制生成内容与 Prompt 的匹配度（推荐 7.5）</li>
            <li><strong>生成步数</strong>: 更多步数通常产生更好的质量（推荐 20-30）</li>
          </ul>
        </div>
        
        <div>
          <h3 class="font-semibold text-text-primary mb-2">6️⃣ 开始扩展</h3>
          <p>点击"开始扩展"按钮，等待 AI 生成扩展内容。生成完成后可以下载结果。</p>
        </div>
      </div>
    </div>
  </div>
  
  <!-- 技巧和提示 -->
  <div class="max-w-4xl mx-auto">
    <div class="card p-6 bg-surface-elevated border border-border rounded-xl">
      <h2 class="text-xl font-semibold text-text-primary mb-4">💡 技巧和提示</h2>
      
      <div class="space-y-3 text-text-secondary">
        <div class="flex items-start gap-3">
          <span class="text-2xl">🎨</span>
          <div>
            <strong class="text-text-primary">保持风格一致</strong>
            <p>在 Prompt 中描述与原图相似的风格和元素，以获得更自然的扩展效果。</p>
          </div>
        </div>
        
        <div class="flex items-start gap-3">
          <span class="text-2xl">📏</span>
          <div>
            <strong class="text-text-primary">合理的扩展尺寸</strong>
            <p>不要一次扩展太多。建议每次扩展 128-256px，需要更大的画布时可以多次扩展。</p>
          </div>
        </div>
        
        <div class="flex items-start gap-3">
          <span class="text-2xl">🔄</span>
          <div>
            <strong class="text-text-primary">多次尝试</strong>
            <p>如果第一次结果不理想，可以调整 Prompt 或参数后重新生成。</p>
          </div>
        </div>
        
        <div class="flex items-start gap-3">
          <span class="text-2xl">⚡</span>
          <div>
            <strong class="text-text-primary">使用 Negative Prompt</strong>
            <p>添加不想要的元素到 Negative Prompt 中，如 "blurry, low quality, distorted"。</p>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <!-- 常见问题 -->
  <div class="max-w-4xl mx-auto">
    <div class="card p-6 bg-surface-elevated border border-border rounded-xl">
      <h2 class="text-xl font-semibold text-text-primary mb-4">❓ 常见问题</h2>
      
      <div class="space-y-4">
        <div>
          <h3 class="font-semibold text-text-primary mb-2">Q: 扩展区域与原图不协调怎么办？</h3>
          <p class="text-text-secondary">
            A: 尝试在 Prompt 中更详细地描述原图的风格、颜色和元素。也可以降低引导强度让生成更自然。
          </p>
        </div>
        
        <div>
          <h3 class="font-semibold text-text-primary mb-2">Q: 可以同时向多个方向扩展吗？</h3>
          <p class="text-text-secondary">
            A: 可以选择"全部"选项同时向四个方向扩展。但建议先单方向扩展，效果更可控。
          </p>
        </div>
        
        <div>
          <h3 class="font-semibold text-text-primary mb-2">Q: 生成速度慢怎么办？</h3>
          <p class="text-text-secondary">
            A: 可以减少生成步数（如设置为 15-20），或者减小扩展尺寸。这会加快生成速度。
          </p>
        </div>
        
        <div>
          <h3 class="font-semibold text-text-primary mb-2">Q: 支持哪些图像格式？</h3>
          <p class="text-text-secondary">
            A: 支持所有常见的图像格式，包括 PNG、JPG、JPEG、WebP、GIF 等。
          </p>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .card {
    background: var(--surface);
  }
</style>
