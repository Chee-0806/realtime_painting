<script lang="ts">
  import { onMount } from 'svelte';
  import { setError, clearError, ErrorType } from '$lib/store';
  import ControlNetItem from './ControlNetItem.svelte';
  import type { ControlNetConfig } from './ControlNetItem.svelte';
  
  // 组件props - 支持外部绑定
  export let controlnets: ControlNetConfig[] = [];
  
  // 组件状态
  let availableTypes: string[] = [];
  let maxControlNets: number = 3;
  
  // UI状态
  let loading: boolean = false;
  
  onMount(async () => {
    // 获取可用的ControlNet类型
    try {
      const response = await fetch('/api/controlnet/types');
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.types) {
          availableTypes = data.types;
          console.log(`✅ 成功获取${data.types.length}个ControlNet类型:`, data.types);
        } else {
          // 使用默认类型列表
          availableTypes = ['canny', 'depth', 'pose', 'scribble', 'lineart', 'normal', 'semantic'];
          console.warn('⚠️ 后端未返回ControlNet类型，使用默认列表');
        }
      } else {
        availableTypes = ['canny', 'depth', 'pose', 'scribble', 'lineart', 'normal', 'semantic'];
        console.warn('⚠️ 无法获取ControlNet类型，使用默认列表');
      }
    } catch (error) {
      availableTypes = ['canny', 'depth', 'pose', 'scribble', 'lineart', 'normal', 'semantic'];
      console.error('❌ 获取ControlNet类型失败:', error);
    }
  });
  
  function addControlNet() {
    if (controlnets.length >= maxControlNets) {
      setError({
        type: ErrorType.VALIDATION,
        message: '已达到最大数量',
        details: `最多只能添加${maxControlNets}个ControlNet`,
        recoverable: true,
        suggestions: ['删除现有的ControlNet后再添加']
      });
      return;
    }
    
    const newControlNet: ControlNetConfig = {
      id: `cn-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type: availableTypes[0] || 'canny',
      image: '',
      weight: 1.0,
      guidanceStart: 0.0,
      guidanceEnd: 1.0
    };
    
    controlnets = [...controlnets, newControlNet];
    clearError();
  }
  
  function removeControlNet(id: string) {
    controlnets = controlnets.filter(cn => cn.id !== id);
  }
  
  function updateControlNet(id: string, field: keyof ControlNetConfig, value: any) {
    controlnets = controlnets.map(cn => 
      cn.id === id ? { ...cn, [field]: value } : cn
    );
  }
  
  // 导出配置供父组件使用
  export function getControlNets(): ControlNetConfig[] {
    return controlnets.filter(cn => cn.image !== '');
  }
  
  // 验证配置
  export function validate(): { valid: boolean; message?: string } {
    const validControlNets = controlnets.filter(cn => cn.image !== '');
    
    if (controlnets.length > 0 && validControlNets.length === 0) {
      return {
        valid: false,
        message: '请为所有ControlNet上传图像'
      };
    }
    
    return { valid: true };
  }
  
  // API调用：生成图像
  export async function generate(params: {
    prompt: string;
    negative_prompt?: string;
    num_inference_steps?: number;
    guidance_scale?: number;
    height?: number;
    width?: number;
    seed?: number;
  }): Promise<{ success: boolean; image?: string; message?: string }> {
    // 验证配置
    const validation = validate();
    if (!validation.valid) {
      return {
        success: false,
        message: validation.message
      };
    }
    
    const validControlNets = getControlNets();
    if (validControlNets.length === 0) {
      return {
        success: false,
        message: '请至少添加一个ControlNet并上传图像'
      };
    }
    
    loading = true;
    clearError();
    
    try {
      // 构建API请求参数
      const requestBody = {
        prompt: params.prompt,
        negative_prompt: params.negative_prompt || '',
        controlnet_configs: validControlNets.map(cn => ({
          type: cn.type,
          image: cn.image,
          weight: cn.weight,
          guidance_start: cn.guidanceStart,
          guidance_end: cn.guidanceEnd
        })),
        num_inference_steps: params.num_inference_steps || 20,
        guidance_scale: params.guidance_scale || 7.5,
        height: params.height || 512,
        width: params.width || 512,
        seed: params.seed
      };
      
      console.log('🚀 发送多ControlNet生成请求:', {
        controlnet_count: validControlNets.length,
        types: validControlNets.map(cn => cn.type),
        prompt: params.prompt
      });
      
      // 调用API
      const response = await fetch('/api/controlnet/multi', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.message || `API错误: ${response.status}`);
      }
      
      if (!result.success) {
        throw new Error(result.message || '生成失败');
      }
      
      console.log('✅ 多ControlNet生成成功');
      
      return {
        success: true,
        image: result.image
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '未知错误';
      console.error('❌ 多ControlNet生成失败:', errorMessage);
      
      setError({
        type: ErrorType.API,
        message: '多ControlNet生成失败',
        details: errorMessage,
        recoverable: true,
        suggestions: [
          '检查网络连接',
          '确保后端服务正常运行',
          '检查ControlNet模型是否已加载',
          '尝试减少ControlNet数量'
        ]
      });
      
      return {
        success: false,
        message: errorMessage
      };
    } finally {
      loading = false;
    }
  }
</script>

<div class="card">
  <div class="flex items-center justify-between mb-4">
    <h3 class="heading">🎮 多ControlNet控制</h3>
    <span class="text-sm text-text-secondary">
      {controlnets.length} / {maxControlNets}
    </span>
  </div>
  
  <!-- ControlNet列表 -->
  <div class="space-y-4">
    {#each controlnets as cn, index (cn.id)}
      <ControlNetItem
        config={cn}
        {index}
        {availableTypes}
        onRemove={removeControlNet}
        onUpdate={updateControlNet}
      />
    {/each}
    
    <!-- 添加按钮 -->
    {#if controlnets.length < maxControlNets}
      <button
        on:click={addControlNet}
        class="btn-secondary w-full"
        disabled={loading}
      >
        + 添加ControlNet
      </button>
    {:else}
      <div class="text-center text-sm text-text-secondary p-2">
        已达到最大数量（{maxControlNets}个）
      </div>
    {/if}
    
    <!-- 空状态提示 -->
    {#if controlnets.length === 0}
      <div class="text-center py-8 text-text-secondary">
        <div class="text-4xl mb-2">🎮</div>
        <p class="text-sm">还没有添加ControlNet</p>
        <p class="text-xs mt-1">点击上方按钮添加最多{maxControlNets}个ControlNet</p>
      </div>
    {/if}
    
    <!-- 加载状态 -->
    {#if loading}
      <div class="text-center py-4">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <p class="text-sm text-text-secondary mt-2">正在生成...</p>
      </div>
    {/if}
  </div>
</div>

<style>
  .card {
    background: var(--color-background);
    border: 1px solid var(--color-border);
    border-radius: 1rem;
    padding: 1.5rem;
  }
  
  .heading {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--color-text-primary);
  }
  
  .label {
    display: block;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--color-text-secondary);
    margin-bottom: 0.5rem;
  }
  
  .input {
    width: 100%;
    padding: 0.5rem 0.75rem;
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: 0.5rem;
    color: var(--color-text-primary);
    font-size: 0.875rem;
    transition: all 0.2s;
  }
  
  .input:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(var(--color-primary-rgb), 0.1);
  }
  
  .btn-secondary {
    padding: 0.5rem 1rem;
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: 0.5rem;
    color: var(--color-text-primary);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .btn-secondary:hover:not(:disabled) {
    background: var(--color-primary);
    color: white;
    border-color: var(--color-primary);
  }
  
  .btn-secondary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
