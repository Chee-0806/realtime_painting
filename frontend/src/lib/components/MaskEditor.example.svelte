<script lang="ts">
  import MaskEditor from './MaskEditor.svelte';
  
  let maskEditor: any;
  let sourceImage: string = '';
  let maskDataURL: string = '';
  let fileInput: HTMLInputElement;
  
  // 示例图像（1x1 透明像素）
  const placeholderImage = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';
  
  function handleFileSelect(event: Event) {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      sourceImage = e.target?.result as string;
    };
    reader.readAsDataURL(file);
  }
  
  function handleMaskChange(event: CustomEvent) {
    const { dataURL } = event.detail;
    maskDataURL = dataURL;
    console.log('蒙版已更新');
  }
  
  function getMask() {
    if (maskEditor) {
      const mask = maskEditor.getMaskDataURL();
      console.log('获取蒙版:', mask.substring(0, 50) + '...');
      alert('蒙版已获取，请查看控制台');
    }
  }
  
  function clearMask() {
    if (maskEditor) {
      maskEditor.clearMask();
    }
  }
  
  function invertMask() {
    if (maskEditor) {
      maskEditor.invertMaskData();
    }
  }
  
  function downloadMask() {
    if (!maskDataURL) {
      alert('请先绘制蒙版');
      return;
    }
    
    const link = document.createElement('a');
    link.href = maskDataURL;
    link.download = `mask_${Date.now()}.png`;
    link.click();
  }
</script>

