<script lang="ts">
  export let theme: 'default' | 'drawing' | 'gallery' = 'default';
  export let title: string = '';
  export let subtitle: string = '';
  export let showActions: boolean = false;
  export let containerClass: string = '';

  $: themeClass = `page-theme-${theme}`;
  $: containerClasses = `container-main ${containerClass}`.trim();
</script>

<div class="page-layout {themeClass}">
  <!-- 页面头部 -->
  <div class="page-header">
    <div class="{containerClasses}">
      <div class="flex items-center justify-between">
        <div class="text-center flex-1">
          {#if title}
            <h1 class="page-title {theme !== 'default' ? 'text-gradient' : ''}">
              {title}
            </h1>
          {/if}
          {#if subtitle}
            <p class="page-subtitle">{subtitle}</p>
          {/if}
        </div>

        {#if showActions}
          <div class="flex items-center gap-4">
            <slot name="actions" />
          </div>
        {/if}
      </div>
    </div>
  </div>

  <!-- 页面内容 -->
  <main class="{containerClasses}">
    <slot />
  </main>

  <!-- 固定操作按钮 -->
  <div class="fixed bottom-6 right-6 z-50">
    <slot name="floating-actions" />
  </div>
</div>

<style>
  .page-layout {
    @apply min-h-screen;
    background: var(--page-bg, var(--color-surface));
    color: var(--text-primary, var(--color-text-primary));
    transition: background var(--duration-normal) var(--ease-out);
  }

  .page-header {
    padding: var(--space-2xl) 0 var(--space-xl);
    text-align: center;
  }

  .page-title {
    font-size: var(--font-size-4xl);
    font-weight: var(--font-weight-bold);
    margin-bottom: var(--space-sm);
    line-height: var(--line-height-tight);
  }

  .page-subtitle {
    font-size: var(--font-size-lg);
    color: var(--text-secondary, var(--color-text-secondary));
    line-height: var(--line-height-normal);
    margin-top: var(--space-xs);
  }

  .container-main {
    max-width: 1280px;
    margin: 0 auto;
    padding: 0 var(--space-md);
  }

  @media (min-width: 640px) {
    .container-main {
      padding: 0 var(--space-lg);
    }
  }

  @media (min-width: 1024px) {
    .container-main {
      padding: 0 var(--space-xl);
    }
  }
</style>