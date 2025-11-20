<script lang="ts">
  import { onMount } from 'svelte';
  import { setError, clearError, ErrorType } from '$lib/store';
  
  // 组件状态
  let sourceImage: string = '';
  let sourceImageElement: HTMLImageElement | null = null;
  
  // Canvas引用
  let previewCanvas: HTMLCanvasElement;
  let previewCtx: CanvasRenderingContext2D | null = null;
  
  // 扩展配置
  type Direction = 'left' | 'right' | 'top' | 'bottom' | 'all';
  let direction: Direction = 'all';
  let pixels: number = 128;
  
  // 参数配置
  let prompt: string = '';
  let negativePrompt: string = '';
  let guidanceScale: number = 7.5;
  let steps: number = 20;
  
  // UI状态
  let loading: boolean = false;
  let resultImage: string = '';
  let showResult: boolean = false;
  
  // 文件上传处理
  let fileInput: HTMLInputElement;
  
  onMount(() => {
    if (previewCanvas) {
      previewCtx = previewCanvas.getContext('2d');
    }
  });
  
  function handleFileSelect(event: Event) {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    
    if (!file) return;
    
    if (!file.type.startsWith('image/')) {
      setError({
        type: ErrorType.VALIDATION,
        message: '请选择图像文件',
        details: '只支持图像格式（PNG, JPG, WebP等）',
        recoverable: true,
        suggestions: ['选择一个有效的图像文件']
      });
      return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      sourceImage = result;
      loadImageToCanvas(result);
      clearError();
    };
    reader.onerror = () => {
      setError({
        type: ErrorType.VALIDATION,
        message: '图像加载失败',
        details: '无法读取选择的文件',
        recoverable: true,
        suggestions: ['尝试选择其他图像文件']
      });
    };
    reader.readAsDataURL(file);
  }
  
  function loadImageToCanvas(imageSrc: string) {
    const img = new Image();
    img.onload = () => {
      sourceImageElement = img;
      updatePreview();
    };
    img.onerror = () => {
      setError({
        type: ErrorType.VALIDATION,
        message: '图像加载失败',
        details: '无法加载图像到画布',
        recoverable: true
      });
    };
    img.src = imageSrc;
  }
  
  function updatePreview() {
    if (!sourceImageElement || !previewCtx) return;
    
    const img = sourceImageElement;
    
    // 计算预览尺寸（保持宽高比，最大512px）
    const maxSize = 512;
    let width = img.width;
    let height = img.height;
    
    if (width > maxSize || height > maxSize) {
      const ratio = Math.min(maxSize / width, maxSize / height);
      width = width * ratio;
      height = height * ratio;
    }
    
    // 根据扩展方向计算新的画布尺寸
    let canvasWidth = width;
    let canvasHeight = height;
    let offsetX = 0;
    let offsetY = 0;
    
    const scaledPixels = pixels * (width / img.width); // 按比例缩放扩展像素
    
    if (direction === 'left' || direction === 'all') {
      canvasWidth += scaledPixels;
      offsetX = scaledPixels;
    }
    if (direction === 'right' || direction === 'all') {
      canvasWidth += scaledPixels;
    }
    if (direction === 'top' || direction === 'all') {
      canvasHeight += scaledPixels;
      offsetY = scaledPixels;
    }
    if (direction === 'bottom' || direction === 'all') {
      canvasHeight += scaledPixels;
    }
    
    // 设置画布尺寸
    previewCanvas.width = canvasWidth;
    previewCanvas.height = canvasHeight;
    
    // 清空画布
    previewCtx.fillStyle = '#e5e7eb';
    previewCtx.fillRect(0, 0, canvasWidth, canvasHeight);
    
    // 绘制原始图像
    previewCtx.drawImage(img, offsetX, offsetY, width, height);
    
    // 绘制扩展区域边框
    previewCtx.strokeStyle = '#3b82f6';
    previewCtx.lineWidth = 2;
    previewCtx.setLineDash([5, 5]);
    
    if (direction === 'left' || direction === 'all') {
      previewCtx.strokeRect(0, offsetY, scaledPixels, height);
    }
    if (direction === 'right' || direction === 'all') {
      previewCtx.strokeRect(offsetX + width, offsetY, scaledPixels, height);
    }
    if (direction === 'top' || direction === 'all') {
      previewCtx.strokeRect(offsetX, 0, width, scaledPixels);
    }
    if (direction === 'bottom' || direction === 'all') {
      previewCtx.strokeRect(offsetX, offsetY + height, width, scaledPixels);
    }
    
    previewCtx.setLineDash([]);
  }
  
  // 当方向或像素数改变时更新预览
  $: if (sourceImageElement && (direction || pixels)) {
    updatePreview();
  }
  
  async function performOutpainting() {
    if (!sourceImage) {
      setError({
        type: ErrorType.VALIDATION,
        message: '请先上传图像',
        recoverable: true,
        suggestions: ['点击"选择图像"按钮上传图像']
      });
      return;
    }
    
    if (!prompt.trim()) {
      setError({
        type: ErrorType.VALIDATION,
        message: '请输入Prompt',
        recoverable: true,
        suggestions: ['在Prompt输入框中描述你想要在扩展区域生成的内容']
      });
      return;
    }
    
    loading = true;
    clearError();
    
    try {
      const response = await fetch('/api/outpaint', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image: sourceImage,
          direction: direction,
          extend_pixels: pixels,  // 后端使用extend_pixels参数名
          prompt: prompt,
          negative_prompt: negativePrompt,
          guidance_scale: guidanceScale,
          num_inference_steps: steps
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP错误: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        resultImage = data.image;
        showResult = true;
      } else {
        setError({
          type: ErrorType.GENERATION,
          message: 'Outpainting失败',
          details: data.message || '未知错误',
          recoverable: true,
          suggestions: [
            '检查Prompt是否合适',
            '尝试调整扩展尺寸',
            '尝试不同的扩展方向'
          ]
        });
      }
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
      console.error('Outpainting失败:', e);
    } finally {
      loading = false;
    }
  }
  
  function downloadResult() {
    if (!resultImage) return;
    
    const link = document.createElement('a');
    link.href = resultImage;
    link.download = `outpaint_result_${Date.now()}.png`;
    link.click();
  }
  
  function reset() {
    sourceImage = '';
    resultImage = '';
    showResult = false;
    prompt = '';
    negativePrompt = '';
    direction = 'all';
    pixels = 128;
    clearError();
  }
