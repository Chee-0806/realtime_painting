<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { lcmLiveStatus, LCMLiveStatus, userIdStore } from '$lib/lcmLive';
  import { page } from '$app/stores';
  
  let imgElement: HTMLImageElement;
  let imageUrl: string | null = null;

  // 支持通过 prop 指定 userId 和流路径
  export let userId: string | null = null;
  export let streamPath: string | null = null;

  // 如果没有通过 prop 传入 userId，则从 store 获取（实时生成功能）
  $: finalUserId = userId ?? $userIdStore;
  $: isRunning = $lcmLiveStatus === LCMLiveStatus.RUNNING || $lcmLiveStatus === LCMLiveStatus.CONNECTED;
  
  // 根据路由或 prop 决定使用哪个接口
  $: {
    if (!finalUserId) {
      imageUrl = null;
    } else if (streamPath) {
      // 如果指定了 streamPath，直接使用
      imageUrl = `${streamPath}/${finalUserId}`;
    } else {
      // 否则根据路由自动判断
      const currentPath = $page.url.pathname;
      if (currentPath.startsWith('/canvas')) {
        // 画板功能使用 /api/stream
        imageUrl = `/api/stream/${finalUserId}`;
      } else {
        // 实时生成功能使用 /api/realtime/stream
        imageUrl = `/api/realtime/stream/${finalUserId}`;
      }
    }
  }

  // 调试日志
  $: console.log('ImagePlayer: userId 变化', {
    finalUserId,
    propUserId: userId,
    storeUserId: $userIdStore,
    status: $lcmLiveStatus,
    isRunning,
    imageUrl,
    streamPath,
    pathname: $page.url.pathname
  });
  
  $: if (imageUrl) {
    console.log('ImagePlayer: 设置流 URL', imageUrl, {
      userId,
      status: $lcmLiveStatus,
      isRunning,
      hasImgElement: !!imgElement
    });
    // 强制浏览器重新加载图像
    if (imgElement && imgElement.src !== imageUrl) {
      imgElement.src = imageUrl;
      console.log('ImagePlayer: 强制更新 img.src', imageUrl);
    }
  } else {
    console.log('ImagePlayer: imageUrl 未设置', {
      userId,
      status: $lcmLiveStatus,
      isRunning
    });
  }
</script>

<div class="flex flex-col items-center justify-center min-h-[512px] bg-surface-elevated rounded-lg border border-border p-4 w-full">
  {#if imageUrl}
    <img
      bind:this={imgElement}
      src={imageUrl}
      alt="生成结果"
      class="max-w-full max-h-full object-contain rounded-lg w-full"
      style="max-height: 70vh; min-height: 200px; background: #1a1a1a;"
      on:load={() => console.log('ImagePlayer: 图像加载成功', imageUrl)}
      on:error={(e) => {
        console.warn('ImagePlayer: 图像流尚未就绪，等待数据...', imageUrl);
        // 不显示错误，因为流可能还没有数据
      }}
    />
  {:else}
    <div class="flex flex-col items-center gap-4 text-text-secondary w-full">
      <div class="text-6xl opacity-50">🖼️</div>
      <p class="text-lg font-medium">生成结果</p>
      {#if !isRunning}
        <p class="text-sm text-text-tertiary text-center">
          点击"开始生成"按钮开始实时生成
        </p>
      {:else}
        <p class="text-sm text-text-tertiary text-center">
          等待生成结果...
        </p>
      {/if}
    </div>
  {/if}
</div>

