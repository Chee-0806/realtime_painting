<script lang="ts">
  import { setError, clearError, ErrorType } from '$lib/store';
  import { 
    parseParameterValues, 
    validateGridConfiguration,
    getExampleValues,
    type ParsedValues 
  } from '$lib/utils/xyz-parser';
  import XYZPlotResult from './XYZPlotResult.svelte';
  
  // 可用的参数类型
  const parameterTypes = [
    { value: 'steps', label: '步数 (Steps)' },
    { value: 'cfg_scale', label: '引导强度 (CFG Scale)' },
    { value: 'denoising_strength', label: '降噪强度 (Denoising)' },
    { value: 'seed', label: '种子 (Seed)' },
    { value: 'sampler', label: '采样器 (Sampler)' },
    { value: 'scheduler', label: '调度器 (Scheduler)' },
    { value: 'width', label: '宽度 (Width)' },
    { value: 'height', label: '高度 (Height)' }
  ];
  
  // X轴配置
  let xAxisType: string = 'steps';
  let xAxisValues: string = '20, 30, 40, 50';
  
  // Y轴配置
  let yAxisType: string = 'cfg_scale';
  let yAxisValues: string = '5.0-10.0:2.5';
  
  // Z轴配置（可选）
  let enableZAxis: boolean = false;
  let zAxisType: string = 'seed';
  let zAxisValues: string = '42, 123, 456';
  
  // 基础Prompt配置
  let basePrompt: string = '';
  let baseNegativePrompt: string = '';
  
  // UI状态
  let loading: boolean = false;
  let progress: number = 0;
  let progressMessage: string = '';
  
  // 结果数据
  let results: {
    images: string[];
    xAxis: { type: string; values: (number | string)[] };
    yAxis: { type: string; values: (number | string)[] };
    zAxis?: { type: string; values: (number | string)[] };
  } | null = null;
  
  // 解析结果
  $: xParsed = parseParameterValues(xAxisValues, xAxisType);
  $: yParsed = parseParameterValues(yAxisValues, yAxisType);
  $: zParsed = enableZAxis ? parseParameterValues(zAxisValues, zAxisType) : { values: [], count: 0, isValid: true };
  
  // 计算预计生成数量
  $: estimatedCount = xParsed.count * yParsed.count * (enableZAxis ? zParsed.count : 1);
  
  // 验证配置
  $: validationResult = validateGridConfiguration(
    xAxisValues,
    yAxisValues,
    enableZAxis ? zAxisValues : null,
    100
  );
  
  function validateConfiguration(): boolean {
    // 验证X轴解析
    if (!xParsed.isValid) {
      setError({
        type: ErrorType.VALIDATION,
        message: 'X轴参数解析失败',
        details: xParsed.error,
        recoverable: true,
        suggestions: [
          '检查参数值格式是否正确',
          `示例: ${getExampleValues(xAxisType)}`
        ]
      });
      return false;
    }
    
    // 验证Y轴解析
    if (!yParsed.isValid) {
      setError({
        type: ErrorType.VALIDATION,
        message: 'Y轴参数解析失败',
        details: yParsed.error,
        recoverable: true,
        suggestions: [
          '检查参数值格式是否正确',
          `示例: ${getExampleValues(yAxisType)}`
        ]
      });
      return false;
    }
    
    // 验证Z轴解析（如果启用）
    if (enableZAxis && !zParsed.isValid) {
      setError({
        type: ErrorType.VALIDATION,
        message: 'Z轴参数解析失败',
        details: zParsed.error,
        recoverable: true,
        suggestions: [
          '检查参数值格式是否正确',
          `示例: ${getExampleValues(zAxisType)}`,
          '或禁用Z轴'
        ]
      });
      return false;
    }
    
    // 验证Prompt
    if (!basePrompt.trim()) {
      setError({
        type: ErrorType.VALIDATION,
        message: '请输入基础Prompt',
        recoverable: true,
        suggestions: ['Prompt用于所有参数组合的图像生成']
      });
      return false;
    }
    
    // 使用统一的验证函数
    if (!validationResult.isValid) {
      setError({
        type: ErrorType.VALIDATION,
        message: '网格配置验证失败',
        details: validationResult.error,
        recoverable: true,
        suggestions: [
          '减少参数值数量',
          '禁用Z轴',
          '增大范围表达式的步长'
        ]
      });
      return false;
    }
    
    clearError();
    return true;
  }
  
  async function startXYZPlot() {
    if (!validateConfiguration()) {
      return;
    }
    
    loading = true;
    progress = 0;
    progressMessage = '准备生成...';
    results = null;
    
    try {
      const requestBody = {
        x_axis: {
          type: xAxisType,
          values: xParsed.values
        },
        y_axis: {
          type: yAxisType,
          values: yParsed.values
        },
        z_axis: enableZAxis ? {
          type: zAxisType,
          values: zParsed.values
        } : null,
        base_prompt: basePrompt,
        base_negative_prompt: baseNegativePrompt
      };
      
      progressMessage = '正在生成参数网格...';
      
      const response = await fetch('/api/xyz-plot', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP错误: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        progressMessage = '生成完成！';
        progress = 100;
        
        // 构建结果数据
        const images: string[] = [];
        const successCount = data.results.filter((r: any) => r.success).length;
        
        // 按照网格顺序排列图像
        for (const result of data.results) {
          if (result.success && result.image) {
            images.push(result.image);
          } else {
            // 如果生成失败，使用占位图
            images.push('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNTEyIiBoZWlnaHQ9IjUxMiIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNTEyIiBoZWlnaHQ9IjUxMiIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LXNpemU9IjI0IiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIj7nlJ/miJDlpLHotKU8L3RleHQ+PC9zdmc+');
          }
        }
        
        results = {
          images,
          xAxis: {
            type: data.x_axis.type,
            values: data.x_axis.values
          },
          yAxis: {
            type: data.y_axis.type,
            values: data.y_axis.values
          },
          zAxis: data.z_axis ? {
            type: data.z_axis.type,
            values: data.z_axis.values
          } : undefined
        };
        
        clearError();
        
        // 显示成功消息
        console.log(`XYZ Plot生成成功: ${successCount}/${data.grid_size} 张图像`);
      } else {
        throw new Error(data.message || '生成失败');
      }
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : String(e);
      
      setError({
        type: ErrorType.API,
        message: 'XYZ Plot生成失败',
        details: errorMessage,
        recoverable: true,
        suggestions: [
          '检查参数配置是否正确',
          '确认后端服务正常运行',
          '查看后端日志获取详细信息'
        ]
      });
      console.error('XYZ Plot失败:', e);
    } finally {
      loading = false;
      if (progress < 100) {
        progress = 0;
        progressMessage = '';
      }
    }
  }
  
  function reset() {
    xAxisType = 'steps';
    xAxisValues = '20, 30, 40, 50';
    yAxisType = 'cfg_scale';
    yAxisValues = '5.0-10.0:2.5';
    enableZAxis = false;
    zAxisType = 'seed';
    zAxisValues = '42, 123, 456';
    basePrompt = '';
    baseNegativePrompt = '';
    clearError();
  }
  
  // 当参数类型改变时，更新示例值
  function updateExampleValues(axis: 'x' | 'y' | 'z') {
    if (axis === 'x') {
      xAxisValues = getExampleValues(xAxisType);
    } else if (axis === 'y') {
      yAxisValues = getExampleValues(yAxisType);
    } else if (axis === 'z') {
      zAxisValues = getExampleValues(zAxisType);
    }
  }
