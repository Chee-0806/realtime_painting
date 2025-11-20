<script lang="ts">
  import { onMount } from 'svelte';
  
  // 状态
  let models: any[] = [];
  let vaes: any[] = [];
  let schedulers: any[] = [];
  
  let selectedModel: string = '';
  let selectedVae: string = '';
  let selectedScheduler: string = '';
  
  let loading = false;
  let error: string = '';
  let successMessage: string = '';
  
  // 加载可用选项
  onMount(async () => {
    await loadOptions();
  });
  
  async function loadOptions() {
    try {
      // 加载模型列表
      const modelsRes = await fetch('/api/models');
      const modelsData = await modelsRes.json();
      models = modelsData.models || [];
      
      // 设置当前选中的模型
      const currentModel = models.find(m => m.loaded);
      if (currentModel) {
        selectedModel = currentModel.id;
      }
      
      // 加载VAE列表
      const vaesRes = await fetch('/api/vaes');
      const vaesData = await vaesRes.json();
      vaes = vaesData.vaes || [];
      
      // 设置当前选中的VAE
      const currentVae = vaes.find(v => v.loaded);
      if (currentVae) {
        selectedVae = currentVae.id;
      }
      
      // 加载采样器列表
      const schedulersRes = await fetch('/api/schedulers');
      const schedulersData = await schedulersRes.json();
      schedulers = schedulersData.schedulers || [];
      
      // 设置当前选中的采样器
      const currentScheduler = schedulers.find(s => s.loaded);
      if (currentScheduler) {
        selectedScheduler = currentScheduler.id;
      }
    } catch (e) {
      error = '加载选项失败: ' + (e instanceof Error ? e.message : String(e));
      console.error('加载选项失败:', e);
    }
  }
  
  async function switchModel() {
    if (!selectedModel) {
      error = '请选择一个模型';
      return;
    }
    
    loading = true;
    error = '';
    successMessage = '';
    
    try {
      const response = await fetch('/api/models/switch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_id: selectedModel,
          vae_id: selectedVae,
          scheduler_id: selectedScheduler
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        successMessage = data.message || '模型切换成功';
        // 重新加载选项以更新状态
        await loadOptions();
        
        // 3秒后清除成功消息
        setTimeout(() => {
          successMessage = '';
        }, 3000);
      } else {
        error = data.message || '模型切换失败';
      }
    } catch (e) {
      error = '模型切换失败: ' + (e instanceof Error ? e.message : String(e));
      console.error('模型切换失败:', e);
    } finally {
      loading = false;
    }
  }
  
  async function switchVae() {
    if (!selectedVae) {
      error = '请选择一个VAE';
      return;
    }
    
    loading = true;
    error = '';
    successMessage = '';
    
    try {
      const response = await fetch('/api/vae/switch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          vae_id: selectedVae
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        successMessage = data.message || 'VAE切换成功';
        await loadOptions();
        
        setTimeout(() => {
          successMessage = '';
        }, 3000);
      } else {
        error = data.message || 'VAE切换失败';
      }
    } catch (e) {
      error = 'VAE切换失败: ' + (e instanceof Error ? e.message : String(e));
      console.error('VAE切换失败:', e);
    } finally {
      loading = false;
    }
  }
  
  async function switchScheduler() {
    if (!selectedScheduler) {
      error = '请选择一个采样器';
      return;
    }
    
    loading = true;
    error = '';
    successMessage = '';
    
    try {
      const response = await fetch('/api/scheduler/set', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          scheduler: selectedScheduler
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        successMessage = data.message || '采样器切换成功';
        await loadOptions();
        
        setTimeout(() => {
          successMessage = '';
        }, 3000);
      } else {
        error = data.message || '采样器切换失败';
      }
    } catch (e) {
      error = '采样器切换失败: ' + (e instanceof Error ? e.message : String(e));
      console.error('采样器切换失败:', e);
    } finally {
      loading = false;
    }
  }
</script>

<div class="space-y-4">
  <!-- 错误提示 -->
  {#if error}
    <div class="px-3 py-2 bg-danger/10 border border-danger/30 rounded-lg text-sm text-danger">
      {error}
    </div>
  {/if}
  
  <!-- 成功提示 -->
  {#if successMessage}
    <div class="px-3 py-2 bg-success/10 border border-success/30 rounded-lg text-sm text-success">
      {successMessage}
    </div>
  {/if}
  
  <!-- 模型选择 -->
  <div class="space-y-2">
    <label for="model-select" class="block text-sm font-medium text-text-primary">
      模型
    </label>
    <select 
      id="model-select"
      bind:value={selectedModel}
      on:change={switchModel}
      disabled={loading}
      class="w-full px-3 py-2 bg-surface-elevated border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
    >
      {#each models as model}
        <option value={model.id}>
          {model.name} {model.loaded ? '(当前)' : ''}
        </option>
      {/each}

  <div class="flex gap-4 items-end">
    <div class="flex-1 space-y-2">
      <label for="model-select" class="text-sm font-medium text-text-secondary">
        选择模型
      </label>
      <select
        id="model-select"
        bind:value={selectedModelId}
        disabled={loading || switching}
        class="w-full px-3 py-2 bg-surface-elevated border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
      >
        {#each models as model}
          <option value={model.id}>
            {model.name}
          </option>
        {/each}
      </select>
    </div>
    
    <Button 
      variant="primary" 
      disabled={loading || switching || !selectedModelId}
      on:click={handleSwitch}
    >
      {#if switching}
        <div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2"></div>
        切换中...
      {:else}
        切换模型
      {/if}
    </Button>
  </div>
  
  {#if selectedModelId}
    {@const model = models.find(m => m.id === selectedModelId)}
    {#if model && model.description}
      <p class="text-xs text-text-secondary">
        {model.description}
      </p>
    {/if}
  {/if}
</div>
