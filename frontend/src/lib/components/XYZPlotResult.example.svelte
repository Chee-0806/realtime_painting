<script lang="ts">
  /**
   * XYZPlotResult 组件使用示例
   * 
   * 展示如何使用 XYZPlotResult 组件显示 XYZ Plot 的结果
   */
  
  import XYZPlotResult from './XYZPlotResult.svelte';
  
  // 示例数据：2x3的网格（2个X值 × 3个Y值）
  const exampleResults2D = {
    images: [
      'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
      'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
      'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA+Y6wLgAAAABJRU5ErkJggg==',
      'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFhAJ/wlseZQAAAABJRU5ErkJggg==',
      'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==',
      'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP4/5+hHgAGgwJ/lK3Q6wAAAABJRU5ErkJggg=='
    ],
    xAxis: {
      type: 'steps',
      values: [20, 30]
    },
    yAxis: {
      type: 'cfg_scale',
      values: [5.0, 7.5, 10.0]
    }
  };
  
  // 示例数据：带Z轴的3D网格（2个X值 × 2个Y值 × 2个Z值）
  const exampleResults3D = {
    images: [
      // Z=42的4张图像
      'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
      'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
      'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA+Y6wLgAAAABJRU5ErkJggg==',
      'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFhAJ/wlseZQAAAABJRU5ErkJggg==',
      // Z=123的4张图像
      'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==',
      'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP4/5+hHgAGgwJ/lK3Q6wAAAABJRU5ErkJggg==',
      'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
      'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
    ],
    xAxis: {
      type: 'steps',
      values: [20, 30]
    },
    yAxis: {
      type: 'cfg_scale',
      values: [5.0, 7.5]
    },
    zAxis: {
      type: 'seed',
      values: [42, 123]
    }
  };
  
  let currentExample: 'none' | '2d' | '3d' = 'none';
  let results: typeof exampleResults2D | null = null;
  
  function show2DExample() {
    currentExample = '2d';
    results = exampleResults2D;
  }
  
  function show3DExample() {
    currentExample = '3d';
    results = exampleResults3D;
  }
  
  function clearExample() {
    currentExample = 'none';
    results = null;
  }
</script>

<div class="max-w-6xl mx-auto p-6 space-y-6">
  <div class="space-y-4">
    <h1 class="text-2xl font-bold text-text-primary">XYZPlotResult 组件示例</h1>
    
    <div class="p-4 bg-surface-elevated border border-border rounded-lg">
      <h2 class="text-lg font-semibold text-text-primary mb-3">功能说明</h2>
      <ul class="space-y-2 text-sm text-text-primary">
        <li>✅ <strong>网格布局</strong>: 以表格形式展示所有参数组合的生成结果</li>
        <li>✅ <strong>参数标签</strong>: 清晰显示X轴、Y轴和Z轴的参数类型和值</li>
        <li>✅ <strong>图像预览</strong>: 点击任意图像可放大查看，显示对应的参数信息</li>
        <li>✅ <strong>批量下载</strong>: 一键下载所有生成的图像，文件名包含参数信息</li>
        <li>✅ <strong>Z轴支持</strong>: 支持3D网格，可通过Z轴选择器切换不同的Z值</li>
        <li>✅ <strong>键盘快捷键</strong>: 按ESC键关闭预览窗口</li>
      </ul>
    </div>
    
    <div class="p-4 bg-surface-elevated border border-border rounded-lg">
      <h2 class="text-lg font-semibold text-text-primary mb-3">示例选择</h2>
      <div class="flex gap-3">
        <button
          on:click={show2DExample}
          class="px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg transition-colors"
        >
          显示2D网格示例 (2×3)
        </button>
        <button
          on:click={show3DExample}
          class="px-4 py-2 bg-success hover:bg-success/90 text-white rounded-lg transition-colors"
        >
          显示3D网格示例 (2×2×2)
        </button>
        <button
          on:click={clearExample}
          class="px-4 py-2 bg-surface-elevated hover:bg-surface-elevated/80 border border-border text-text-primary rounded-lg transition-colors"
        >
          清除示例
        </button>
      </div>
    </div>
  </div>
  
  <!-- XYZPlotResult 组件 -->
  <div class="p-6 bg-surface border border-border rounded-lg">
    <XYZPlotResult {results} />
  </div>
  
  <!-- 使用说明 -->
  <div class="p-4 bg-info/10 border border-info/30 rounded-lg">
    <h2 class="text-lg font-semibold text-text-primary mb-3">💡 使用说明</h2>
    <div class="space-y-2 text-sm text-text-primary">
      <p><strong>基本用法:</strong></p>
      <pre class="p-3 bg-surface rounded text-xs overflow-x-auto"><code>{`<script>
  import XYZPlotResult from '$lib/components/XYZPlotResult.svelte';
  
  let results = {
    images: ['data:image/png;base64,...', ...],
    xAxis: { type: 'steps', values: [20, 30, 40] },
    yAxis: { type: 'cfg_scale', values: [5.0, 7.5, 10.0] },
    zAxis: { type: 'seed', values: [42, 123] } // 可选
  };
</script>

<XYZPlotResult {results} />`}</code></pre>
      
      <p class="mt-4"><strong>数据格式:</strong></p>
      <ul class="list-disc list-inside space-y-1 ml-4">
        <li><code>images</code>: Base64编码的图像数组，按照 Z → Y → X 的顺序排列</li>
        <li><code>xAxis</code>: X轴配置，包含参数类型和值数组</li>
        <li><code>yAxis</code>: Y轴配置，包含参数类型和值数组</li>
        <li><code>zAxis</code>: Z轴配置（可选），包含参数类型和值数组</li>
      </ul>
      
      <p class="mt-4"><strong>支持的参数类型:</strong></p>
      <ul class="list-disc list-inside space-y-1 ml-4">
        <li><code>steps</code>: 步数</li>
        <li><code>cfg_scale</code>: CFG引导强度</li>
        <li><code>denoising_strength</code>: 降噪强度</li>
        <li><code>seed</code>: 随机种子</li>
        <li><code>sampler</code>: 采样器</li>
        <li><code>scheduler</code>: 调度器</li>
        <li><code>width</code>: 宽度</li>
        <li><code>height</code>: 高度</li>
      </ul>
    </div>
  </div>
</div>

<style>
  code {
    font-family: 'Courier New', monospace;
    background-color: rgba(0, 0, 0, 0.1);
    padding: 0.125rem 0.25rem;
    border-radius: 0.25rem;
  }
</style>
