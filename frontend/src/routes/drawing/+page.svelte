<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import type { Fields } from '$lib/types';
  import PipelineOptions from '$lib/components/PipelineOptions.svelte';
  import ModelManager from '$lib/components/ModelManager.svelte';
  import ErrorHandler from '$lib/components/ErrorHandler.svelte';
  import ImagePlayer from '$lib/components/ImagePlayer.svelte';
  import PromptTemplates from '$lib/components/PromptTemplates.svelte';
  import { getPipelineValues, pipelineValues, setError, ErrorType } from '$lib/store';
  import { HistoryManager } from '$lib/utils/history';
  import { keyboardManager } from '$lib/utils/keyboard';
  import KeyboardShortcuts from '$lib/components/KeyboardShortcuts.svelte';
  import { WebSocketManager } from '$lib/utils/websocket';

  // 应用专业画板主题
  onMount(() => {
    if (typeof document !== 'undefined') {
      document.body.classList.add('page-theme-professional');
    }
  });

  onDestroy(() => {
    if (typeof document !== 'undefined') {
      document.body.classList.remove('page-theme-professional');
    }
  });

  let showShortcuts = false;
  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D | null = null;
  let isDrawing = false;
  let lastX = 0;
  let lastY = 0;

  // 画笔设置
  let color = '#000000';
  let brushSize = 5;
  let brushTool = 'pen'; // pen, eraser, marker, pencil

  // 撤销/重做历史
  let canvasHistory: HistoryManager<ImageData> | null = null;
  let canUndo = false;
  let canRedo = false;

  // WebSocket连接
  let wsManager: WebSocketManager | null = null;
  let userId: string | null = null;
  let isSending = false;
  let connectionStatus = '未连接';
  let isConnected = false;
  let isSendingFrame = false;
  let hasUserDrawn = false;

  // 帧捕获优化（30fps 节流）
  const THROTTLE = 1000 / 30;
  let lastFrameMillis = 0;
  let frameCaptureId: number | null = null;

  // 参数配置
  let pipelineParams: Fields | null = null;
  let showParams = false;
  let showHistory = false;
  let showTools = true;

  // 生成历史
  let generatedImages: Array<{
    id: string;
    url: string;
    timestamp: Date;
    prompt: string;
  }> = [];

  // 生成 UUID
  function generateUUID(): string {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  let unregisterShortcuts: (() => void)[] = [];

  onMount(async () => {
    if (canvas) {
      ctx = canvas.getContext('2d');
      if (ctx) {
        // 初始化画布为白色
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = color;

        // 初始化历史记录
        canvasHistory = new HistoryManager<ImageData>(50);
        saveCanvasState();

        console.log('✅ 专业画板初始化完成');
      }
    }

    // 注册快捷键
    const registerShortcuts = () => {
      const shortcuts = [
        { key: 'z', ctrl: true, handler: undoCanvas, desc: '撤销' },
        { key: 'z', ctrl: true, shift: true, handler: redoCanvas, desc: '重做' },
        { key: 's', ctrl: true, handler: saveDrawing, desc: '保存画作' },
        { key: 'Delete', handler: clearCanvas, desc: '清空画布' },
        { key: 'b', handler: () => brushTool = 'pen', desc: '画笔工具' },
        { key: 'e', handler: () => brushTool = 'eraser', desc: '橡皮擦' },
        { key: 'm', handler: () => brushTool = 'marker', desc: '马克笔' },
        { key: 'p', handler: () => brushTool = 'pencil', desc: '铅笔' },
        { key: '[', handler: () => brushSize = Math.max(1, brushSize - 2), desc: '减小画笔' },
        { key: ']', handler: () => brushSize = Math.min(100, brushSize + 2), desc: '增大画笔' },
        { key: '?', shift: true, handler: () => showShortcuts = true, desc: '快捷键帮助' }
      ];

      return shortcuts.map(({ key, ctrl, shift, handler, desc }) => {
        if (key === '?' && shift) {
          return keyboardManager.register({ key, shift }, (e) => {
            showShortcuts = !showShortcuts;
            return false;
          });
        }

        return keyboardManager.register(
          { key, ctrl: ctrl || false, shift: shift || false },
          (e) => {
            if (typeof window !== 'undefined' &&
                document.activeElement?.tagName !== 'INPUT' &&
                document.activeElement?.tagName !== 'TEXTAREA') {
              handler();
              return false;
            }
            return true;
          }
        );
      });
    };

    unregisterShortcuts = registerShortcuts();

    // 从后端获取参数配置
    try {
      const response = await fetch('/api/canvas/settings');
      const data = await response.json();
      if (data.input_params?.properties) {
        const params = data.input_params.properties as Fields;
        pipelineParams = params;
        const initialValues: Record<string, any> = {};
        for (const [key, field] of Object.entries(params)) {
          initialValues[key] = field.default;
        }
        pipelineValues.set(initialValues);
      }
    } catch (error) {
      console.error('获取参数配置失败:', error);
    }
  });

  onDestroy(() => {
    stopSending();
    stopFrameCapture();

    if (wsManager) {
      wsManager.destroy();
      wsManager = null;
    }

    unregisterShortcuts.forEach(unregister => unregister());
  });

  // 保存画布状态到历史记录
  function saveCanvasState() {
    if (!canvas || !ctx || !canvasHistory) return;
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    canvasHistory.push(imageData);
    updateHistoryButtons();
  }

  function updateHistoryButtons() {
    if (!canvasHistory) return;
    const info = canvasHistory.getInfo();
    canUndo = info.canUndo;
    canRedo = info.canRedo;
  }

  function undoCanvas() {
    if (!canvasHistory || !canUndo) return;
    const state = canvasHistory.undo();
    restoreCanvasState(state);
  }

  function redoCanvas() {
    if (!canvasHistory || !canRedo) return;
    const state = canvasHistory.redo();
    restoreCanvasState(state);
  }

  function restoreCanvasState(imageData: ImageData | null) {
    if (!canvas || !ctx || !imageData) return;
    ctx.putImageData(imageData, 0, 0);
    updateHistoryButtons();
  }

  let savedBeforeDrawing = false;

  function startDrawing(e: MouseEvent | TouchEvent) {
    isDrawing = true;
    savedBeforeDrawing = false;
    hasUserDrawn = true;

    const rect = canvas.getBoundingClientRect();
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
    lastX = clientX - rect.left;
    lastY = clientY - rect.top;

    requestAnimationFrame(() => {
      if (isDrawing && !savedBeforeDrawing && canvasHistory && ctx) {
        const currentState = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const lastState = canvasHistory.getCurrent();
        if (!lastState || !areImageDataEqual(currentState, lastState)) {
          canvasHistory.push(currentState);
          updateHistoryButtons();
          savedBeforeDrawing = true;
        }
      }
    });
  }

  function draw(e: MouseEvent | TouchEvent) {
    if (!isDrawing || !ctx) return;

    const rect = canvas.getBoundingClientRect();
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
    const currentX = clientX - rect.left;
    const currentY = clientY - rect.top;

    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    switch (brushTool) {
      case 'eraser':
        ctx.globalCompositeOperation = 'destination-out';
        ctx.lineWidth = brushSize * 2;
        break;
      case 'marker':
        ctx.globalCompositeOperation = 'multiply';
        ctx.globalAlpha = 0.5;
        ctx.strokeStyle = color;
        ctx.lineWidth = brushSize * 3;
        break;
      case 'pencil':
        ctx.globalCompositeOperation = 'source-over';
        ctx.globalAlpha = 0.8;
        ctx.strokeStyle = color;
        ctx.lineWidth = Math.max(1, brushSize / 2);
        break;
      default: // pen
        ctx.globalCompositeOperation = 'source-over';
        ctx.globalAlpha = 1;
        ctx.strokeStyle = color;
        ctx.lineWidth = brushSize;
    }

    ctx.beginPath();
    ctx.moveTo(lastX, lastY);
    ctx.lineTo(currentX, currentY);
    ctx.stroke();

    // 重置设置
    ctx.globalCompositeOperation = 'source-over';
    ctx.globalAlpha = 1;

    lastX = currentX;
    lastY = currentY;
  }

  function stopDrawing() {
    if (isDrawing) {
      isDrawing = false;
      savedBeforeDrawing = false;
      // 自动保存状态
      if (canvasHistory) {
        saveCanvasState();
      }
    }
  }

  function areImageDataEqual(a: ImageData, b: ImageData): boolean {
    if (a.width !== b.width || a.height !== b.height) return false;
    return a.data.length === b.data.length;
  }

  async function clearCanvas() {
    if (ctx) {
      saveCanvasState();
      ctx.fillStyle = 'white';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = color;
      hasUserDrawn = false;
      saveCanvasState();

      if (wsManager && wsManager.isConnected()) {
        try {
          const clearMessage = JSON.stringify({ status: 'clear_canvas' });
          wsManager.send(clearMessage);
          console.log('🗑️ 已发送清空画布信号');
        } catch (error) {
          console.error('发送清空信号失败:', error);
        }
      }
    }
  }

  async function connectToServer() {
    if (wsManager && wsManager.isConnected()) {
      wsManager.disconnect();
      wsManager = null;
      return;
    }

    try {
      userId = generateUUID();
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/api/canvas/sessions/${userId}/ws`;

      connectionStatus = '连接中...';

      wsManager = new WebSocketManager(
        { url: wsUrl, maxReconnectAttempts: 5, reconnectDelay: 1000, maxReconnectDelay: 30000, reconnectDecayRate: 1.5 },
        {
          onOpen: () => {
            connectionStatus = '已连接';
            isConnected = true;
            console.log('✅ WebSocket连接成功');
          },
          onClose: () => {
            connectionStatus = '未连接';
            isConnected = false;
            if (isSending) {
              stopSending();
            }
          },
          onError: (error) => {
            console.error('❌ WebSocket错误:', error);
            connectionStatus = '连接错误';
            isConnected = false;
            setError({
              type: ErrorType.WEBSOCKET,
              message: 'WebSocket连接错误',
              details: '无法建立或维持WebSocket连接',
              recoverable: true,
              suggestions: ['检查后端服务是否正常运行', '检查网络连接', '尝试刷新页面重新连接']
            });
          },
          onMessage: async (event) => {
            try {
              if (event.data instanceof Blob || event.data instanceof ArrayBuffer) {
                return;
              }

              const data = JSON.parse(event.data);
              if (data.status === 'send_frame') {
                if (isSending && isConnected) {
                  if (!frameCaptureId) {
                    startFrameCapture();
                  }
                  requestAnimationFrame(() => {
                    if (isSending && isConnected) {
                      sendFrame();
                    }
                  });
                }
              }
            } catch (e) {
              console.error('解析 WebSocket 消息失败:', e);
            }
          }
        }
      );

      wsManager.connect();
    } catch (error) {
      console.error('❌ 连接失败:', error);
      connectionStatus = '连接失败';
    }
  }

  async function captureFrame(now: DOMHighResTimeStamp) {
    if (now - lastFrameMillis < THROTTLE) {
      frameCaptureId = requestAnimationFrame(captureFrame);
      return;
    }

    if (!ctx || !canvas) {
      frameCaptureId = requestAnimationFrame(captureFrame);
      return;
    }

    if (isSending && isConnected && !isSendingFrame) {
      await sendFrame();
    }

    lastFrameMillis = now;

    if (isSending) {
      frameCaptureId = requestAnimationFrame(captureFrame);
    } else {
      frameCaptureId = null;
    }
  }

  function startFrameCapture() {
    if (!frameCaptureId && isSending) {
      lastFrameMillis = performance.now();
      frameCaptureId = requestAnimationFrame(captureFrame);
      console.log('🚀 启动帧捕获');
    }
  }

  function stopFrameCapture() {
    if (frameCaptureId) {
      cancelAnimationFrame(frameCaptureId);
      frameCaptureId = null;
      console.log('⏹️ 停止帧捕获');
    }
  }

  async function sendFrame() {
    if (!wsManager || !wsManager.isConnected() || !isSending || isSendingFrame) {
      return;
    }

    if (!hasUserDrawn) {
      return;
    }

    isSendingFrame = true;

    try {
      const DOWNSAMPLE_SIZE = 512;

      const tempCanvas = document.createElement('canvas');
      tempCanvas.width = DOWNSAMPLE_SIZE;
      tempCanvas.height = DOWNSAMPLE_SIZE;
      const tempCtx = tempCanvas.getContext('2d');

      if (!tempCtx) {
        console.error('无法创建临时 canvas 上下文');
        return;
      }

      tempCtx.imageSmoothingEnabled = true;
      tempCtx.imageSmoothingQuality = 'high';
      tempCtx.drawImage(canvas, 0, 0, DOWNSAMPLE_SIZE, DOWNSAMPLE_SIZE);

      await new Promise<void>((resolve, reject) => {
        tempCanvas.toBlob(async (blob) => {
          try {
            if (!blob) {
              console.error('无法将画布转换为 Blob');
              resolve();
              return;
            }

            if (!wsManager || !wsManager.isConnected() || !isSending) {
              resolve();
              return;
            }

            const currentParams = getPipelineValues();
            const params: Record<string, any> = {
              prompt: currentParams.prompt || (pipelineParams?.prompt?.default || ''),
              negative_prompt: currentParams.negative_prompt || (pipelineParams?.negative_prompt?.default || 'blurry, low quality, distorted, deformed'),
              steps: currentParams.steps ?? (pipelineParams?.steps?.default ?? 4),
              cfg_scale: currentParams.cfg_scale ?? (pipelineParams?.cfg_scale?.default ?? 2.0),
              denoise: currentParams.denoise ?? (pipelineParams?.denoise?.default ?? 0.5),
              width: 512,
              height: 512,
              seed: currentParams.seed ?? (pipelineParams?.seed?.default ?? -1),
            };

            const jsonString = JSON.stringify({ status: 'next_frame', params: params });
            const jsonBytes = new TextEncoder().encode(jsonString);
            const jsonLen = jsonBytes.length;

            const imageBuffer = await blob.arrayBuffer();
            const totalLen = 4 + jsonLen + imageBuffer.byteLength;
            const buffer = new Uint8Array(totalLen);
            const view = new DataView(buffer.buffer);

            view.setUint32(0, jsonLen, false);
            buffer.set(jsonBytes, 4);
            buffer.set(new Uint8Array(imageBuffer), 4 + jsonLen);

            wsManager.send(buffer);

            // 添加到生成历史
            const imageUrl = URL.createObjectURL(blob);
            generatedImages.unshift({
              id: generateUUID(),
              url: imageUrl,
              timestamp: new Date(),
              prompt: params.prompt
            });

            if (generatedImages.length > 20) {
              generatedImages = generatedImages.slice(0, 20);
            }

            resolve();
          } catch (error) {
            console.error('发送图像失败:', error);
            reject(error);
          }
        }, 'image/png', 0.9);
      });
    } catch (error) {
      console.error('发送图像失败:', error);
    } finally {
      isSendingFrame = false;
    }
  }

  function startSending() {
    if (!wsManager || !isConnected) {
      setError({
        type: ErrorType.WEBSOCKET,
        message: '请先连接服务器',
        details: '在开始发送之前，需要先建立WebSocket连接',
        recoverable: true,
        suggestions: ['点击"连接服务器"按钮建立连接']
      });
      return;
    }

    isSending = true;
    startFrameCapture();
    console.log('📡 开始发送画布数据');
  }

  function stopSending() {
    isSending = false;
    stopFrameCapture();
    console.log('⏹️ 停止发送');
  }

  function saveDrawing() {
    if (!canvas) return;

    const link = document.createElement('a');
    link.download = `artwork_${new Date().getTime()}.png`;
    link.href = canvas.toDataURL();
    link.click();

    setError({
      type: ErrorType.API,
      message: '画作已保存',
      details: '画作已下载到本地',
      recoverable: true,
      suggestions: []
    });
  }

  function downloadImage(imageUrl: string, prompt: string) {
    const link = document.createElement('a');
    link.download = `generated_${prompt.substring(0, 20)}_${new Date().getTime()}.png`;
    link.href = imageUrl;
    link.click();
  }
</script>

<svelte:head>
  <title>专业画板 - ArtFlow</title>
</svelte:head>

<!-- 使用设计令牌的统一布局 -->
<main class="page-layout page-theme-professional">
  <div class="container">
    <ErrorHandler />

    <!-- 页面标题 -->
    <header class="page-header">
      <h1 class="page-title text-gradient">
        🎨 专业画板
      </h1>
      <p class="page-subtitle">创作你的艺术作品，实时AI生成</p>
    </header>

    <!-- 专业工具栏 -->
    <section class="professional-toolbar">
      <div class="toolbar-container">

        <!-- 左侧：绘画工具组 -->
        <div class="tools-section">
          <div class="tool-category">
            <div class="category-title">
              <span class="category-icon">🎨</span>
              <span>绘画工具</span>
            </div>
            <div class="tool-grid">
              <button
                on:click={() => brushTool = 'pen'}
                class="tool-button {brushTool === 'pen' ? 'active' : ''}"
                title="画笔工具 (B)"
              >
                <span class="tool-emoji">✏️</span>
                <span class="tool-name">画笔</span>
              </button>
              <button
                on:click={() => brushTool = 'pencil'}
                class="tool-button {brushTool === 'pencil' ? 'active' : ''}"
                title="铅笔工具 (P)"
              >
                <span class="tool-emoji">✍️</span>
                <span class="tool-name">铅笔</span>
              </button>
              <button
                on:click={() => brushTool = 'marker'}
                class="tool-button {brushTool === 'marker' ? 'active' : ''}"
                title="马克笔 (M)"
              >
                <span class="tool-emoji">🖊️</span>
                <span class="tool-name">马克笔</span>
              </button>
              <button
                on:click={() => brushTool = 'eraser'}
                class="tool-button {brushTool === 'eraser' ? 'active' : ''}"
                title="橡皮擦 (E)"
              >
                <span class="tool-emoji">🧹</span>
                <span class="tool-name">橡皮擦</span>
              </button>
            </div>
          </div>

          <!-- 颜色和大小控制 -->
          <div class="controls-category">
            <div class="control-group">
              <label class="control-label">
                <span class="label-icon">🎨</span>
                <span>颜色</span>
              </label>
              <div class="color-controls">
                <input
                  type="color"
                  bind:value={color}
                  class="color-input"
                  aria-label="画笔颜色"
                />
                <div class="preset-colors-grid">
                  {#each ['#000000', '#FF4444', '#44FF44', '#4444FF', '#FFFF44', '#FF44FF', '#44FFFF', '#FFFFFF'] as presetColor}
                    <button
                      on:click={() => color = presetColor}
                      class="preset-color-btn"
                      style="background-color: {presetColor}"
                      title={presetColor}
                    ></button>
                  {/each}
                </div>
              </div>
            </div>

            <div class="control-group">
              <label class="control-label">
                <span class="label-icon">📏</span>
                <span>画笔大小</span>
              </label>
              <div class="size-controls">
                <input
                  type="range"
                  bind:value={brushSize}
                  min="1"
                  max="100"
                  class="size-slider"
                  aria-label="画笔大小"
                />
                <div class="size-display">{brushSize}px</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 中间：编辑操作组 -->
        <div class="actions-section">
          <div class="action-category">
            <div class="category-title">
              <span class="category-icon">⚡</span>
              <span>快捷操作</span>
            </div>
            <div class="action-buttons">
              <button
                on:click={undoCanvas}
                disabled={!canUndo}
                class="action-button secondary"
                title="撤销操作 (Ctrl+Z)"
              >
                <span class="action-icon">↶</span>
                <span>撤销</span>
              </button>
              <button
                on:click={redoCanvas}
                disabled={!canRedo}
                class="action-button secondary"
                title="重做操作 (Ctrl+Shift+Z)"
              >
                <span class="action-icon">↷</span>
                <span>重做</span>
              </button>
              <button
                on:click={clearCanvas}
                class="action-button danger"
                title="清空画布 (Delete)"
              >
                <span class="action-icon">🗑️</span>
                <span>清空</span>
              </button>
              <button
                on:click={saveDrawing}
                class="action-button success"
                title="保存画作 (Ctrl+S)"
              >
                <span class="action-icon">💾</span>
                <span>保存</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 右侧：AI生成控制 -->
        <div class="ai-section">
          <div class="ai-category">
            <div class="category-title">
              <span class="category-icon">🤖</span>
              <span>AI 生成控制</span>
            </div>
            <div class="ai-controls">
              <div class="connection-control">
                <button
                  on:click={connectToServer}
                  class="ai-button {isConnected ? 'disconnected' : 'connected'}"
                >
                  <span class="ai-icon">{isConnected ? '🔌' : '🔗'}</span>
                  <span>{isConnected ? '断开连接' : '连接AI'}</span>
                </button>
              </div>

              <div class="generation-controls">
                <button
                  on:click={startSending}
                  disabled={!isConnected || isSending}
                  class="ai-button start"
                >
                  <span class="ai-icon">▶️</span>
                  <span>开始生成</span>
                </button>
                <button
                  on:click={stopSending}
                  disabled={!isSending}
                  class="ai-button stop"
                >
                  <span class="ai-icon">⏹️</span>
                  <span>停止生成</span>
                </button>
              </div>

              <div class="status-indicator">
                <div class="status-dot {isConnected ? 'online' : 'offline'}"></div>
                <div class="status-info">
                  <span class="status-text">{connectionStatus}</span>
                  {#if isSending}
                    <span class="generating-text">AI生成中...</span>
                  {/if}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 主要内容区域 -->
    <div class="main-grid">

      <!-- 左侧：画布区域 -->
      <div class="canvas-section">
        <div class="surface">
          <div class="section-header">
            <h2 class="section-title">
              <span>🎨</span>
              <span>绘画区域</span>
              <span class="canvas-size">1024 × 1024</span>
            </h2>
          </div>
          <div class="canvas-container">
            <canvas
              bind:this={canvas}
              width="1024"
              height="1024"
              class="drawing-canvas"
              on:mousedown={startDrawing}
              on:mousemove={draw}
              on:mouseup={stopDrawing}
              on:mouseleave={stopDrawing}
              on:touchstart={startDrawing}
              on:touchmove={draw}
              on:touchend={stopDrawing}
            ></canvas>
            {#if isSending}
              <div class="generating-indicator">
                <div class="pulse-dot"></div>
                AI生成中...
              </div>
            {/if}
          </div>
        </div>
      </div>

      <!-- 右侧：生成结果和设置 -->
      <div class="sidebar-section">

        <!-- AI生成结果 -->
        <div class="surface">
          <div class="section-header">
            <h2 class="section-title">
              <span>✨</span>
              <span>AI生成结果</span>
            </h2>
          </div>
          {#if userId}
            <ImagePlayer {userId} streamPath="/api/canvas/sessions" />
          {:else}
            <div class="empty-state">
              <span class="empty-icon">🤖</span>
              <p class="empty-text">点击"连接AI"开始创作</p>
            </div>
          {/if}
        </div>

        <!-- 快速设置 -->
        <div class="surface">
          <div class="section-header">
            <h2 class="section-title">
              <span>⚙️</span>
              <span>生成设置</span>
            </h2>
            <button
              on:click={() => showParams = !showParams}
              class="toggle-btn"
            >
              {showParams ? '隐藏详情' : '显示详情'}
            </button>
          </div>

          {#if pipelineParams && showParams}
            <PipelineOptions {pipelineParams} />
          {:else}
            <div class="settings-placeholder">
              <p>当前使用默认生成参数</p>
              <p>点击"显示详情"查看完整参数</p>
            </div>
          {/if}
        </div>

        <!-- 模型管理 -->
        <div class="surface">
          <div class="section-header">
            <h2 class="section-title">
              <span>🎭</span>
              <span>模型选择</span>
            </h2>
          </div>
          <ModelManager />
        </div>

        <!-- 提示词模板 -->
        <div class="surface">
          <div class="section-header">
            <h2 class="section-title">
              <span>💭</span>
              <span>提示词模板</span>
            </h2>
          </div>
          <PromptTemplates />
        </div>
      </div>
    </div>

    <!-- 生成历史 -->
    {#if generatedImages.length > 0}
      <section class="history-section surface">
        <div class="section-header">
          <h2 class="section-title">
            <span>📸</span>
            <span>生成历史</span>
            <span class="history-count">({generatedImages.length} 张)</span>
          </h2>
          <button
            on:click={() => showHistory = !showHistory}
            class="toggle-btn"
          >
            {showHistory ? '隐藏' : '显示'}
          </button>
        </div>

        {#if showHistory}
          <div class="history-grid">
            {#each generatedImages as image (image.id)}
              <div class="history-item">
                <button
                  type="button"
                  on:click={() => window.open(image.url, '_blank')}
                  class="history-image"
                  title="查看原图"
                >
                  <img
                    src={image.url}
                    alt="生成结果: {image.prompt}"
                    class="image-thumb"
                  />
                </button>
                <div class="image-overlay">
                  <button
                    on:click|stopPropagation={() => downloadImage(image.url, image.prompt)}
                    class="download-btn"
                    title="下载"
                  >
                    💾
                  </button>
                </div>
                <p class="image-caption">{image.prompt || '无提示词'}</p>
              </div>
            {/each}
          </div>
        {/if}
      </section>
    {/if}

    <!-- 使用提示 -->
    <section class="tips-section">
      <h3 class="tips-title">💡 使用提示</h3>
      <div class="tips-content">
        <p>🎨 选择绘画工具，调整颜色和大小，在画布上自由创作</p>
        <p>🤖 点击"连接AI"建立连接，然后点击"开始生成"实时查看AI处理效果</p>
        <p>⌨️ 使用快捷键 B/E/M/P 切换工具，[ / ] 调整画笔大小，Ctrl+Z 撤销操作</p>
        <p>💾 随时保存你的画作到本地，系统也会自动记录生成历史</p>
      </div>
    </section>
  </div>

  <!-- 快捷键帮助面板 -->
  <KeyboardShortcuts bind:show={showShortcuts} />

  <!-- 快捷键提示按钮 -->
  <div class="help-button">
    <button
      on:click={() => showShortcuts = true}
      class="help-trigger"
      title="快捷键帮助 (Shift+?)"
    >
      ⌨️
    </button>
  </div>
</main>

<!-- 统一样式 -->
<style>
  /* 导入设计令牌 */
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: var(--font-family-base);
    background: var(--page-bg);
    color: var(--text-primary);
    min-height: 100vh;
    transition: var(--duration-normal) var(--ease-in-out);
  }

  /* 页面布局 */
  .page-layout {
    min-height: 100vh;
    padding: var(--space-lg);
  }

  .container {
    max-width: 1400px;
    margin: 0 auto;
  }

  /* 页面标题 */
  .page-header {
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
  }

  /* 专业工具栏样式 */
  .professional-toolbar {
    background: var(--card-bg);
    border: var(--card-border);
    border-radius: var(--card-radius);
    padding: var(--toolbar-padding);
    margin-bottom: var(--space-xl);
    box-shadow: var(--shadow-xl);
    backdrop-filter: blur(15px);
  }

  .toolbar-container {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: var(--space-xl);
    align-items: start;
  }

  .tools-section, .actions-section, .ai-section {
    display: flex;
    flex-direction: column;
    gap: var(--space-lg);
  }

  .tool-category, .action-category, .ai-category {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-xl);
    padding: var(--space-lg);
    backdrop-filter: blur(10px);
  }

  .category-title {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    margin-bottom: var(--space-md);
    font-size: var(--font-size-md);
    font-weight: var(--font-weight-semibold);
    color: var(--text-primary);
  }

  .category-icon {
    font-size: var(--font-size-lg);
  }

  /* 工具按钮样式 */
  .tool-grid, .action-buttons {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    gap: var(--space-sm);
  }

  .tool-button, .action-button {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-xs);
    padding: var(--space-md) var(--space-sm);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    background: var(--hover-bg);
    color: var(--text-primary);
    cursor: pointer;
    transition: var(--duration-normal) var(--ease-in-out);
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-medium);
  }

  .tool-button:hover, .action-button:hover:not(:disabled) {
    background: var(--active-bg);
    border-color: var(--accent-color);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  }

  .tool-button.active {
    background: var(--accent-color);
    border-color: var(--accent-color);
    color: white;
    box-shadow: var(--accent-glow) 0 0 20px;
  }

  .tool-emoji, .action-icon {
    font-size: var(--font-size-lg);
  }

  /* 控制组样式 */
  .controls-category {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  .control-group {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: var(--radius-lg);
    padding: var(--space-md);
  }

  .control-label {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    margin-bottom: var(--space-sm);
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--text-secondary);
  }

  .label-icon {
    font-size: var(--font-size-md);
  }

  /* 颜色控制 */
  .color-controls {
    display: flex;
    align-items: center;
    gap: var(--space-md);
    flex-wrap: wrap;
  }

  .color-input {
    width: 3rem;
    height: 3rem;
    border: 2px solid var(--border-color);
    border-radius: var(--radius-lg);
    cursor: pointer;
    background: transparent;
    transition: var(--duration-normal) var(--ease-in-out);
  }

  .color-input:hover {
    border-color: var(--accent-color);
    transform: scale(1.05);
  }

  .preset-colors-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--space-xs);
  }

  .preset-color-btn {
    width: 2rem;
    height: 2rem;
    border: 2px solid var(--border-color);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: var(--duration-fast) var(--ease-in-out);
  }

  .preset-color-btn:hover {
    transform: scale(1.15);
    border-color: var(--accent-color);
    box-shadow: 0 0 12px currentColor;
  }

  /* 大小控制 */
  .size-controls {
    display: flex;
    align-items: center;
    gap: var(--space-md);
  }

  .size-slider {
    flex: 1;
    height: 0.5rem;
    -webkit-appearance: none;
    appearance: none;
    background: var(--border-color);
    border-radius: var(--radius-full);
    outline: none;
  }

  .size-slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 1.25rem;
    height: 1.25rem;
    background: var(--accent-color);
    border-radius: var(--radius-full);
    cursor: pointer;
    box-shadow: var(--accent-glow) 0 0 10px;
  }

  .size-display {
    font-family: var(--font-family-mono);
    font-size: var(--font-size-sm);
    padding: var(--space-xs) var(--space-sm);
    background: var(--hover-bg);
    border-radius: var(--radius-md);
    min-width: 3.5rem;
    text-align: center;
    color: var(--text-primary);
    border: 1px solid var(--border-color);
  }

  /* AI控制样式 */
  .ai-controls {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
  }

  .connection-control, .generation-controls {
    display: flex;
    gap: var(--space-sm);
  }

  .ai-button {
    flex: 1;
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    padding: var(--space-md);
    border: none;
    border-radius: var(--radius-lg);
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    cursor: pointer;
    transition: var(--duration-normal) var(--ease-in-out);
  }

  .ai-button.connected {
    background: var(--accent-color);
    color: white;
    box-shadow: var(--accent-glow) 0 0 20px;
  }

  .ai-button.connected:hover:not(:disabled) {
    background: var(--color-primary-hover);
    transform: translateY(-1px);
  }

  .ai-button.disconnected {
    background: var(--color-danger);
    color: white;
  }

  .ai-button.start {
    background: var(--color-success);
    color: white;
  }

  .ai-button.start:hover:not(:disabled) {
    background: var(--color-success-hover);
    transform: translateY(-1px);
  }

  .ai-button.stop {
    background: var(--color-warning);
    color: white;
  }

  .ai-button.stop:hover:not(:disabled) {
    background: var(--color-warning-hover);
    transform: translateY(-1px);
  }

  .ai-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none !important;
  }

  .ai-icon {
    font-size: var(--font-size-md);
  }

  /* 状态指示器 */
  .status-indicator {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    padding: var(--space-md);
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: var(--radius-lg);
  }

  .status-info {
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
  }

  .status-text {
    font-size: var(--font-size-sm);
    color: var(--text-secondary);
  }

  .generating-text {
    font-size: var(--font-size-xs);
    color: var(--color-success);
    font-weight: var(--font-weight-medium);
  }

  .status-dot {
    width: 0.75rem;
    height: 0.75rem;
    border-radius: var(--radius-full);
  }

  .status-dot.online {
    background: var(--color-success);
    box-shadow: var(--shadow-success);
  }

  .status-dot.offline {
    background: var(--color-danger);
    box-shadow: 0 0 8px rgba(239, 68, 68, 0.5);
  }

  /* 工具栏 */
  .toolbar {
    padding: var(--space-lg);
    margin-bottom: var(--space-xl);
  }

  .toolbar-grid {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: var(--space-lg);
    align-items: center;
  }

  .tool-group {
    display: flex;
    align-items: center;
    gap: var(--space-md);
    flex-wrap: wrap;
  }

  .tool-subgroup {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    padding: var(--space-sm);
    background: rgba(255, 255, 255, 0.8);
    border-radius: var(--radius-lg);
    backdrop-filter: blur(8px);
  }

  .tool-label {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--text-secondary);
    white-space: nowrap;
  }

  .tool-buttons {
    display: flex;
    gap: var(--space-xs);
  }

  .tool-btn {
    padding: var(--space-sm);
    border: none;
    border-radius: var(--radius-md);
    background: var(--color-surface);
    color: var(--text-primary);
    cursor: pointer;
    transition: var(--duration-normal) var(--ease-in-out);
    font-size: var(--font-size-md);
  }

  .tool-btn:hover {
    background: var(--color-surface-hover);
    transform: translateY(-1px);
  }

  .tool-btn.active {
    background: var(--color-primary);
    color: white;
    box-shadow: var(--shadow-glow);
  }

  .color-picker {
    width: 2rem;
    height: 2rem;
    border: 2px solid var(--color-border);
    border-radius: var(--radius-md);
    cursor: pointer;
    background: transparent;
  }

  .preset-colors {
    display: flex;
    gap: var(--space-xs);
  }

  .preset-color {
    width: 1.5rem;
    height: 1.5rem;
    border: 2px solid var(--color-border);
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: var(--duration-fast) var(--ease-in-out);
  }

  .preset-color:hover {
    transform: scale(1.1);
    border-color: var(--color-primary);
  }

  .size-slider {
    width: 6rem;
    height: 0.5rem;
    -webkit-appearance: none;
    appearance: none;
    background: var(--color-border);
    border-radius: var(--radius-full);
    outline: none;
  }

  .size-slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 1.25rem;
    height: 1.25rem;
    background: var(--color-primary);
    border-radius: var(--radius-full);
    cursor: pointer;
  }

  .size-display {
    font-family: var(--font-family-mono);
    font-size: var(--font-size-sm);
    padding: var(--space-xs) var(--space-sm);
    background: var(--color-surface);
    border-radius: var(--radius-sm);
    min-width: 2.5rem;
    text-align: center;
  }

  /* 按钮样式 */
  .action-btn {
    padding: var(--space-sm) var(--space-md);
    border: none;
    border-radius: var(--radius-lg);
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    cursor: pointer;
    transition: var(--duration-normal) var(--ease-in-out);
    display: inline-flex;
    align-items: center;
    gap: var(--space-xs);
  }

  .action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .action-btn.primary {
    background: var(--color-primary);
    color: white;
  }

  .action-btn.success {
    background: var(--color-success);
    color: white;
  }

  .action-btn.warning {
    background: var(--color-warning);
    color: white;
  }

  .action-btn.danger {
    background: var(--color-danger);
    color: white;
  }

  .action-btn.secondary {
    background: var(--color-surface);
    color: var(--text-primary);
    border: 1px solid var(--color-border);
  }

  .action-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
  }

  /* 连接状态 */
  .connection-status {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    padding: var(--space-sm) var(--space-md);
    background: rgba(255, 255, 255, 0.8);
    border-radius: var(--radius-lg);
    backdrop-filter: blur(8px);
  }

  .status-dot {
    width: 0.75rem;
    height: 0.75rem;
    border-radius: var(--radius-full);
  }

  .status-dot.connected {
    background: var(--color-success);
    box-shadow: var(--shadow-success);
  }

  .status-dot.disconnected {
    background: var(--color-danger);
    box-shadow: 0 0 8px rgba(239, 68, 68, 0.5);
  }

  .status-text {
    font-size: var(--font-size-sm);
    color: var(--text-secondary);
  }

  /* 主网格布局 */
  .main-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: var(--space-xl);
    margin-bottom: var(--space-2xl);
  }

  /* 表面卡片 */
  .surface {
    background: var(--card-bg);
    border-radius: var(--radius-2xl);
    padding: var(--space-lg);
    box-shadow: var(--shadow-lg);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
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
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-semibold);
    color: var(--text-primary);
    margin: 0;
  }

  .toggle-btn {
    background: none;
    border: none;
    color: var(--color-primary);
    font-size: var(--font-size-sm);
    cursor: pointer;
    transition: var(--duration-fast) var(--ease-in-out);
  }

  .toggle-btn:hover {
    color: var(--color-primary-hover);
  }

  /* 画布区域 */
  .canvas-container {
    position: relative;
    background: var(--color-surface);
    border-radius: var(--radius-xl);
    padding: var(--space-lg);
    border: 2px solid var(--color-border);
  }

  .drawing-canvas {
    width: 100%;
    height: auto;
    border-radius: var(--radius-lg);
    cursor: crosshair;
    background: white;
    box-shadow: var(--shadow-xl);
    max-width: 100%;
    aspect-ratio: 1/1;
  }

  .canvas-size {
    font-size: var(--font-size-sm);
    color: var(--text-secondary);
    margin-left: auto;
  }

  .generating-indicator {
    position: absolute;
    top: var(--space-md);
    right: var(--space-md);
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    padding: var(--space-xs) var(--space-sm);
    background: var(--color-success);
    color: white;
    border-radius: var(--radius-full);
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    box-shadow: var(--shadow-success);
  }

  .pulse-dot {
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

  /* 空状态 */
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--space-3xl);
    text-align: center;
    background: var(--color-surface);
    border-radius: var(--radius-xl);
    border: 2px dashed var(--color-border-light);
  }

  .empty-icon {
    font-size: 3rem;
    margin-bottom: var(--space-md);
    opacity: 0.5;
  }

  .empty-text {
    color: var(--text-secondary);
    font-size: var(--font-size-md);
  }

  /* 设置占位符 */
  .settings-placeholder {
    color: var(--text-secondary);
    font-size: var(--font-size-sm);
    line-height: var(--line-height-relaxed);
  }

  /* 历史记录 */
  .history-section {
    margin-bottom: var(--space-xl);
  }

  .history-count {
    font-size: var(--font-size-sm);
    color: var(--text-secondary);
  }

  .history-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: var(--space-md);
    max-height: 16rem;
    overflow-y: auto;
  }

  .history-item {
    position: relative;
    group: true;
  }

  .history-image {
    width: 100%;
    height: 6rem;
    border: 2px solid var(--color-border);
    border-radius: var(--radius-lg);
    cursor: pointer;
    transition: var(--duration-normal) var(--ease-in-out);
    padding: 0;
    overflow: hidden;
    background: transparent;
  }

  .history-image:hover {
    border-color: var(--color-primary);
    transform: scale(1.02);
  }

  .image-thumb {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .image-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: var(--duration-fast) var(--ease-in-out);
    border-radius: var(--radius-lg);
  }

  .history-item:hover .image-overlay {
    opacity: 1;
  }

  .download-btn {
    padding: var(--space-xs);
    background: rgba(255, 255, 255, 0.9);
    border: none;
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: var(--duration-fast) var(--ease-in-out);
  }

  .download-btn:hover {
    background: white;
  }

  .image-caption {
    font-size: var(--font-size-xs);
    color: var(--text-secondary);
    margin-top: var(--space-xs);
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  /* 使用提示 */
  .tips-section {
    background: rgba(255, 255, 255, 0.6);
    border-radius: var(--radius-2xl);
    padding: var(--space-xl);
    text-align: center;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.3);
  }

  .tips-title {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    margin-bottom: var(--space-md);
    color: var(--text-primary);
  }

  .tips-content {
    font-size: var(--font-size-sm);
    color: var(--text-secondary);
    line-height: var(--line-height-relaxed);
  }

  .tips-content p {
    margin: var(--space-xs) 0;
  }

  /* 帮助按钮 */
  .help-button {
    position: fixed;
    bottom: var(--space-xl);
    right: var(--space-xl);
  }

  .help-trigger {
    width: 3rem;
    height: 3rem;
    border-radius: var(--radius-full);
    border: none;
    background: var(--card-bg);
    color: var(--text-secondary);
    font-size: var(--font-size-lg);
    cursor: pointer;
    box-shadow: var(--shadow-lg);
    transition: var(--duration-normal) var(--ease-in-out);
    backdrop-filter: blur(10px);
  }

  .help-trigger:hover {
    transform: scale(1.05);
    box-shadow: var(--shadow-xl);
    color: var(--text-primary);
  }

  /* 专业工具栏响应式设计 */
  @media (max-width: 1200px) {
    .toolbar-container {
      grid-template-columns: 1fr;
      gap: var(--space-lg);
    }

    .tool-grid, .action-buttons {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  @media (max-width: 768px) {
    .professional-toolbar {
      padding: var(--space-md);
    }

    .tool-category, .action-category, .ai-category {
      padding: var(--space-md);
    }

    .tool-grid, .action-buttons {
      grid-template-columns: repeat(2, 1fr);
      gap: var(--space-xs);
    }

    .tool-button, .action-button {
      padding: var(--space-sm) var(--space-xs);
      font-size: 0.7rem;
    }

    .color-controls {
      flex-direction: column;
      align-items: stretch;
    }

    .preset-colors-grid {
      grid-template-columns: repeat(8, 1fr);
    }

    .generation-controls {
      flex-direction: column;
    }

    .toolbar-grid {
      grid-template-columns: 1fr;
      gap: var(--space-md);
    }

    .tool-group {
      justify-content: center;
    }

    .main-grid {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: 640px) {
    .page-layout {
      padding: var(--space-sm);
    }

    .page-title {
      font-size: var(--font-size-2xl);
    }

    .tool-grid, .action-buttons {
      grid-template-columns: repeat(2, 1fr);
    }

    .tool-button, .action-button {
      padding: var(--space-xs);
      font-size: 0.65rem;
      min-width: 80px;
    }

    .tool-emoji, .action-icon {
      font-size: var(--font-size-md);
    }

    .category-title {
      font-size: var(--font-size-sm);
    }

    .control-group {
      padding: var(--space-sm);
    }

    .size-controls {
      flex-direction: column;
      gap: var(--space-sm);
    }

    .size-slider {
      width: 100%;
    }

    .ai-controls {
      gap: var(--space-sm);
    }

    .connection-control, .generation-controls {
      flex-direction: column;
    }

    .tool-subgroup {
      flex-wrap: wrap;
      justify-content: center;
    }

    .history-grid {
      grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    }
  }

  @media (max-width: 480px) {
    .tool-grid, .action-buttons {
      grid-template-columns: 1fr;
    }

    .tool-button, .action-button {
      flex-direction: row;
      justify-content: flex-start;
      min-width: auto;
    }

    .preset-colors-grid {
      grid-template-columns: repeat(4, 1fr);
    }
  }
</style>