</script>

<div class="space-y-4">
  <div class="flex items-center justify-between mb-4">
    <h3 class="text-lg font-semibold text-text-primary">🖼️ 画布扩展 (Outpainting)</h3>
    <button 
      on:click={reset}
      class="px-3 py-1 text-sm bg-surface-elevated hover:bg-surface-elevated/80 border border-border rounded-lg text-text-secondary transition-colors"
    >
      重置
    </button>
  </div>
  
  <!-- 图像上传 -->
  <div class="space-y-2">
    <label for="outpaint-image-upload" class="block text-sm font-medium text-text-primary">
      源图像
    </label>
    <input
      id="outpaint-image-upload"
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
  </div>
  
  {#if sourceImage}
    <!-- 预览区域 -->
    <div class="space-y-3">
      <div class="border border-border rounded-lg overflow-hidden bg-surface-elevated p-4">
        <canvas
          bind:this={previewCanvas}
          class="w-full h-auto mx-auto"
          style="max-width: 100%; image-rendering: pixelated;"
        ></canvas>
      </div>
      
      <p class="text-xs text-text-secondary">
        💡 蓝色虚线区域表示将要扩展的部分
      </p>
    </div>
    
    <!-- 扩展方向选择 -->
    <div class="space-y-3 p-4 bg-surface-elevated border border-border rounded-lg">
      <label class="block text-sm font-medium text-text-primary">扩展方向</label>
      
      <div class="grid grid-cols-5 gap-2">
        <button
          on:click={() => direction = 'left'}
          class="px-3 py-2 rounded-lg font-medium transition-colors {direction === 'left' ? 'bg-primary text-white' : 'bg-surface hover:bg-surface/80 text-text-secondary'}"
          title="向左扩展"
        >
          ← 左
        </button>
        <button
          on:click={() => direction = 'right'}
          class="px-3 py-2 rounded-lg font-medium transition-colors {direction === 'right' ? 'bg-primary text-white' : 'bg-surface hover:bg-surface/80 text-text-secondary'}"
          title="向右扩展"
        >
          右 →
        </button>
        <button
          on:click={() => direction = 'top'}
          class="px-3 py-2 rounded-lg font-medium transition-colors {direction === 'top' ? 'bg-primary text-white' : 'bg-surface hover:bg-surface/80 text-text-secondary'}"
          title="向上扩展"
        >
          ↑ 上
        </button>
        <button
          on:click={() => direction = 'bottom'}
          class="px-3 py-2 rounded-lg font-medium transition-colors {direction === 'bottom' ? 'bg-primary text-white' : 'bg-surface hover:bg-surface/80 text-text-secondary'}"
          title="向下扩展"
        >
          下 ↓
        </button>
        <button
          on:click={() => direction = 'all'}
          class="px-3 py-2 rounded-lg font-medium transition-colors {direction === 'all' ? 'bg-primary text-white' : 'bg-surface hover:bg-surface/80 text-text-secondary'}"
          title="全方向扩展"
        >
          ⊕ 全部
        </button>
      </div>
    </div>
    
    <!-- 扩展尺寸 -->
    <div class="space-y-2">
      <div class="flex justify-between items-center">
        <label for="pixels-slider" class="text-sm font-medium text-text-primary">扩展尺寸</label>
        <span class="text-sm text-text-secondary">{pixels}px</span>
      </div>
      <input
        id="pixels-slider"
        type="range"
        bind:value={pixels}
        min="64"
        max="512"
        step="64"
        class="w-full"
      />
      <p class="text-xs text-text-secondary">
        建议使用64的倍数以获得更好的效果
      </p>
    </div>
    
    <!-- Prompt输入 -->
    <div class="space-y-2">
      <label for="outpaint-prompt-input" class="block text-sm font-medium text-text-primary">
        Prompt
      </label>
      <textarea
        id="outpaint-prompt-input"
        bind:value={prompt}
        rows="3"
        class="w-full px-3 py-2 bg-surface-elevated border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary resize-none"
        placeholder="描述你想要在扩展区域生成的内容..."
      ></textarea>
    </div>
    
    <!-- Negative Prompt -->
    <div class="space-y-2">
      <label for="outpaint-negative-prompt-input" class="block text-sm font-medium text-text-primary">
        Negative Prompt
      </label>
      <textarea
        id="outpaint-negative-prompt-input"
        bind:value={negativePrompt}
        rows="2"
        class="w-full px-3 py-2 bg-surface-elevated border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary resize-none"
        placeholder="描述你不想要的内容..."
      ></textarea>
    </div>
    
    <!-- 参数配置 -->
    <div class="space-y-3 p-4 bg-surface-elevated border border-border rounded-lg">
      <h4 class="text-sm font-semibold text-text-primary">参数配置</h4>
      
      <!-- 引导强度 -->
      <div class="space-y-2">
        <div class="flex justify-between items-center">
          <label for="outpaint-guidance-slider" class="text-sm font-medium text-text-primary">引导强度</label>
          <span class="text-sm text-text-secondary">{guidanceScale.toFixed(1)}</span>
        </div>
        <input
          id="outpaint-guidance-slider"
          type="range"
          bind:value={guidanceScale}
          min="1.0"
          max="20.0"
          step="0.5"
          class="w-full"
        />
      </div>
      
      <!-- 生成步数 -->
      <div class="space-y-2">
        <div class="flex justify-between items-center">
          <label for="outpaint-steps-slider" class="text-sm font-medium text-text-primary">生成步数</label>
          <span class="text-sm text-text-secondary">{steps}</span>
        </div>
        <input
          id="outpaint-steps-slider"
          type="range"
          bind:value={steps}
          min="10"
          max="50"
          step="5"
          class="w-full"
        />
      </div>
    </div>
    
    <!-- 操作按钮 -->
    <div class="flex gap-3">
      <button
        on:click={performOutpainting}
        disabled={loading || !prompt.trim()}
        class="flex-1 px-4 py-3 bg-success hover:bg-success/90 disabled:bg-surface-elevated disabled:text-text-secondary text-white rounded-lg transition-colors font-medium disabled:cursor-not-allowed"
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
    </div>
  {/if}
  
  <!-- 结果显示 -->
  {#if showResult && resultImage}
    <div class="space-y-3 p-4 bg-surface-elevated border border-success/30 rounded-lg">
      <div class="flex items-center justify-between">
        <h4 class="text-sm font-semibold text-text-primary">✨ 生成结果</h4>
        <button
          on:click={downloadResult}
          class="px-3 py-1 text-sm bg-primary hover:bg-primary/90 text-white rounded-lg transition-colors"
        >
          下载
        </button>
      </div>
      <img 
        src={resultImage} 
        alt="Outpainting结果" 
        class="w-full h-auto rounded-lg border border-border"
      />
    </div>
  {/if}
</div>

<style>
  canvas {
    image-rendering: pixelated;
    image-rendering: -moz-crisp-edges;
    image-rendering: crisp-edges;
  }
</style>
