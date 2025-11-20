<script lang="ts">
  export let message: string = '';
  
  $: show = message.length > 0;
</script>

{#if show}
  <div class="card-compact mb-6 bg-warning/10 border-warning/30">
    <div class="flex items-center gap-2">
      <span class="text-warning text-lg">⚠️</span>
      <p class="text-sm text-text-primary">{message}</p>
    </div>
  </div>
{/if}

