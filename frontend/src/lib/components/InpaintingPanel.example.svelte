<script lang="ts">
  /**
   * InpaintingPanel 使用示例
   * 
   * 这个文件展示了如何在实际页面中使用InpaintingPanel组件
   */
  import InpaintingPanel from './InpaintingPanel.svelte';
  import ErrorHandler from './ErrorHandler.svelte';
  
  let showPanel = true;
</script>

<div class="min-h-screen bg-surface p-6">
  <div class="max-w-4xl mx-auto">
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-text-primary mb-2">
        Inpainting 工具
      </h1>
      <p class="text-text-secondary">
        使用AI技术局部重绘图像的指定区域
      </p>
    </div>
    
    <!-- 错误处理组件 -->
    <ErrorHandler />
    
    <!-- 控制按钮 -->
    <div class="mb-4">
      <button
        on:click={() => showPanel = !showPanel}
        class="px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg transition-colors"
      >
        {showPanel ? '隐藏' : '显示'} Inpainting面板
      </button>
    </div>
    
    <!-- Inpainting面板 -->
    {#if showPanel}
      <div class="card p-6 bg-surface-elevated border border-border rounded-xl shadow-lg">
        <InpaintingPanel />
      </div>
    {/if}
    
    <!-- 使用说明 -->
    <div class="mt-8 p-6 bg-surface-elevated border border-border rounded-xl">
      <h2 class="text-xl font-semibold text-text-primary mb-4">
        📖 使用说明
      </h2>
      
      <div class="space-y-4 text-text-secondary">
        <div>
          <h3 class="font-semibold text-text-primary mb-2">1. 上传图像</h3>
          <p>点击"选择图像"按钮，选择你想要编辑的图像文件。</p>
        </div>
        
        <div>
          <h3 class="font-semibold text-text-primary mb-2">2. 绘制蒙版</h3>
          <p>使用画笔工具在图像上绘制红色区域，标记需要重绘的部分。可以调整画笔大小和硬度。</p>
        </div>
        
        <div>
          <h3 class="font-semibold text-text-primary mb-2">3. 输入Prompt</h3>
          <p>在Prompt输入框中描述你想要在蒙版区域生成的内容。</p>
        </div>
        
        <div>
          <h3 class="font-semibold text-text-primary mb-2">4. 调整参数</h3>
          <p>根据需要调整重绘强度、引导强度和生成步数。</p>
        </div>
        
        <div>
          <h3 class="font-semibold text-text-primary mb-2">5. 开始生成</h3>
          <p>点击"开始重绘"按钮，等待AI生成结果。</p>
        </div>
      </div>
    </div>
    
    <!-- 技巧提示 -->
    <div class="mt-6 p-4 bg-primary/10 border border-primary/30 rounded-lg">
      <h3 class="font-semibold text-text-primary mb-2">💡 使用技巧</h3>
      <ul class="list-disc list-inside space-y-1 text-sm text-text-secondary">
        <li>使用较小的画笔可以更精确地绘制蒙版</li>
        <li>较高的画笔硬度会产生更清晰的边缘</li>
        <li>重绘强度越高，生成的内容与原图差异越大</li>
        <li>可以使用橡皮擦工具修正蒙版</li>
        <li>点击"清除"按钮可以重新绘制蒙版</li>
      </ul>
    </div>
  </div>
</div>

<style>
  :global(body) {
    background-color: var(--color-surface);
  }
</style>
