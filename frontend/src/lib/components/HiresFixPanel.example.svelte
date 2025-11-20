<script lang="ts">
  import HiresFixPanel from './HiresFixPanel.svelte';
  
  let showPanel = true;
</script>

<div class="min-h-screen bg-surface p-8">
  <div class="max-w-4xl mx-auto">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-text-primary mb-2">
        HiresFixPanel 组件示例
      </h1>
      <p class="text-text-secondary">
        演示高分辨率修复（Hires.fix）功能的使用
      </p>
    </div>
    
    <!-- 控制按钮 -->
    <div class="mb-6 flex gap-3">
      <button
        on:click={() => showPanel = !showPanel}
        class="px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg transition-colors font-medium"
      >
        {showPanel ? '隐藏面板' : '显示面板'}
      </button>
    </div>
    
    <!-- 使用说明 -->
    <div class="mb-6 p-4 bg-info/10 border border-info/30 rounded-lg">
      <h2 class="text-lg font-semibold text-text-primary mb-3">📖 使用说明</h2>
      <div class="space-y-2 text-sm text-text-primary">
        <p><strong>方式一：从头生成高分辨率图像</strong></p>
        <ol class="list-decimal list-inside space-y-1 ml-4">
          <li>输入 Prompt 描述想要生成的内容</li>
          <li>配置参数（步数、放大倍数、放大算法等）</li>
          <li>点击"开始生成"按钮</li>
          <li>等待两阶段生成完成</li>
          <li>下载高分辨率结果</li>
        </ol>
        
        <p class="mt-4"><strong>方式二：基于现有图像进行高分辨率修复</strong></p>
        <ol class="list-decimal list-inside space-y-1 ml-4">
          <li>点击"选择图像"上传源图像</li>
          <li>输入 Prompt 描述图像内容</li>
          <li>调整降噪强度等参数</li>
          <li>点击"开始生成"进行放大和细化</li>
          <li>下载高分辨率结果</li>
        </ol>
      </div>
    </div>
    
    <!-- 参数推荐 -->
    <div class="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="p-4 bg-surface-elevated border border-border rounded-lg">
        <h3 class="text-sm font-semibold text-text-primary mb-2">⚡ 快速预览</h3>
        <ul class="text-xs text-text-secondary space-y-1">
          <li>• 放大算法: Latent</li>
          <li>• 第一阶段: 15 步</li>
          <li>• 高分辨率: 10 步</li>
          <li>• 放大倍数: 2.0x</li>
        </ul>
      </div>
      
      <div class="p-4 bg-surface-elevated border border-border rounded-lg">
        <h3 class="text-sm font-semibold text-text-primary mb-2">✨ 高质量</h3>
        <ul class="text-xs text-text-secondary space-y-1">
          <li>• 放大算法: ESRGAN 4x</li>
          <li>• 第一阶段: 25 步</li>
          <li>• 高分辨率: 20 步</li>
          <li>• 放大倍数: 2.0-3.0x</li>
        </ul>
      </div>
      
      <div class="p-4 bg-surface-elevated border border-border rounded-lg">
        <h3 class="text-sm font-semibold text-text-primary mb-2">🎯 极致质量</h3>
        <ul class="text-xs text-text-secondary space-y-1">
          <li>• 放大算法: LDSR</li>
          <li>• 第一阶段: 30 步</li>
          <li>• 高分辨率: 25 步</li>
          <li>• 放大倍数: 4.0x</li>
        </ul>
      </div>
    </div>
    
    <!-- HiresFixPanel 组件 -->
    {#if showPanel}
      <div class="bg-surface-elevated border border-border rounded-xl p-6 shadow-lg">
        <HiresFixPanel />
      </div>
    {/if}
    
    <!-- 技术说明 -->
    <div class="mt-8 p-4 bg-surface-elevated border border-border rounded-lg">
      <h2 class="text-lg font-semibold text-text-primary mb-3">🔧 技术说明</h2>
      <div class="space-y-3 text-sm text-text-secondary">
        <div>
          <h3 class="font-semibold text-text-primary mb-1">什么是 Hires.fix？</h3>
          <p>
            Hires.fix 是一种两阶段图像生成技术，先在低分辨率下生成图像，
            然后使用放大算法和额外的扩散步骤来提升到高分辨率。
            这种方法可以生成更清晰、细节更丰富的图像。
          </p>
        </div>
        
        <div>
          <h3 class="font-semibold text-text-primary mb-1">放大算法对比</h3>
          <ul class="list-disc list-inside space-y-1 ml-4">
            <li><strong>Latent</strong>: 在潜空间进行放大，速度最快，适合快速预览</li>
            <li><strong>ESRGAN</strong>: 基于 GAN 的超分辨率，适合照片和真实图像</li>
            <li><strong>LDSR</strong>: 基于扩散的超分辨率，质量最高但速度较慢</li>
          </ul>
        </div>
        
        <div>
          <h3 class="font-semibold text-text-primary mb-1">降噪强度说明</h3>
          <p>
            降噪强度控制高分辨率阶段的变化程度：
          </p>
          <ul class="list-disc list-inside space-y-1 ml-4">
            <li><strong>0.5-0.6</strong>: 保持与低分辨率图像高度一致</li>
            <li><strong>0.7-0.8</strong>: 平衡一致性和细节增强（推荐）</li>
            <li><strong>0.9-1.0</strong>: 大幅改变，可能产生新细节</li>
          </ul>
        </div>
      </div>
    </div>
    
    <!-- 示例 Prompts -->
    <div class="mt-6 p-4 bg-surface-elevated border border-border rounded-lg">
      <h2 class="text-lg font-semibold text-text-primary mb-3">💡 示例 Prompts</h2>
      <div class="space-y-3">
        <div class="p-3 bg-surface rounded-lg">
          <h3 class="text-sm font-semibold text-text-primary mb-1">风景照片</h3>
          <p class="text-xs text-text-secondary">
            "a beautiful mountain landscape at sunset, high quality, detailed, 8k, photorealistic"
          </p>
        </div>
        
        <div class="p-3 bg-surface rounded-lg">
          <h3 class="text-sm font-semibold text-text-primary mb-1">人物肖像</h3>
          <p class="text-xs text-text-secondary">
            "portrait of a young woman, professional photography, sharp focus, detailed face, high resolution"
          </p>
        </div>
        
        <div class="p-3 bg-surface rounded-lg">
          <h3 class="text-sm font-semibold text-text-primary mb-1">建筑设计</h3>
          <p class="text-xs text-text-secondary">
            "modern architecture building, glass facade, detailed textures, architectural photography, 4k"
          </p>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  :global(body) {
    --surface: #1a1a1a;
    --surface-elevated: #2a2a2a;
    --border: #3a3a3a;
    --text-primary: #ffffff;
    --text-secondary: #a0a0a0;
    --primary: #3b82f6;
    --success: #10b981;
    --info: #06b6d4;
  }
</style>
