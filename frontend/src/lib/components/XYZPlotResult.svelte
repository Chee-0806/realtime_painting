<script lang="ts">
  /**
   * XYZ Plot 结果展示组件
   * 
   * 功能:
   * - 网格布局展示生成的图像
   * - 参数标签显示
   * - 图像点击放大预览
   * - 批量下载功能
   */
  
  export let results: {
    images: string[];  // Base64图像数组
    xAxis: { type: string; values: (number | string)[] };
    yAxis: { type: string; values: (number | string)[] };
    zAxis?: { type: string; values: (number | string)[] };
  } | null = null;
  
  // 参数类型的中文标签映射
  const parameterLabels: Record<string, string> = {
    steps: '步数',
    cfg_scale: 'CFG',
    denoising_strength: '降噪',
    seed: '种子',
    sampler: '采样器',
    scheduler: '调度器',
    width: '宽度',
    height: '高度'
  };
  
  // 预览状态
  let previewImage: string | null = null;
  let previewParams: { x: string; y: string; z?: string } | null = null;
  
  // 下载状态
  let downloading = false;
  
  /**
   * 获取参数的显示标签
   */
  function getParameterLabel(type: string): string {
    return parameterLabels[type] || type;
  }
  
  /**
   * 格式化参数值
   */
  function formatValue(value: number | string): string {
    if (typeof value === 'number') {
      // 如果是整数，不显示小数点
      return Number.isInteger(value) ? value.toString() : value.toFixed(2);
    }
    return String(value);
  }
  
  /**
   * 获取图像索引
   */
  function getImageIndex(xIndex: number, yIndex: number, zIndex: number = 0): number {
    if (!results) return -1;
    
    const xCount = results.xAxis.values.length;
    const yCount = results.yAxis.values.length;
    
    // 计算索引: z * (x * y) + y * x + x
    return zIndex * (xCount * yCount) + yIndex * xCount + xIndex;
  }
  
  /**
   * 打开图像预览
   */
  function openPreview(xIndex: number, yIndex: number, zIndex: number = 0) {
    if (!results) return;
    
    const imageIndex = getImageIndex(xIndex, yIndex, zIndex);
    if (imageIndex >= 0 && imageIndex < results.images.length) {
      previewImage = results.images[imageIndex];
      previewParams = {
        x: `${getParameterLabel(results.xAxis.type)}: ${formatValue(results.xAxis.values[xIndex])}`,
        y: `${getParameterLabel(results.yAxis.type)}: ${formatValue(results.yAxis.values[yIndex])}`,
        z: results.zAxis ? `${getParameterLabel(results.zAxis.type)}: ${formatValue(results.zAxis.values[zIndex])}` : undefined
      };
    }
  }
  
  /**
   * 关闭预览
   */
  function closePreview() {
    previewImage = null;
    previewParams = null;
  }
  
  /**
   * 下载单张图像
   */
  function downloadImage(imageData: string, filename: string) {
    const link = document.createElement('a');
    link.href = imageData;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
  
  /**
   * 批量下载所有图像
   */
  async function downloadAll() {
    if (!results || downloading) return;
    
    downloading = true;
    
    try {
      // 创建一个延迟函数，避免浏览器阻止多个下载
      const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
      
      for (let zIndex = 0; zIndex < (results.zAxis?.values.length || 1); zIndex++) {
        for (let yIndex = 0; yIndex < results.yAxis.values.length; yIndex++) {
          for (let xIndex = 0; xIndex < results.xAxis.values.length; xIndex++) {
            const imageIndex = getImageIndex(xIndex, yIndex, zIndex);
            if (imageIndex >= 0 && imageIndex < results.images.length) {
              const xValue = formatValue(results.xAxis.values[xIndex]);
              const yValue = formatValue(results.yAxis.values[yIndex]);
              const zValue = results.zAxis ? formatValue(results.zAxis.values[zIndex]) : '';
              
              const filename = results.zAxis
                ? `xyz_${results.xAxis.type}_${xValue}_${results.yAxis.type}_${yValue}_${results.zAxis.type}_${zValue}.png`
                : `xy_${results.xAxis.type}_${xValue}_${results.yAxis.type}_${yValue}.png`;
              
              downloadImage(results.images[imageIndex], filename);
              
              // 延迟100ms，避免浏览器阻止
              await delay(100);
            }
          }
        }
      }
    } catch (e) {
      console.error('批量下载失败:', e);
      alert('批量下载失败，请重试');
    } finally {
      downloading = false;
    }
  }
  
  /**
   * 清除结果
   */
  function clearResults() {
    if (confirm('确定要清除所有结果吗？')) {
      results = null;
    }
  }
  
  // 键盘事件处理
  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape' && previewImage) {
      closePreview();
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

{#if results}
  <div class="space-y-4">
    <!-- 标题和操作栏 -->
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-text-primary">
        📊 XYZ Plot 结果
      </h3>
      <div class="flex gap-2">
        <button
          on:click={downloadAll}
          disabled={downloading}
          class="px-3 py-1.5 text-sm bg-primary hover:bg-primary/90 disabled:bg-surface-elevated disabled:text-text-secondary text-white rounded-lg transition-colors disabled:cursor-not-allowed"
        >
          {#if downloading}
            <span class="flex items-center gap-2">
              <div class="animate-spin h-3 w-3 border-2 border-white border-t-transparent rounded-full"></div>
              下载中...
            </span>
          {:else}
            📥 批量下载
          {/if}
        </button>
        <button
          on:click={clearResults}
          class="px-3 py-1.5 text-sm bg-surface-elevated hover:bg-surface-elevated/80 border border-border rounded-lg text-text-secondary transition-colors"
        >
          🗑️ 清除
        </button>
      </div>
    </div>
    
    <!-- 结果信息 -->
    <div class="p-3 bg-info/10 border border-info/30 rounded-lg">
      <div class="flex items-center gap-4 text-sm text-text-primary">
        <span>
          <strong>X轴:</strong> {getParameterLabel(results.xAxis.type)} ({results.xAxis.values.length}个值)
        </span>
        <span>
          <strong>Y轴:</strong> {getParameterLabel(results.yAxis.type)} ({results.yAxis.values.length}个值)
        </span>
        {#if results.zAxis}
          <span>
            <strong>Z轴:</strong> {getParameterLabel(results.zAxis.type)} ({results.zAxis.values.length}个值)
          </span>
        {/if}
        <span class="ml-auto">
          <strong>总计:</strong> {results.images.length} 张图像
        </span>
      </div>
    </div>
    
    <!-- Z轴选择器（如果有Z轴） -->
    {#if results.zAxis}
      <div class="p-4 bg-surface-elevated border border-border rounded-lg">
        <label class="block text-sm font-medium text-text-primary mb-2">
          {getParameterLabel(results.zAxis.type)} 选择:
        </label>
        <div class="flex flex-wrap gap-2">
          {#each results.zAxis.values as zValue, zIndex}
            <button
              on:click={() => {
                // 滚动到对应的网格
                const element = document.getElementById(`grid-z-${zIndex}`);
                element?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }}
              class="px-3 py-1.5 text-sm bg-surface hover:bg-primary/20 border border-border hover:border-primary rounded-lg text-text-primary transition-colors"
            >
              {formatValue(zValue)}
            </button>
          {/each}
        </div>
      </div>
    {/if}
    
    <!-- 网格展示 -->
    <div class="space-y-8">
      {#each Array(results.zAxis?.values.length || 1) as _, zIndex}
        <div id="grid-z-{zIndex}" class="space-y-3">
          {#if results.zAxis}
            <h4 class="text-md font-semibold text-text-primary">
              {getParameterLabel(results.zAxis.type)}: {formatValue(results.zAxis.values[zIndex])}
            </h4>
          {/if}
          
          <div class="overflow-x-auto">
            <div class="inline-block min-w-full">
              <!-- 网格表格 -->
              <table class="border-collapse">
                <thead>
                  <tr>
                    <th class="p-2 bg-surface-elevated border border-border text-sm font-medium text-text-primary">
                      {getParameterLabel(results.yAxis.type)} \ {getParameterLabel(results.xAxis.type)}
                    </th>
                    {#each results.xAxis.values as xValue}
                      <th class="p-2 bg-surface-elevated border border-border text-sm font-medium text-text-primary min-w-[120px]">
                        {formatValue(xValue)}
                      </th>
                    {/each}
                  </tr>
                </thead>
                <tbody>
                  {#each results.yAxis.values as yValue, yIndex}
                    <tr>
                      <td class="p-2 bg-surface-elevated border border-border text-sm font-medium text-text-primary">
                        {formatValue(yValue)}
                      </td>
                      {#each results.xAxis.values as xValue, xIndex}
                        {@const imageIndex = getImageIndex(xIndex, yIndex, zIndex)}
                        <td class="p-2 border border-border bg-surface">
                          {#if imageIndex >= 0 && imageIndex < results.images.length}
                            <button
                              on:click={() => openPreview(xIndex, yIndex, zIndex)}
                              class="block w-full h-full group relative overflow-hidden rounded-lg hover:ring-2 hover:ring-primary transition-all"
                            >
                              <img
                                src={results.images[imageIndex]}
                                alt="Result {imageIndex}"
                                class="w-full h-auto object-cover transition-transform group-hover:scale-105"
                              />
                              <div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
                                <span class="text-white opacity-0 group-hover:opacity-100 transition-opacity text-2xl">
                                  🔍
                                </span>
                              </div>
                            </button>
                          {:else}
                            <div class="w-full aspect-square bg-surface-elevated flex items-center justify-center text-text-secondary text-xs">
                              加载中...
                            </div>
                          {/if}
                        </td>
                      {/each}
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      {/each}
    </div>
  </div>
{:else}
  <div class="p-8 text-center text-text-secondary">
    <div class="text-4xl mb-3">📊</div>
    <p class="text-sm">暂无结果</p>
    <p class="text-xs mt-1">配置参数并生成网格后，结果将显示在这里</p>
  </div>
{/if}

<!-- 图像预览模态框 -->
{#if previewImage && previewParams}
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
    on:click={closePreview}
    on:keydown={(e) => e.key === 'Escape' && closePreview()}
    role="button"
    tabindex="0"
  >
    <div
      class="relative max-w-4xl max-h-[90vh] bg-surface rounded-lg overflow-hidden"
      on:click|stopPropagation
      on:keydown|stopPropagation
      role="dialog"
      tabindex="-1"
    >
      <!-- 关闭按钮 -->
      <button
        on:click={closePreview}
        class="absolute top-4 right-4 z-10 w-8 h-8 flex items-center justify-center bg-black/50 hover:bg-black/70 text-white rounded-full transition-colors"
        aria-label="关闭预览"
      >
        ✕
      </button>
      
      <!-- 参数信息 -->
      <div class="absolute top-4 left-4 z-10 bg-black/70 text-white px-3 py-2 rounded-lg text-sm space-y-1">
        <div>{previewParams.x}</div>
        <div>{previewParams.y}</div>
        {#if previewParams.z}
          <div>{previewParams.z}</div>
        {/if}
      </div>
      
      <!-- 图像 -->
      <div class="flex items-center justify-center p-4">
        <img
          src={previewImage}
          alt="预览"
          class="max-w-full max-h-[80vh] object-contain"
        />
      </div>
      
      <!-- 下载按钮 -->
      <div class="absolute bottom-4 right-4 z-10">
        <button
          on:click={() => {
            if (previewImage) {
              const filename = `preview_${Date.now()}.png`;
              downloadImage(previewImage, filename);
            }
          }}
          class="px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg transition-colors text-sm"
        >
          📥 下载图像
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  table {
    border-spacing: 0;
  }
  
  th, td {
    text-align: center;
    vertical-align: middle;
  }
  
  /* 确保图像容器有固定的宽高比 */
  td button {
    aspect-ratio: 1;
  }
</style>
