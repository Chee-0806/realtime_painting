<script lang="ts">
  import { onMount } from 'svelte';
  import { setError, clearError, ErrorType } from '$lib/store';
  
  // 组件状态
  let sourceImage: string = '';
  let sourceImageElement: HTMLImageElement | null = null;
  
  // Canvas引用
  let previewCanvas: HTMLCanvasElement;
  let previewCtx: CanvasRenderingContext2D | null = null;
  
  // 面部修复参数配置
  let model: string = 'codeformer';
  let strength: number = 0.8;
  
  // UI状态
  let loading: boolean = false;
  let resultImage: string = '';
  let showResult: boolean = false;
  let progress: number = 0;
  let showComparison: boolean = false;
  let comparisonSlider: number = 50;
  
  // 文件上传处理
  let fileInput: HTMLInputElement;
  
  // 可用的面部修复模型选项
  const modelOptions = [
    { value: 'codeformer', label: 'CodeFormer (推荐)', description: '最新技术，效果最佳' },
    { value: 'gfpgan', label: 'GFPGAN', description: '经典模型，速度快' }
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
  
  async function performFaceRestore() {
    if (!sourceImage) {
      setError({
        type: ErrorType.VALIDATION,
        message: '请选择源图像',
        recoverable: true,
        suggestions: ['上传一张包含人脸的图像']
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
      }, 300);
      
      const requestBody = {
        image: sourceImage,
        model: model,
        strength: strength
      };
      
      const response = await fetch('/api/face-restore', {
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
        showComparison = true;
        progress = 100;
        
        // 显示成功提示
        setTimeout(() => {
          progress = 0;
        }, 2000);
      } else {
        throw new Error(data.message || '面部修复失败');
      }
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : String(e);
      
      // 根据错误类型提供不同的建议
      let suggestions = [
        '确保图像中包含清晰的人脸',
        '尝试使用不同的模型',
        '调整修复强度参数'
      ];
      
      if (errorMessage.includes('HTTP错误: 400')) {
        suggestions = [
          '检查输入参数是否有效',
          '确保图像格式正确',
          '确认图像中包含人脸'
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
      } else if (errorMessage.includes('Pipeline') || errorMessage.includes('model')) {
        suggestions = [
          '面部修复模型可能未加载',
          '检查后端配置',
          '查看后端启动日志',
          '确认模型文件已下载'
        ];
      }
      
      setError({
        type: ErrorType.API,
        message: '面部修复失败',
        details: errorMessage,
        recoverable: true,
        suggestions: suggestions
      });
      console.error('面部修复失败:', e);
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
    link.download = `face_restored_${model}_${Date.now()}.png`;
    link.click();
  }
  
  function reset() {
    sourceImage = '';
    resultImage = '';
    showResult = false;
    showComparison = false;
    model = 'codeformer';
    strength = 0.8;
    progress = 0;
    comparisonSlider = 50;
    clearError();
  }
  
  function toggleComparison() {
    showComparison = !showComparison;
  }
</script>

<div class="space-y-4">
  <div class="flex items-center justify-between mb-4">
    <h3 class="text-lg font-semibold text-text-primary">👤 面部修复 (Face Restore)</h3>
    <button 
      on:click={reset}
      class="px-3 py-1 text-sm bg-surface-elevated hover:bg-surface-elevated/80 border border-border rounded-lg text-text-secondary transition-colors"
    >
      重置
    </button>
  </div>
  
  <div class="p-3 bg-info/10 border border-info/30 rounded-lg">
    <p class="text-sm text-text-primary">
      💡 <strong>面部修复</strong> 使用 AI 技术修复和增强人脸细节，改善模糊或低质量的面部图像。
    </p>
  </div>
  
  <!-- 图像上传 -->
  <div class="space-y-2">
    <label for="face-restore-image-upload" class="block text-sm font-medium text-text-primary">
      选择图像
    </label>
    <input
      id="face-restore-image-upload"
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
          style="max-width: 100%;"
        ></canvas>
      </div>
      <p class="text-xs text-text-secondary">
        原始尺寸: {sourceImageElement?.width || 0} × {sourceImageElement?.height || 0} px
      </p>
    </div>
  {/if}
  
  <!-- 参数配置 -->
  <div class="space-y-4 p-4 bg-surface-elevated border border-border rounded-lg">
    <h4 class="text-sm font-semibold text-text-primary">参数配置</h4>
    
    <!-- 模型选择 -->
    <div class="space-y-2">
      <label for="model-select" class="block text-sm font-medium text-text-primary">
        修复模型
      </label>
      <select
        id="model-select"
        bind:value={model}
        class="w-full px-3 py-2 bg-surface border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary"
      >
        {#each modelOptions as option}
          <option value={option.value}>{option.label}</option>
        {/each}
      </select>
      <div class="text-xs text-text-secondary space-y-1">
        {#each modelOptions as option}
          {#if option.value === model}
            <p>💡 <strong>{option.label}</strong>: {option.description}</p>
          {/if}
        {/each}
      </div>
    </div>
    
    <!-- 修复强度 -->
    <div class="space-y-2">
      <div class="flex justify-between items-center">
        <label for="strength-slider" class="text-sm font-medium text-text-primary">修复强度</label>
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
      <div class="flex justify-between text-xs text-text-secondary">
        <span>保留原貌</span>
        <span>完全修复</span>
      </div>
      <p class="text-xs text-text-secondary">
        {#if strength < 0.3}
          轻微修复，保留更多原始特征
        {:else if strength < 0.7}
          平衡修复，推荐设置
        {:else}
          强力修复，可能改变面部特征
        {/if}
      </p>
    </div>
  </div>
  
  <!-- 进度显示 -->
  {#if loading}
    <div class="p-4 bg-primary/10 border border-primary/30 rounded-lg space-y-3">
      <div class="flex items-center gap-3">
        <div class="animate-spin h-5 w-5 border-2 border-primary border-t-transparent rounded-full"></div>
        <span class="text-sm font-medium text-text-primary">正在修复面部...</span>
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
                检测面部...
              {:else if progress < 95}
                修复中...
              {:else}
                完成！
              {/if}
            </span>
          </div>
        </div>
      {/if}
      
      <div class="text-xs text-text-secondary">
        <p>🤖 使用 {modelOptions.find(o => o.value === model)?.label || model}</p>
        <p>💪 修复强度: {(strength * 100).toFixed(0)}%</p>
      </div>
    </div>
  {/if}
  
  <!-- 操作按钮 -->
  <div class="flex gap-3">
    <button
      on:click={performFaceRestore}
      disabled={loading || !sourceImage}
      class="flex-1 px-4 py-3 bg-success hover:bg-success/90 disabled:bg-surface-elevated disabled:text-text-secondary text-white rounded-lg transition-colors font-medium disabled:cursor-not-allowed"
    >
      {#if loading}
        <span class="flex items-center justify-center gap-2">
          <div class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
          修复中...
        </span>
      {:else}
        开始修复
      {/if}
    </button>
  </div>
  
  <!-- 结果显示 -->
  {#if showResult && resultImage}
    <div class="space-y-3 p-4 bg-surface-elevated border border-success/30 rounded-lg">
      <div class="flex items-center justify-between">
        <h4 class="text-sm font-semibold text-text-primary">✨ 修复结果</h4>
        <div class="flex gap-2">
          <button
            on:click={toggleComparison}
            class="px-3 py-1 text-sm bg-surface hover:bg-surface/80 border border-border text-text-primary rounded-lg transition-colors"
          >
            {showComparison ? '隐藏对比' : '显示对比'}
          </button>
          <button
            on:click={downloadResult}
            class="px-3 py-1 text-sm bg-primary hover:bg-primary/90 text-white rounded-lg transition-colors"
          >
            下载
          </button>
        </div>
      </div>
      
      {#if showComparison}
        <!-- 前后对比视图 -->
        <div class="space-y-3">
          <div class="relative border border-border rounded-lg overflow-hidden bg-surface">
            <div class="comparison-container">
              <!-- 原始图像 -->
              <div class="comparison-image original">
                <img 
                  src={sourceImage} 
                  alt="原始图像" 
                  class="w-full h-auto"
                />
                <div class="comparison-label left">原始</div>
              </div>
              
              <!-- 修复后图像 -->
              <div 
                class="comparison-image restored"
                style="clip-path: inset(0 {100 - comparisonSlider}% 0 0);"
              >
                <img 
                  src={resultImage} 
                  alt="修复后" 
                  class="w-full h-auto"
                />
                <div class="comparison-label right">修复后</div>
              </div>
              
              <!-- 滑动分隔线 -->
              <div 
                class="comparison-divider"
                style="left: {comparisonSlider}%;"
              >
                <div class="comparison-handle">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M15 18l-6-6 6-6"/>
                    <path d="M9 18l6-6-6-6"/>
                  </svg>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 对比滑块 -->
          <div class="space-y-2">
            <input
              type="range"
              bind:value={comparisonSlider}
              min="0"
              max="100"
              step="1"
              class="w-full"
            />
            <div class="flex justify-between text-xs text-text-secondary">
              <span>← 原始</span>
              <span>修复后 →</span>
            </div>
          </div>
        </div>
      {:else}
        <!-- 仅显示修复结果 -->
        <img 
          src={resultImage} 
          alt="修复结果" 
          class="w-full h-auto rounded-lg border border-border"
        />
      {/if}
      
      <p class="text-xs text-text-secondary">
        使用 {modelOptions.find(o => o.value === model)?.label || model} 修复（强度: {(strength * 100).toFixed(0)}%）
      </p>
    </div>
  {/if}
</div>

<style>
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
  
  .comparison-container {
    position: relative;
    width: 100%;
    overflow: hidden;
  }
  
  .comparison-image {
    position: relative;
    width: 100%;
  }
  
  .comparison-image.restored {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
  }
  
  .comparison-image img {
    display: block;
    width: 100%;
    height: auto;
    user-select: none;
    pointer-events: none;
  }
  
  .comparison-label {
    position: absolute;
    top: 12px;
    padding: 4px 12px;
    background: rgba(0, 0, 0, 0.7);
    color: white;
    font-size: 12px;
    font-weight: 600;
    border-radius: 4px;
    backdrop-filter: blur(4px);
  }
  
  .comparison-label.left {
    left: 12px;
  }
  
  .comparison-label.right {
    right: 12px;
  }
  
  .comparison-divider {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background: white;
    cursor: ew-resize;
    z-index: 10;
    transform: translateX(-50%);
  }
  
  .comparison-handle {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 40px;
    height: 40px;
    background: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    color: #333;
  }
  
  .comparison-handle svg {
    width: 24px;
    height: 24px;
  }
</style>
