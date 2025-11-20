<script lang="ts">
  import { onMount } from 'svelte';
  import { setError, clearError, ErrorType } from '$lib/store';
  
  // 组件状态
  let sourceImage: string = '';
  let maskImage: string = '';
  let sourceImageElement: HTMLImageElement | null = null;
  
  // Canvas引用
  let sourceCanvas: HTMLCanvasElement;
  let maskCanvas: HTMLCanvasElement;
  let sourceCtx: CanvasRenderingContext2D | null = null;
  let maskCtx: CanvasRenderingContext2D | null = null;
  
  // 画笔工具状态
  let brushSize: number = 30;
  let brushHardness: number = 0.8;
  let isDrawing: boolean = false;
  let tool: 'brush' | 'eraser' = 'brush';
  
  // 参数配置
  let prompt: string = '';
  let negativePrompt: string = '';
  let strength: number = 0.6;
  let guidanceScale: number = 7.5;
  let steps: number = 20;
  
  // UI状态
  let loading: boolean = false;
  let resultImage: string = '';
  let showResult: boolean = false;
  
  // 文件上传处理
  let fileInput: HTMLInputElement;
  
  onMount(() => {
    if (sourceCanvas && maskCanvas) {
      sourceCtx = sourceCanvas.getContext('2d');
      maskCtx = maskCanvas.getContext('2d');
      
      // 初始化蒙版画布为透明
      if (maskCtx) {
        maskCtx.fillStyle = 'rgba(0, 0, 0, 0)';
        maskCtx.fillRect(0, 0, maskCanvas.width, maskCanvas.height);
      }
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
      
      // 调整canvas大小以匹配图像
      const maxWidth = 512;
      const maxHeight = 512;
      let width = img.width;
      let height = img.height;
      
      // 保持宽高比缩放
      if (width > maxWidth || height > maxHeight) {
        const ratio = Math.min(maxWidth / width, maxHeight / height);
        width = width * ratio;
        height = height * ratio;
      }
      
      sourceCanvas.width = width;
      sourceCanvas.height = height;
      maskCanvas.width = width;
      maskCanvas.height = height;
      
      // 绘制源图像
      if (sourceCtx) {
        sourceCtx.drawImage(img, 0, 0, width, height);
      }
      
      // 清空蒙版
      clearMask();
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
  
  function startDrawing(event: MouseEvent) {
    isDrawing = true;
    draw(event);
  }
  
  function stopDrawing() {
    isDrawing = false;
  }
  
  function draw(event: MouseEvent) {
    if (!isDrawing || !maskCtx) return;
    
    const rect = maskCanvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    maskCtx.beginPath();
    maskCtx.arc(x, y, brushSize / 2, 0, Math.PI * 2);
    
    if (tool === 'brush') {
      // 绘制白色蒙版（表示要重绘的区域）
      const gradient = maskCtx.createRadialGradient(x, y, 0, x, y, brushSize / 2);
      gradient.addColorStop(0, `rgba(255, 255, 255, ${brushHardness})`);
      gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
      maskCtx.fillStyle = gradient;
    } else {
      // 橡皮擦：绘制透明
      maskCtx.globalCompositeOperation = 'destination-out';
      maskCtx.fillStyle = 'rgba(255, 255, 255, 1)';
    }
    
    maskCtx.fill();
    
    // 重置混合模式
    if (tool === 'eraser') {
      maskCtx.globalCompositeOperation = 'source-over';
    }
  }
  
  function clearMask() {
    if (!maskCtx) return;
    
    maskCtx.clearRect(0, 0, maskCanvas.width, maskCanvas.height);
    maskCtx.fillStyle = 'rgba(0, 0, 0, 0)';
    maskCtx.fillRect(0, 0, maskCanvas.width, maskCanvas.height);
  }
  
  function getMaskDataURL(): string {
    return maskCanvas.toDataURL('image/png');
  }
  
  async function performInpainting() {
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
        suggestions: ['在Prompt输入框中描述你想要生成的内容']
      });
      return;
    }
    
    loading = true;
    clearError();
    
    try {
      const maskDataURL = getMaskDataURL();
      
      const response = await fetch('/api/inpaint', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image: sourceImage,
          mask: maskDataURL,
          prompt: prompt,
          negative_prompt: negativePrompt,
          strength: strength,
          guidance_scale: guidanceScale,
          num_inference_steps: steps  // 后端期望 num_inference_steps
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
          message: 'Inpainting失败',
          details: data.message || '未知错误',
          recoverable: true,
          suggestions: [
            '检查Prompt是否合适',
            '尝试调整参数',
            '确保蒙版区域正确'
          ]
        });
      }
    } catch (e) {
      setError({
        type: ErrorType.API,
        message: 'Inpainting请求失败',
        details: e instanceof Error ? e.message : String(e),
        recoverable: true,
        suggestions: [
          '检查网络连接',
          '确认后端服务正常运行',
          '查看浏览器控制台获取更多信息'
        ]
      });
      console.error('Inpainting失败:', e);
    } finally {
      loading = false;
    }
  }
  
  function downloadResult() {
    if (!resultImage) return;
    
    const link = document.createElement('a');
    link.href = resultImage;
    link.download = `inpaint_result_${Date.now()}.png`;
    link.click();
  }
  
  function reset() {
    sourceImage = '';
    maskImage = '';
    resultImage = '';
    showResult = false;
    prompt = '';
    negativePrompt = '';
    clearMask();
    clearError();
  }
</script>

