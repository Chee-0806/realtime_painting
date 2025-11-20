<script lang="ts">
  import type { Fields } from '$lib/types';
  import { pipelineValues } from '$lib/store';
  import PromptTools from './PromptTools.svelte';
  
  export let pipelineParams: Fields;
  
  let promptToolsRef: PromptTools;
  
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

