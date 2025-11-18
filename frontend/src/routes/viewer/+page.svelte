<script lang="ts">
  import { onMount, onDestroy } from 'svelte';

  let imageUrl: string = '';
  let error: string = '';
  let userId: string | null = null;
  let userIdInput: string = '';
  let connectionStatus = '未连接';
  let showUserIdInput = true;
  let imageLoaded = false;

  // 从 URL 参数获取 userId
  onMount(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const urlUserId = urlParams.get('userId');
    if (urlUserId) {
      userIdInput = urlUserId;
      showUserIdInput = false;
      connectToStream();
    }
  });

  // 连接到 MJPEG 流
  function connectToStream() {
    if (!userIdInput.trim()) {
      error = '请输入画板应用的 User ID';
      return;
    }

    userId = userIdInput.trim();
    connectionStatus = '正在连接...';
    error = '';
    imageLoaded = false;
    clearTimeoutCheck();

    // 构建 MJPEG 流 URL
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
    imageUrl = `${protocol}//${window.location.host}/api/stream/${userId}`;
    
    // 启动超时检测
    startTimeoutCheck();
  }

  function disconnect() {
    imageUrl = '';
    userId = null;
    connectionStatus = '未连接';
    error = '';
    imageLoaded = false;
    clearTimeoutCheck();
  }
  
  // 组件销毁时清理定时器
  onDestroy(() => {
    clearTimeoutCheck();
  });

  function handleImageLoad() {
    imageLoaded = true;
    error = '';
    connectionStatus = '已连接 - 正在接收图像';
    clearTimeoutCheck(); // 清除超时检测
  }

  function handleImageError() {
    error = '无法加载图像流。请确保：\n1. 画板应用已连接服务器（显示"已连接"状态）\n2. 画板应用已点击"开始发送"按钮\n3. User ID 正确（从画板应用复制）\n4. 画板应用正在绘制内容（空白画布可能不会发送）';
    connectionStatus = '连接错误';
    imageLoaded = false;
  }
  
  // 添加超时检测
  let timeoutTimer: ReturnType<typeof setTimeout> | null = null;
  
  function startTimeoutCheck() {
    if (timeoutTimer) {
      clearTimeout(timeoutTimer);
    }
    // 30 秒后如果还没有加载图像，显示错误提示
    timeoutTimer = setTimeout(() => {
      if (!imageLoaded && imageUrl && userId) {
        error = '图像流加载超时。请检查：\n1. 画板应用是否已点击"开始发送"按钮\n2. 画板应用是否正在绘制内容\n3. 网络连接是否正常\n\n如果问题持续，请尝试：\n- 断开并重新连接\n- 检查画板应用的控制台是否有错误';
        connectionStatus = '连接超时';
      }
    }, 30000);
  }
  
  function clearTimeoutCheck() {
    if (timeoutTimer) {
      clearTimeout(timeoutTimer);
      timeoutTimer = null;
    }
  }
</script>

<svelte:head>
  <title>实时图像生成查看器 - ArtFlow</title>
</svelte:head>

<main class="min-h-screen bg-surface">
  <div class="container mx-auto max-w-7xl px-4 py-6">
    <div class="mb-6">
      <h1 class="title">👁️ 查看器</h1>
      <p class="subtitle">实时查看画板生成的AI图像结果</p>
    </div>

  <div class="card">
    {#if showUserIdInput}
      <div class="card-compact mb-6">
        <label for="userIdInput" class="label">
          请输入画板应用的 User ID：
        </label>
        <div class="flex gap-3">
          <input
            id="userIdInput"
            type="text"
            bind:value={userIdInput}
            placeholder="从画板应用复制 User ID"
            class="input flex-1"
            on:keydown={(e) => {
              if (e.key === 'Enter') {
                connectToStream();
              }
            }}
          />
          <button
            on:click={connectToStream}
            disabled={!userIdInput.trim() || !!imageUrl}
            class="btn-primary"
          >
            连接
          </button>
        </div>
        <p class="text-xs text-text-tertiary mt-3">
          提示：在画板应用中连接服务器后，会显示 User ID，请复制并粘贴到这里
        </p>
      </div>
    {/if}

    <div class="flex items-center justify-between mb-6 pb-6 border-b border-border">
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2 px-3 py-2 bg-surface rounded-xl">
          <div class="status-dot {imageUrl && imageLoaded ? 'status-dot-online' : 'status-dot-offline'}"></div>
          <span class="text-sm text-text-secondary">{connectionStatus}</span>
        </div>
        {#if userId}
          <div class="text-xs text-text-tertiary px-3 py-2 bg-surface rounded-xl">
            User ID: {userId.slice(0, 8)}...
          </div>
        {/if}
      </div>
      <div class="flex gap-2">
        {#if !imageUrl && !showUserIdInput}
          <button
            on:click={connectToStream}
            class="btn-primary"
          >
            重新连接
          </button>
        {:else if imageUrl}
          <button
            on:click={disconnect}
            class="btn-danger"
          >
            断开连接
          </button>
        {/if}
      </div>
    </div>

    {#if error}
      <div class="bg-danger/20 border border-danger/30 text-danger p-4 rounded-xl mb-6">
        <p class="text-sm whitespace-pre-line">{error}</p>
      </div>
    {/if}

    <div class="relative w-full aspect-square bg-black rounded-2xl overflow-hidden border border-border shadow-large">
      {#if imageUrl && userId}
        <img
          src={imageUrl}
          alt="实时生成图像"
          class="w-full h-full object-contain"
          on:load={handleImageLoad}
          on:error={handleImageError}
        />
        {#if !imageLoaded && !error}
          <div class="absolute inset-0 flex items-center justify-center bg-black/50">
            <div class="text-center">
              <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
              <p class="text-text-secondary">等待图像流...</p>
            </div>
          </div>
        {/if}
      {:else}
        <div class="flex items-center justify-center h-full">
          <div class="text-center">
            <p class="text-lg text-text-secondary mb-2">未连接</p>
            <p class="text-sm text-text-tertiary">请输入 User ID 并连接</p>
          </div>
        </div>
      {/if}
    </div>

    <div class="mt-6 text-xs text-text-tertiary text-center">
      <p>提示: 确保画板应用已连接并开始发送，图像将实时显示在这里</p>
    </div>
  </div>
</main>

