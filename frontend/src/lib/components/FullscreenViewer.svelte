<script lang="ts">
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';

  // Props
  export let imageUrl: string | null = null;
  export let isOpen: boolean = false;
  export let title: string = '全屏预览';
  export let showControls: boolean = true;

  // 内部状态
  let isFullscreenActive: boolean = false;
  let imgElement: HTMLImageElement;
  let viewerContainer: HTMLDivElement;
  let hideTimeout: number | null = null;
  let controlsVisible: boolean = true;

  const dispatch = createEventDispatcher();

  // 全屏状态管理
  $: {
    if (isOpen && viewerContainer) {
      requestFullscreen();
    } else if (!isOpen && isFullscreenActive) {
      exitFullscreen();
    }
  }

  function requestFullscreen() {
    if (viewerContainer && !isFullscreenActive) {
      if (viewerContainer.requestFullscreen) {
        viewerContainer.requestFullscreen();
      } else if ((viewerContainer as any).webkitRequestFullscreen) {
        (viewerContainer as any).webkitRequestFullscreen();
      } else if ((viewerContainer as any).mozRequestFullScreen) {
        (viewerContainer as any).mozRequestFullScreen();
      } else if ((viewerContainer as any).msRequestFullscreen) {
        (viewerContainer as any).msRequestFullscreen();
      }
    }
  }

  function exitFullscreen() {
    if (isFullscreenActive) {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      } else if ((document as any).webkitExitFullscreen) {
        (document as any).webkitExitFullscreen();
      } else if ((document as any).mozCancelFullScreen) {
        (document as any).mozCancelFullScreen();
      } else if ((document as any).msExitFullscreen) {
        (document as any).msExitFullscreen();
      }
    }
  }

  function handleFullscreenChange() {
    isFullscreenActive = !!(
      document.fullscreenElement ||
      (document as any).webkitFullscreenElement ||
      (document as any).mozFullScreenElement ||
      (document as any).msFullscreenElement
    );

    if (!isFullscreenActive) {
      // 退出全屏时关闭组件
      dispatch('close');
    }
  }

  function handleClose() {
    dispatch('close');
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      handleClose();
    } else if (e.key === 'f' || e.key === 'F') {
      toggleControls();
    }
  }

  function handleImageClick(e: MouseEvent) {
    // 双击切换全屏状态（但这里已经在全屏中了，所以关闭）
    if (e.detail === 2) {
      handleClose();
    }
  }

  function toggleControls() {
    controlsVisible = !controlsVisible;

    if (hideTimeout) {
      clearTimeout(hideTimeout);
      hideTimeout = null;
    }

    if (!controlsVisible) {
      hideTimeout = setTimeout(() => {
        controlsVisible = true;
      }, 3000);
    }
  }

  function handleMouseMove() {
    if (!controlsVisible) {
      controlsVisible = true;
    }

    if (hideTimeout) {
      clearTimeout(hideTimeout);
    }

    hideTimeout = setTimeout(() => {
      controlsVisible = false;
    }, 3000);
  }

  onMount(() => {
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('keydown', handleKeydown);

    if (viewerContainer) {
      viewerContainer.addEventListener('mousemove', handleMouseMove);
    }
  });

  onDestroy(() => {
    document.removeEventListener('fullscreenchange', handleFullscreenChange);
    document.removeEventListener('keydown', handleKeydown);

    if (hideTimeout) {
      clearTimeout(hideTimeout);
    }

    if (isFullscreenActive) {
      exitFullscreen();
    }
  });
</script>

