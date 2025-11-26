<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { page } from '$app/stores';
  import ErrorHandler from '$lib/components/ErrorHandler.svelte';
  import { setError, ErrorType } from '$lib/store';

  let userId: string | null = null;
  let imageLoaded = false;
  let currentImageUrl: string = '';
  let error: string = '';
  let connectionStatus = '未连接';

  // 获取路由参数中的 userId
  onMount(() => {
    userId = $page.params.userId;
    if (userId) {
      connectToStream();
    }
  });

  function connectToStream() {
    if (!userId) {
      error = '无效的 User ID';
      return;
    }

    connectionStatus = '正在连接...';
    error = '';
    imageLoaded = false;

    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
    currentImageUrl = `${protocol}//${window.location.host}/api/canvas/sessions/${userId}/stream`;
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

  function openGallery() {
    window.location.href = `/gallery?userId=${userId}`;
  }

  function copyShareUrl() {
    const shareUrl = window.location.href;
    navigator.clipboard.writeText(shareUrl).then(() => {
      setError({
        type: ErrorType.API,
        message: '链接已复制',
        details: '分享链接已复制到剪贴板',
        recoverable: true,
        suggestions: []
      });
    });
  }
</script>

<svelte:head>
  <title>查看画板 - {userId} - ArtFlow</title>
</svelte:head>

<main class="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 dark:from-slate-900 dark:to-slate-800">
  <div class="container mx-auto max-w-4xl px-4 py-6">
    <ErrorHandler />

    <!-- 页面标题 -->
    <div class="mb-6 text-center">
      <h1 class="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-2">
        👁️ 画板直播
      </h1>
      <p class="text-lg text-gray-600 dark:text-gray-300">
        实时查看 User ID: <span class="font-mono bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded">{userId}</span>
      </p>
    </div>

    <!-- 状态栏 -->
    <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-4 mb-6">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-slate-700 rounded-lg">
            <div class="w-2 h-2 rounded-full {currentImageUrl && imageLoaded ? 'bg-green-500' : 'bg-red-500'}"></div>
            <span class="text-sm text-gray-600 dark:text-gray-300">{connectionStatus}</span>
          </div>
          <span class="text-xs text-gray-500 dark:text-gray-400">
            {imageLoaded ? '实时接收中...' : '等待连接...'}
          </span>
        </div>
        <div class="flex gap-2">
          <button
            on:click={openGallery}
            class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm"
          >
            🖼️ 打开图库
          </button>
          <button
            on:click={copyShareUrl}
            class="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors text-sm"
          >
            📤 分享链接
          </button>
        </div>
      </div>
    </div>

    <!-- 主要内容 -->
    <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-xl overflow-hidden">
      {#if currentImageUrl && userId}
        <div class="relative aspect-square bg-black">
          <img
            src={currentImageUrl}
            alt="画板实时图像"
            class="w-full h-full object-contain"
            on:load={handleImageLoad}
            on:error={handleImageError}
          />

          {#if !imageLoaded && !error}
            <div class="absolute inset-0 flex items-center justify-center bg-black/50">
              <div class="text-center">
                <div class="animate-spin rounded-full h-16 w-16 border-b-4 border-white mx-auto mb-4"></div>
                <p class="text-white text-lg">等待画板连接...</p>
                <p class="text-white/70 text-sm mt-2">请确保画板应用已开始发送</p>
              </div>
            </div>
          {/if}

          {#if imageLoaded}
            <div class="absolute top-4 right-4 px-4 py-2 bg-green-500/90 backdrop-blur text-white rounded-full text-sm flex items-center gap-2">
              <div class="w-3 h-3 bg-white rounded-full animate-pulse"></div>
              <span class="font-medium">直播中</span>
            </div>

            <div class="absolute top-4 left-4 px-3 py-2 bg-black/50 backdrop-blur text-white rounded-lg text-xs">
              User ID: {userId.slice(0, 8)}...
            </div>
          {/if}
        </div>
      {:else}
        <div class="aspect-square bg-gray-100 dark:bg-slate-700 flex items-center justify-center border-2 border-dashed border-gray-300 dark:border-slate-600">
          <div class="text-center">
            <span class="text-8xl mb-6 block opacity-30">🎨</span>
            <h3 class="text-xl font-semibold text-gray-600 dark:text-gray-300 mb-2">等待画板连接</h3>
            <p class="text-gray-500 dark:text-gray-400 mb-4">
              请确保画板应用已连接服务器并开始发送数据
            </p>
            <div class="text-sm text-gray-400 dark:text-gray-500 space-y-1">
              <p>• 检查 User ID 是否正确</p>
              <p>• 确认画板应用已连接服务器</p>
              <p>• 点击"开始发送"按钮</p>
            </div>
          </div>
        </div>
      {/if}

      {#if error}
        <div class="p-6 bg-red-50 dark:bg-red-900/20 border-t-4 border-red-500">
          <div class="flex items-start gap-3">
            <span class="text-2xl">⚠️</span>
            <div class="flex-1">
              <h3 class="font-semibold text-red-700 dark:text-red-300 mb-1">连接错误</h3>
              <p class="text-sm text-red-600 dark:text-red-400 whitespace-pre-line">{error}</p>
              <div class="mt-3 text-xs text-red-500 dark:text-red-500 space-y-1">
                <p>💡 解决方案:</p>
                <ul class="list-disc list-inside space-y-1 ml-4">
                  <li>刷新页面重试</li>
                  <li>检查 User ID 是否正确</li>
                  <li>确认画板应用正在运行</li>
                  <li>检查网络连接是否正常</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      {/if}
    </div>

    <!-- 使用说明 -->
    <div class="mt-8 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-2xl p-6">
      <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 text-center">📖 使用说明</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-gray-600 dark:text-gray-300">
        <div>
          <h4 class="font-semibold mb-2 text-gray-700 dark:text-gray-200">🎨 画板端</h4>
          <ul class="space-y-1">
            <li>• 打开画板应用并连接服务器</li>
            <li>• 复制生成的 User ID</li>
            <li>• 点击"开始发送"按钮</li>
            <li>• 在画布上绘制内容</li>
          </ul>
        </div>
        <div>
          <h4 class="font-semibold mb-2 text-gray-700 dark:text-gray-200">👁️ 观看端</h4>
          <ul class="space-y-1">
            <li>• 访问画板分享的链接</li>
            <li>• 实时查看AI生成结果</li>
            <li>• 打开图库管理作品</li>
            <li>• 分享链接给其他人</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="mt-6 text-center">
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
        想要查看其他画板？<a href="/gallery" class="text-blue-500 hover:text-blue-600 transition-colors">前往图库页面</a>
      </p>
    </div>
  </div>
</main>