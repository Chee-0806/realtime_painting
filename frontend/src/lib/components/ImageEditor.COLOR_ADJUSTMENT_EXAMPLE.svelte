<script lang="ts">
  import ImageEditor from './ImageEditor.svelte';
  
  let editor: ImageEditor;
  
  // 示例：获取编辑后的图像
  function getEditedImage() {
    if (editor) {
      const dataURL = editor.getImageDataURL();
      console.log('编辑后的图像:', dataURL);
    }
  }
</script>

<div class="container mx-auto p-6 max-w-4xl">
  <div class="mb-6">
    <h1 class="text-2xl font-bold text-text-primary mb-2">
      🎨 图像编辑器 - 颜色调整示例
    </h1>
    <p class="text-text-secondary">
      演示如何使用 ImageEditor 组件的颜色调整功能
    </p>
  </div>
  
  <!-- 使用说明 -->
  <div class="mb-6 p-4 bg-primary/10 border border-primary/30 rounded-lg">
    <h2 class="text-lg font-semibold text-text-primary mb-3">📖 使用说明</h2>
    <ol class="list-decimal list-inside space-y-2 text-sm text-text-secondary">
      <li>点击"选择图像"按钮上传一张图片</li>
      <li>在"颜色调整"面板中拖动滑块：
        <ul class="list-disc list-inside ml-6 mt-1">
          <li><strong>亮度</strong>: 调整图像的明暗程度 (-100 到 +100)</li>
          <li><strong>对比度</strong>: 调整明暗对比 (-100 到 +100)</li>
          <li><strong>饱和度</strong>: 调整色彩鲜艳程度 (-100 到 +100)</li>
        </ul>
      </li>
      <li>实时预览效果，满意后点击"✓ 应用"保存更改</li>
      <li>点击"↶ 重置"可以恢复到调整前的状态</li>
      <li>可以配合其他工具（裁剪、旋转、缩放）一起使用</li>
    </ol>
  </div>
  
  <!-- 颜色调整示例场景 -->
  <div class="mb-6 p-4 bg-surface-elevated border border-border rounded-lg">
    <h2 class="text-lg font-semibold text-text-primary mb-3">💡 常用调整场景</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
      <div class="p-3 bg-surface rounded-lg">
        <h3 class="font-semibold text-text-primary mb-2">🌅 增强日落照片</h3>
        <ul class="space-y-1 text-text-secondary">
          <li>• 亮度: +10 到 +20</li>
          <li>• 对比度: +20 到 +30</li>
          <li>• 饱和度: +30 到 +50</li>
        </ul>
      </div>
      
      <div class="p-3 bg-surface rounded-lg">
        <h3 class="font-semibold text-text-primary mb-2">🌙 修复曝光不足</h3>
        <ul class="space-y-1 text-text-secondary">
          <li>• 亮度: +30 到 +50</li>
          <li>• 对比度: +10 到 +20</li>
          <li>• 饱和度: +10 到 +20</li>
        </ul>
      </div>
      
      <div class="p-3 bg-surface rounded-lg">
        <h3 class="font-semibold text-text-primary mb-2">📷 复古黑白效果</h3>
        <ul class="space-y-1 text-text-secondary">
          <li>• 亮度: -10 到 +10</li>
          <li>• 对比度: +30 到 +50</li>
          <li>• 饱和度: -100 (完全灰度)</li>
        </ul>
      </div>
      
      <div class="p-3 bg-surface rounded-lg">
        <h3 class="font-semibold text-text-primary mb-2">🎨 柔和淡雅风格</h3>
        <ul class="space-y-1 text-text-secondary">
          <li>• 亮度: +20 到 +30</li>
          <li>• 对比度: -20 到 -30</li>
          <li>• 饱和度: -20 到 -30</li>
        </ul>
      </div>
    </div>
  </div>
  
  <!-- ImageEditor 组件 -->
  <div class="bg-surface-elevated border border-border rounded-lg p-6">
    <ImageEditor bind:this={editor} />
  </div>
  
  <!-- 操作按钮 -->
  <div class="mt-6 flex gap-3">
    <button
      on:click={getEditedImage}
      class="px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg transition-colors font-medium"
    >
      获取编辑后的图像
    </button>
  </div>
  
  <!-- 技术说明 -->
  <div class="mt-6 p-4 bg-surface-elevated border border-border rounded-lg">
    <h2 class="text-lg font-semibold text-text-primary mb-3">🔧 技术特性</h2>
    <ul class="space-y-2 text-sm text-text-secondary">
      <li>
        <strong class="text-text-primary">实时预览</strong>: 
        拖动滑块时立即看到效果，无需等待
      </li>
      <li>
        <strong class="text-text-primary">无损调整</strong>: 
        从原始图像数据开始计算，避免累积误差
      </li>
      <li>
        <strong class="text-text-primary">历史记录</strong>: 
        支持撤销/重做，最多保存 20 步操作
      </li>
      <li>
        <strong class="text-text-primary">组合使用</strong>: 
        可以与裁剪、旋转、缩放等工具配合使用
      </li>
      <li>
        <strong class="text-text-primary">标准算法</strong>: 
        使用业界标准的颜色调整算法，效果自然
      </li>
    </ul>
  </div>
  
  <!-- 快捷键提示 -->
  <div class="mt-6 p-4 bg-warning/10 border border-warning/30 rounded-lg">
    <h2 class="text-lg font-semibold text-text-primary mb-3">⌨️ 快捷键</h2>
    <div class="grid grid-cols-2 gap-3 text-sm text-text-secondary">
      <div>
        <kbd class="px-2 py-1 bg-surface border border-border rounded text-xs">Ctrl+Z</kbd>
        <span class="ml-2">撤销</span>
      </div>
      <div>
        <kbd class="px-2 py-1 bg-surface border border-border rounded text-xs">Ctrl+Shift+Z</kbd>
        <span class="ml-2">重做</span>
      </div>
    </div>
  </div>
</div>

<style>
  kbd {
    font-family: monospace;
  }
</style>
