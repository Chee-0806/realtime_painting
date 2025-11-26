<script lang="ts">
  import '../styles/navigation.css';
  import Navigation from '$lib/components/Navigation.svelte';

  export let hideNavigation: boolean = false;
  export let fullWidth: boolean = false;
  export let title: string = '';
  export let subtitle: string = '';

  // 根据当前路由自动判断是否隐藏导航
  import { page } from '$app/stores';

  $: shouldHideNavigation = hideNavigation || $page.url.pathname.startsWith('/gallery/');
</script>

<div class="app-layout {fullWidth ? 'full-width' : ''}">
  {#if !shouldHideNavigation}
    <Navigation>
      <slot name="nav-actions" />
    </Navigation>
  {/if}

  <div class="app-content">
    {#if title || subtitle}
      <div class="page-header">
        <div class="container-main">
          {#if title}
            <h1 class="page-title">{title}</h1>
          {/if}
          {#if subtitle}
            <p class="page-subtitle">{subtitle}</p>
          {/if}
        </div>
      </div>
    {/if}

    <main class="page-main">
      <slot />
    </main>
  </div>

  <div class="fixed bottom-6 right-6 z-50">
    <slot name="floating-actions" />
  </div>
</div>

<style>
  .app-layout {
    @apply min-h-screen bg-surface text-text-primary;
    font-family: var(--font-family-base);
  }

  .app-layout.full-width {
    --container-max-width: 100%;
  }

  .app-content {
    @apply min-h-screen;
  }

  .app-layout:not(.full-width) .app-content {
    padding-top: 4rem; /* 为导航栏留出空间 */
  }

  .page-header {
    padding: var(--space-2xl) 0 var(--space-xl);
  }

  .page-title {
    @apply title;
    margin-bottom: var(--space-sm);
  }

  .page-subtitle {
    @apply subtitle;
  }

  .page-main {
    padding-bottom: var(--space-2xl);
  }

  .container-main {
    @apply container-main;
  }
</style>