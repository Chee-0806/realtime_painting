<script lang="ts">
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  
  const navItems = [
    { path: '/', label: '🎨 实时生成', icon: '🎨' },
    { path: '/canvas', label: '✏️ 画板', icon: '✏️' },
    { path: '/settings', label: '⚙️ 设置', icon: '⚙️' },
    { path: '/tools', label: '🛠️ 工具', icon: '🛠️' },
  ];
  
  function isActive(path: string): boolean {
    if (path === '/') {
      return $page.url.pathname === '/';
    }
    return $page.url.pathname.startsWith(path);
  }
  
  function handleLogoClick() {
    goto('/');
  }
</script>

<nav class="bg-surface-elevated border-b border-border sticky top-0 z-50">
  <div class="container mx-auto max-w-7xl px-4">
    <div class="flex items-center justify-between h-16">
      <!-- Logo -->
      <div class="flex items-center gap-4">
        <button
          on:click={handleLogoClick}
          class="text-xl font-bold text-text-primary hover:text-primary transition-colors cursor-pointer"
          type="button"
        >
          ArtFlow
        </button>
      </div>
      
      <!-- Navigation Links -->
      <div class="flex items-center gap-1">
        {#each navItems as item}
          <a
            href={item.path}
            class="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
              {isActive(item.path)
                ? 'bg-primary text-white'
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

