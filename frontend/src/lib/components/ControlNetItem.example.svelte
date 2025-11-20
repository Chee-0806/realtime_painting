<script lang="ts">
  import ControlNetItem from './ControlNetItem.svelte';
  import type { ControlNetConfig } from './ControlNetItem.svelte';
  
  // 示例配置
  let controlnets: ControlNetConfig[] = [
    {
      id: 'example-cn-1',
      type: 'canny',
      image: '',
      weight: 1.0,
      guidanceStart: 0.0,
      guidanceEnd: 1.0
    },
    {
      id: 'example-cn-2',
      type: 'depth',
      image: '',
      weight: 0.8,
      guidanceStart: 0.2,
      guidanceEnd: 0.9
    }
  ];
  
  // 可用的ControlNet类型
  const availableTypes = [
    'canny',
    'depth',
    'pose',
    'scribble',
    'lineart',
    'normal',
    'semantic'
  ];
  
  // 删除ControlNet
  function removeControlNet(id: string) {
    controlnets = controlnets.filter(cn => cn.id !== id);
    console.log('删除 ControlNet:', id);
  }
  
  // 更新ControlNet配置
  function updateControlNet(id: string, field: keyof ControlNetConfig, value: any) {
    controlnets = controlnets.map(cn => 
      cn.id === id ? { ...cn, [field]: value } : cn
    );
    console.log('更新 ControlNet:', id, field, value);
  }
  
  // 添加新的ControlNet
  function addControlNet() {
    const newControlNet: ControlNetConfig = {
      id: `example-cn-${Date.now()}`,
      type: 'canny',
      image: '',
      weight: 1.0,
      guidanceStart: 0.0,
      guidanceEnd: 1.0
    };
    controlnets = [...controlnets, newControlNet];
  }
  
  // 获取配置摘要
  function getConfigSummary(config: ControlNetConfig): string {
    return `类型: ${config.type}, 权重: ${config.weight.toFixed(2)}, 引导: ${config.guidanceStart.toFixed(2)}-${config.guidanceEnd.toFixed(2)}`;
  }
</script>

