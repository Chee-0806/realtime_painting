<script lang="ts">
  import FaceRestorePanel from './FaceRestorePanel.svelte';
  
  let showPanel = true;
</script>

<div class="example-container">
  <div class="example-header">
    <h1>FaceRestorePanel 组件示例</h1>
    <p class="description">
      演示面部修复面板的功能和用法
    </p>
  </div>
  
  <div class="example-controls">
    <button 
      on:click={() => showPanel = !showPanel}
      class="toggle-button"
    >
      {showPanel ? '隐藏面板' : '显示面板'}
    </button>
  </div>
  
  {#if showPanel}
    <div class="panel-container">
      <FaceRestorePanel />
    </div>
  {/if}
  
  <div class="example-info">
    <h2>使用说明</h2>
    
    <div class="info-section">
      <h3>📋 基本步骤</h3>
      <ol>
        <li>点击"选择图像"上传包含人脸的图像</li>
        <li>选择修复模型（CodeFormer 或 GFPGAN）</li>
        <li>调整修复强度（0.0-1.0）</li>
        <li>点击"开始修复"执行面部修复</li>
        <li>使用对比滑块查看修复效果</li>
        <li>点击"下载"保存修复结果</li>
      </ol>
    </div>
    
    <div class="info-section">
      <h3>🤖 模型说明</h3>
      <ul>
        <li><strong>CodeFormer</strong>: 最新技术，效果最佳，适合高质量修复</li>
        <li><strong>GFPGAN</strong>: 经典模型，速度快，适合快速处理</li>
      </ul>
    </div>
    
    <div class="info-section">
      <h3>💪 强度建议</h3>
      <ul>
        <li><strong>0.0-0.3</strong>: 轻微修复，保留更多原始特征</li>
        <li><strong>0.3-0.7</strong>: 平衡修复，推荐设置</li>
        <li><strong>0.7-1.0</strong>: 强力修复，可能改变面部特征</li>
      </ul>
    </div>
    
    <div class="info-section">
      <h3>✨ 功能特性</h3>
      <ul>
        <li>支持多种面部修复模型</li>
        <li>可调节的修复强度</li>
        <li>交互式前后对比视图</li>
        <li>实时进度显示</li>
        <li>完善的错误处理</li>
        <li>一键下载结果</li>
      </ul>
    </div>
    
    <div class="info-section">
      <h3>⚠️ 注意事项</h3>
      <ul>
        <li>确保图像中包含清晰可见的人脸</li>
        <li>推荐图像分辨率：512x512 到 2048x2048</li>
        <li>修复时间取决于图像大小和模型选择</li>
        <li>强度过高可能改变原始面部特征</li>
      </ul>
    </div>
    
    <div class="info-section">
      <h3>🔧 集成示例</h3>
      <pre><code>{`<script>
  import FaceRestorePanel from '$lib/components/FaceRestorePanel.svelte';
</script>

<FaceRestorePanel />`}</code></pre>
    </div>
  </div>
</div>

<style>
  .example-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    font-family: system-ui, -apple-system, sans-serif;
  }
  
  .example-header {
    text-align: center;
    margin-bottom: 2rem;
  }
  
  .example-header h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #1a1a1a;
    margin-bottom: 0.5rem;
  }
  
  .description {
    font-size: 1rem;
    color: #666;
  }
  
  .example-controls {
    display: flex;
    justify-content: center;
    margin-bottom: 2rem;
  }
  
  .toggle-button {
    padding: 0.75rem 1.5rem;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 0.5rem;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s;
  }
  
  .toggle-button:hover {
    background: #2563eb;
  }
  
  .panel-container {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 2rem;
    margin-bottom: 2rem;
  }
  
  .example-info {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 2rem;
  }
  
  .example-info h2 {
    font-size: 1.5rem;
    font-weight: 600;
    color: #1a1a1a;
    margin-bottom: 1.5rem;
    border-bottom: 2px solid #3b82f6;
    padding-bottom: 0.5rem;
  }
  
  .info-section {
    margin-bottom: 1.5rem;
  }
  
  .info-section h3 {
    font-size: 1.125rem;
    font-weight: 600;
    color: #374151;
    margin-bottom: 0.75rem;
  }
  
  .info-section ul,
  .info-section ol {
    margin-left: 1.5rem;
    color: #4b5563;
    line-height: 1.75;
  }
  
  .info-section li {
    margin-bottom: 0.5rem;
  }
  
  .info-section strong {
    color: #1f2937;
    font-weight: 600;
  }
  
  .info-section pre {
    background: #f3f4f6;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    padding: 1rem;
    overflow-x: auto;
    margin-top: 0.5rem;
  }
  
  .info-section code {
    font-family: 'Monaco', 'Courier New', monospace;
    font-size: 0.875rem;
    color: #1f2937;
  }
  
  @media (max-width: 768px) {
    .example-container {
      padding: 1rem;
    }
    
    .example-header h1 {
      font-size: 1.5rem;
    }
    
    .panel-container {
      padding: 1rem;
    }
    
    .example-info {
      padding: 1rem;
    }
  }
</style>