<div class="space-y-4">
  <div class="flex items-center justify-between mb-4">
    <h3 class="text-lg font-semibold text-text-primary">🎨 局部重绘 (Inpainting)</h3>
    <button 
      on:click={reset}
      class="px-3 py-1 text-sm bg-surface-elevated hover:bg-surface-elevated/80 border border-border rounded-lg text-text-secondary transition-colors"
    >
      重置
    </button>
  </div>
  
  <!-- 图像上传 -->
  <div class="space-y-2">
    <label for="image-upload" class="block text-sm font-medium text-text-primary">
      源图像
    </label>
    <input
      id="image-upload"
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
    <!-- Canvas区域 -->
    <div class="space-y-3">
      <div class="relative border border-border rounded-lg overflow-hidden bg-surface-elevated">
        <!-- 源图像Canvas -->
        <canvas
          bind:this={sourceCanvas}
          class="absolute inset-0 w-full h-full"
          style="pointer-events: none;"
        ></canvas>
        
        <!-- 蒙版Canvas（可交互） -->
        <canvas
          bind:this={maskCanvas}
          on:mousedown={startDrawing}
          on:mousemove={draw}
          on:mouseup={stopDrawing}
          on:mouseleave={stopDrawing}
          class="relative w-full h-full cursor-crosshair"
          style="mix-blend-mode: multiply; background-color: rgba(255, 0, 0, 0.3);"
        ></canvas>
      </div>
      
      <p class="text-xs text-text-secondary">
        💡 在图像上绘制红色区域标记需要重绘的部分
      </p>
    </div>
    
    <!-- 画笔工具 -->
    <div class="space-y-3 p-4 bg-surface-elevated border border-border rounded-lg">
      <div class="flex gap-2">
        <button
          on:click={() => tool = 'brush'}
          class="flex-1 px-3 py-2 rounded-lg font-medium transition-colors {tool === 'brush' ? 'bg-primary text-white' : 'bg-surface hover:bg-surface/80 text-text-secondary'}"
        >
          🖌️ 画笔
        </button>
        <button
          on:click={() => tool = 'eraser'}
          class="flex-1 px-3 py-2 rounded-lg font-medium transition-colors {tool === 'eraser' ? 'bg-primary text-white' : 'bg-surface hover:bg-surface/80 text-text-secondary'}"
        >
          🧹 橡皮擦
        </button>
        <button
          on:click={clearMask}
          class="px-3 py-2 bg-danger/10 hover:bg-danger/20 text-danger rounded-lg font-medium transition-colors"
        >
          清除
        </button>
      </div>
      
      <!-- 画笔大小 -->
      <div class="space-y-2">
        <label for="brush-size" class="block text-sm font-medium text-text-primary">
          画笔大小: {brushSize}px
        </label>
        <input
          id="brush-size"
          type="range"
          bind:value={brushSize}
          min="5"
          max="100"
          step="5"
          class="w-full"
        />
      </div>
      
      <!-- 画笔硬度 -->
      <div class="space-y-2">
        <label for="brush-hardness" class="block text-sm font-medium text-text-primary">
          画笔硬度: {(brushHardness * 100).toFixed(0)}%
        </label>
        <input
          id="brush-hardness"
          type="range"
          bind:value={brushHardness}
          min="0.1"
          max="1.0"
          step="0.1"
          class="w-full"
        />
      </div>
    </div>
    
    <!-- Prompt输入 -->
    <div class="space-y-2">
      <label for="prompt-input" class="block text-sm font-medium text-text-primary">
        Prompt
      </label>
      <textarea
        id="prompt-input"
        bind:value={prompt}
        rows="3"
        class="w-full px-3 py-2 bg-surface-elevated border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary resize-none"
        placeholder="描述你想要在蒙版区域生成的内容..."
      ></textarea>
    </div>
    
    <!-- Negative Prompt -->
    <div class="space-y-2">
      <label for="negative-prompt-input" class="block text-sm font-medium text-text-primary">
        Negative Prompt
      </label>
      <textarea
        id="negative-prompt-input"
        bind:value={negativePrompt}
        rows="2"
        class="w-full px-3 py-2 bg-surface-elevated border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary resize-none"
        placeholder="描述你不想要的内容..."
      ></textarea>
    </div>
    
    <!-- 参数配置 -->
    <div class="space-y-3 p-4 bg-surface-elevated border border-border rounded-lg">
      <h4 class="text-sm font-semibold text-text-primary">参数配置</h4>
      
      <!-- 重绘强度 -->
      <div class="space-y-2">
        <div class="flex justify-between items-center">
          <label for="strength-slider" class="text-sm font-medium text-text-primary">重绘强度</label>
          <span class="text-sm text-text-secondary">{strength.toFixed(2)}</span>
        </div>
        <input
          id="strength-slider"
          type="range"
          bind:value={strength}
          min="0.0"
          max="1.0"
          step="0.05"
          class="w-full"
        />
        <p class="text-xs text-text-secondary">
          值越高，重绘区域变化越大
        </p>
      </div>
      
      <!-- 引导强度 -->
      <div class="space-y-2">
        <div class="flex justify-between items-center">
          <label for="guidance-slider" class="text-sm font-medium text-text-primary">引导强度</label>
          <span class="text-sm text-text-secondary">{guidanceScale.toFixed(1)}</span>
        </div>
        <input
          id="guidance-slider"
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
          <label for="steps-slider" class="text-sm font-medium text-text-primary">生成步数</label>
          <span class="text-sm text-text-secondary">{steps}</span>
        </div>
        <input
          id="steps-slider"
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
        on:click={performInpainting}
        disabled={loading || !prompt.trim()}
        class="flex-1 px-4 py-3 bg-success hover:bg-success/90 disabled:bg-surface-elevated disabled:text-text-secondary text-white rounded-lg transition-colors font-medium disabled:cursor-not-allowed"
      >
        {#if loading}
          <span class="flex items-center justify-center gap-2">
            <div class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
            生成中...
          </span>
        {:else}
          开始重绘
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
        alt="Inpainting结果" 
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