<div class="example-container">
  <h1 class="title">ControlNetItem 组件示例</h1>
  
  <div class="section">
    <h2 class="section-title">基础用法</h2>
    <p class="description">
      展示单个 ControlNet 配置项的基本功能，包括类型选择、图像上传、权重调整和引导范围设置。
    </p>
    
    <div class="demo">
      <div class="controlnet-list">
        {#each controlnets as cn, index (cn.id)}
          <ControlNetItem
            config={cn}
            {index}
            {availableTypes}
            onRemove={removeControlNet}
            onUpdate={updateControlNet}
          />
        {/each}
      </div>
      
      <button on:click={addControlNet} class="btn-add">
        + 添加 ControlNet
      </button>
    </div>
  </div>
  
  <div class="section">
    <h2 class="section-title">配置状态</h2>
    <p class="description">
      实时显示当前所有 ControlNet 的配置状态。
    </p>
    
    <div class="config-display">
      {#if controlnets.length === 0}
        <p class="empty-state">暂无 ControlNet 配置</p>
      {:else}
        {#each controlnets as cn, index}
          <div class="config-item">
            <div class="config-header">
              <span class="config-index">#{index + 1}</span>
              <span class="config-id">{cn.id}</span>
            </div>
            <div class="config-details">
              <p>{getConfigSummary(cn)}</p>
              {#if cn.image}
                <p class="has-image">✅ 已上传图像</p>
              {:else}
                <p class="no-image">⚠️ 未上传图像</p>
              {/if}
            </div>
          </div>
        {/each}
      {/if}
    </div>
  </div>
  
  <div class="section">
    <h2 class="section-title">使用说明</h2>
    <div class="instructions">
      <ol>
        <li>点击"添加 ControlNet"按钮创建新的配置项</li>
        <li>从下拉菜单中选择 ControlNet 类型</li>
        <li>点击"选择文件"上传控制图像</li>
        <li>调整权重滑块控制影响强度（0.0-2.0）</li>
        <li>设置引导范围控制生效时机（0.0-1.0）</li>
        <li>点击右上角的 ✕ 按钮删除配置项</li>
      </ol>
    </div>
  </div>
  
  <div class="section">
    <h2 class="section-title">参数说明</h2>
    <div class="params-table">
      <table>
        <thead>
          <tr>
            <th>参数</th>
            <th>范围</th>
            <th>默认值</th>
            <th>说明</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>类型 (Type)</td>
            <td>预设列表</td>
            <td>canny</td>
            <td>ControlNet 的类型，决定控制方式</td>
          </tr>
          <tr>
            <td>权重 (Weight)</td>
            <td>0.0 - 2.0</td>
            <td>1.0</td>
            <td>控制影响强度，越大影响越强</td>
          </tr>
          <tr>
            <td>引导开始</td>
            <td>0.0 - 1.0</td>
            <td>0.0</td>
            <td>开始生效的步数比例</td>
          </tr>
          <tr>
            <td>引导结束</td>
            <td>0.0 - 1.0</td>
            <td>1.0</td>
            <td>停止生效的步数比例</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

<style>
  .example-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    background: var(--color-background, #0d0d0d);
    color: var(--color-text-primary, #ffffff);
  }
  
  .title {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 2rem;
    color: var(--color-text-primary, #ffffff);
  }
  
  .section {
    margin-bottom: 3rem;
  }
  
  .section-title {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 0.75rem;
    color: var(--color-text-primary, #ffffff);
  }
  
  .description {
    font-size: 0.9375rem;
    color: var(--color-text-secondary, #999999);
    margin-bottom: 1.5rem;
    line-height: 1.6;
  }
  
  .demo {
    background: var(--color-surface, #1a1a1a);
    border: 1px solid var(--color-border, #333333);
    border-radius: 1rem;
    padding: 1.5rem;
  }
  
  .controlnet-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 1rem;
  }
  
  .btn-add {
    width: 100%;
    padding: 0.75rem 1rem;
    background: var(--color-primary, #3b82f6);
    color: white;
    border: none;
    border-radius: 0.5rem;
    font-size: 0.9375rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .btn-add:hover {
    background: var(--color-primary-hover, #2563eb);
    transform: translateY(-1px);
  }
  
  .config-display {
    background: var(--color-surface, #1a1a1a);
    border: 1px solid var(--color-border, #333333);
    border-radius: 1rem;
    padding: 1.5rem;
  }
  
  .empty-state {
    text-align: center;
    color: var(--color-text-secondary, #999999);
    padding: 2rem;
  }
  
  .config-item {
    padding: 1rem;
    background: var(--color-background, #0d0d0d);
    border: 1px solid var(--color-border, #333333);
    border-radius: 0.5rem;
    margin-bottom: 0.75rem;
  }
  
  .config-item:last-child {
    margin-bottom: 0;
  }
  
  .config-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }
  
  .config-index {
    font-weight: 600;
    color: var(--color-primary, #3b82f6);
  }
  
  .config-id {
    font-size: 0.75rem;
    color: var(--color-text-secondary, #999999);
    font-family: monospace;
  }
  
  .config-details p {
    font-size: 0.875rem;
    margin: 0.25rem 0;
  }
  
  .has-image {
    color: var(--color-success, #10b981);
  }
  
  .no-image {
    color: var(--color-warning, #f59e0b);
  }
  
  .instructions {
    background: var(--color-surface, #1a1a1a);
    border: 1px solid var(--color-border, #333333);
    border-radius: 1rem;
    padding: 1.5rem;
  }
  
  .instructions ol {
    margin: 0;
    padding-left: 1.5rem;
  }
  
  .instructions li {
    margin-bottom: 0.5rem;
    line-height: 1.6;
  }
  
  .params-table {
    background: var(--color-surface, #1a1a1a);
    border: 1px solid var(--color-border, #333333);
    border-radius: 1rem;
    padding: 1.5rem;
    overflow-x: auto;
  }
  
  table {
    width: 100%;
    border-collapse: collapse;
  }
  
  th, td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid var(--color-border, #333333);
  }
  
  th {
    font-weight: 600;
    color: var(--color-text-primary, #ffffff);
    background: var(--color-background, #0d0d0d);
  }
  
  td {
    color: var(--color-text-secondary, #999999);
  }
  
  tbody tr:last-child td {
    border-bottom: none;
  }
  
  @media (max-width: 768px) {
    .example-container {
      padding: 1rem;
    }
    
    .title {
      font-size: 1.5rem;
    }
    
    .section-title {
      font-size: 1.25rem;
    }
  }
</style>
