<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { pipelineValues } from '$lib/store';
  
  const dispatch = createEventDispatcher();
  
  // Props
  export let initialImageUrl: string = '';
  export let showCloseButton: boolean = true;
  export let autoApplyPrompt: boolean = false;
  
  // CLIP反推配置
  let clipImageUrl: string = initialImageUrl;
  let clipMode: 'fast' | 'classic' | 'negative' = 'fast';
  let clipInterrogating = false;
  let clipResult: {
    flavors: string[];
    prompt: string;
    negative_prompt: string;
    mode: string;
  } | null = null;
  let clipError: string = '';
  
  // 文件上传
  let fileInput: HTMLInputElement;
  
  // 监听 initialImageUrl 变化
  $: if (initialImageUrl) {
    clipImageUrl = initialImageUrl;
    clipResult = null;
    clipError = '';
  }
  
  /**
   * 处理文件上传
   */
  function handleFileUpload(event: Event) {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    
    if (!file) return;
    
    // 验证文件类型
    if (!file.type.startsWith('image/')) {
      clipError = '请上传图像文件';
      return;
    }
    
    // 验证文件大小（最大 10MB）
    if (file.size > 10 * 1024 * 1024) {
      clipError = '图像文件过大，请上传小于 10MB 的文件';
      return;
    }
    
    // 读取文件为 base64
    const reader = new FileReader();
    reader.onload = (e) => {
      clipImageUrl = e.target?.result as string;
      clipResult = null;
      clipError = '';
    };
    reader.onerror = () => {
      clipError = '读取文件失败';
    };
    reader.readAsDataURL(file);
  }
  
  /**
   * 触发文件选择
   */
  function triggerFileUpload() {
    fileInput?.click();
  }
  
  /**
   * 清除图像
   */
  function clearImage() {
    clipImageUrl = '';
    clipResult = null;
    clipError = '';
    if (fileInput) {
      fileInput.value = '';
    }
  }
  
  /**
   * 执行 CLIP 反推
   */
  async function performCLIPInterrogation() {
    if (!clipImageUrl) {
      clipError = '请先上传或选择图像';
      return;
    }
    
    clipInterrogating = true;
    clipError = '';
    clipResult = null;
    
    try {
      // 准备图像数据
      let imageData = clipImageUrl;
      
      // 如果不是 base64 格式，尝试获取
      if (!imageData.startsWith('data:')) {
        try {
          const response = await fetch(imageData);
          const blob = await response.blob();
          imageData = await new Promise<string>((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result as string);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
          });
        } catch (err) {
          console.error('获取图像失败:', err);
          clipError = '无法获取图像数据';
          return;
        }
      }
      
      const response = await fetch('/api/clip/interrogate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image: imageData,
          mode: clipMode,
        }),
      });
      
      const data = await response.json();
      
      if (!response.ok || !data.success) {
        clipError = data.message || 'CLIP 反推失败';
        return;
      }
      
      clipResult = {
        flavors: data.flavors || [],
        prompt: data.prompt || '',
        negative_prompt: data.negative_prompt || '',
        mode: data.mode || clipMode,
      };
      
      // 触发结果事件
      dispatch('result', clipResult);
      
      // 自动应用 Prompt
      if (autoApplyPrompt) {
        applyPrompt();
      }
    } catch (err) {
      console.error('CLIP 反推失败:', err);
      clipError = err instanceof Error ? err.message : '未知错误';
    } finally {
      clipInterrogating = false;
    }
  }
  
  /**
   * 应用 Prompt 到参数
   */
  function applyPrompt() {
    if (!clipResult) return;
    
    pipelineValues.update(values => ({
      ...values,
      prompt: clipResult.prompt,
      negative_prompt: clipResult.negative_prompt,
    }));
    
    dispatch('apply', clipResult);
  }
  
  /**
   * 复制 Prompt
   */
  async function copyPrompt() {
    if (!clipResult) return;
    
    try {
      await navigator.clipboard.writeText(clipResult.prompt);
      dispatch('copy', { type: 'prompt', text: clipResult.prompt });
    } catch (err) {
      console.error('复制失败:', err);
    }
  }
  
  /**
   * 复制 Negative Prompt
   */
  async function copyNegativePrompt() {
    if (!clipResult) return;
    
    try {
      await navigator.clipboard.writeText(clipResult.negative_prompt);
      dispatch('copy', { type: 'negative_prompt', text: clipResult.negative_prompt });
    } catch (err) {
      console.error('复制失败:', err);
    }
  }
  
  /**
   * 关闭面板
   */
  function closePanel() {
    dispatch('close');
  }
