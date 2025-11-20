<script lang="ts">
  import { onMount } from 'svelte';
  import { setError, clearError, ErrorType } from '$lib/store';
  
  // 组件状态
  let sourceImage: string = '';
  let sourceImageElement: HTMLImageElement | null = null;
  
  // Canvas引用
  let previewCanvas: HTMLCanvasElement;
  let previewCtx: CanvasRenderingContext2D | null = null;
  
  // Hires.fix参数配置
  let firstPassSteps: number = 20;
  let hiresSteps: number = 15;
  let upscaler: string = 'Latent';
  let upscaleBy: number = 2.0;
  let denoisingStrength: number = 0.7;
  
  // Prompt配置
  let prompt: string = '';
  let negativePrompt: string = '';
  let guidanceScale: number = 7.5;
  
  // UI状态
  let loading: boolean = false;
  let resultImage: string = '';
  let showResult: boolean = false;
  let currentStage: string = '';
  let progress: number = 0;
  
  // 文件上传处理
  let fileInput: HTMLInputElement;
  
  // 可用的Upscaler选项
  const upscalerOptions = [
    { value: 'Latent', label: 'Latent (快速)' },
    { value: 'Latent (nearest)', label: 'Latent (最近邻)' },
    { value: 'Latent (bicubic)', label: 'Latent (双三次)' },
    { value: 'ESRGAN_4x', label: 'ESRGAN 4x' },
    { value: 'R-ESRGAN 4x+', label: 'R-ESRGAN 4x+' },
    { value: 'LDSR', label: 'LDSR (高质量)' }
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
  
  async function performHiresFix() {
    if (!prompt.trim()) {
      setError({
        type: ErrorType.VALIDATION,
        message: '请输入Prompt',
        recoverable: true,
        suggestions: ['在Prompt输入框中描述你想要生成的内容']
      });
      return;
    }
    
    // 如果没有源图像，需要创建一个空白图像
    if (!sourceImage) {
      setError({
        type: ErrorType.VALIDATION,
        message: '请选择源图像',
        recoverable: true,
        suggestions: ['上传一张图像作为 Hires.fix 的起点']
      });
      return;
    }
    
    loading = true;
    currentStage = '准备中...';
    progress = 0;
    clearError();
    
    try {
      // 计算目标尺寸
      const firstStageWidth = sourceImageElement ? sourceImageElement.width : 512;
      const firstStageHeight = sourceImageElement ? sourceImageElement.height : 512;
      const secondStageWidth = Math.round(firstStageWidth * upscaleBy);
      const secondStageHeight = Math.round(firstStageHeight * upscaleBy);
      
      const requestBody: any = {
        image: sourceImage,
        prompt: prompt,
        negative_prompt: negativePrompt,
        first_stage_width: firstStageWidth,
        first_stage_height: firstStageHeight,
        second_stage_width: secondStageWidth,
        second_stage_height: secondStageHeight,
        first_stage_steps: firstPassSteps,
        second_stage_steps: hiresSteps,
        first_stage_guidance_scale: guidanceScale,
        second_stage_guidance_scale: guidanceScale,
        second_stage_denoising_strength: denoisingStrength,
        upscaler: upscaler !== 'Latent' ? upscaler : null,  // Latent 是默认，不需要额外的 upscaler
      };
      
      // 模拟两阶段进度
      currentStage = '第一阶段：低分辨率生成';
      progress = 10;
      
      // 启动进度模拟
      const progressInterval = setInterval(() => {
        if (progress < 45) {
          progress += 5;
        } else if (progress < 90) {
          progress += 2;
        }
      }, 500);
      
      const response = await fetch('/api/hires-fix', {
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
      
      currentStage = '第二阶段：高分辨率修复';
      progress = 95;
      
      const data = await response.json();
      
      if (data.success) {
        resultImage = data.image;
        showResult = true;
        currentStage = '完成';
        progress = 100;
        
        // 显示成功提示
        setTimeout(() => {
          currentStage = '';
          progress = 0;
        }, 2000);
      } else {
        throw new Error(data.message || '生成失败');
      }
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : String(e);
      
      // 根据错误类型提供不同的建议
      let suggestions = [
        '检查Prompt是否合适',
        '尝试调整参数',
        '尝试不同的Upscaler'
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
          'Hires.fix Pipeline 可能未初始化',
          '检查后端配置',
          '查看后端启动日志'
        ];
      }
      
      setError({
        type: ErrorType.API,
        message: 'Hires.fix 生成失败',
        details: errorMessage,
        recoverable: true,
        suggestions: suggestions
      });
      console.error('Hires.fix失败:', e);
    } finally {
      loading = false;
      if (!showResult) {
        currentStage = '';
        progress = 0;
      }
    }
  }
  
  function downloadResult() {
    if (!resultImage) return;
    
    const link = document.createElement('a');
    link.href = resultImage;
    link.download = `hires_fix_result_${Date.now()}.png`;
    link.click();
  }
  
  function reset() {
    sourceImage = '';
    resultImage = '';
    showResult = false;
    prompt = '';
    negativePrompt = '';
    firstPassSteps = 20;
    hiresSteps = 15;
    upscaler = 'Latent';
    upscaleBy = 2.0;
    denoisingStrength = 0.7;
    guidanceScale = 7.5;
    currentStage = '';
    progress = 0;
    clearError();
  }
</script>

<div class="space-y-4">
  <div class="flex items-center justify-between mb-4">
    <h3 class="text-lg font-semibold text-text-primary">🔍 高分辨率修复 (Hires.fix)</h3>
    <button 
      on:click={reset}
      class="px-3 py-1 text-sm bg-surface-elevated hover:bg-surface-elevated/80 border border-border rounded-lg text-text-secondary transition-colors"
    >
      重置
    </button>
  </div>
  
  <div class="p-3 bg-info/10 border border-info/30 rounded-lg">
    <p class="text-sm text-text-primary">
      💡 <strong>Hires.fix</strong> 通过两阶段生成提升图像质量：先生成低分辨率图像，再放大并细化细节。
    </p>
  </div>
  
  <!-- 可选：图像上传（用于已有图像的高分辨率修复） -->
  <div class="space-y-2">
    <label for="hires-image-upload" class="block text-sm font-medium text-text-primary">
      源图像 <span class="text-text-secondary text-xs">(可选，留空则从头生成)</span>
    </label>
    <input
      id="hires-image-upload"
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
      {sourceImage ? '更换图像' : '选择图像（可选）'}
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
        原始图像将被放大 {upscaleBy}x 并进行高分辨率修复
      </p>
    </div>
  {/if}
  
  <!-- Prompt输入 -->
  <div class="space-y-2">
    <label for="hires-prompt-input" class="block text-sm font-medium text-text-primary">
      Prompt
    </label>
    <textarea
      id="hires-prompt-input"
      bind:value={prompt}
      rows="3"
      class="w-full px-3 py-2 bg-surface-elevated border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary resize-none"
      placeholder="描述你想要生成的高质量图像..."
    ></textarea>
  </div>
  
  <!-- Negative Prompt -->
  <div class="space-y-2">
    <label for="hires-negative-prompt-input" class="block text-sm font-medium text-text-primary">
      Negative Prompt
    </label>
    <textarea
      id="hires-negative-prompt-input"
      bind:value={negativePrompt}
      rows="2"
      class="w-full px-3 py-2 bg-surface-elevated border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary resize-none"
      placeholder="描述你不想要的内容..."
    ></textarea>
  </div>
  
  <!-- 参数配置 -->
  <div class="space-y-4 p-4 bg-surface-elevated border border-border rounded-lg">
    <h4 class="text-sm font-semibold text-text-primary">参数配置</h4>
    
    <!-- 第一阶段步数 -->
    <div class="space-y-2">
      <div class="flex justify-between items-center">
        <label for="first-pass-steps" class="text-sm font-medium text-text-primary">
          第一阶段步数
        </label>
        <input
          id="first-pass-steps"
          type="number"
          bind:value={firstPassSteps}
          min="10"
          max="50"
          class="w-20 px-2 py-1 bg-surface border border-border rounded text-text-primary text-sm text-center"
        />
      </div>
      <p class="text-xs text-text-secondary">
        低分辨率生成的步数（推荐 15-25）
      </p>
    </div>
    
    <!-- 高分辨率步数 -->
    <div class="space-y-2">
      <div class="flex justify-between items-center">
        <label for="hires-steps" class="text-sm font-medium text-text-primary">
          高分辨率步数
        </label>
        <input
          id="hires-steps"
          type="number"
          bind:value={hiresSteps}
          min="5"
          max="50"
          class="w-20 px-2 py-1 bg-surface border border-border rounded text-text-primary text-sm text-center"
        />
      </div>
      <p class="text-xs text-text-secondary">
        高分辨率细化的步数（推荐 10-20）
      </p>
    </div>
    
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
        <p>💡 <strong>Latent</strong>: 速度快，适合快速预览</p>
        <p>💡 <strong>ESRGAN</strong>: 质量高，适合照片和真实场景</p>
        <p>💡 <strong>LDSR</strong>: 最高质量，但速度较慢</p>
      </div>
    </div>
    
    <!-- 放大倍数 -->
    <div class="space-y-2">
      <div class="flex justify-between items-center">
        <label for="upscale-by-slider" class="text-sm font-medium text-text-primary">放大倍数</label>
        <span class="text-sm text-text-secondary">{upscaleBy.toFixed(1)}x</span>
      </div>
      <input
        id="upscale-by-slider"
        type="range"
        bind:value={upscaleBy}
        min="1.0"
        max="4.0"
        step="0.1"
        class="w-full"
      />
      <p class="text-xs text-text-secondary">
        图像将被放大到原始尺寸的 {upscaleBy}x
      </p>
    </div>
    
    <!-- 降噪强度 -->
    <div class="space-y-2">
      <div class="flex justify-between items-center">
        <label for="denoising-slider" class="text-sm font-medium text-text-primary">降噪强度</label>
        <span class="text-sm text-text-secondary">{denoisingStrength.toFixed(2)}</span>
      </div>
      <input
        id="denoising-slider"
        type="range"
        bind:value={denoisingStrength}
        min="0.0"
        max="1.0"
        step="0.05"
        class="w-full"
      />
      <p class="text-xs text-text-secondary">
        值越高，高分辨率阶段变化越大（推荐 0.6-0.8）
      </p>
    </div>
    
    <!-- 引导强度 -->
    <div class="space-y-2">
      <div class="flex justify-between items-center">
        <label for="hires-guidance-slider" class="text-sm font-medium text-text-primary">引导强度</label>
        <span class="text-sm text-text-secondary">{guidanceScale.toFixed(1)}</span>
      </div>
      <input
        id="hires-guidance-slider"
        type="range"
        bind:value={guidanceScale}
        min="1.0"
        max="20.0"
        step="0.5"
        class="w-full"
      />
    </div>
  </div>
  
  <!-- 进度显示 -->
  {#if loading}
    <div class="p-4 bg-primary/10 border border-primary/30 rounded-lg space-y-3">
      <div class="flex items-center gap-3">
        <div class="animate-spin h-5 w-5 border-2 border-primary border-t-transparent rounded-full"></div>
        <span class="text-sm font-medium text-text-primary">{currentStage}</span>
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
                第一阶段生成中...
              {:else if progress < 95}
                第二阶段修复中...
              {:else}
                即将完成...
              {/if}
            </span>
          </div>
        </div>
      {/if}
      
      <div class="text-xs text-text-secondary">
        <p>⏱️ 预计时间：{firstPassSteps + hiresSteps} 步 × {upscaleBy}x 放大</p>
        <p>📐 目标尺寸：{sourceImageElement ? Math.round(sourceImageElement.width * upscaleBy) : '?'} × {sourceImageElement ? Math.round(sourceImageElement.height * upscaleBy) : '?'} px</p>
      </div>
    </div>
  {/if}
  
  <!-- 操作按钮 -->
  <div class="flex gap-3">
    <button
      on:click={performHiresFix}
      disabled={loading || !prompt.trim()}
      class="flex-1 px-4 py-3 bg-success hover:bg-success/90 disabled:bg-surface-elevated disabled:text-text-secondary text-white rounded-lg transition-colors font-medium disabled:cursor-not-allowed"
    >
      {#if loading}
        <span class="flex items-center justify-center gap-2">
          <div class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
          生成中...
        </span>
      {:else}
        开始生成
      {/if}
    </button>
  </div>
  
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
        alt="Hires.fix结果" 
        class="w-full h-auto rounded-lg border border-border"
      />
      <p class="text-xs text-text-secondary">
        高分辨率图像已生成（{upscaleBy}x 放大）
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
