<script lang="ts">
  import '../styles/page-templates.css';

  export let layout: 'sidebar' | 'centered' | 'full' | 'grid' = 'centered';
  export let title: string = '';
  export let subtitle: string = '';
  export let padding: 'normal' | 'tight' | 'loose' = 'normal';
  export let maxWidth: 'sm' | 'md' | 'lg' | 'xl' | 'full' = 'lg';
  export let background: 'default' | 'gradient' | 'pattern' = 'default';

  $: layoutClass = `layout-${layout}`;
  $: paddingClass = `padding-${padding}`;
  $: maxWidthClass = `max-width-${maxWidth}`;
  $: backgroundClass = `background-${background}`;
  $: containerClasses = `${layoutClass} ${paddingClass} ${maxWidthClass} ${backgroundClass}`.trim();
</script>

<div class="page-template {containerClasses}">
  <!-- 页面头部 -->
  {#if title || subtitle}
    <header class="page-header">
      <div class="header-content">
        {#if title}
          <h1 class="page-title">{title}</h1>
        {/if}
        {#if subtitle}
          <p class="page-subtitle">{subtitle}</p>
        {/if}
      </div>
    </header>
  {/if}

  <!-- 页面内容 -->
  <main class="page-content">
    <slot />
  </main>

  <!-- 页面底部 -->
  <footer class="page-footer">
    <slot name="footer" />
  </footer>

  <!-- 浮动操作区域 -->
  <div class="floating-actions">
    <slot name="floating" />
  </div>
</div>

<style>
  .page-template {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    position: relative;
  }

  /* 布局类型 */
  .layout-centered {
    max-width: 1024px;
    margin: 0 auto;
    padding: var(--space-lg);
  }

  .layout-sidebar {
    display: grid;
    grid-template-columns: 300px 1fr;
    gap: var(--space-xl);
    padding: var(--space-lg);
    max-width: 1400px;
    margin: 0 auto;
  }

  .layout-full {
    padding: var(--space-lg);
  }

  .layout-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: var(--space-xl);
    padding: var(--space-lg);
    max-width: 1200px;
    margin: 0 auto;
  }

  /* 内边距 */
  .padding-tight {
    padding: var(--space-md);
  }

  .padding-normal {
    padding: var(--space-lg);
  }

  .padding-loose {
    padding: var(--space-2xl);
  }

  /* 最大宽度 */
  .max-width-sm {
    max-width: 640px;
  }

  .max-width-md {
    max-width: 768px;
  }

  .max-width-lg {
    max-width: 1024px;
  }

  .max-width-xl {
    max-width: 1280px;
  }

  .max-width-full {
    max-width: none;
  }

  /* 背景 */
  .background-default {
    background: var(--color-surface);
  }

  .background-gradient {
    background: var(--gradient-primary);
  }

  .background-pattern {
    background: var(--color-surface);
    background-image:
      radial-gradient(circle at 1px 1px, var(--color-border) 1px, transparent 1px);
    background-size: 20px 20px;
  }

  /* 页面头部 */
  .page-header {
    margin-bottom: var(--space-2xl);
    text-align: center;
  }

  .header-content {
    max-width: 800px;
    margin: 0 auto;
  }

  .page-title {
    font-size: var(--font-size-3xl);
    font-weight: var(--font-weight-bold);
    color: var(--color-text-primary);
    margin-bottom: var(--space-sm);
    line-height: var(--line-height-tight);
  }

  .page-subtitle {
    font-size: var(--font-size-lg);
    color: var(--color-text-secondary);
    line-height: var(--line-height-normal);
  }

  /* 页面内容 */
  .page-content {
    flex: 1;
    width: 100%;
  }

  /* 页面底部 */
  .page-footer {
    margin-top: var(--space-2xl);
    padding-top: var(--space-xl);
    border-top: 1px solid var(--color-border);
  }

  /* 浮动操作 */
  .floating-actions {
    position: fixed;
    bottom: var(--space-xl);
    right: var(--space-xl);
    z-index: var(--z-fixed);
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
  }

  /* 响应式设计 */
  @media (max-width: 768px) {
    .layout-sidebar {
      grid-template-columns: 1fr;
      gap: var(--space-lg);
    }

    .layout-grid {
      grid-template-columns: 1fr;
      gap: var(--space-lg);
    }

    .page-title {
      font-size: var(--font-size-2xl);
    }

    .floating-actions {
      bottom: var(--space-lg);
      right: var(--space-lg);
    }
  }
</style>