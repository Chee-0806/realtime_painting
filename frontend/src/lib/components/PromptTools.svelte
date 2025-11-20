<script lang="ts">
  import { pipelineValues } from '$lib/store';
  
  // Prompt模板
  const promptTemplates = [
    { name: '默认', value: '' },
    { name: '写实风格', value: 'photorealistic, highly detailed, 8k uhd, professional photography' },
    { name: '动漫风格', value: 'anime style, vibrant colors, detailed illustration, high quality' },
    { name: '油画风格', value: 'oil painting, artistic, classical art style, detailed brushstrokes' },
    { name: '赛博朋克', value: 'cyberpunk style, neon lights, futuristic, sci-fi, detailed' },
    { name: '水彩画', value: 'watercolor painting, soft colors, artistic, delicate' }
  ];
  
  // 通配符选项
  const wildcards = [
    { name: '随机颜色', value: '{red|blue|green|yellow|purple|orange}' },
    { name: '随机时间', value: '{morning|afternoon|evening|night}' },
    { name: '随机天气', value: '{sunny|cloudy|rainy|snowy|foggy}' },
    { name: '随机情绪', value: '{happy|sad|angry|peaceful|excited}' }
  ];
  
  // Prompt历史记录（最多保存20条）
  let promptHistory: string[] = [];
  const MAX_HISTORY = 20;
  
  // 从localStorage加载历史记录
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('prompt_history');
    if (saved) {
      try {
        promptHistory = JSON.parse(saved);
      } catch (e) {
        console.error('Failed to load prompt history:', e);
      }
    }
  }
  
  // 保存历史记录到localStorage
  function saveHistory() {
    if (typeof window !== 'undefined') {
      localStorage.setItem('prompt_history', JSON.stringify(promptHistory));
    }
  }
  
  // 添加到历史记录
  export function addToHistory(prompt: string) {
    if (!prompt || prompt.trim() === '') return;
    
    // 移除重复项
    promptHistory = promptHistory.filter(p => p !== prompt);
    
    // 添加到开头
    promptHistory.unshift(prompt);
    
    // 限制数量
    if (promptHistory.length > MAX_HISTORY) {
      promptHistory = promptHistory.slice(0, MAX_HISTORY);
    }
    
    saveHistory();
  }
  
  // 应用模板
  function applyTemplate(template: string) {
    const currentPrompt = $pipelineValues.prompt || '';
    const newPrompt = currentPrompt ? `${currentPrompt}, ${template}` : template;
    
    pipelineValues.update(values => ({
      ...values,
      prompt: newPrompt
    }));
  }
  
  // 插入通配符
  function insertWildcard(wildcard: string) {
    const currentPrompt = $pipelineValues.prompt || '';
    const newPrompt = currentPrompt ? `${currentPrompt} ${wildcard}` : wildcard;
    
    pipelineValues.update(values => ({
      ...values,
      prompt: newPrompt
    }));
  }
  
  // 从历史记录加载
  function loadFromHistory(prompt: string) {
    pipelineValues.update(values => ({
      ...values,
      prompt: prompt
    }));
  }
  
  // 清除历史记录
  function clearHistory() {
    if (confirm('确定要清除所有历史记录吗？')) {
      promptHistory = [];
      saveHistory();
    }
  }
  
  // 显示/隐藏状态
  let showTemplates = false;
  let showWildcards = false;
  let showHistory = false;
</script>

<div class="prompt-tools space-y-2">
  <!-- 工具栏按钮 -->
  <div class="flex gap-2 flex-wrap">
    <button
      type="button"
      class="btn-secondary text-sm"
      on:click={() => showTemplates = !showTemplates}
    >
      📝 模板
    </button>
    
    <button
      type="button"
      class="btn-secondary text-sm"
      on:click={() => showWildcards = !showWildcards}
    >
      🎲 通配符
    </button>
    
    <button
      type="button"
      class="btn-secondary text-sm"
      on:click={() => showHistory = !showHistory}
    >
      📜 历史 ({promptHistory.length})
    </button>
  </div>
  
  <!-- 模板面板 -->
  {#if showTemplates}
    <div class="tool-panel">
      <div class="flex justify-between items-center mb-2">
        <h4 class="text-sm font-semibold">Prompt模板</h4>
        <button
          type="button"
          class="text-text-secondary hover:text-text-primary"
          on:click={() => showTemplates = false}
        >
          ✕
        </button>
      </div>
      <div class="grid grid-cols-2 gap-2">
        {#each promptTemplates as template}
          <button
            type="button"
            class="btn-ghost text-sm text-left"
            on:click={() => applyTemplate(template.value)}
            disabled={!template.value}
          >
            {template.name}
          </button>
        {/each}
      </div>
    </div>
  {/if}
  
  <!-- 通配符面板 -->
  {#if showWildcards}
    <div class="tool-panel">
      <div class="flex justify-between items-center mb-2">
        <h4 class="text-sm font-semibold">通配符</h4>
        <button
          type="button"
          class="text-text-secondary hover:text-text-primary"
          on:click={() => showWildcards = false}
        >
          ✕
        </button>
      </div>
      <div class="space-y-1">
        {#each wildcards as wildcard}
          <button
            type="button"
            class="btn-ghost text-sm text-left w-full"
            on:click={() => insertWildcard(wildcard.value)}
          >
            <span class="font-medium">{wildcard.name}:</span>
            <span class="text-text-secondary ml-2">{wildcard.value}</span>
          </button>
        {/each}
      </div>
      <div class="mt-2 text-xs text-text-secondary">
        💡 通配符会在生成时随机选择一个选项
      </div>
    </div>
  {/if}
  
  <!-- 历史记录面板 -->
  {#if showHistory}
    <div class="tool-panel">
      <div class="flex justify-between items-center mb-2">
        <h4 class="text-sm font-semibold">历史记录</h4>
        <div class="flex gap-2">
          {#if promptHistory.length > 0}
            <button
              type="button"
              class="text-xs text-text-secondary hover:text-text-primary"
              on:click={clearHistory}
            >
              清除
            </button>
          {/if}
          <button
            type="button"
            class="text-text-secondary hover:text-text-primary"
            on:click={() => showHistory = false}
          >
            ✕
          </button>
        </div>
      </div>
      {#if promptHistory.length > 0}
        <div class="space-y-1 max-h-60 overflow-y-auto">
          {#each promptHistory as prompt, index}
            <button
              type="button"
              class="btn-ghost text-sm text-left w-full truncate"
              on:click={() => loadFromHistory(prompt)}
              title={prompt}
            >
              {index + 1}. {prompt}
            </button>
          {/each}
        </div>
      {:else}
        <div class="text-sm text-text-secondary text-center py-4">
          暂无历史记录
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .prompt-tools {
    margin-top: 0.5rem;
  }
  
  .tool-panel {
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.5rem;
    padding: 0.75rem;
  }
  
  .btn-secondary {
    padding: 0.375rem 0.75rem;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 0.375rem;
    color: inherit;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .btn-secondary:hover {
    background: rgba(255, 255, 255, 0.15);
    border-color: rgba(255, 255, 255, 0.3);
  }
  
  .btn-ghost {
    padding: 0.375rem 0.75rem;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 0.375rem;
    color: inherit;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .btn-ghost:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  .btn-ghost:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
