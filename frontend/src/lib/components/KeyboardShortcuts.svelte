<script lang="ts">
  export let show: boolean = false;
  
  const shortcuts = [
    { key: 'Shift + ?', description: '显示/隐藏快捷键帮助' },
  ];
</script>

{#if show}
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    role="dialog"
    aria-modal="true"
    aria-labelledby="shortcuts-title"
    on:click={() => show = false}
    on:keydown={(e) => {
      if (e.key === 'Escape') {
        show = false;
      }
    }}
  >
    <div
      class="card max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto"
      on:click|stopPropagation
      role="document"
    >
      <div class="flex items-center justify-between mb-6">
        <h2 id="shortcuts-title" class="title">⌨️ 快捷键</h2>
        <button
          class="btn-ghost"
          on:click={() => show = false}
          type="button"
          aria-label="关闭"
        >
          ✕
        </button>
      </div>
      
      <div class="space-y-4">
        {#each shortcuts as shortcut}
          <div class="flex items-center justify-between py-2 border-b border-border">
            <span class="text-text-secondary">{shortcut.description}</span>
            <kbd class="px-3 py-1 bg-surface-elevated border border-border rounded-lg text-sm font-mono text-text-primary">
              {shortcut.key}
            </kbd>
          </div>
        {/each}
      </div>
      
      <div class="mt-6 pt-4 border-t border-border">
        <button
          class="btn-secondary w-full"
          on:click={() => show = false}
          type="button"
        >
          关闭
        </button>
      </div>
    </div>
  </div>
{/if}

