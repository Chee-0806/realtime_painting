<script lang="ts">
  import InpaintingTools from '$lib/components/InpaintingTools.svelte';
</script>

<svelte:head>
  <title>工具 - ArtFlow</title>
</svelte:head>

<main class="min-h-screen bg-surface">
  <div class="container mx-auto max-w-6xl px-4 py-6">
    <div class="mb-6">
      <h1 class="title">🛠️ 高级工具</h1>
      <p class="subtitle">图像编辑和处理工具集合</p>
    </div>
    
    <div class="card">
      <InpaintingTools />
    </div>
  </div>
</main>

