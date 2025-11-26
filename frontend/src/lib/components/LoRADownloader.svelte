<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { setError, clearError, ErrorType } from '$lib/store';

  // 组件状态
  let loading = true;
  let presets: any[] = [];
  let downloadTasks: any[] = [];
  let showPresets = true;

  // WebSocket连接
  let ws: WebSocket | null = null;
  let wsReconnectTimer: number | null = null;

  // API函数
  const API_BASE = '/api/lora';

  async function fetchPresets() {
    try {
      const response = await fetch(`${API_BASE}/presets`);
      if (!response.ok) throw new Error('获取预设失败');
      presets = await response.json();
    } catch (error) {
      console.error('获取预设失败:', error);
      setError(ErrorType.NETWORK, '获取LoRA预设失败');
    }
  }

  async function fetchDownloadStatus() {
    try {
      const response = await fetch(`${API_BASE}/download/status`);
      if (!response.ok) return;
      downloadTasks = await response.json();
    } catch (error) {
      console.error('获取下载状态失败:', error);
    }
  }

  async function startDownload(presetId: string, mirrorIndex = 0) {
    try {
      clearError();
      const response = await fetch(`${API_BASE}/download/${presetId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preset_id: presetId, mirror_index: mirrorIndex })
      });

      if (!response.ok) throw new Error('开始下载失败');

      const result = await response.json();
      console.log('下载开始:', result);

      // 立即刷新状态
      await fetchDownloadStatus();
    } catch (error) {
      console.error('开始下载失败:', error);
      setError(ErrorType.NETWORK, '开始下载失败');
    }
  }

  async function cancelDownload(presetId: string) {
    try {
      const response = await fetch(`${API_BASE}/download/${presetId}/cancel`, {
        method: 'POST'
      });

      if (!response.ok) throw new Error('取消下载失败');

      await fetchDownloadStatus();
    } catch (error) {
      console.error('取消下载失败:', error);
      setError(ErrorType.NETWORK, '取消下载失败');
    }
  }

  async function deletePreset(presetId: string) {
    try {
      if (!confirm('确定要删除这个LoRA文件吗？')) return;

      const response = await fetch(`${API_BASE}/presets/${presetId}`, {
        method: 'DELETE'
      });

      if (!response.ok) throw new Error('删除失败');

      await fetchPresets();
      await fetchDownloadStatus();
    } catch (error) {
      console.error('删除失败:', error);
      setError(ErrorType.NETWORK, '删除失败');
    }
  }

  function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  function formatSpeed(kbps: number): string {
    if (kbps < 1024) return `${kbps.toFixed(1)} KB/s`;
    return `${(kbps / 1024).toFixed(1)} MB/s`;
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'downloading': return 'text-blue-600';
      case 'completed': return 'text-green-600';
      case 'failed': return 'text-red-600';
      case 'cancelled': return 'text-gray-600';
      default: return 'text-gray-600';
    }
  }

  function getStatusText(status: string): string {
    switch (status) {
      case 'pending': return '等待中';
      case 'downloading': return '下载中';
      case 'completed': return '已完成';
      case 'failed': return '失败';
      case 'cancelled': return '已取消';
      default: return status;
    }
  }

  function getTaskForPreset(presetId: string) {
    return downloadTasks.find(task => task.preset_id === presetId);
  }

  // WebSocket连接
  function connectWebSocket() {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}${API_BASE}/ws/progress`;

      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('LoRA下载进度WebSocket连接成功');
        if (wsReconnectTimer) {
          clearTimeout(wsReconnectTimer);
          wsReconnectTimer = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'progress_update') {
            // 更新下载任务状态
            data.tasks.forEach((task: any) => {
              const existingIndex = downloadTasks.findIndex(t => t.preset_id === task.preset_id);
              if (existingIndex >= 0) {
                downloadTasks[existingIndex] = { ...downloadTasks[existingIndex], ...task };
              } else {
                downloadTasks.push(task);
              }
            });
            downloadTasks = [...downloadTasks]; // 触发响应式更新
          }
        } catch (e) {
          console.error('WebSocket消息解析失败:', e);
        }
      };

      ws.onclose = () => {
        console.log('LoRA下载进度WebSocket连接关闭');
        // 3秒后重连
        wsReconnectTimer = setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
      };

    } catch (error) {
      console.error('WebSocket连接失败:', error);
      // 5秒后重试
      wsReconnectTimer = setTimeout(connectWebSocket, 5000);
    }
  }

  function disconnectWebSocket() {
    if (wsReconnectTimer) {
      clearTimeout(wsReconnectTimer);
      wsReconnectTimer = null;
    }
    if (ws) {
      ws.close();
      ws = null;
    }
  }

  onMount(async () => {
    loading = true;
    await fetchPresets();
    await fetchDownloadStatus();
    loading = false;

    // 连接WebSocket
    connectWebSocket();

    // 定期刷新下载状态（WebSocket备用）
    const statusInterval = setInterval(fetchDownloadStatus, 5000);

    onDestroy(() => {
      clearInterval(statusInterval);
      disconnectWebSocket();
    });
  });

  // 根据标签过滤预设
  $: acceleratedPresets = presets.filter(p => p.tags.includes('speed') || p.tags.includes('lcm'));
  $: stylePresets = presets.filter(p => p.tags.includes('style') && !p.tags.includes('speed'));
