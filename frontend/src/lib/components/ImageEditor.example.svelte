<script lang="ts">
  import ImageEditor from './ImageEditor.svelte';
  import { errorState } from '$lib/store';
  
  let imageEditor: ImageEditor;
  
  function handleExportImage() {
    if (imageEditor) {
      const dataURL = imageEditor.getImageDataURL();
      console.log('导出的图像数据:', dataURL.substring(0, 50) + '...');
      alert('图像已导出到控制台！');
    }
  }
  
  function handleGetCanvas() {
    if (imageEditor) {
      const canvas = imageEditor.getCanvas();
      console.log('Canvas元素:', canvas);
      console.log('Canvas尺寸:', canvas.width, 'x', canvas.height);
      alert(`Canvas尺寸: ${canvas.width}x${canvas.height}`);
    }
  }
</script>

<div class="min-h-screen bg-surface p-8">
  <div class="max-w-4xl mx-auto">
    <h1 class="text-3xl font-bold text-text-primary mb-2">ImageEditor 组件示例</h1>
    <p class="text-text-secondary mb-8">
      演示图像编辑器组件的基础功能：图像加载、预览和Canvas编辑器
    </p>
    
    <!-- 错误处理显示 -->
    {#if $errorState.hasError}
      <div class="mb-6 p-4 bg-danger/10 border border-danger/30 rounded-lg">
        <div class="flex items-start gap-3">
          <span class="text-2xl">⚠️</span>
          <div class="flex-1">
            <h4 class="font-semibold text-danger">{$errorState.message}</h4>
            {#if $errorState.details}
              <p class="text-sm mt-1 text-text-secondary">{$errorState.details}</p>
            {/if}
          </div>
        </div>
      </div>
    {/if}
    
    <!-- ImageEditor组件 -->
    <div class="bg-surface-elevated border border-border rounded-xl p-6 shadow-lg">
      <ImageEditor bind:this={imageEditor} />
    </div>
    
    <!-- 外部操作按钮 -->
    <div class="mt-6 p-4 bg-surface-elevated border border-border rounded-lg">
      <h3 class="text-lg font-semibold text-text-primary mb-4">外部操作示例</h3>
      <div class="flex gap-3">
        <button
          on:click={handleExportImage}
          class="px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg transition-colors"
        >
          导出图像数据
        </button>
        <button
          on:click={handleGetCanvas}
          class="px-4 py-2 bg-secondary hover:bg-secondary/90 text-white rounded-lg transition-colors"
        >
          获取Canvas信息
        </button>
      </div>
      <p class="text-xs text-text-secondary mt-3">
        💡 这些按钮演示了如何从父组件访问ImageEditor的导出方法
      </p>
    </div>
    
    <!-- 使用说明 -->
    <div class="mt-6 p-4 bg-primary/10 border border-primary/30 rounded-lg">
      <h3 class="text-sm font-semibold text-text-primary mb-2">📖 使用说明</h3>
      <ul class="text-sm text-text-secondary space-y-1 list-disc list-inside">
        <li>点击"选择图像"按钮上传图像文件</li>
        <li>图像会自动缩放以适应画布（最大800x600px）</li>
        <li>使用"撤销"和"重做"按钮管理编辑历史（最多20步）</li>
        <li>点击"重置"恢复到原始图像</li>
        <li>点击"下载"保存编辑后的图像</li>
        <li>点击"清空"清除画布并重新开始</li>
      </ul>
    </div>
    
    <!-- 功能特性 -->
    <div class="mt-6 p-4 bg-success/10 border border-success/30 rounded-lg">
      <h3 class="text-sm font-semibold text-text-primary mb-2">✨ 当前功能</h3>
      <div class="grid grid-cols-2 gap-3 text-sm text-text-secondary">
        <div class="flex items-center gap-2">
          <span class="text-success">✓</span>
          <span>图像加载和预览</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-success">✓</span>
          <span>Canvas编辑器</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-success">✓</span>
          <span>撤销/重做功能</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-success">✓</span>
          <span>图像下载</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-success">✓</span>
          <span>历史记录管理</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-success">✓</span>
          <span>导出API</span>
        </div>
      </div>
    </div>
    
    <!-- 待实现功能 -->
    <div class="mt-6 p-4 bg-warning/10 border border-warning/30 rounded-lg">
      <h3 class="text-sm font-semibold text-text-primary mb-2">🚧 待实现功能（后续任务）</h3>
      <div class="grid grid-cols-2 gap-3 text-sm text-text-secondary">
        <div class="flex items-center gap-2">
          <span class="text-warning">○</span>
          <span>裁剪工具</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-warning">○</span>
          <span>旋转工具</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-warning">○</span>
          <span>缩放工具</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-warning">○</span>
          <span>颜色调整</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-warning">○</span>
          <span>滤镜效果</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-warning">○</span>
          <span>前后对比视图</span>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
  }
</style>
