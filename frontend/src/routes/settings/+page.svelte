<script lang="ts">
  import { onMount } from 'svelte';
  import type { Fields } from '$lib/types';
  import ModelManager from '$lib/components/ModelManager.svelte';
  import PipelineOptions from '$lib/components/PipelineOptions.svelte';
  import Spinner from '$lib/icons/spinner.svelte';
  import { pipelineValues } from '$lib/store';
  
  let pipelineParams: Fields | null = null;
  let loading = true;
  
  onMount(async () => {
    try {
      const settings = await fetch('/api/settings').then((r) => r.json());
      pipelineParams = settings.input_params.properties;
      
      // 初始化默认值
      const initialValues: Record<string, any> = {};
      for (const [key, field] of Object.entries(pipelineParams)) {
        initialValues[key] = field.default;
      }
      pipelineValues.set(initialValues);
    } catch (error) {
      console.error('加载设置失败:', error);
    } finally {
      loading = false;
    }
  });
</script>

<svelte:head>
  <title>设置 - ArtFlow</title>
</svelte:head>

<main class="min-h-screen bg-surface">
  <div class="container mx-auto max-w-6xl px-4 py-6">
    <div class="mb-6">
      <h1 class="title">⚙️ 设置</h1>
      <p class="subtitle">管理模型和生成参数</p>
    </div>
    
    {#if loading}
      <div class="flex items-center justify-center gap-4 py-48">
        <Spinner classList={'animate-spin opacity-50'} />
        <p class="text-xl text-text-secondary">加载中...</p>
      </div>
    {:else}
      <div class="space-y-6">
        <!-- 模型管理 -->
        <div class="card">
          <h3 class="heading">🤖 模型管理</h3>
          <ModelManager />
        </div>
        
        <!-- 生成参数 -->
        {#if pipelineParams}
          <div class="card">
            <h3 class="heading">🎛️ 生成参数</h3>
            <p class="text-sm text-text-secondary mb-4">
              配置默认的生成参数，这些参数会在所有生成模式中使用
            </p>
            <PipelineOptions {pipelineParams} />
          </div>
        {/if}
      </div>
    {/if}
  </div>
</main>

