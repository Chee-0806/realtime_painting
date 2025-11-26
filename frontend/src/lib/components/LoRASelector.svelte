<script lang="ts">
  import { onMount } from 'svelte';
  import { setError, ErrorType } from '$lib/store';
  import { pipelineValues, getPipelineValues } from '$lib/store';

  // 组件状态
  let loading = true;
  let availableLoRAs: any[] = [];
  let selectedLoRA = 'none';

  // API函数
  const API_BASE = '/api/lora';

  async function fetchAvailableLoRAs() {
    try {
      const response = await fetch(`${API_BASE}/presets`);
      if (!response.ok) throw new Error('获取LoRA列表失败');

      const presets = await response.json();
      // 只显示已下载的LoRA
      availableLoRAs = presets.filter(preset => preset.is_downloaded);

      // 从store中获取当前选中的LoRA
      const currentValues = getPipelineValues();
      selectedLoRA = currentValues.lora_selection || 'none';

    } catch (error) {
      console.error('获取LoRA列表失败:', error);
      setError(ErrorType.NETWORK, '获取LoRA列表失败');
    } finally {
      loading = false;
    }
  }

  // 更新选中的LoRA
  function updateLoRASelection() {
    const currentValues = getPipelineValues();
    pipelineValues.set({
      ...currentValues,
      lora_selection: selectedLoRA
    });
  }

  // 响应选中LoRA的变化
  $: {
    if (selectedLoRA !== undefined) {
      updateLoRASelection();
    }
  }

  onMount(async () => {
    await fetchAvailableLoRAs();
  });

  // 分类LoRA
  $: acceleratedLoRAs = availableLoRAs.filter(lora =>
    lora.tags.includes('speed') || lora.tags.includes('lcm')
  );
  $: styleLoRAs = availableLoRAs.filter(lora =>
    lora.tags.includes('style') && !lora.tags.includes('speed')
  );
  $: otherLoRAs = availableLoRAs.filter(lora =>
    !lora.tags.includes('speed') && !lora.tags.includes('lcm') && !lora.tags.includes('style')
  );
</script>

<div class="space-y-4">
  <div class="flex items-center justify-between">
    <h3 class="heading">🎨 LoRA 选择</h3>
    <div class="text-xs text-text-tertiary">
      已安装: {availableLoRAs.length} 个
    </div>
  </div>

  {#if loading}
    <div class="flex justify-center py-4">
      <div class="animate-spin h-5 w-5 border-2 border-primary border-t-transparent rounded-full"></div>
    </div>
  {:else if availableLoRAs.length === 0}
    <div class="text-center py-6 bg-surface/50 rounded-xl border border-border">
      <div class="text-3xl mb-2">📦</div>
      <p class="text-sm text-text-secondary mb-1">暂无已安装的LoRA</p>
      <p class="text-xs text-text-tertiary">请先在模型管理器中下载LoRA</p>
    </div>
  {:else}
    <!-- LoRA选择器 -->
    <div class="space-y-3">
      <div>
        <label for="lora-select" class="label">选择LoRA模型</label>
        <select
          id="lora-select"
          bind:value={selectedLoRA}
          class="input"
          on:change={updateLoRASelection}
        >
          <option value="none">不使用LoRA</option>

          {#if acceleratedLoRAs.length > 0}
            <optgroup label="⚡ 加速类LoRA">
              {#each acceleratedLoRAs as lora}
                <option value={lora.id}>{lora.name} ({lora.size})</option>
              {/each}
            </optgroup>
          {/if}

          {#if styleLoRAs.length > 0}
            <optgroup label="🎨 风格类LoRA">
              {#each styleLoRAs as lora}
                <option value={lora.id}>{lora.name} ({lora.size})</option>
              {/each}
            </optgroup>
          {/if}

          {#if otherLoRAs.length > 0}
            <optgroup label="📦 其他LoRA">
              {#each otherLoRAs as lora}
                <option value={lora.id}>{lora.name} ({lora.size})</option>
              {/each}
            </optgroup>
          {/if}
        </select>
      </div>

      <!-- 当前选中LoRA的详细信息 -->
      {#if selectedLoRA !== 'none'}
        {@const selectedLoraInfo = availableLoRAs.find(lora => lora.id === selectedLoRA)}
        {#if selectedLoraInfo}
          <div class="bg-surface/50 p-4 rounded-xl border border-border">
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <h4 class="text-sm font-semibold text-text-primary mb-1">
                  {selectedLoraInfo.name}
                </h4>
                <p class="text-xs text-text-secondary mb-2">
                  {selectedLoraInfo.description}
                </p>
                <div class="flex flex-wrap gap-1">
                  {#each selectedLoraInfo.tags as tag}
                    <span class="px-2 py-1 bg-primary/10 text-primary rounded-full text-xs">
                      {tag}
                    </span>
                  {/each}
                  <span class="px-2 py-1 bg-surface text-text-tertiary rounded-full text-xs">
                    {selectedLoraInfo.size}
                  </span>
                </div>
              </div>
            </div>
          </div>
        {/if}
      {:else}
        <div class="bg-surface/30 p-3 rounded-xl border border-border">
          <p class="text-sm text-text-secondary">
            📌 当前未选择LoRA，将使用基础模型进行生成
          </p>
        </div>
      {/if}
    </div>
  {/if}
</div>