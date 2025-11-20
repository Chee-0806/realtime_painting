<script lang="ts">
  import { onMount } from 'svelte';
  import { setError, clearError, ErrorType } from '$lib/store';
  
  // 组件状态
  let sourceImage: string = '';
  let sourceImageElement: HTMLImageElement | null = null;
  
  // Canvas引用
  let previewCanvas: HTMLCanvasElement;
  let previewCtx: CanvasRenderingContext2D | null = null;
  
  // Upscale参数配置
  let upscaler: string = 'real-esrgan';
  let scale: number = 2.0;
  
  // UI状态
  let loading: boolean = false;
  let resultImage: string = '';
  let showResult: boolean = false;
  let progress: number = 0;
  
  // 文件上传处理
  let fileInput: HTMLInputElement;
  
  // 可用的Upscaler选项
  const upscalerOptions = [
    { value: 'real-esrgan', label: 'Real-ESRGAN (高质量)' },
    { value: 'lanczos', label: 'Lanczos (快速)' },
    { value: 'bicubic', label: 'Bicubic (标准)' }
  ];
  
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
    
    // 设置画布尺寸
    previewCanvas.width = width;
    previewCanvas.height = height;
    
    // 绘制图像
    previewCtx.drawImage(img, 0, 0, width, height);
  }
  
  async function performUpscale() {
    if (!sourceImage) {
      setError({
        type: ErrorType.VALIDATION,
        message: '请选择源图像',
        recoverable: true,
        suggestions: ['上传一张图像进行放大']
      });
      return;
    }
    
    loading = true;
    progress = 10;
    clearError();
    
    try {
      // 模拟进度
      const progressInterval = setInterval(() => {
        if (progress < 90) {
          progress += 10;
        }
      }, 200);
      
      const requestBody = {
        image: sourceImage,
        scale: scale,
        upscaler: upscaler
      };
      
      const response = await fetch('/api/upscale', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });
      
      clearInterval(progressInterval);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP错误: ${response.status}`);
      }
      
      progress = 95;
      
      const data = await response.json();
      
      if (data.success) {
        resultImage = data.image;
        showResult = true;
        progress = 100;
        
        // 显示成功提示
        setTimeout(() => {
          progress = 0;
        }, 2000);
      } else {
        throw new Error(data.message || '放大失败');
      }
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : String(e);
      
      // 根据错误类型提供不同的建议
      let suggestions = [
        '检查图像是否有效',
        '尝试使用不同的Upscaler',
        '尝试较小的放大倍数'
      ];
      
      if (errorMessage.includes('HTTP错误: 400')) {
        suggestions = [
          '检查输入参数是否有效',
          '确保图像格式正确',
          '尝试使用不同的图像'
        ];
      } else if (errorMessage.includes('HTTP错误: 500')) {
        suggestions = [
          '后端服务可能遇到问题',
          '检查后端日志',
          '尝试重启后端服务'
        ];
      } else if (errorMessage.includes('Failed to fetch') || errorMessage.includes('NetworkError')) {
        suggestions = [
          '检查网络连接',
          '确认后端服务正常运行',
          '检查防火墙设置'
        ];
      } else if (errorMessage.includes('Pipeline')) {
        suggestions = [
          'Upscale Pipeline 可能未初始化',
          '检查后端配置',
          '查看后端启动日志'
        ];
      }
      
      setError({
        type: ErrorType.API,
        message: '图像放大失败',
        details: errorMessage,
        recoverable: true,
        suggestions: suggestions
      });
      console.error('Upscale失败:', e);
    } finally {
      loading = false;
      if (!showResult) {
        progress = 0;
      }
    }
  }
  
  function downloadResult() {
    if (!resultImage) return;
    
    const link = document.createElement('a');
    link.href = resultImage;
    link.download = `upscaled_${scale}x_${Date.now()}.png`;
    link.click();
  }
  
  function reset() {
    sourceImage = '';
    resultImage = '';
    showResult = false;
    upscaler = 'real-esrgan';
    scale = 2.0;
    progress = 0;
    clearError();
  }
</script>

<div class="space-y-4">
  <div class="flex items-center justify-between mb-4">
    <h3 class="text-lg font-semibold text-text-primary">🔍 图像放大 (Upscale)</h3>
    <button 
      on:click={reset}
      class="px-3 py-1 text-sm bg-surface-elevated hover:bg-surface-elevated/80 border border-border rounded-lg text-text-secondary transition-colors"
    >
      重置
    </button>
  </div>
  
  <div class="p-3 bg-info/10 border border-info/30 rounded-lg">
    <p class="text-sm text-text-primary">
      💡 <strong>图像放大</strong> 使用 AI 算法提升图像分辨率，保持细节清晰。
    </p>
  </div>
  
  <!-- 图像上传 -->
  <div class="space-y-2">
    <label for="upscale-image-upload" class="block text-sm font-medium text-text-primary">
      选择图像
    </label>
    <input
      id="upscale-image-upload"
      type="file"
      bind:this={fileInput}
      on:change={handleFileSelect}
      accept="image/*"
      class="hidden"
    />
    <button
      on:click={() => fileInput.click()}
      class="w-full px-4 py-3 bg-surface-elevated hover:bg-surface border border-border text-text-primary rounded-lg transition-colors font-medium"
    >
      {sourceImage ? '更换图像' : '选择图像'}
    </button>
  </div>
  
  {#if sourceImage}
    <!-- 预览区域 -->
    <div class="space-y-2">
      <div class="border border-border rounded-lg overflow-hidden bg-surface-elevated p-4">
        <canvas
          bind:this={previewCanvas}
          class="w-full h-auto mx-auto"
          style="max-width: 100%; image-rendering: pixelated;"
        ></canvas>
      </div>
      <p class="text-xs text-text-secondary">
        原始尺寸: {sourceImageElement?.width || 0} × {sourceImageElement?.height || 0} px
        → 目标尺寸: {sourceImageElement ? Math.round(sourceImageElement.width * scale) : 0} × {sourceImageElement ? Math.round(sourceImageElement.height * scale) : 0} px
      </p>
    </div>
  {/if}
  
  <!-- 参数配置 -->
  <div class="space-y-4 p-4 bg-surface-elevated border border-border rounded-lg">
    <h4 class="text-sm font-semibold text-text-primary">参数配置</h4>
    
    <!-- Upscaler选择 -->
    <div class="space-y-2">
      <label for="upscaler-select" class="block text-sm font-medium text-text-primary">
        放大算法
      </label>
      <select
        id="upscaler-select"
        bind:value={upscaler}
        class="w-full px-3 py-2 bg-surface border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary"
      >
        {#each upscalerOptions as option}
          <option value={option.value}>{option.label}</option>
        {/each}
      </select>
      <div class="text-xs text-text-secondary space-y-1">
        <p>💡 <strong>Real-ESRGAN</strong>: AI 增强，最高质量，适合照片和艺术作品</p>
        <p>💡 <strong>Lanczos</strong>: 传统算法，速度快，适合快速预览</p>
        <p>💡 <strong>Bicubic</strong>: 标准插值，平衡质量和速度</p>
      </div>
    </div>
    
    <!-- 放大倍数 -->
    <div class="space-y-2">
      <div class="flex justify-between items-center">
        <label for="scale-slider" class="text-sm font-medium text-text-primary">放大倍数</label>
        <span class="text-sm text-text-secondary">{scale.toFixed(1)}x</span>
      </div>
      <input
        id="scale-slider"
        type="range"
        bind:value={scale}
        min="1.0"
        max="4.0"
        step="0.1"
        class="w-full"
      />
      <p class="text-xs text-text-secondary">
        图像将被放大到原始尺寸的 {scale}x
      </p>
    </div>
  </div>
  
  <!-- 进度显示 -->
  {#if loading}
    <div class="p-4 bg-primary/10 border border-primary/30 rounded-lg space-y-3">
      <div class="flex items-center gap-3">
        <div class="animate-spin h-5 w-5 border-2 border-primary border-t-transparent rounded-full"></div>
        <span class="text-sm font-medium text-text-primary">正在放大图像...</span>
      </div>
      
      {#if progress > 0}
        <div class="space-y-1">
          <div class="w-full bg-surface-elevated rounded-full h-2.5 overflow-hidden">
            <div 
              class="bg-gradient-to-r from-primary to-success h-2.5 rounded-full transition-all duration-500 ease-out"
              style="width: {progress}%"
            ></div>
          </div>
          <div class="flex justify-between text-xs text-text-secondary">
            <span>{progress}%</span>
            <span>
              {#if progress < 50}
                处理中...
              {:else if progress < 95}
                即将完成...
              {:else}
                完成！
              {/if}
            </span>
          </div>
        </div>
      {/if}
      
      <div class="text-xs text-text-secondary">
        <p>🔍 使用 {upscalerOptions.find(o => o.value === upscaler)?.label || upscaler}</p>
        <p>📐 放大倍数: {scale}x</p>
      </div>
    </div>
  {/if}
  
  <!-- 操作按钮 -->
  <div class="flex gap-3">
    <button
      on:click={performUpscale}
      disabled={loading || !sourceImage}
      class="flex-1 px-4 py-3 bg-success hover:bg-success/90 disabled:bg-surface-elevated disabled:text-text-secondary text-white rounded-lg transition-colors font-medium disabled:cursor-not-allowed"
    >
      {#if loading}
        <span class="flex items-center justify-center gap-2">
          <div class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
          放大中...
        </span>
      {:else}
        开始放大
      {/if}
    </button>
  </div>
  
  <!-- 结果显示 -->
  {#if showResult && resultImage}
    <div class="space-y-3 p-4 bg-surface-elevated border border-success/30 rounded-lg">
      <div class="flex items-center justify-between">
        <h4 class="text-sm font-semibold text-text-primary">✨ 放大结果</h4>
        <button
          on:click={downloadResult}
          class="px-3 py-1 text-sm bg-primary hover:bg-primary/90 text-white rounded-lg transition-colors"
        >
          下载
        </button>
      </div>
      <img 
        src={resultImage} 
        alt="放大结果" 
        class="w-full h-auto rounded-lg border border-border"
      />
      <p class="text-xs text-text-secondary">
        图像已放大 {scale}x（使用 {upscalerOptions.find(o => o.value === upscaler)?.label || upscaler}）
      </p>
    </div>
  {/if}
</div>

<style>
  canvas {
    image-rendering: pixelated;
    image-rendering: -moz-crisp-edges;
    image-rendering: crisp-edges;
  }
  
  input[type="range"] {
    -webkit-appearance: none;
    appearance: none;
    height: 6px;
    border-radius: 3px;
    background: var(--surface-elevated, #2a2a2a);
    outline: none;
  }
  
  input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: var(--primary, #3b82f6);
    cursor: pointer;
  }
  
  input[type="range"]::-moz-range-thumb {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: var(--primary, #3b82f6);
    cursor: pointer;
    border: none;
  }
</style>
