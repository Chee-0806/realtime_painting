<script lang="ts">
  import { page } from '$app/stores';

  const navItems = [
    { path: '/', label: '🎨 实时生成', icon: '🎨' },
    { path: '/drawing', label: '🖌️ 专业画板', icon: '🖌️' },
    { path: '/canvas', label: '✏️ 简易画板', icon: '✏️' },
    { path: '/gallery', label: '🖼️ 作品图库', icon: '🖼️' },
    { path: '/settings', label: '⚙️ 设置', icon: '⚙️' },
    { path: '/tools', label: '🛠️ 工具', icon: '🛠️' },
  ];

  // 响应式计算当前路径
  $: currentPath = $page.url.pathname;
</script>

<nav class="bg-surface-elevated border-b border-border sticky top-0 z-50">
  <div class="container mx-auto max-w-7xl px-4">
    <div class="flex items-center justify-between h-16">
      <!-- Logo -->
      <div class="flex items-center gap-4">
        <a
          href="/"
          class="text-xl font-bold text-text-primary hover:text-primary transition-colors cursor-pointer"
        >
          ArtFlow
        </a>
      </div>

      <!-- Navigation Links -->
      <div class="flex items-center gap-1">
        {#each navItems as item}
          <a
            href={item.path}
            class="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 no-underline
              {currentPath === item.path
                ? 'bg-primary text-white shadow-lg'
                : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover'}"
          >
            {item.label}
          </a>
        {/each}
      </div>
      
      <!-- Actions Slot -->
      <div class="flex items-center gap-2">
        <slot name="actions" />
      </div>
    </div>
  </div>
</nav>

<style>
  nav {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  }
</style>