</script>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <h3 class="text-lg font-semibold">📦 LoRA 管理器</h3>
    <div class="flex gap-2">
      <button
        class="btn btn-sm {showPresets ? 'btn-primary' : 'btn-secondary'}"
        on:click={() => showPresets = true}
      >
        预设模型
      </button>
      <button
        class="btn btn-sm {!showPresets ? 'btn-primary' : 'btn-secondary'}"
        on:click={() => showPresets = false}
      >
        下载任务
      </button>
    </div>
  </div>

  {#if loading}
    <div class="flex justify-center py-8">
      <div class="loading loading-spinner"></div>
    </div>
  {:else if showPresets}
    <!-- 加速类LoRA -->
    {#if acceleratedPresets.length > 0}
      <div class="space-y-3">
        <h4 class="text-md font-medium text-blue-600">⚡ 加速类 LoRA</h4>
        <div class="grid gap-4 md:grid-cols-2">
          {#each acceleratedPresets as preset}
            {@const task = getTaskForPreset(preset.id)}
            <div class="card card-compact bg-base-100 shadow">
              <div class="card-body">
                <div class="flex justify-between items-start">
                  <div class="flex-1">
                    <h5 class="card-title text-sm">{preset.name}</h5>
                    <p class="text-xs text-gray-600 mt-1">{preset.description}</p>
                    <div class="flex gap-2 mt-2">
                      <span class="badge badge-primary badge-xs">加速</span>
                      <span class="badge badge-ghost badge-xs">{preset.size}</span>
                      {#if preset.is_downloaded}
                        <span class="badge badge-success badge-xs">已下载</span>
                      {/if}
                    </div>
                  </div>
                </div>

                <!-- 下载进度 -->
                {#if task && task.status === 'downloading'}
                  <div class="mt-3 space-y-1">
                    <div class="flex justify-between text-xs">
                      <span>{getStatusText(task.status)}</span>
                      <span>{task.progress.toFixed(1)}%</span>
                    </div>
                    <progress
                      class="progress progress-primary w-full"
                      value={task.progress}
                      max="100"
                    ></progress>
                    {#if task.speed > 0}
                      <div class="text-xs text-gray-600">
                        {formatSpeed(task.speed)} - {formatFileSize(task.downloaded_size)}/{formatFileSize(task.total_size)}
                      </div>
                    {/if}
                  </div>
                {/if}

                <!-- 操作按钮 -->
                <div class="card-actions justify-end mt-3">
                  {#if !preset.is_downloaded}
                    {#if task && task.status === 'downloading'}
                      <button
                        class="btn btn-sm btn-error"
                        on:click={() => cancelDownload(preset.id)}
                      >
                        取消
                      </button>
                    {:else}
                      <button
                        class="btn btn-sm btn-primary"
                        on:click={() => startDownload(preset.id)}
                        disabled={task && task.status === 'downloading'}
                      >
                        📥 下载
                      </button>
                    {/if}
                  {:else}
                    <button
                      class="btn btn-sm btn-error"
                      on:click={() => deletePreset(preset.id)}
                    >
                      删除
                    </button>
                  {/if}
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- 风格类LoRA -->
    {#if stylePresets.length > 0}
      <div class="space-y-3">
        <h4 class="text-md font-medium text-purple-600">🎨 风格类 LoRA</h4>
        <div class="grid gap-4 md:grid-cols-2">
          {#each stylePresets as preset}
            {@const task = getTaskForPreset(preset.id)}
            <div class="card card-compact bg-base-100 shadow">
              <div class="card-body">
                <div class="flex justify-between items-start">
                  <div class="flex-1">
                    <h5 class="card-title text-sm">{preset.name}</h5>
                    <p class="text-xs text-gray-600 mt-1">{preset.description}</p>
                    <div class="flex gap-2 mt-2">
                      {#each preset.tags as tag}
                        <span class="badge badge-secondary badge-xs">{tag}</span>
                      {/each}
                      <span class="badge badge-ghost badge-xs">{preset.size}</span>
                      {#if preset.is_downloaded}
                        <span class="badge badge-success badge-xs">已下载</span>
                      {/if}
                    </div>
                  </div>
                </div>

                <!-- 下载进度 -->
                {#if task && task.status === 'downloading'}
                  <div class="mt-3 space-y-1">
                    <div class="flex justify-between text-xs">
                      <span>{getStatusText(task.status)}</span>
                      <span>{task.progress.toFixed(1)}%</span>
                    </div>
                    <progress
                      class="progress progress-secondary w-full"
                      value={task.progress}
                      max="100"
                    ></progress>
                  </div>
                {/if}

                <!-- 操作按钮 -->
                <div class="card-actions justify-end mt-3">
                  {#if !preset.is_downloaded}
                    {#if task && task.status === 'downloading'}
                      <button
                        class="btn btn-sm btn-error"
                        on:click={() => cancelDownload(preset.id)}
                      >
                        取消
                      </button>
                    {:else}
                      <button
                        class="btn btn-sm btn-secondary"
                        on:click={() => startDownload(preset.id)}
                        disabled={task && task.status === 'downloading'}
                      >
                        📥 下载
                      </button>
                    {/if}
                  {:else}
                    <button
                      class="btn btn-sm btn-error"
                      on:click={() => deletePreset(preset.id)}
                    >
                      删除
                    </button>
                  {/if}
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

  {:else}
    <!-- 下载任务列表 -->
    <div class="space-y-3">
      <h4 class="text-md font-medium">📊 下载任务</h4>
      {#if downloadTasks.length === 0}
        <div class="text-center py-8 text-gray-500">
          暂无下载任务
        </div>
      {:else}
        <div class="space-y-3">
          {#each downloadTasks as task}
            <div class="card card-compact bg-base-100 shadow">
              <div class="card-body">
                <div class="flex justify-between items-center">
                  <div>
                    <h5 class="font-medium">{task.filename}</h5>
                    <p class="text-sm text-gray-600">
                      状态: <span class="{getStatusColor(task.status)}">{getStatusText(task.status)}</span>
                    </p>
                  </div>
                  <div class="text-right">
                    {#if task.status === 'downloading'}
                      <div class="text-sm font-medium">{task.progress.toFixed(1)}%</div>
                      {#if task.speed > 0}
                        <div class="text-xs text-gray-600">{formatSpeed(task.speed)}</div>
                      {/if}
                    {/if}
                  </div>
                </div>

                {#if task.status === 'downloading' && task.progress > 0}
                  <progress
                    class="progress progress-primary w-full mt-3"
                    value={task.progress}
                    max="100"
                  ></progress>
                {/if}

                {#if task.error_message}
                  <div class="alert alert-error alert-sm mt-2">
                    <span class="text-xs">{task.error_message}</span>
                  </div>
                {/if}

                <div class="card-actions justify-end mt-2">
                  {#if task.status === 'downloading'}
                    <button
                      class="btn btn-sm btn-error"
                      on:click={() => cancelDownload(task.preset_id)}
                    >
                      取消
                    </button>
                  {/if}
                </div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>
  {/if}
</div>