</script>


<div class="space-y-4">
  <div class="flex items-center justify-between mb-4">
    <h3 class="text-lg font-semibold text-text-primary">📊 XYZ Plot 参数对比</h3>
    <button 
      on:click={reset}
      class="px-3 py-1 text-sm bg-surface-elevated hover:bg-surface-elevated/80 border border-border rounded-lg text-text-secondary transition-colors"
    >
      重置
    </button>
  </div>
  
  <div class="p-3 bg-info/10 border border-info/30 rounded-lg">
    <p class="text-sm text-text-primary">
      💡 <strong>XYZ Plot</strong> 可以生成参数网格对比图，帮助你找到最佳参数组合。
    </p>
  </div>
  
  <!-- 基础Prompt配置 -->
  <div class="space-y-4 p-4 bg-surface-elevated border border-border rounded-lg">
    <h4 class="text-sm font-semibold text-text-primary">基础配置</h4>
    
    <div class="space-y-2">
      <label for="xyz-base-prompt" class="block text-sm font-medium text-text-primary">
        基础Prompt
      </label>
      <textarea
        id="xyz-base-prompt"
        bind:value={basePrompt}
        rows="3"
        class="w-full px-3 py-2 bg-surface border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary resize-none"
        placeholder="输入基础Prompt，将应用于所有参数组合..."
      ></textarea>
    </div>
    
    <div class="space-y-2">
      <label for="xyz-base-negative" class="block text-sm font-medium text-text-primary">
        基础Negative Prompt
      </label>
      <textarea
        id="xyz-base-negative"
        bind:value={baseNegativePrompt}
        rows="2"
        class="w-full px-3 py-2 bg-surface border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary resize-none"
        placeholder="输入不想要的内容..."
      ></textarea>
    </div>
  </div>
  
  <!-- X轴配置 -->
  <div class="space-y-3 p-4 bg-surface-elevated border border-border rounded-lg">
    <h4 class="text-sm font-semibold text-text-primary">X轴参数</h4>
    
    <div class="space-y-2">
      <label for="x-axis-type" class="block text-sm font-medium text-text-primary">
        参数类型
      </label>
      <select
        id="x-axis-type"
        bind:value={xAxisType}
        class="w-full px-3 py-2 bg-surface border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary"
      >
        {#each parameterTypes as param}
          <option value={param.value}>{param.label}</option>
        {/each}
      </select>
    </div>
    
    <div class="space-y-2">
      <label for="x-axis-values" class="block text-sm font-medium text-text-primary">
        参数值
      </label>
      <input
        id="x-axis-values"
        type="text"
        bind:value={xAxisValues}
        class="w-full px-3 py-2 bg-surface border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary"
        placeholder={getExampleValues(xAxisType)}
      />
      <div class="flex items-center justify-between text-xs">
        {#if xParsed.isValid}
          <span class="text-success">✓ 已解析 {xParsed.count} 个值</span>
        {:else}
          <span class="text-error">✗ {xParsed.error}</span>
        {/if}
        <button
          on:click={() => updateExampleValues('x')}
          class="text-primary hover:underline"
        >
          使用示例
        </button>
      </div>
      <p class="text-xs text-text-secondary">
        💡 支持格式: "1, 2, 3" 或 "1.0-5.0:1.0" 或 "1-5, 步长1"
      </p>
    </div>
  </div>
  
  <!-- Y轴配置 -->
  <div class="space-y-3 p-4 bg-surface-elevated border border-border rounded-lg">
    <h4 class="text-sm font-semibold text-text-primary">Y轴参数</h4>
    
    <div class="space-y-2">
      <label for="y-axis-type" class="block text-sm font-medium text-text-primary">
        参数类型
      </label>
      <select
        id="y-axis-type"
        bind:value={yAxisType}
        class="w-full px-3 py-2 bg-surface border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary"
      >
        {#each parameterTypes as param}
          <option value={param.value}>{param.label}</option>
        {/each}
      </select>
    </div>
    
    <div class="space-y-2">
      <label for="y-axis-values" class="block text-sm font-medium text-text-primary">
        参数值
      </label>
      <input
        id="y-axis-values"
        type="text"
        bind:value={yAxisValues}
        class="w-full px-3 py-2 bg-surface border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary"
        placeholder={getExampleValues(yAxisType)}
      />
      <div class="flex items-center justify-between text-xs">
        {#if yParsed.isValid}
          <span class="text-success">✓ 已解析 {yParsed.count} 个值</span>
        {:else}
          <span class="text-error">✗ {yParsed.error}</span>
        {/if}
        <button
          on:click={() => updateExampleValues('y')}
          class="text-primary hover:underline"
        >
          使用示例
        </button>
      </div>
      <p class="text-xs text-text-secondary">
        💡 支持格式: "1, 2, 3" 或 "1.0-5.0:1.0" 或 "1-5, 步长1"
      </p>
    </div>
  </div>
  
  <!-- Z轴配置（可选） -->
  <div class="space-y-3 p-4 bg-surface-elevated border border-border rounded-lg">
    <div class="flex items-center justify-between">
      <h4 class="text-sm font-semibold text-text-primary">Z轴参数 <span class="text-text-secondary text-xs">(可选)</span></h4>
      <label class="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          bind:checked={enableZAxis}
          class="w-4 h-4 text-primary bg-surface border-border rounded focus:ring-2 focus:ring-primary"
        />
        <span class="text-sm text-text-primary">启用Z轴</span>
      </label>
    </div>
    
    {#if enableZAxis}
      <div class="space-y-2">
        <label for="z-axis-type" class="block text-sm font-medium text-text-primary">
          参数类型
        </label>
        <select
          id="z-axis-type"
          bind:value={zAxisType}
          class="w-full px-3 py-2 bg-surface border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary"
        >
          {#each parameterTypes as param}
            <option value={param.value}>{param.label}</option>
          {/each}
        </select>
      </div>
      
      <div class="space-y-2">
        <label for="z-axis-values" class="block text-sm font-medium text-text-primary">
          参数值
        </label>
        <input
          id="z-axis-values"
          type="text"
          bind:value={zAxisValues}
          class="w-full px-3 py-2 bg-surface border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary"
          placeholder={getExampleValues(zAxisType)}
        />
        <div class="flex items-center justify-between text-xs">
          {#if zParsed.isValid}
            <span class="text-success">✓ 已解析 {zParsed.count} 个值</span>
          {:else}
            <span class="text-error">✗ {zParsed.error}</span>
          {/if}
          <button
            on:click={() => updateExampleValues('z')}
            class="text-primary hover:underline"
          >
            使用示例
          </button>
        </div>
        <p class="text-xs text-text-secondary">
          💡 支持格式: "1, 2, 3" 或 "1.0-5.0:1.0" 或 "1-5, 步长1"
        </p>
      </div>
    {/if}
  </div>
  
  <!-- 预计生成数量 -->
  <div class="p-4 bg-primary/10 border border-primary/30 rounded-lg">
    <div class="flex items-center justify-between">
      <div>
        <h4 class="text-sm font-semibold text-text-primary">预计生成数量</h4>
        <p class="text-xs text-text-secondary mt-1">
          {xParsed.count} × {yParsed.count}
          {#if enableZAxis}
            × {zParsed.count}
          {/if}
          = {estimatedCount} 张图像
        </p>
      </div>
      <div class="text-3xl font-bold text-primary">
        {estimatedCount}
      </div>
    </div>
    
    {#if estimatedCount > 50}
      <div class="mt-3 p-2 bg-warning/10 border border-warning/30 rounded">
        <p class="text-xs text-warning">
          ⚠️ 生成数量较多，可能需要较长时间
        </p>
      </div>
    {/if}
  </div>
  
  <!-- 操作按钮 -->
  <div class="flex gap-3">
    <button
      on:click={startXYZPlot}
      disabled={loading || !basePrompt.trim() || estimatedCount < 2}
      class="flex-1 px-4 py-3 bg-success hover:bg-success/90 disabled:bg-surface-elevated disabled:text-text-secondary text-white rounded-lg transition-colors font-medium disabled:cursor-not-allowed"
    >
      {#if loading}
        <span class="flex items-center justify-center gap-2">
          <div class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
          生成中...
        </span>
      {:else}
        开始生成网格
      {/if}
    </button>
  </div>
  
  <!-- 进度显示 -->
  {#if loading && progressMessage}
    <div class="p-4 bg-primary/10 border border-primary/30 rounded-lg">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium text-text-primary">{progressMessage}</span>
        {#if progress > 0}
          <span class="text-sm text-text-secondary">{progress.toFixed(0)}%</span>
        {/if}
      </div>
      {#if progress > 0}
        <div class="w-full bg-surface-elevated rounded-full h-2 overflow-hidden">
          <div
            class="bg-primary h-full transition-all duration-300"
            style="width: {progress}%"
          ></div>
        </div>
      {/if}
    </div>
  {/if}
</div>

<!-- 结果展示 -->
{#if results}
  <div class="mt-6">
    <XYZPlotResult {results} />
  </div>
{/if}

<style>
  input[type="checkbox"] {
    cursor: pointer;
  }
</style>