<div class="max-w-4xl mx-auto p-6 space-y-6">
  <div class="text-center">
    <h1 class="text-3xl font-bold text-text-primary mb-2">
      MaskEditor 组件示例
    </h1>
    <p class="text-text-secondary">
      演示 MaskEditor 组件的各种功能
    </p>
  </div>
  
  <!-- 图像上传 -->
  <div class="card p-6 space-y-4">
    <h2 class="text-xl font-semibold text-text-primary">1. 上传源图像</h2>
    <input
      type="file"
      bind:this={fileInput}
      on:change={handleFileSelect}
      accept="image/*"
      class="hidden"
    />
    <button
      on:click={() => fileInput.click()}
      class="w-full px-4 py-3 bg-primary hover:bg-primary/90 text-white rounded-lg transition-colors font-medium"
    >
      {sourceImage ? '更换图像' : '选择图像'}
    </button>
    
    {#if !sourceImage}
      <p class="text-sm text-text-secondary text-center">
        💡 或者使用占位图像进行测试
      </p>
      <button
        on:click={() => sourceImage = placeholderImage}
        class="w-full px-4 py-2 bg-surface hover:bg-surface/80 text-text-secondary rounded-lg transition-colors"
      >
        使用占位图像
      </button>
    {/if}
  </div>
  
  <!-- MaskEditor 组件 -->
  {#if sourceImage}
    <div class="card p-6 space-y-4">
      <h2 class="text-xl font-semibold text-text-primary">2. 绘制蒙版</h2>
      
      <MaskEditor
        bind:this={maskEditor}
        width={512}
        height={512}
        sourceImage={sourceImage}
        on:change={handleMaskChange}
      />
    </div>
    
    <!-- 操作按钮 -->
    <div class="card p-6 space-y-4">
      <h2 class="text-xl font-semibold text-text-primary">3. 操作</h2>
      
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <button
          on:click={getMask}
          class="px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg transition-colors font-medium"
        >
          获取蒙版
        </button>
        
        <button
          on:click={clearMask}
          class="px-4 py-2 bg-danger/10 hover:bg-danger/20 text-danger rounded-lg transition-colors font-medium"
        >
          清除蒙版
        </button>
        
        <button
          on:click={invertMask}
          class="px-4 py-2 bg-surface hover:bg-surface/80 text-text-secondary rounded-lg transition-colors font-medium"
        >
          反转蒙版
        </button>
        
        <button
          on:click={downloadMask}
          class="px-4 py-2 bg-success hover:bg-success/90 text-white rounded-lg transition-colors font-medium"
        >
          下载蒙版
        </button>
      </div>
    </div>
    
    <!-- 蒙版预览 -->
    {#if maskDataURL}
      <div class="card p-6 space-y-4">
        <h2 class="text-xl font-semibold text-text-primary">4. 蒙版预览</h2>
        <div class="border border-border rounded-lg overflow-hidden bg-surface-elevated">
          <img 
            src={maskDataURL} 
            alt="蒙版预览" 
            class="w-full h-auto"
          />
        </div>
        <p class="text-sm text-text-secondary">
          白色区域表示将被处理的部分
        </p>
      </div>
    {/if}
  {/if}
  
  <!-- 使用说明 -->
  <div class="card p-6 space-y-4">
    <h2 class="text-xl font-semibold text-text-primary">使用说明</h2>
    
    <div class="space-y-3 text-sm text-text-secondary">
      <div class="flex items-start gap-2">
        <span class="text-primary font-bold">1.</span>
        <p>上传一张图像或使用占位图像</p>
      </div>
      
      <div class="flex items-start gap-2">
        <span class="text-primary font-bold">2.</span>
        <p>使用画笔工具在图像上绘制需要处理的区域（白色）</p>
      </div>
      
      <div class="flex items-start gap-2">
        <span class="text-primary font-bold">3.</span>
        <p>使用橡皮擦工具擦除不需要的部分</p>
      </div>
      
      <div class="flex items-start gap-2">
        <span class="text-primary font-bold">4.</span>
        <p>使用填充工具快速填充大面积区域</p>
      </div>
      
      <div class="flex items-start gap-2">
        <span class="text-primary font-bold">5.</span>
        <p>点击"显示预览"可以叠加显示源图像和蒙版</p>
      </div>
      
      <div class="flex items-start gap-2">
        <span class="text-primary font-bold">6.</span>
        <p>使用"反转"功能可以快速创建反向蒙版</p>
      </div>
    </div>
    
    <div class="mt-4 p-4 bg-surface-elevated border border-border rounded-lg">
      <h3 class="font-semibold text-text-primary mb-2">键盘快捷键</h3>
      <div class="grid grid-cols-2 gap-2 text-xs text-text-secondary">
        <div><kbd class="px-2 py-1 bg-surface rounded">B</kbd> 画笔工具</div>
        <div><kbd class="px-2 py-1 bg-surface rounded">E</kbd> 橡皮擦工具</div>
        <div><kbd class="px-2 py-1 bg-surface rounded">F</kbd> 填充工具</div>
        <div><kbd class="px-2 py-1 bg-surface rounded">C</kbd> 清除蒙版</div>
        <div><kbd class="px-2 py-1 bg-surface rounded">I</kbd> 反转蒙版</div>
        <div><kbd class="px-2 py-1 bg-surface rounded">[</kbd> 减小画笔</div>
        <div><kbd class="px-2 py-1 bg-surface rounded">]</kbd> 增大画笔</div>
      </div>
    </div>
  </div>
  
  <!-- API 示例 -->
  <div class="card p-6 space-y-4">
    <h2 class="text-xl font-semibold text-text-primary">API 使用示例</h2>
    
    <div class="space-y-3">
      <div class="p-4 bg-surface-elevated border border-border rounded-lg">
        <h3 class="font-semibold text-text-primary mb-2 text-sm">获取蒙版 Data URL</h3>
        <pre class="text-xs text-text-secondary overflow-x-auto"><code>const maskDataURL = maskEditor.getMaskDataURL();</code></pre>
      </div>
      
      <div class="p-4 bg-surface-elevated border border-border rounded-lg">
        <h3 class="font-semibold text-text-primary mb-2 text-sm">获取蒙版 ImageData</h3>
        <pre class="text-xs text-text-secondary overflow-x-auto"><code>const imageData = maskEditor.getMaskImageData();</code></pre>
      </div>
      
      <div class="p-4 bg-surface-elevated border border-border rounded-lg">
        <h3 class="font-semibold text-text-primary mb-2 text-sm">清除蒙版</h3>
        <pre class="text-xs text-text-secondary overflow-x-auto"><code>maskEditor.clearMask();</code></pre>
      </div>
      
      <div class="p-4 bg-surface-elevated border border-border rounded-lg">
        <h3 class="font-semibold text-text-primary mb-2 text-sm">反转蒙版</h3>
        <pre class="text-xs text-text-secondary overflow-x-auto"><code>maskEditor.invertMaskData();</code></pre>
      </div>
      
      <div class="p-4 bg-surface-elevated border border-border rounded-lg">
        <h3 class="font-semibold text-text-primary mb-2 text-sm">从 Data URL 加载蒙版</h3>
        <pre class="text-xs text-text-secondary overflow-x-auto"><code>maskEditor.setMaskFromDataURL(dataURL);</code></pre>
      </div>
      
      <div class="p-4 bg-surface-elevated border border-border rounded-lg">
        <h3 class="font-semibold text-text-primary mb-2 text-sm">监听蒙版变化</h3>
        <pre class="text-xs text-text-secondary overflow-x-auto"><code>&lt;MaskEditor on:change={'{'}handleChange{'}'} /&gt;

function handleChange(event) {'{'}
  const {'{'} dataURL, imageData {'}'} = event.detail;
  console.log('蒙版已更新');
{'}'}</code></pre>
      </div>
    </div>
  </div>
</div>

<style>
  kbd {
    font-family: monospace;
  }
</style>