</script>

<div class="card-compact">
  <!-- 标题栏 -->
  <div class="flex items-center justify-between mb-4">
    <h3 class="heading mb-0">🔍 CLIP Prompt反推</h3>
    {#if showCloseButton}
      <button
        on:click={closePanel}
        class="btn-ghost text-sm px-2 py-1"
        title="关闭CLIP面板"
      >
        ✕
      </button>
    {/if}
  </div>
  
  <!-- 图像上传区域 -->
  <div class="mb-4">
    <input
      bind:this={fileInput}
      type="file"
      accept="image/*"
      on:change={handleFileUpload}
      class="hidden"
      aria-label="上传图像"
    />
    
    {#if !clipImageUrl}
      <!-- 上传按钮 -->
      <button
        on:click={triggerFileUpload}
        class="btn-primary w-full flex items-center justify-center gap-2 py-8 border-2 border-dashed border-primary/30 hover:border-primary/50 transition-colors"
      >
        <span class="text-2xl">📁</span>
        <span>点击上传图像</span>
      </button>
      <p class="text-xs text-text-tertiary mt-2 text-center">
        支持 JPG、PNG、WebP 等格式，最大 10MB
      </p>
    {:else}
      <!-- 图像预览 -->
      <div class="bg-surface/50 p-4 rounded-xl border border-border">
        <div class="flex items-center justify-between mb-2">
          <span class="label mb-0">预览图像</span>
          <div class="flex gap-2">
            <button
              on:click={triggerFileUpload}
              class="btn-ghost text-xs px-2 py-1"
              title="更换图像"
            >
              🔄 更换
            </button>
            <button
              on:click={clearImage}
              class="btn-ghost text-xs px-2 py-1"
              title="清除图像"
            >
              🗑️ 清除
            </button>
          </div>
        </div>
        <div class="flex justify-center">
          <img
            src={clipImageUrl}
            alt="预览图像"
            class="max-w-full h-auto max-h-64 border border-border rounded-xl shadow-medium"
          />
        </div>
      </div>
    {/if}
  </div>
  
  {#if clipImageUrl}
    <!-- 模式选择 -->
    <div class="mb-4">
      <label for="clipMode" class="label">反推模式</label>
      <select
        id="clipMode"
        bind:value={clipMode}
        class="input"
        disabled={clipInterrogating}
      >
        <option value="fast">⚡ 快速模式 (Fast)</option>
        <option value="classic">🎯 经典模式 (Classic)</option>
        <option value="negative">🚫 负面Prompt (Negative)</option>
      </select>
      <div class="mt-2 p-3 bg-surface/50 rounded-lg border border-border">
        <p class="text-xs text-text-secondary">
          {#if clipMode === 'fast'}
            <span class="font-semibold text-text-primary">⚡ 快速模式：</span>使用BLIP快速生成图像描述，然后通过CLIP进行优化，速度快但可能不够详细。
          {:else if clipMode === 'classic'}
            <span class="font-semibold text-text-primary">🎯 经典模式：</span>生成更详细和准确的Prompt描述，但处理时间较长，适合需要精确描述的场景。
          {:else}
            <span class="font-semibold text-text-primary">🚫 负面Prompt：</span>专门生成负面提示词，用于排除不想要的元素和特征。
          {/if}
        </p>
      </div>
    </div>
    
    <!-- 反推按钮 -->
    <button
      on:click={performCLIPInterrogation}
      disabled={clipInterrogating}
      class="btn-primary w-full mb-4 relative overflow-hidden disabled:opacity-70"
    >
      {#if clipInterrogating}
        <span class="flex items-center justify-center gap-2">
          <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span>正在分析图像...</span>
        </span>
      {:else}
        <span>🚀 开始反推</span>
      {/if}
    </button>
  {/if}
  
  <!-- 错误提示 -->
  {#if clipError}
    <div class="bg-danger/20 border border-danger/30 text-danger p-4 rounded-xl text-sm mb-4">
      <div class="flex items-start gap-2">
        <span class="text-lg">⚠️</span>
        <div class="flex-1">
          <p class="font-semibold mb-1">反推失败</p>
          <p>{clipError}</p>
        </div>
        <button
          on:click={() => clipError = ''}
          class="btn-ghost text-xs px-2 py-1"
        >
          ✕
        </button>
      </div>
    </div>
  {/if}
  
  <!-- 结果显示 -->
  {#if clipResult}
    <div class="space-y-4 bg-surface/50 p-4 rounded-xl border border-border">
      <div class="flex items-center justify-between">
        <h4 class="text-sm font-semibold text-text-primary flex items-center gap-2">
          <span>✨</span>
          <span>反推结果</span>
        </h4>
        <span class="text-xs text-text-tertiary px-2 py-1 bg-surface rounded-lg border border-border">
          模式: {clipResult.mode === 'fast' ? '⚡ 快速' : clipResult.mode === 'classic' ? '🎯 经典' : '🚫 负面'}
        </span>
      </div>
      
      <!-- Prompt -->
      <div class="bg-white/5 p-3 rounded-lg border border-border">
        <div class="flex justify-between items-center mb-2">
          <span class="label mb-0 text-xs font-semibold">Prompt</span>
          <div class="flex gap-2">
            <button
              on:click={copyPrompt}
              class="btn-ghost text-xs px-2 py-1 hover:bg-surface"
              title="复制Prompt"
            >
              📋 复制
            </button>
            <button
              on:click={applyPrompt}
              class="btn-success text-xs px-2 py-1"
              title="应用到参数"
            >
              ✓ 应用
            </button>
          </div>
        </div>
        <textarea
          value={clipResult.prompt}
          readonly
          class="input-textarea font-mono text-sm bg-transparent resize-none"
          rows="4"
          aria-label="Prompt"
        ></textarea>
      </div>
      
      <!-- Negative Prompt -->
      <div class="bg-white/5 p-3 rounded-lg border border-border">
        <div class="flex justify-between items-center mb-2">
          <span class="label mb-0 text-xs font-semibold">Negative Prompt</span>
          <button
            on:click={copyNegativePrompt}
            class="btn-ghost text-xs px-2 py-1 hover:bg-surface"
            title="复制Negative Prompt"
          >
            📋 复制
          </button>
        </div>
        <textarea
          value={clipResult.negative_prompt}
          readonly
          class="input-textarea font-mono text-sm bg-transparent resize-none"
          rows="3"
          aria-label="Negative Prompt"
        ></textarea>
      </div>
      
      <!-- 风格标签 -->
      {#if clipResult.flavors && clipResult.flavors.length > 0}
        <div class="bg-white/5 p-3 rounded-lg border border-border">
          <span class="label mb-2 text-xs font-semibold">🎨 风格标签</span>
          <div class="flex flex-wrap gap-2">
            {#each clipResult.flavors as flavor}
              <span class="px-3 py-1 bg-primary/10 border border-primary/30 text-primary rounded-full text-xs font-medium">
                {flavor}
              </span>
            {/each}
          </div>
        </div>
      {/if}
      
      <!-- 操作提示 -->
      <div class="text-xs text-text-tertiary p-3 bg-surface/50 rounded-lg border border-border">
        <p class="font-semibold mb-1">💡 使用提示：</p>
        <ul class="list-disc list-inside space-y-1">
          <li>点击"应用"按钮将Prompt和Negative Prompt应用到参数</li>
          <li>点击"复制"按钮可以单独复制Prompt或Negative Prompt</li>
          <li>风格标签显示了图像的主要风格特征</li>
        </ul>
      </div>
    </div>
  {/if}
</div>

<style>
  /* 自定义样式 */
  .card-compact {
    @apply bg-surface/80 backdrop-blur-sm p-6 rounded-2xl border border-border shadow-large;
  }
</style>
