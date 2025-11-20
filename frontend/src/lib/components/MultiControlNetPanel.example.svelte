<script lang="ts">
  import MultiControlNetPanel from './MultiControlNetPanel.svelte';
  import { setError, ErrorType } from '$lib/store';
  
  let multiControlNetPanel: MultiControlNetPanel;
  let loading = false;
  let resultImage = '';
  
  async function handleGenerate() {
    // 验证配置
    const validation = multiControlNetPanel.validate();
    if (!validation.valid) {
      setError({
        type: ErrorType.VALIDATION,
        message: '配置验证失败',
        details: validation.message || '请检查ControlNet配置',
        recoverable: true
      });
      return;
    }
    
    // 获取ControlNet配置
    const controlnets = multiControlNetPanel.getControlNets();
    
    if (controlnets.length === 0) {
      setError({
        type: ErrorType.VALIDATION,
        message: '没有可用的ControlNet',
        details: '请至少添加一个ControlNet并上传图像',
        recoverable: true
      });
      return;
    }
    
    console.log('准备生成，ControlNet配置:', controlnets);
    
    loading = true;
    
    try {
      // 调用多ControlNet API（使用正确的端点）
      const response = await fetch('/api/controlnet/multi', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          prompt: 'a beautiful landscape with mountains and lake, highly detailed',
          negative_prompt: 'ugly, blurry, low quality',
          controlnet_configs: controlnets.map(cn => ({
            type: cn.type,
            image: cn.image,
            weight: cn.weight
          })),
          num_inference_steps: 20,
          guidance_scale: 7.5,
          height: 512,
          width: 512
        })
      });
      
      if (!response.ok) {
        throw new Error(`API请求失败: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success && data.image) {
        resultImage = data.image;
        console.log('✅ 生成成功');
      } else {
        throw new Error(data.message || '生成失败');
      }
    } catch (error) {
      console.error('❌ 生成失败:', error);
      setError({
        type: ErrorType.GENERATION,
        message: '图像生成失败',
        details: error instanceof Error ? error.message : '未知错误',
        recoverable: true,
        suggestions: [
          '检查网络连接',
          '确保后端服务正常运行',
          '检查ControlNet图像是否有效'
        ]
      });
    } finally {
      loading = false;
    }
  }
</script>

<div class="container">
  <h1 class="title">多ControlNet示例</h1>
  
  <div class="grid">
    <!-- 左侧：配置面板 -->
    <div class="panel">
      <MultiControlNetPanel bind:this={multiControlNetPanel} />
      
      <button
        on:click={handleGenerate}
        disabled={loading}
        class="btn-primary mt-4"
      >
        {loading ? '生成中...' : '开始生成'}
      </button>
    </div>
    
    <!-- 右侧：结果展示 -->
    <div class="panel">
      <h3 class="heading">生成结果</h3>
      {#if resultImage}
        <img
          src={resultImage}
          alt="生成结果"
          class="result-image"
        />
      {:else}
        <div class="empty-state">
          <div class="text-4xl mb-2">🖼️</div>
          <p class="text-sm text-text-secondary">生成的图像将显示在这里</p>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  .title {
    font-size: 2rem;
    font-weight: 700;
    color: var(--color-text-primary);
    margin-bottom: 2rem;
  }
  
  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
  }
  
  .panel {
    background: var(--color-background);
    border: 1px solid var(--color-border);
    border-radius: 1rem;
    padding: 1.5rem;
  }
  
  .heading {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--color-text-primary);
    margin-bottom: 1rem;
  }
  
  .btn-primary {
    width: 100%;
    padding: 0.75rem 1.5rem;
    background: var(--color-primary);
    color: white;
    border: none;
    border-radius: 0.5rem;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .btn-primary:hover:not(:disabled) {
    background: var(--color-primary-dark);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
  
  .btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .result-image {
    width: 100%;
    height: auto;
    border-radius: 0.5rem;
    border: 1px solid var(--color-border);
  }
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 400px;
    text-align: center;
  }
  
  @media (max-width: 768px) {
    .grid {
      grid-template-columns: 1fr;
    }
  }
</style>
