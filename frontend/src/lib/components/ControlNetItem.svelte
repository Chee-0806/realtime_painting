<script lang="ts" context="module">
  // ControlNet配置接口
  export interface ControlNetConfig {
    id: string;
    type: string;
    image: string;
    weight: number;
    guidanceStart: number;
    guidanceEnd: number;
  }
</script>

<script lang="ts">
  import { setError, clearError, ErrorType } from '$lib/store';
  
  // Props
  export let config: ControlNetConfig;
  export let index: number;
  export let availableTypes: string[] = ['canny', 'depth', 'pose', 'scribble', 'lineart', 'normal', 'semantic'];
  export let onRemove: (id: string) => void = () => {};
  export let onUpdate: (id: string, field: keyof ControlNetConfig, value: any) => void = () => {};
  
  // 处理图像上传
  function handleImageUpload(event: Event) {
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
      onUpdate(config.id, 'image', result);
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
  
  // 处理类型变化
  function handleTypeChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    onUpdate(config.id, 'type', target.value);
  }
  
  // 处理权重变化
  function handleWeightChange(event: Event) {
    const target = event.target as HTMLInputElement;
    onUpdate(config.id, 'weight', parseFloat(target.value));
  }
  
  // 处理引导开始变化
  function handleGuidanceStartChange(event: Event) {
    const target = event.target as HTMLInputElement;
    onUpdate(config.id, 'guidanceStart', parseFloat(target.value));
  }
  
  // 处理引导结束变化
  function handleGuidanceEndChange(event: Event) {
    const target = event.target as HTMLInputElement;
    onUpdate(config.id, 'guidanceEnd', parseFloat(target.value));
  }
  
  // 处理删除
  function handleRemove() {
    onRemove(config.id);
  }
</script>

<div class="controlnet-item">
  <div class="header">
    <h4 class="title">ControlNet {index + 1}</h4>
    <button
      on:click={handleRemove}
      class="btn-remove"
      title="删除此ControlNet"
    >
      ✕
    </button>
  </div>
  
  <!-- 类型选择 -->
  <div class="field">
    <label class="label">类型</label>
    <select
      value={config.type}
      on:change={handleTypeChange}
      class="input"
    >
      {#each availableTypes as type}
        <option value={type}>{type}</option>
      {/each}
    </select>
  </div>
  
  <!-- 图像上传 -->
  <div class="field">
    <label class="label">控制图像</label>
    <input
      type="file"
      accept="image/*"
      on:change={handleImageUpload}
      class="input"
    />
    {#if config.image}
      <div class="image-preview">
        <img
          src={config.image}
          alt="ControlNet预览"
          class="preview-img"
        />
      </div>
    {/if}
  </div>
  
  <!-- 权重滑块 -->
  <div class="field">
    <label class="label">
      权重: {config.weight.toFixed(2)}
    </label>
    <input
      type="range"
      min="0"
      max="2"
      step="0.1"
      value={config.weight}
      on:input={handleWeightChange}
      class="slider"
    />
    <div class="slider-labels">
      <span>0.0</span>
      <span>1.0</span>
      <span>2.0</span>
    </div>
  </div>
  
  <!-- 引导范围 -->
  <div class="guidance-range">
    <div class="field">
      <label class="label">
        引导开始: {config.guidanceStart.toFixed(2)}
      </label>
      <input
        type="range"
        min="0"
        max="1"
        step="0.05"
        value={config.guidanceStart}
        on:input={handleGuidanceStartChange}
        class="slider"
      />
    </div>
    <div class="field">
      <label class="label">
        引导结束: {config.guidanceEnd.toFixed(2)}
      </label>
      <input
        type="range"
        min="0"
        max="1"
        step="0.05"
        value={config.guidanceEnd}
        on:input={handleGuidanceEndChange}
        class="slider"
      />
    </div>
  </div>
</div>

<style>
  .controlnet-item {
    padding: 1rem;
    background: var(--color-surface);
    border-radius: 0.75rem;
    border: 1px solid var(--color-border);
  }
  
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.75rem;
  }
  
  .title {
    font-size: 0.9375rem;
    font-weight: 600;
    color: var(--color-text-primary);
    margin: 0;
  }
  
  .btn-remove {
    padding: 0.25rem 0.5rem;
    background: transparent;
    border: none;
    border-radius: 0.25rem;
    font-size: 1rem;
    color: var(--color-error);
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .btn-remove:hover {
    background: rgba(var(--color-error-rgb), 0.1);
  }
  
  .field {
    margin-bottom: 0.75rem;
  }
  
  .field:last-child {
    margin-bottom: 0;
  }
  
  .label {
    display: block;
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--color-text-secondary);
    margin-bottom: 0.375rem;
  }
  
  .input {
    width: 100%;
    padding: 0.5rem 0.75rem;
    background: var(--color-background);
    border: 1px solid var(--color-border);
    border-radius: 0.5rem;
    color: var(--color-text-primary);
    font-size: 0.875rem;
    transition: all 0.2s;
  }
  
  .input:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(var(--color-primary-rgb), 0.1);
  }
  
  .image-preview {
    margin-top: 0.5rem;
  }
  
  .preview-img {
    max-width: 100%;
    height: auto;
    max-height: 8rem;
    border-radius: 0.5rem;
    border: 1px solid var(--color-border);
  }
  
  .slider {
    width: 100%;
    height: 0.5rem;
    background: var(--color-background);
    border-radius: 0.25rem;
    outline: none;
    -webkit-appearance: none;
  }
  
  .slider::-webkit-slider-thumb {
    appearance: none;
    -webkit-appearance: none;
    width: 1rem;
    height: 1rem;
    background: var(--color-primary);
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .slider::-webkit-slider-thumb:hover {
    transform: scale(1.1);
  }
  
  .slider::-moz-range-thumb {
    width: 1rem;
    height: 1rem;
    background: var(--color-primary);
    border-radius: 50%;
    cursor: pointer;
    border: none;
    transition: all 0.2s;
  }
  
  .slider::-moz-range-thumb:hover {
    transform: scale(1.1);
  }
  
  .slider-labels {
    display: flex;
    justify-content: space-between;
    font-size: 0.6875rem;
    color: var(--color-text-secondary);
    margin-top: 0.25rem;
  }
  
  .guidance-range {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
  }
  
  @media (max-width: 640px) {
    .guidance-range {
      grid-template-columns: 1fr;
    }
  }
</style>
