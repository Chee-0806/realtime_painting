<script lang="ts">
  import type { Fields } from '$lib/types';
  import { pipelineValues } from '$lib/store';
  import PromptTools from './PromptTools.svelte';
  import LoRADownloader from './LoRADownloader.svelte';

  export let pipelineParams: Fields;

  let promptToolsRef: PromptTools;
  let showLoRADownloader = false;
  
  function updateValue(key: string, value: any) {
    pipelineValues.update((values) => {
      values[key] = value;
      return values;
    });
    
    // 如果更新的是prompt，添加到历史记录
    if (key === 'prompt' && value && value.trim() !== '' && promptToolsRef) {
      promptToolsRef.addToHistory(value);
    }
  }
  
  $: currentValues = $pipelineValues;
</script>

<div class="space-y-4">
  {#each Object.entries(pipelineParams) as [key, field]}
    <div class="space-y-2">
      <label class="label" for={key}>
        {field.title || key}
      </label>
      
      {#if field.field === 'textarea'}
        <textarea
          id={key}
          class="input-textarea w-full"
          rows="3"
          value={currentValues[key] ?? field.default}
          on:input={(e) => updateValue(key, e.currentTarget.value)}
          placeholder={field.title}
        ></textarea>
        
        <!-- 如果是prompt字段，添加PromptTools -->
        {#if key === 'prompt'}
          <PromptTools bind:this={promptToolsRef} />
        {/if}
      {:else if field.field === 'range'}
        <div class="flex items-center gap-4">
          <input
            type="range"
            id={key}
            class="flex-1"
            min={field.min ?? 0}
            max={field.max ?? 100}
            step={key === 'cfg_scale' || key === 'denoise' ? 0.1 : 1}
            value={currentValues[key] ?? field.default}
            on:input={(e) => updateValue(key, Number(e.currentTarget.value))}
          />
          <span class="text-sm text-text-secondary min-w-[60px] text-right">
            {currentValues[key] ?? field.default}
          </span>
        </div>
      {:else if field.field === 'select'}
        {#if key === 'lora_selection'}
          <!-- LoRA选择特殊处理 -->
          <div class="space-y-2">
            <select
              id={key}
              class="input w-full"
              value={currentValues[key] ?? field.default}
              on:change={(e) => updateValue(key, e.currentTarget.value)}
            >
              {#if field.values}
                {#each field.values as option}
                  <option value={option.value}>{option.label}</option>
                {/each}
              {/if}
            </select>

            <!-- LoRA下载器 -->
            {#if currentValues[key] && currentValues[key].startsWith('preset:')}
              <div class="alert alert-info alert-sm">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <div>
                  <h3 class="font-bold">提示</h3>
                  <div class="text-xs">这是一个预制LoRA模型，选择后将自动开始下载。</div>
                </div>
              </div>
            {/if}

            <!-- LoRA管理按钮 -->
            <button
              type="button"
              class="btn btn-sm btn-outline w-full"
              on:click={() => showLoRADownloader = true}
            >
              📦 LoRA 管理器
            </button>
          </div>

          <!-- LoRA下载器模态框 -->
          {#if showLoRADownloader}
            <div class="modal modal-open">
              <div class="modal-box w-11/12 max-w-4xl">
                <div class="flex justify-between items-center mb-4">
                  <h3 class="font-bold text-lg">📦 LoRA 管理器</h3>
                  <button
                    class="btn btn-sm btn-circle btn-ghost"
                    on:click={() => showLoRADownloader = false}
                  >
                    ✕
                  </button>
                </div>

                <LoRADownloader />
              </div>
            </div>
          {/if}
        {:else}
          <select
            id={key}
            class="input w-full"
            value={currentValues[key] ?? field.default}
            on:change={(e) => updateValue(key, e.currentTarget.value)}
          >
            {#if field.values}
              {#each field.values as option}
                <option value={option.value}>{option.label}</option>
              {/each}
            {/if}
          </select>
        {/if}
      {:else}
        <input
          type={field.type || 'text'}
          id={key}
          class="input w-full"
          value={currentValues[key] ?? field.default}
          min={field.min}
          max={field.max}
          on:input={(e) => {
            const value = field.type === 'number' 
              ? Number(e.currentTarget.value) 
              : e.currentTarget.value;
            updateValue(key, value);
          }}
          placeholder={field.title}
        />
      {/if}
    </div>
  {/each}
</div>