{#if isOpen}
  <div
    bind:this={viewerContainer}
    class="fullscreen-viewer"
    on:click={handleClose}
  >
    <!-- 背景遮罩 -->
    <div class="fullscreen-backdrop"></div>

    <!-- 图像容器 -->
    <div class="fullscreen-content">
      {#if imageUrl}
        <img
          bind:this={imgElement}
          src={imageUrl}
          alt={title}
          class="fullscreen-image"
          on:click|stopPropagation={handleImageClick}
          on:load={() => console.log('FullscreenViewer: 图像加载成功')}
          on:error={(e) => {
            console.warn('FullscreenViewer: 图像加载失败', imageUrl);
          }}
        />
      {:else}
        <div class="fullscreen-empty">
          <div class="empty-icon">🖼️</div>
          <div class="empty-text">无图像可显示</div>
        </div>
      {/if}
    </div>

    <!-- 控制栏 -->
    {#if showControls}
      <div
        class="fullscreen-controls {controlsVisible ? 'visible' : 'hidden'}"
        on:click|stopPropagation
      >
        <div class="controls-header">
          <h3 class="controls-title">{title}</h3>
          <div class="controls-actions">
            <button
              on:click={toggleControls}
              class="control-btn"
              title="显示/隐藏控制栏 (F)"
            >
              {controlsVisible ? '👁️' : '👁️‍🗨️'}
            </button>
            <button
              on:click={handleClose}
              class="control-btn close"
              title="关闭全屏 (ESC)"
            >
              ✕
            </button>
          </div>
        </div>

        <div class="controls-info">
          <div class="info-item">
            <span class="info-label">状态:</span>
            <span class="info-value">
              {imageUrl ? '实时流' : '未连接'}
            </span>
          </div>
          <div class="info-item">
            <span class="info-label">提示:</span>
            <span class="info-value">双击图像或按 ESC 退出全屏</span>
          </div>
        </div>
      </div>
    {/if}
  </div>
{/if}

<style>
  .fullscreen-viewer {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    background: rgba(0, 0, 0, 0.95);
    backdrop-filter: blur(10px);
  }

  .fullscreen-backdrop {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: radial-gradient(circle at center, rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.95));
    z-index: -1;
  }

  .fullscreen-content {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    overflow: hidden;
  }

  .fullscreen-image {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    border-radius: 8px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8);
    cursor: pointer;
    transition: transform 0.3s ease;
  }

  .fullscreen-image:hover {
    transform: scale(1.02);
  }

  .fullscreen-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    color: #888;
    text-align: center;
  }

  .empty-icon {
    font-size: 6rem;
    opacity: 0.5;
  }

  .empty-text {
    font-size: 1.2rem;
    font-weight: 500;
  }

  .fullscreen-controls {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    background: linear-gradient(to bottom, rgba(0, 0, 0, 0.9), transparent);
    padding: 1.5rem 2rem;
    color: white;
    transition: opacity 0.3s ease, transform 0.3s ease;
  }

  .fullscreen-controls.hidden {
    opacity: 0;
    transform: translateY(-20px);
    pointer-events: none;
  }

  .fullscreen-controls.visible {
    opacity: 1;
    transform: translateY(0);
  }

  .controls-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
  }

  .controls-title {
    font-size: 1.5rem;
    font-weight: 600;
    margin: 0;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
  }

  .controls-actions {
    display: flex;
    gap: 0.5rem;
  }

  .control-btn {
    background: rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: white;
    padding: 0.5rem 0.75rem;
    border-radius: 6px;
    cursor: pointer;
    font-size: 1.1rem;
    transition: all 0.2s ease;
    backdrop-filter: blur(10px);
  }

  .control-btn:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: translateY(-1px);
  }

  .control-btn.close {
    background: rgba(239, 68, 68, 0.8);
    border-color: rgba(239, 68, 68, 0.9);
  }

  .control-btn.close:hover {
    background: rgba(239, 68, 68, 1);
  }

  .controls-info {
    display: flex;
    gap: 2rem;
    font-size: 0.9rem;
    opacity: 0.9;
  }

  .info-item {
    display: flex;
    gap: 0.5rem;
  }

  .info-label {
    font-weight: 500;
    opacity: 0.7;
  }

  .info-value {
    font-weight: 400;
  }

  /* 移动端适配 */
  @media (max-width: 768px) {
    .fullscreen-content {
      padding: 1rem;
    }

    .fullscreen-controls {
      padding: 1rem;
    }

    .controls-title {
      font-size: 1.2rem;
    }

    .controls-info {
      flex-direction: column;
      gap: 0.5rem;
      font-size: 0.8rem;
    }

    .control-btn {
      padding: 0.4rem 0.6rem;
      font-size: 1rem;
    }

    .empty-icon {
      font-size: 4rem;
    }

    .empty-text {
      font-size: 1rem;
    }
  }

  /* 触摸设备优化 */
  @media (pointer: coarse) {
    .fullscreen-image {
      cursor: default;
    }

    .fullscreen-controls {
      /* 在触摸设备上默认显示控制栏，因为鼠标移动事件可能不触发 */
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* 高对比度模式支持 */
  @media (prefers-contrast: high) {
    .fullscreen-viewer {
      background: black;
    }

    .fullscreen-controls {
      background: rgba(0, 0, 0, 1);
    }

    .control-btn {
      background: white;
      color: black;
      border: 2px solid white;
    }

    .control-btn.close {
      background: red;
      color: white;
      border-color: red;
    }
  }

  /* 减少动画模式支持 */
  @media (prefers-reduced-motion: reduce) {
    .fullscreen-image,
    .fullscreen-controls,
    .control-btn {
      transition: none;
    }

    .fullscreen-image:hover {
      transform: none;
    }
  }
</style>