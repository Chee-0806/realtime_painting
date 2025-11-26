<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import type { Fields } from '$lib/types';
  import ErrorHandler from '$lib/components/ErrorHandler.svelte';
  import FullscreenViewer from '$lib/components/FullscreenViewer.svelte';
  import { setError, ErrorType } from '$lib/store';

  let userId: string | null = null;
  let userIdInput: string = '';
  let connectionStatus = '未连接';
  let imageLoaded = false;
  let currentImageUrl: string = '';
  let error: string = '';

  // 图库相关
  let galleryImages: Array<{
    id: string;
    url: string;
    timestamp: Date;
    prompt: string;
    isFavorite: boolean;
  }> = [];
  let showFavoritesOnly = false;
  let isAutoSaveEnabled = true;
  let autoSaveInterval: number | null = null;
  let showViewer = true;
  let showGallery = true;

  // 全屏预览状态
  let isFullscreenOpen = false;
  let fullscreenTitle = '实时预览 - 全屏模式';

  // 视图设置
  let viewMode: 'grid' | 'list' | 'masonry' = 'grid';
  let sortBy: 'timestamp' | 'prompt' | 'favorite' = 'timestamp';
  let sortOrder: 'asc' | 'desc' = 'desc';
  let searchQuery: string = '';

  // 分页和懒加载
  let currentPage = 1;
  let imagesPerPage = 12;
  let isLoadingMore = false;
  let hasMoreImages = false;

  // 应用图库主题
  onMount(() => {
    if (typeof document !== 'undefined') {
      document.body.classList.add('page-theme-gallery');
    }

    const urlParams = new URLSearchParams(window.location.search);
    const urlUserId = urlParams.get('userId');
    if (urlUserId) {
      userIdInput = urlUserId;
      connectToStream();
    }

    // 从本地存储加载图库
    loadGalleryFromStorage();

    // 启动自动保存
    if (isAutoSaveEnabled) {
      startAutoSave();
    }
  });

  onDestroy(() => {
    if (typeof document !== 'undefined') {
      document.body.classList.remove('page-theme-gallery');
    }
    if (autoSaveInterval) {
      clearInterval(autoSaveInterval);
    }
  });

  function loadGalleryFromStorage() {
    try {
      const stored = localStorage.getItem('artflow_gallery');
      if (stored) {
        galleryImages = JSON.parse(stored).map((img: any) => ({
          ...img,
          timestamp: new Date(img.timestamp)
        }));
        updateGalleryStats();
      }
    } catch (err) {
      console.error('加载图库失败:', err);
    }
  }

  function saveGalleryToStorage() {
    try {
      localStorage.setItem('artflow_gallery', JSON.stringify(galleryImages));
    } catch (err) {
      console.error('保存图库失败:', err);
      setError({
        type: ErrorType.API,
        message: '存储空间不足',
        details: '无法保存更多图像到本地存储',
        recoverable: true,
        suggestions: ['清理浏览器缓存', '删除一些收藏的图像']
      });
    }
  }

  function startAutoSave() {
    if (autoSaveInterval) clearInterval(autoSaveInterval);
    autoSaveInterval = setInterval(() => {
      if (currentImageUrl && imageLoaded) {
        captureCurrentImage();
      }
    }, 5000); // 每5秒自动保存一次
  }

  function stopAutoSave() {
    if (autoSaveInterval) {
      clearInterval(autoSaveInterval);
      autoSaveInterval = null;
    }
  }

  function connectToStream() {
    if (!userIdInput.trim()) {
      error = '请输入画板应用的 User ID';
      return;
    }

    userId = userIdInput.trim();
    connectionStatus = '正在连接...';
    error = '';
    imageLoaded = false;

    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
    currentImageUrl = `${protocol}//${window.location.host}/api/canvas/sessions/${userId}/stream`;
  }

  function disconnect() {
    currentImageUrl = '';
    userId = null;
    connectionStatus = '未连接';
    error = '';
    imageLoaded = false;
  }

  function handleImageLoad() {
    imageLoaded = true;
    error = '';
    connectionStatus = '已连接 - 正在接收图像';
  }

  function handleImageError() {
    error = '无法加载图像流。请确保：\n1. 画板应用已连接服务器\n2. 画板应用已点击"开始发送"按钮\n3. User ID 正确\n4. 画板应用正在绘制内容';
    connectionStatus = '连接错误';
    imageLoaded = false;
  }

  function captureCurrentImage() {
    if (!currentImageUrl || !imageLoaded) return;

    // 创建临时图像元素来捕获当前帧
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(img, 0, 0);
        canvas.toBlob((blob) => {
          if (blob) {
            const url = URL.createObjectURL(blob);
            const newImage = {
              id: Date.now().toString(),
              url: url,
              timestamp: new Date(),
              prompt: `自动保存 - ${new Date().toLocaleTimeString()}`,
              isFavorite: false
            };

            // 避免重复添加相似的图像
            const isDuplicate = galleryImages.some(existing => {
              return Math.abs(existing.timestamp.getTime() - newImage.timestamp.getTime()) < 1000;
            });

            if (!isDuplicate) {
              galleryImages.unshift(newImage);
              saveGalleryToStorage();
              updateGalleryStats();
            }
          }
        }, 'image/jpeg', 0.9);
      }
    };
    img.src = currentImageUrl;
  }

  function manualCapture() {
    captureCurrentImage();
    setError({
      type: ErrorType.API,
      message: '图像已保存到图库',
      details: '当前图像已成功保存到本地图库',
      recoverable: true,
      suggestions: []
    });
  }

  function toggleFavorite(imageId: string) {
    const image = galleryImages.find(img => img.id === imageId);
    if (image) {
      image.isFavorite = !image.isFavorite;
      saveGalleryToStorage();
    }
  }

  function deleteImage(imageId: string) {
    const index = galleryImages.findIndex(img => img.id === imageId);
    if (index !== -1) {
      URL.revokeObjectURL(galleryImages[index].url); // 释放内存
      galleryImages.splice(index, 1);
      saveGalleryToStorage();
      updateGalleryStats();
    }
  }

  function downloadImage(image: any) {
    const link = document.createElement('a');
    link.download = `artflow_${image.prompt.replace(/[^a-zA-Z0-9]/g, '_')}_${image.timestamp.getTime()}.jpg`;
    link.href = image.url;
    link.click();
  }

  function updateGalleryStats() {
    // 更新统计信息
    const totalImages = galleryImages.length;
    const favoriteCount = galleryImages.filter(img => img.isFavorite).length;
    console.log(`图库统计: 总计 ${totalImages} 张，收藏 ${favoriteCount} 张`);
  }

  function clearGallery() {
    if (confirm('确定要清空整个图库吗？此操作不可恢复。')) {
      // 释放所有图像URL
      galleryImages.forEach(img => URL.revokeObjectURL(img.url));
      galleryImages = [];
      saveGalleryToStorage();
      updateGalleryStats();
    }
  }

  function exportGallery() {
    if (galleryImages.length === 0) {
      setError({
        type: ErrorType.VALIDATION,
        message: '图库为空',
        details: '没有图像可以导出',
        recoverable: true,
        suggestions: []
      });
      return;
    }

    // 创建导出数据
    const exportData = {
      version: '1.0',
      timestamp: new Date().toISOString(),
      imageCount: galleryImages.length,
      images: galleryImages.map(img => ({
        id: img.id,
        timestamp: img.timestamp.toISOString(),
        prompt: img.prompt,
        isFavorite: img.isFavorite
        // 注意：不包含图像URL，因为它们是临时的blob URL
      }))
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.download = `artflow_gallery_export_${new Date().toISOString().split('T')[0]}.json`;
    link.href = url;
    link.click();
    URL.revokeObjectURL(url);

    setError({
      type: ErrorType.API,
      message: '图库元数据已导出',
      details: `导出了 ${galleryImages.length} 张图像的元数据`,
      recoverable: true,
      suggestions: ['注意：图像数据未包含在导出文件中']
    });
  }

  // 排序和过滤
  $: filteredAndSortedImages = galleryImages
    .filter(img => {
      if (showFavoritesOnly && !img.isFavorite) return false;
      if (searchQuery && !img.prompt.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      return true;
    })
    .sort((a, b) => {
      let comparison = 0;
      switch (sortBy) {
        case 'timestamp':
          comparison = a.timestamp.getTime() - b.timestamp.getTime();
          break;
        case 'prompt':
          comparison = a.prompt.localeCompare(b.prompt);
          break;
        case 'favorite':
          comparison = (a.isFavorite ? 1 : 0) - (b.isFavorite ? 1 : 0);
          break;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });

  // 分页
  $: paginatedImages = filteredAndSortedImages.slice(0, currentPage * imagesPerPage);
  $: hasMoreImages = paginatedImages.length < filteredAndSortedImages.length;

  function loadMoreImages() {
    if (!isLoadingMore && hasMoreImages) {
      isLoadingMore = true;
      setTimeout(() => {
        currentPage++;
        isLoadingMore = false;
      }, 300);
    }
  }

  function generateShareUrl(image: any) {
    const shareData = {
      title: 'ArtFlow 作品分享',
      text: `查看我的AI艺术作品: ${image.prompt}`,
      url: window.location.href
    };

    if (navigator.share && navigator.canShare && navigator.canShare(shareData)) {
      navigator.share(shareData);
    } else {
      // 复制链接到剪贴板
      navigator.clipboard.writeText(window.location.href).then(() => {
        setError({
          type: ErrorType.API,
          message: '链接已复制',
          details: '图库链接已复制到剪贴板',
          recoverable: true,
          suggestions: []
        });
      });
    }
  }

  // 全屏预览功能
  function openFullscreen() {
    if (currentImageUrl && imageLoaded) {
      isFullscreenOpen = true;
      fullscreenTitle = userId ? `实时预览 - ${userId}` : '实时预览 - 全屏模式';
    } else {
      setError({
        type: ErrorType.VALIDATION,
        message: '无法进入全屏模式',
        details: '请先连接画板应用并等待图像加载',
        recoverable: true,
        suggestions: ['确保画板应用已连接', '等待图像流开始']
      });
    }
  }

  function closeFullscreen() {
    isFullscreenOpen = false;
  }

  function handleFullscreenClose() {
    isFullscreenOpen = false;
  }
</script>

<svelte:head>
  <title>作品图库 - ArtFlow</title>
</svelte:head>

<!-- 使用专业图库主题 -->
<main class="page-layout page-theme-gallery">
  <div class="container">
    <ErrorHandler />

    <!-- 专业页面标题 -->
    <header class="gallery-header">
      <h1 class="page-title text-gradient">
        🖼️ 作品图库
      </h1>
      <p class="page-subtitle">展示和管理你的AI艺术作品集</p>

      <!-- 统计信息 -->
      <div class="gallery-stats">
        <div class="stat-item">
          <span class="stat-icon">📸</span>
          <div class="stat-content">
            <span class="stat-number">{galleryImages.length}</span>
            <span class="stat-label">总作品</span>
          </div>
        </div>
        <div class="stat-item">
          <span class="stat-icon">⭐</span>
          <div class="stat-content">
            <span class="stat-number">{galleryImages.filter(img => img.isFavorite).length}</span>
            <span class="stat-label">收藏</span>
          </div>
        </div>
        <div class="stat-item">
          <span class="stat-icon">🔄</span>
          <div class="stat-content">
            <span class="stat-number">{isAutoSaveEnabled ? '开启' : '关闭'}</span>
            <span class="stat-label">自动保存</span>
          </div>
        </div>
      </div>
    </header>

    <!-- 专业控制面板 -->
    <section class="control-panel">
      <div class="control-grid">
        <!-- 连接控制模块 -->
        <div class="control-module">
          <div class="module-header">
            <span class="module-icon">🔗</span>
            <h3 class="module-title">连接画板</h3>
          </div>
          <div class="module-content">
            <div class="connection-controls">
              <div class="input-group">
                <input
                  type="text"
                  bind:value={userIdInput}
                  placeholder="输入画板应用的 User ID"
                  class="connection-input"
                  on:keydown={(e) => {
                    if (e.key === 'Enter') {
                      connectToStream();
                    }
                  }}
                />
                <button
                  on:click={connectToStream}
                  disabled={!userIdInput.trim() || !!currentImageUrl}
                  class="connect-btn"
                >
                  {currentImageUrl ? '已连接' : '连接'}
                </button>
              </div>

              <div class="status-group">
                <div class="connection-status">
                  <div class="status-dot {currentImageUrl && imageLoaded ? 'online' : 'offline'}"></div>
                  <span class="status-text">{connectionStatus}</span>
                </div>
                {#if currentImageUrl}
                  <button
                    on:click={disconnect}
                    class="disconnect-btn"
                  >
                    断开连接
                  </button>
                {/if}
              </div>
            </div>
          </div>
        </div>

        <!-- 自动保存控制模块 -->
        <div class="control-module">
          <div class="module-header">
            <span class="module-icon">💾</span>
            <h3 class="module-title">自动保存</h3>
            <div class="module-badge">{galleryImages.length} 张图像</div>
          </div>
          <div class="module-content">
            <div class="auto-save-controls">
              <div class="toggle-group">
                <span class="toggle-label">自动保存</span>
                <button
                  on:click={() => {
                    isAutoSaveEnabled = !isAutoSaveEnabled;
                    if (isAutoSaveEnabled) {
                      startAutoSave();
                    } else {
                      stopAutoSave();
                    }
                  }}
                  class="toggle-switch {isAutoSaveEnabled ? 'active' : ''}"
                >
                  <div class="toggle-slider"></div>
                </button>
              </div>

              <div class="action-buttons">
                <button
                  on:click={manualCapture}
                  disabled={!currentImageUrl || !imageLoaded}
                  class="action-btn capture"
                >
                  <span class="action-icon">📸</span>
                  <span>手动保存</span>
                </button>
                <button
                  on:click={exportGallery}
                  disabled={galleryImages.length === 0}
                  class="action-btn export"
                >
                  <span class="action-icon">📤</span>
                  <span>导出数据</span>
                </button>
                <button
                  on:click={clearGallery}
                  disabled={galleryImages.length === 0}
                  class="action-btn clear"
                >
                  <span class="action-icon">🗑️</span>
                  <span>清空</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 主内容区域 -->
    <div class="main-content-grid">

      <!-- 实时预览模块 -->
      <section class="preview-section">
        <div class="section-header">
          <div class="section-title">
            <span class="section-icon">📺</span>
            <h3>实时预览</h3>
          </div>
          <div class="section-actions">
            <button
              on:click={openFullscreen}
              disabled={!currentImageUrl || !imageLoaded}
              class="fullscreen-btn"
              title="进入全屏模式"
            >
              🔳 全屏
            </button>
            <button
              on:click={() => showViewer = !showViewer}
              class="toggle-btn"
            >
              {showViewer ? '隐藏' : '显示'}
            </button>
          </div>
        </div>

              {#if showViewer}
          <div class="preview-container">
            {#if currentImageUrl && userId}
              <div class="preview-image-wrapper" role="button" tabindex="0" on:dblclick={openFullscreen} on:keydown={(e) => { if (e.key === 'Enter') openFullscreen(); }}>
                <img
                  src={currentImageUrl}
                  alt="实时生成图像"
                  class="preview-image"
                  on:load={handleImageLoad}
                  on:error={handleImageError}
                  title="双击进入全屏模式"
                />
                {#if !imageLoaded && !error}
                  <div class="preview-loading">
                    <div class="loading-spinner"></div>
                    <p class="loading-text">等待图像流...</p>
                  </div>
                {/if}
                {#if imageLoaded}
                  <div class="live-indicator">
                    <div class="live-dot"></div>
                    <span>实时</span>
                  </div>
                  <div class="fullscreen-hint">
                    <span>🔳 双击全屏</span>
                  </div>
                {/if}
              </div>
            {:else}
              <div class="preview-empty">
                <div class="empty-content">
                  <span class="empty-icon">🖼️</span>
                  <p class="empty-title">未连接</p>
                  <p class="empty-subtitle">输入 User ID 并连接画板应用</p>
                </div>
              </div>
            {/if}

            {#if error}
              <div class="error-message">
                <p class="error-text">{error}</p>
              </div>
            {/if}
          </div>
        {/if}
      </section>

      <!-- 图库管理模块 -->
      <section class="gallery-section">
        <div class="section-header">
          <div class="section-title">
            <span class="section-icon">🎨</span>
            <h3>作品集</h3>
            <div class="image-count">{filteredAndSortedImages.length} 张</div>
          </div>
          <button
            on:click={() => showGallery = !showGallery}
            class="toggle-btn"
          >
            {showGallery ? '隐藏' : '显示'}
          </button>
        </div>

        {#if showGallery}
          <!-- 筛选和排序控件 -->
          <div class="filter-controls">
            <div class="search-group">
              <input
                type="text"
                bind:value={searchQuery}
                placeholder="搜索提示词..."
                class="search-input"
              />
              <span class="search-icon">🔍</span>
            </div>

            <div class="filter-options">
              <select bind:value={viewMode} class="filter-select">
                <option value="grid">网格视图</option>
                <option value="list">列表视图</option>
                <option value="masonry">瀑布流</option>
              </select>

              <select bind:value={sortBy} class="filter-select">
                <option value="timestamp">按时间排序</option>
                <option value="prompt">按提示词</option>
                <option value="favorite">按收藏</option>
              </select>

              <select bind:value={sortOrder} class="filter-select">
                <option value="desc">降序</option>
                <option value="asc">升序</option>
              </select>

              <button
                on:click={() => showFavoritesOnly = !showFavoritesOnly}
                class="filter-btn {showFavoritesOnly ? 'active' : ''}"
              >
                {showFavoritesOnly ? '⭐ 已收藏' : '⭐ 全部'}
              </button>
            </div>
          </div>

          <!-- 图库内容 -->
          <div class="gallery-content">
            {#if paginatedImages.length === 0}
              <div class="empty-gallery">
                <span class="empty-icon">📷</span>
                <p class="empty-title">
                  {showFavoritesOnly ? '没有收藏的图像' : '图库为空'}
                </p>
                <p class="empty-subtitle">
                  连接画板应用并开始创作，图像会自动保存到这里
                </p>
              </div>
            {:else}
              <!-- 图库视图会在这里渲染 -->
              <div class="gallery-grid">
                {#each paginatedImages as image (image.id)}
                  <div class="gallery-item">
                    <div class="image-container">
                      <img
                        src={image.url}
                        alt={image.prompt}
                        class="gallery-image"
                      />
                      <div class="image-overlay">
                        <button
                          on:click={() => toggleFavorite(image.id)}
                          class="overlay-btn"
                          title={image.isFavorite ? '取消收藏' : '添加收藏'}
                        >
                          {image.isFavorite ? '⭐' : '☆'}
                        </button>
                        <button
                          on:click={() => downloadImage(image)}
                          class="overlay-btn"
                          title="下载"
                        >
                          💾
                        </button>
                        <button
                          on:click={() => generateShareUrl(image)}
                          class="overlay-btn"
                          title="分享"
                        >
                          📤
                        </button>
                        <button
                          on:click={() => deleteImage(image.id)}
                          class="overlay-btn delete"
                          title="删除"
                        >
                          🗑️
                        </button>
                      </div>
                      {#if image.isFavorite}
                        <div class="favorite-badge">⭐</div>
                      {/if}
                    </div>
                    <div class="image-info">
                      <p class="image-title" title={image.prompt}>
                        {image.prompt}
                      </p>
                      <p class="image-time">
                        {image.timestamp.toLocaleString()}
                      </p>
                    </div>
                  </div>
                {/each}
              </div>

              <!-- 加载更多按钮 -->
              {#if hasMoreImages}
                <div class="load-more">
                  <button
                    on:click={loadMoreImages}
                    disabled={isLoadingMore}
                    class="load-more-btn"
                  >
                    {isLoadingMore ? '加载中...' : '加载更多'}
                  </button>
                </div>
              {/if}
            {/if}
          </div>
        {/if}
      </section>
    </div>

    <!-- 专业使用指南 -->
    <section class="usage-guide">
      <div class="guide-header">
        <h3 class="guide-title">
          <span class="guide-icon">💡</span>
          <span>使用指南</span>
        </h3>
      </div>
      <div class="guide-content">
        <div class="guide-section">
          <div class="guide-item">
            <div class="guide-item-icon">🔗</div>
            <div class="guide-item-content">
              <h4 class="guide-item-title">连接画板</h4>
              <ul class="guide-item-list">
                <li>在画板应用中获取 User ID</li>
                <li>输入 User ID 并点击"连接"</li>
                <li>确保画板应用已开始发送数据</li>
              </ul>
            </div>
          </div>
        </div>
        <div class="guide-section">
          <div class="guide-item">
            <div class="guide-item-icon">📸</div>
            <div class="guide-item-content">
              <h4 class="guide-item-title">图库管理</h4>
              <ul class="guide-item-list">
                <li>启用自动保存持续收集作品</li>
                <li>使用筛选和排序功能管理作品</li>
                <li>收藏、下载、分享你的创作</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</main>

<!-- 全屏预览组件 -->
<FullscreenViewer
  bind:isOpen={isFullscreenOpen}
  imageUrl={currentImageUrl}
  title={fullscreenTitle}
  on:close={handleFullscreenClose}
/>

<!-- 专业图库样式 -->
<style>
  /* 基础布局 */
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: var(--font-family-base);
    background: var(--page-bg);
    color: var(--text-primary);
    min-height: 100vh;
    transition: var(--duration-normal) var(--ease-in-out);
  }

  .page-layout {
    min-height: 100vh;
    padding: var(--space-lg);
  }

  .container {
    max-width: 1400px;
    margin: 0 auto;
  }

  /* 页面标题区域 */
  .gallery-header {
    text-align: center;
    margin-bottom: var(--space-2xl);
  }

  .page-title {
    font-size: var(--font-size-4xl);
    font-weight: var(--font-weight-bold);
    margin-bottom: var(--space-sm);
  }

  .page-subtitle {
    font-size: var(--font-size-lg);
    color: var(--text-secondary);
    font-weight: var(--font-weight-normal);
    margin-bottom: var(--space-xl);
  }

  /* 统计信息 */
  .gallery-stats {
    display: flex;
    justify-content: center;
    gap: var(--space-xl);
    flex-wrap: wrap;
  }

  .stat-item {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    padding: var(--space-md) var(--space-lg);
    background: var(--glass-bg);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-xl);
    backdrop-filter: blur(10px);
    transition: var(--duration-normal) var(--ease-in-out);
  }

  .stat-item:hover {
    background: var(--hover-bg);
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  }

  .stat-icon {
    font-size: var(--font-size-xl);
  }

  .stat-content {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }

  .stat-number {
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-bold);
    color: var(--text-primary);
    line-height: 1;
  }

  .stat-label {
    font-size: var(--font-size-sm);
    color: var(--text-secondary);
    font-weight: var(--font-weight-medium);
  }

  /* 控制面板 */
  .control-panel {
    background: var(--card-bg);
    border: var(--card-border);
    border-radius: var(--radius-2xl);
    padding: var(--space-xl);
    margin-bottom: var(--space-xl);
    box-shadow: var(--shadow-xl);
    backdrop-filter: blur(15px);
  }

  .control-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-xl);
  }

  .control-module {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: var(--radius-xl);
    padding: var(--space-lg);
    backdrop-filter: blur(10px);
  }

  .module-header {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    margin-bottom: var(--space-lg);
  }

  .module-icon {
    font-size: var(--font-size-xl);
  }

  .module-title {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    color: var(--text-primary);
    margin: 0;
    flex: 1;
  }

  .module-badge {
    font-size: var(--font-size-xs);
    padding: var(--space-xs) var(--space-sm);
    background: var(--accent-color);
    color: white;
    border-radius: var(--radius-full);
    font-weight: var(--font-weight-medium);
  }

  /* 连接控制 */
  .connection-controls {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  .input-group {
    display: flex;
    gap: var(--space-sm);
  }

  .connection-input {
    flex: 1;
    padding: var(--space-md);
    background: var(--hover-bg);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    color: var(--text-primary);
    font-size: var(--font-size-sm);
    transition: var(--duration-normal) var(--ease-in-out);
  }

  .connection-input:focus {
    outline: none;
    border-color: var(--accent-color);
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
  }

  .connection-input::placeholder {
    color: var(--text-tertiary);
  }

  .connect-btn {
    padding: var(--space-md) var(--space-lg);
    background: var(--accent-color);
    color: white;
    border: none;
    border-radius: var(--radius-lg);
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    cursor: pointer;
    transition: var(--duration-normal) var(--ease-in-out);
    white-space: nowrap;
  }

  .connect-btn:hover:not(:disabled) {
    background: var(--accent-color);
    filter: brightness(1.1);
    transform: translateY(-1px);
  }

  .connect-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .status-group {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-md);
  }

  .connection-status {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    padding: var(--space-sm) var(--space-md);
    background: var(--glass-bg);
    border-radius: var(--radius-lg);
    border: 1px solid var(--border-color);
  }

  .status-dot {
    width: 0.75rem;
    height: 0.75rem;
    border-radius: var(--radius-full);
  }

  .status-dot.online {
    background: var(--success-color);
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
  }

  .status-dot.offline {
    background: var(--danger-color);
    box-shadow: 0 0 8px rgba(239, 68, 68, 0.5);
  }

  .status-text {
    font-size: var(--font-size-sm);
    color: var(--text-secondary);
    font-weight: var(--font-weight-medium);
  }

  .disconnect-btn {
    padding: var(--space-sm) var(--space-md);
    background: var(--danger-color);
    color: white;
    border: none;
    border-radius: var(--radius-lg);
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-medium);
    cursor: pointer;
    transition: var(--duration-normal) var(--ease-in-out);
  }

  .disconnect-btn:hover {
    background: var(--danger-color);
    filter: brightness(1.1);
  }

  /* 自动保存控制 */
  .auto-save-controls {
    display: flex;
    flex-direction: column;
    gap: var(--space-lg);
  }

  .toggle-group {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-md);
  }

  .toggle-label {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--text-secondary);
  }

  .toggle-switch {
    position: relative;
    width: 3rem;
    height: 1.5rem;
    background: var(--border-color);
    border-radius: var(--radius-full);
    border: none;
    cursor: pointer;
    transition: var(--duration-normal) var(--ease-in-out);
  }

  .toggle-switch.active {
    background: var(--success-color);
  }

  .toggle-slider {
    position: absolute;
    top: 0.125rem;
    left: 0.125rem;
    width: 1.25rem;
    height: 1.25rem;
    background: white;
    border-radius: var(--radius-full);
    transition: var(--duration-normal) var(--ease-in-out);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  .toggle-switch.active .toggle-slider {
    transform: translateX(1.5rem);
  }

  .action-buttons {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-sm);
  }

  .action-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-xs);
    padding: var(--space-md);
    border: none;
    border-radius: var(--radius-lg);
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-medium);
    cursor: pointer;
    transition: var(--duration-normal) var(--ease-in-out);
    color: white;
  }

  .action-btn.capture {
    background: var(--success-color);
  }

  .action-btn.export {
    background: var(--warning-color);
  }

  .action-btn.clear {
    background: var(--danger-color);
    grid-column: span 2;
  }

  .action-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  }

  .action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none !important;
  }

  .action-icon {
    font-size: var(--font-size-sm);
  }

  /* 主内容区域 */
  .main-content-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-xl);
    margin-bottom: var(--space-2xl);
  }

  .preview-section, .gallery-section {
    background: var(--card-bg);
    border: var(--card-border);
    border-radius: var(--radius-2xl);
    padding: var(--space-lg);
    box-shadow: var(--shadow-xl);
    backdrop-filter: blur(10px);
  }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: var(--space-lg);
  }

  .section-title {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
  }

  .section-icon {
    font-size: var(--font-size-xl);
  }

  .section-title h3 {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    color: var(--text-primary);
    margin: 0;
  }

  .section-actions {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
  }

  .fullscreen-btn {
    background: var(--accent-color);
    color: white;
    border: none;
    padding: var(--space-xs) var(--space-sm);
    border-radius: var(--radius-md);
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    cursor: pointer;
    transition: var(--duration-fast) var(--ease-in-out);
    white-space: nowrap;
  }

  .fullscreen-btn:hover:not(:disabled) {
    background: var(--accent-color);
    filter: brightness(1.1);
    transform: translateY(-1px);
  }

  .fullscreen-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    filter: none;
  }

  .image-count {
    font-size: var(--font-size-xs);
    padding: var(--space-xs) var(--space-sm);
    background: var(--accent-color);
    color: white;
    border-radius: var(--radius-full);
    font-weight: var(--font-weight-medium);
  }

  .toggle-btn {
    background: none;
    border: none;
    color: var(--accent-color);
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    cursor: pointer;
    transition: var(--duration-fast) var(--ease-in-out);
    padding: var(--space-xs) var(--space-sm);
    border-radius: var(--radius-md);
  }

  .toggle-btn:hover {
    background: var(--glass-bg);
    color: var(--text-primary);
  }

  /* 预览区域 */
  .preview-container {
    position: relative;
  }

  .preview-image-wrapper {
    position: relative;
    aspect-ratio: 1/1;
    background: #000;
    border-radius: var(--radius-xl);
    overflow: hidden;
    cursor: pointer;
    transition: var(--duration-normal) var(--ease-in-out);
  }

  .preview-image-wrapper:hover {
    transform: scale(1.01);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  }

  .preview-image {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }

  .preview-loading {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.7);
    color: white;
  }

  .loading-spinner {
    width: 3rem;
    height: 3rem;
    border: 3px solid rgba(255, 255, 255, 0.3);
    border-top: 3px solid white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: var(--space-md);
  }

  .loading-text {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .live-indicator {
    position: absolute;
    top: var(--space-md);
    right: var(--space-md);
    display: flex;
    align-items: center;
    gap: var(--space-xs);
    padding: var(--space-xs) var(--space-sm);
    background: var(--success-color);
    color: white;
    border-radius: var(--radius-full);
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-medium);
    box-shadow: 0 0 12px rgba(16, 185, 129, 0.5);
  }

  .live-dot {
    width: 0.5rem;
    height: 0.5rem;
    background: white;
    border-radius: var(--radius-full);
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }

  .fullscreen-hint {
    position: absolute;
    bottom: var(--space-md);
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: var(--space-xs) var(--space-md);
    border-radius: var(--radius-full);
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-medium);
    backdrop-filter: blur(10px);
    opacity: 0;
    transition: var(--duration-normal) var(--ease-in-out);
    pointer-events: none;
    white-space: nowrap;
  }

  .preview-image-wrapper:hover .fullscreen-hint {
    opacity: 1;
    transform: translateX(-50%) translateY(-2px);
  }

  .preview-empty {
    aspect-ratio: 1/1;
    background: var(--glass-bg);
    border: 2px dashed var(--border-color);
    border-radius: var(--radius-xl);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .empty-content {
    text-align: center;
    max-width: 200px;
  }

  .empty-icon {
    font-size: 4rem;
    display: block;
    margin-bottom: var(--space-md);
    opacity: 0.5;
  }

  .empty-title {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    color: var(--text-primary);
    margin-bottom: var(--space-xs);
  }

  .empty-subtitle {
    font-size: var(--font-size-sm);
    color: var(--text-secondary);
    line-height: var(--line-height-relaxed);
  }

  .error-message {
    padding: var(--space-md);
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: var(--radius-lg);
    margin-top: var(--space-md);
  }

  .error-text {
    font-size: var(--font-size-sm);
    color: #fca5a5;
    white-space: pre-line;
    line-height: var(--line-height-relaxed);
  }

  /* 图库筛选控件 */
  .filter-controls {
    background: var(--glass-bg);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-xl);
    padding: var(--space-lg);
    backdrop-filter: blur(10px);
    margin-bottom: var(--space-lg);
  }

  .search-group {
    position: relative;
    margin-bottom: var(--space-md);
  }

  .search-input {
    width: 100%;
    padding: var(--space-md) var(--space-md) var(--space-md) 3rem;
    background: var(--hover-bg);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    color: var(--text-primary);
    font-size: var(--font-size-sm);
    transition: var(--duration-normal) var(--ease-in-out);
  }

  .search-input:focus {
    outline: none;
    border-color: var(--accent-color);
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
  }

  .search-input::placeholder {
    color: var(--text-tertiary);
  }

  .search-icon {
    position: absolute;
    left: var(--space-md);
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-tertiary);
    font-size: var(--font-size-md);
  }

  .filter-options {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: var(--space-sm);
  }

  .filter-select {
    padding: var(--space-sm) var(--space-md);
    background: var(--hover-bg);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    color: var(--text-primary);
    font-size: var(--font-size-sm);
    cursor: pointer;
    transition: var(--duration-normal) var(--ease-in-out);
  }

  .filter-select:focus {
    outline: none;
    border-color: var(--accent-color);
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
  }

  .filter-btn {
    padding: var(--space-sm) var(--space-md);
    background: var(--hover-bg);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    color: var(--text-primary);
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    cursor: pointer;
    transition: var(--duration-normal) var(--ease-in-out);
  }

  .filter-btn.active {
    background: var(--accent-color);
    border-color: var(--accent-color);
    color: white;
  }

  .filter-btn:hover {
    background: var(--active-bg);
    border-color: var(--accent-color);
  }

  /* 图库内容 */
  .gallery-content {
    background: var(--glass-bg);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-xl);
    padding: var(--space-lg);
    backdrop-filter: blur(10px);
  }

  .empty-gallery {
    text-align: center;
    padding: var(--space-2xl) var(--space-lg);
  }

  .empty-gallery .empty-icon {
    font-size: 4rem;
    display: block;
    margin-bottom: var(--space-md);
    opacity: 0.5;
  }

  .empty-gallery .empty-title {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    color: var(--text-primary);
    margin-bottom: var(--space-xs);
  }

  .empty-gallery .empty-subtitle {
    font-size: var(--font-size-sm);
    color: var(--text-secondary);
    line-height: var(--line-height-relaxed);
  }

  /* 图库网格 */
  .gallery-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: var(--space-lg);
  }

  .gallery-item {
    background: var(--hover-bg);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    overflow: hidden;
    transition: var(--duration-normal) var(--ease-in-out);
  }

  .gallery-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    border-color: var(--accent-color);
  }

  .image-container {
    position: relative;
    aspect-ratio: 1/1;
    overflow: hidden;
  }

  .gallery-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: var(--duration-normal) var(--ease-in-out);
  }

  .gallery-item:hover .gallery-image {
    transform: scale(1.05);
  }

  .image-overlay {
    position: absolute;
    inset: 0;
    background: var(--gallery-overlay);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-sm);
    opacity: 0;
    transition: var(--duration-normal) var(--ease-in-out);
  }

  .gallery-item:hover .image-overlay {
    opacity: 1;
  }

  .overlay-btn {
    padding: var(--space-sm);
    background: rgba(255, 255, 255, 0.9);
    border: none;
    border-radius: var(--radius-full);
    color: var(--text-primary);
    cursor: pointer;
    transition: var(--duration-fast) var(--ease-in-out);
    font-size: var(--font-size-md);
  }

  .overlay-btn:hover {
    background: white;
    transform: scale(1.1);
  }

  .overlay-btn.delete {
    background: rgba(239, 68, 68, 0.9);
    color: white;
  }

  .overlay-btn.delete:hover {
    background: var(--danger-color);
  }

  .favorite-badge {
    position: absolute;
    top: var(--space-sm);
    left: var(--space-sm);
    background: var(--warning-color);
    color: white;
    padding: var(--space-xs);
    border-radius: var(--radius-full);
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-medium);
    box-shadow: 0 2px 8px rgba(245, 158, 11, 0.5);
  }

  .image-info {
    padding: var(--space-md);
  }

  .image-title {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--text-primary);
    margin-bottom: var(--space-xs);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .image-time {
    font-size: var(--font-size-xs);
    color: var(--text-secondary);
  }

  /* 加载更多按钮 */
  .load-more {
    text-align: center;
    margin-top: var(--space-xl);
  }

  .load-more-btn {
    padding: var(--space-md) var(--space-xl);
    background: var(--accent-color);
    color: white;
    border: none;
    border-radius: var(--radius-lg);
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    cursor: pointer;
    transition: var(--duration-normal) var(--ease-in-out);
  }

  .load-more-btn:hover:not(:disabled) {
    background: var(--accent-color);
    filter: brightness(1.1);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
  }

  .load-more-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none !important;
  }

  /* 使用指南 */
  .usage-guide {
    background: var(--glass-bg);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-2xl);
    padding: var(--space-xl);
    backdrop-filter: blur(10px);
    margin-top: var(--space-2xl);
  }

  .guide-header {
    text-align: center;
    margin-bottom: var(--space-lg);
  }

  .guide-title {
    display: inline-flex;
    align-items: center;
    gap: var(--space-sm);
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-semibold);
    color: var(--text-primary);
    margin: 0;
  }

  .guide-icon {
    font-size: var(--font-size-xl);
  }

  .guide-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-xl);
  }

  .guide-section {
    background: var(--hover-bg);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-xl);
    padding: var(--space-lg);
    transition: var(--duration-normal) var(--ease-in-out);
  }

  .guide-section:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
    border-color: var(--accent-color);
  }

  .guide-item {
    display: flex;
    align-items: flex-start;
    gap: var(--space-md);
  }

  .guide-item-icon {
    font-size: var(--font-size-2xl);
    flex-shrink: 0;
    margin-top: var(--space-xs);
  }

  .guide-item-content {
    flex: 1;
  }

  .guide-item-title {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    color: var(--text-primary);
    margin: 0 0 var(--space-sm) 0;
  }

  .guide-item-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .guide-item-list li {
    font-size: var(--font-size-sm);
    color: var(--text-secondary);
    line-height: var(--line-height-relaxed);
    padding: var(--space-xs) 0;
    position: relative;
    padding-left: var(--space-md);
  }

  .guide-item-list li::before {
    content: '•';
    position: absolute;
    left: 0;
    color: var(--accent-color);
    font-weight: bold;
  }

  /* 响应式设计 */
  @media (max-width: 1024px) {
    .control-grid,
    .main-content-grid {
      grid-template-columns: 1fr;
      gap: var(--space-lg);
    }

    .action-buttons {
      grid-template-columns: 1fr 1fr 1fr;
    }

    .action-btn.clear {
      grid-column: span 3;
    }

    .gallery-grid {
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: var(--space-md);
    }
  }

  @media (max-width: 768px) {
    .page-layout {
      padding: var(--space-md);
    }

    .gallery-stats {
      gap: var(--space-md);
    }

    .stat-item {
      padding: var(--space-sm) var(--space-md);
      min-width: 120px;
    }

    .control-panel {
      padding: var(--space-md);
    }

    .control-module {
      padding: var(--space-md);
    }

    .input-group {
      flex-direction: column;
    }

    .action-buttons {
      grid-template-columns: 1fr;
    }

    .action-btn.clear {
      grid-column: span 1;
    }
  }

  @media (max-width: 640px) {
    .page-title {
      font-size: var(--font-size-2xl);
    }

    .gallery-stats {
      flex-direction: column;
      align-items: center;
    }

    .stat-item {
      width: 100%;
      max-width: 200px;
      justify-content: center;
    }

    .section-header {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--space-sm);
    }

    .section-actions {
      width: 100%;
      justify-content: flex-end;
    }

    .fullscreen-btn {
      font-size: var(--font-size-xs);
      padding: var(--space-xs);
    }

    .gallery-grid {
      grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
      gap: var(--space-sm);
    }

    .filter-options {
      grid-template-columns: 1fr 1fr;
      gap: var(--space-xs);
    }

    .filter-select,
    .filter-btn {
      font-size: var(--font-size-xs);
      padding: var(--space-xs) var(--space-sm);
    }

    .overlay-btn {
      padding: var(--space-xs);
      font-size: var(--font-size-sm);
    }

    .image-info {
      padding: var(--space-sm);
    }

    .image-title {
      font-size: var(--font-size-xs);
    }

    .image-time {
      font-size: 0.65rem;
    }

    .usage-guide {
      padding: var(--space-lg);
      margin-top: var(--space-lg);
    }

    .guide-content {
      grid-template-columns: 1fr;
      gap: var(--space-lg);
    }

    .guide-section {
      padding: var(--space-md);
    }

    .guide-item-icon {
      font-size: var(--font-size-xl);
    }

    .guide-item-title {
      font-size: var(--font-size-md);
    }

    .guide-item-list li {
      font-size: var(--font-size-xs);
    }
  }
</style>