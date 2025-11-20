<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import type { Fields } from '$lib/types';
  import PipelineOptions from '$lib/components/PipelineOptions.svelte';
  import ModelManager from '$lib/components/ModelManager.svelte';
  import ErrorHandler from '$lib/components/ErrorHandler.svelte';
  import MultiControlNetPanel from '$lib/components/MultiControlNetPanel.svelte';
  import ImagePlayer from '$lib/components/ImagePlayer.svelte';
  import { getPipelineValues, pipelineValues, setError, ErrorType } from '$lib/store';
  import { HistoryManager } from '$lib/utils/history';
  import { keyboardManager } from '$lib/utils/keyboard';
  import KeyboardShortcuts from '$lib/components/KeyboardShortcuts.svelte';
  import { WebSocketManager, ConnectionStatus } from '$lib/utils/websocket';
  import { lcmLiveActions, LCMLiveStatus, userIdStore } from '$lib/lcmLive';
  import { onFrameChangeStore } from '$lib/mediaStream';
  
  let showShortcuts = false;

  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D | null = null;
  let isDrawing = false;
  let lastX = 0;
  let lastY = 0;
  
  let color = '#000000';
  let brushSize = 5;
  
  // 撤销/重做历史
  let canvasHistory: HistoryManager<ImageData> | null = null;
  let canUndo = false;
  let canRedo = false;
  
  // MultiControlNet配置
  let showMultiControlNet = false;
  let multiControlNetConfig: Array<{
    id: string;
    type: string;
    image: string;
    weight: number;
    guidanceStart: number;
    guidanceEnd: number;
  }> = [];
  
  // 监听MultiControlNet配置变化
  $: {
    if (multiControlNetConfig.length > 0) {
      console.log(`🎮 MultiControlNet状态: ${multiControlNetConfig.length}个ControlNet已配置`);
      multiControlNetConfig.forEach((cn, index) => {
        console.log(`  - ControlNet ${index + 1}: 类型=${cn.type}, 权重=${cn.weight}`);
      });
    }
  }
  
  let wsManager: WebSocketManager | null = null;
  let userId: string | null = null;
  let isSending = false;
  let connectionStatus = '未连接';
  let isConnected = false;
  let isSendingFrame = false; // 防止并发发送
  let canvasChanged = false; // 标记画布是否发生变化
  let debounceTimer: ReturnType<typeof setTimeout> | null = null; // 防抖定时器
  let animationFrameId: number | null = null; // requestAnimationFrame ID
  const DEBOUNCE_DELAY = 100; // 防抖延迟（100ms）
  
  // 性能优化：差分传输
  let lastSentImageData: ImageData | null = null;
  let useDiffTransfer = true;  // 启用差分传输
  let diffThreshold = 10;  // 差异阈值（0-255）
  
  // 参数配置
  let pipelineParams: Fields | null = null;
  let showParams = false;
  
  // CLIP反推配置
  let showCLIPInterrogator = false;
  let clipImageUrl: string = '';
  let clipMode: 'fast' | 'classic' | 'negative' = 'fast';
  let clipInterrogating = false;
  let clipResult: {
    prompt: string;
    negative_prompt: string;
    flavors: string[];
    mode: string;
  } | null = null;
  let clipError: string = '';
  
  // 监听pipelineValues变化，特别是prompt变化时触发发送
  let lastPrompt = '';
  let lastNegativePrompt = '';
  $: {
    const currentPrompt = $pipelineValues.prompt || '';
    const currentNegativePrompt = $pipelineValues.negative_prompt || '';
    
    // 如果prompt或negative_prompt变化，且正在发送，触发发送新帧
    if (isSending && isConnected && (currentPrompt !== lastPrompt || currentNegativePrompt !== lastNegativePrompt)) {
      lastPrompt = currentPrompt;
      lastNegativePrompt = currentNegativePrompt;
      
      // 标记画布已变化，触发防抖发送
      canvasChanged = true;
      scheduleSend();
    } else {
      // 初始化时设置初始值
      if (!lastPrompt && currentPrompt) {
        lastPrompt = currentPrompt;
      }
      if (!lastNegativePrompt && currentNegativePrompt) {
        lastNegativePrompt = currentNegativePrompt;
      }
    }
  }
  
  /**
   * 调度发送：使用防抖机制减少发送频率
   */
  function scheduleSend() {
    // 清除之前的防抖定时器
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    
    // 取消之前的动画帧请求
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }
    
    // 设置新的防抖定时器
    debounceTimer = setTimeout(() => {
      // 使用单个requestAnimationFrame确保绘制完成
      animationFrameId = requestAnimationFrame(() => {
        if (isSending && isConnected && canvasChanged) {
          sendFrame();
          canvasChanged = false;
        }
        animationFrameId = null;
      });
      debounceTimer = null;
    }, DEBOUNCE_DELAY);
  }

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

  // 快捷键取消注册函数
  let unregisterShortcuts: (() => void)[] = [];

  // 帧捕获相关（照搬streamdiffusion的VideoInput核心逻辑）
  let frameCaptureId: number | null = null;
  const THROTTLE = 1000 / 120; // 120fps
  let lastFrameMillis = 0;
  
  async function captureFrame(now: DOMHighResTimeStamp) {
    if (now - lastFrameMillis < THROTTLE) {
      frameCaptureId = requestAnimationFrame(captureFrame);
      return;
    }
    
    if (!ctx || !canvas) {
      frameCaptureId = requestAnimationFrame(captureFrame);
      return;
    }

    // 将画布转换为blob（照搬streamdiffusion的VideoInput逻辑）
    const blob = await new Promise<Blob>((resolve) => {
      canvas.toBlob(
        (blob) => {
          resolve(blob as Blob);
        },
        'image/jpeg',
        0.95
      );
    });
    
    // 更新onFrameChangeStore（照搬streamdiffusion的核心逻辑）
    onFrameChangeStore.set({ blob });
    lastFrameMillis = now;
    frameCaptureId = requestAnimationFrame(captureFrame);
  }

  onMount(async () => {
    if (canvas) {
      ctx = canvas.getContext('2d');
      if (ctx) {
        // 初始化画布为白色
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = color;
        
        // 初始化历史记录
        canvasHistory = new HistoryManager<ImageData>(20);
        saveCanvasState();
        
        // 开始帧捕获（照搬streamdiffusion的VideoInput核心逻辑）
        lastFrameMillis = performance.now();
        frameCaptureId = requestAnimationFrame(captureFrame);
      }
    }
    
    // 注册快捷键
    const unregisterUndo = keyboardManager.register(
      { key: 'z', ctrl: true },
      (e) => {
        if (!e.shiftKey) {
          undoCanvas();
          return false; // 阻止默认行为
        }
      }
    );
    
    const unregisterRedo = keyboardManager.register(
      { key: 'z', ctrl: true, shift: true },
      (e) => {
        redoCanvas();
        return false; // 阻止默认行为
      }
    );
    
    const unregisterClear = keyboardManager.register(
      { key: 'Delete' },
      (e) => {
        if (document.activeElement?.tagName !== 'INPUT' && document.activeElement?.tagName !== 'TEXTAREA') {
          clearCanvas();
          return false;
        }
      }
    );
    
    const unregisterHelp = keyboardManager.register(
      { key: '?', shift: true },
      (e) => {
        showShortcuts = !showShortcuts;
        return false;
      }
    );
    
    // 保存取消注册函数
    unregisterShortcuts = [unregisterUndo, unregisterRedo, unregisterClear, unregisterHelp];
    
    // 从后端获取参数配置
    try {
      const response = await fetch('/api/settings');
      const data = await response.json();
      if (data.input_params?.properties) {
        const params = data.input_params.properties as Fields;
        pipelineParams = params;
        // 初始化默认值
        const initialValues: Record<string, any> = {};
        for (const [key, field] of Object.entries(params)) {
          initialValues[key] = field.default;
        }
        // 使用 store 来管理参数值
        pipelineValues.set(initialValues);
      }
      

    } catch (error) {
      console.error('获取参数配置失败:', error);
    }
  });

  // 保存画布状态到历史记录
  function saveCanvasState() {
    if (!canvas || !ctx || !canvasHistory) return;
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    canvasHistory.push(imageData);
    updateHistoryButtons();
  }
  
  // 从历史记录恢复画布状态
  function restoreCanvasState(imageData: ImageData | null) {
    if (!canvas || !ctx || !imageData) return;
    ctx.putImageData(imageData, 0, 0);
    canvasChanged = true;
    updateHistoryButtons();
  }
  
  // 更新撤销/重做按钮状态
  function updateHistoryButtons() {
    if (!canvasHistory) return;
    const info = canvasHistory.getInfo();
    canUndo = info.canUndo;
    canRedo = info.canRedo;
  }
  
  // 撤销
  function undoCanvas() {
    if (!canvasHistory || !canUndo) return;
    const state = canvasHistory.undo();
    restoreCanvasState(state);
    // 如果正在发送，触发防抖发送
    if (isSending && isConnected) {
      scheduleSend();
    }
  }
  
  // 重做
  function redoCanvas() {
    if (!canvasHistory || !canRedo) return;
    const state = canvasHistory.redo();
    restoreCanvasState(state);
    // 如果正在发送，触发防抖发送
    if (isSending && isConnected) {
      scheduleSend();
    }
  }

  // 标记是否已保存当前笔画开始前的状态
  let savedBeforeDrawing = false;

  function startDrawing(e: MouseEvent | TouchEvent) {
    isDrawing = true;
    savedBeforeDrawing = false;
    
    const rect = canvas.getBoundingClientRect();
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
    lastX = clientX - rect.left;
    lastY = clientY - rect.top;
    
    // 延迟保存，确保这是新笔画的开始
    requestAnimationFrame(() => {
      if (isDrawing && !savedBeforeDrawing && canvasHistory && ctx) {
        const currentState = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const lastState = canvasHistory.getCurrent();
        // 只在状态真正变化时才保存
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

    ctx.strokeStyle = color;
    ctx.lineWidth = brushSize;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    ctx.beginPath();
    ctx.moveTo(lastX, lastY);
    ctx.lineTo(currentX, currentY);
    ctx.stroke();

    lastX = currentX;
    lastY = currentY;
    
    // 标记画布已变化，触发防抖发送
    canvasChanged = true;
    if (isSending && isConnected) {
      scheduleSend();
    }
  }

  function stopDrawing() {
    if (!isDrawing) return;
    isDrawing = false;
    savedBeforeDrawing = false; // 重置标记，为下一笔做准备
    
    // 停止绘制后，触发防抖发送以确保最后一笔被发送
    if (canvasChanged && isSending && isConnected) {
      scheduleSend();
    }
  }
  
  // 比较两个ImageData是否相同（简单版本，只比较数据长度）
  function areImageDataEqual(a: ImageData, b: ImageData): boolean {
    if (a.width !== b.width || a.height !== b.height) return false;
    // 简单比较：只检查数据长度，不比较每个像素（性能考虑）
    return a.data.length === b.data.length;
  }

  function clearCanvas() {
    if (ctx) {
      // 保存清空前的状态
      saveCanvasState();
      
      ctx.fillStyle = 'white';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = color;
      
      // 保存清空后的状态
      saveCanvasState();
      
      // 清空画布后立即发送（清除防抖，立即发送）
      canvasChanged = true;
      if (isSending && isConnected) {
        // 清除防抖定时器，立即发送
        if (debounceTimer) {
          clearTimeout(debounceTimer);
          debounceTimer = null;
        }
        if (animationFrameId) {
          cancelAnimationFrame(animationFrameId);
          animationFrameId = null;
        }
        
        // 使用单个requestAnimationFrame确保清空操作完成
        requestAnimationFrame(() => {
          if (isSending && isConnected) {
            sendFrame();
            canvasChanged = false;
          }
        });
      }
    }
  }

  async function connectToServer() {
    // 如果已连接，则断开
    if (wsManager && wsManager.isConnected()) {
      wsManager.disconnect();
      wsManager = null;
      return;
    }

    try {
      userId = generateUUID();
      // 使用相对路径，让 Vite 代理处理
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/api/ws/${userId}`;
      
      connectionStatus = '连接中...';
      
      // 创建 WebSocketManager 实例
      wsManager = new WebSocketManager(
        {
          url: wsUrl,
          maxReconnectAttempts: 5,
          reconnectDelay: 1000,
          maxReconnectDelay: 30000,
          reconnectDecayRate: 1.5
        },
        {
          onOpen: () => {
            connectionStatus = '已连接';
            isConnected = true;
            userIdStore.set(userId); // Sync userId with ImagePlayer
            console.log('✅ WebSocket连接成功，等待后端请求或用户开始发送');
          },
          
          onClose: () => {
            connectionStatus = '未连接';
            isConnected = false;
            userIdStore.set(null); // Clear userId from ImagePlayer
            if (isSending) {
              stopSending();
            }
          },
          
          onError: (error) => {
            console.error('❌ WebSocket错误:', error);
            connectionStatus = '连接错误';
            isConnected = false;
            userIdStore.set(null); // Clear userId on error
            setError({
              type: ErrorType.WEBSOCKET,
              message: 'WebSocket连接错误',
              details: '无法建立或维持WebSocket连接',
              recoverable: true,
              suggestions: [
                '检查后端服务是否正常运行',
                '检查网络连接',
                '尝试刷新页面重新连接'
              ]
            });
          },
          
          onMessage: async (event) => {
            try {
              if (event.data instanceof Blob || event.data instanceof ArrayBuffer) {
                return;
              }
              
              const data = JSON.parse(event.data);
              
              if (data.status === 'send_frame') {
                // 如果收到 send_frame 请求，应该立即发送当前画布状态
                if (isSending && isConnected) {
                  // 清除防抖，立即发送当前状态
                  if (debounceTimer) {
                    clearTimeout(debounceTimer);
                    debounceTimer = null;
                  }
                  if (animationFrameId) {
                    cancelAnimationFrame(animationFrameId);
                    animationFrameId = null;
                  }
                  
                  // 立即发送
                  requestAnimationFrame(() => {
                    if (isSending && isConnected) {
                      sendFrame();
                      canvasChanged = false;
                    }
                  });
                } else if (!isSending && isConnected) {
                  // 如果还没有开始发送，自动开始发送
                  console.log('收到 send_frame 请求，自动开始发送');
                  startSending();
                }
              } else if (data.status === 'connected') {
                // 连接成功消息
                console.log('WebSocket 连接成功');
                // 连接成功后，如果还没有开始发送，自动开始发送
                // 这样可以确保viewer能立即看到初始状态
                if (!isSending && isConnected) {
                  console.log('收到connected消息，自动开始发送');
                  startSending();
                }
              } else if (data.status === 'wait') {
                // 等待消息，不做处理
                console.log('收到 wait 消息');
                // 收到wait消息时，如果还没有开始发送，也自动开始发送
                if (!isSending && isConnected) {
                  console.log('收到wait消息，自动开始发送');
                  startSending();
                }
              }
            } catch (e) {
              // 忽略非 JSON 消息
              console.error('解析 WebSocket 消息失败:', e);
            }
          },
          
          onReconnecting: (attempt, maxAttempts) => {
            connectionStatus = `重连中 (${attempt}/${maxAttempts})`;
            console.log(`🔄 WebSocket重连中... (尝试 ${attempt}/${maxAttempts})`);
            setError({
              type: ErrorType.WEBSOCKET,
              message: 'WebSocket连接断开，正在重连...',
              details: `正在进行第 ${attempt} 次重连尝试（共 ${maxAttempts} 次）`,
              recoverable: true,
              suggestions: [
                '请稍候，系统正在自动重连',
                '如果持续失败，请检查网络连接',
                '可以尝试刷新页面'
              ]
            });
          },
          
          onReconnectFailed: () => {
            connectionStatus = '连接失败';
            isConnected = false;
            setError({
              type: ErrorType.WEBSOCKET,
              message: 'WebSocket重连失败',
              details: '已达到最大重连次数，请刷新页面或检查网络连接',
              recoverable: false,
              suggestions: [
                '刷新页面重新连接',
                '检查后端服务是否正常运行',
                '检查网络连接是否稳定'
              ]
            });
          }
        }
      );
      
      // 开始连接
      wsManager.connect();
      
    } catch (error) {
      console.error('❌ 连接失败:', error);
      connectionStatus = '连接失败';
      setError({
        type: ErrorType.WEBSOCKET,
        message: 'WebSocket连接失败',
        details: error instanceof Error ? error.message : '未知错误',
        recoverable: true,
        suggestions: [
          '确认后端服务已启动',
          '检查WebSocket端口是否可访问',
          '查看浏览器控制台获取详细错误信息'
        ]
      });
    }
  }

  /**
   * 性能优化：检查画布是否有显著变化
   * 如果变化很小，跳过发送，减少不必要的推理
   */
  function hasSignificantChange(): boolean {
    if (!ctx || !lastSentImageData) {
      return true;  // 首次发送
    }

    const currentImageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const prevData = lastSentImageData.data;
    const currData = currentImageData.data;
    
    // 采样检查（每隔 10 个像素检查一次，提高性能）
    let diffPixels = 0;
    const sampleRate = 10;
    const totalSamples = Math.floor(currData.length / (4 * sampleRate));
    
    for (let i = 0; i < currData.length; i += 4 * sampleRate) {
      const rDiff = Math.abs(currData[i] - prevData[i]);
      const gDiff = Math.abs(currData[i + 1] - prevData[i + 1]);
      const bDiff = Math.abs(currData[i + 2] - prevData[i + 2]);
      
      if (rDiff > diffThreshold || gDiff > diffThreshold || bDiff > diffThreshold) {
        diffPixels++;
      }
    }
    
    // 如果超过 1% 的采样像素有变化，认为有显著变化
    const changeRatio = diffPixels / totalSamples;
    return changeRatio > 0.01;
  }

  async function sendFrame() {
    if (!wsManager || !wsManager.isConnected() || !isSending || isSendingFrame) {
      return;
    }

    // 性能优化：智能跳帧 - 如果画布没有显著变化，跳过发送
    if (useDiffTransfer && !hasSignificantChange()) {
      console.log('⚡ 画布无显著变化，跳过发送');
      canvasChanged = false; // 重置标记
      return;
    }

    isSendingFrame = true;
    const perfStart = performance.now();
    
    try {
      // 高性能优化：降采样 + 二进制传输
      // 降采样到 384x384 以减少数据量（可选：256 或 512）
      const DOWNSAMPLE_SIZE = 384; // 384x384 平衡质量和性能
      
      // 创建临时 canvas 进行降采样
      const tempCanvas = document.createElement('canvas');
      tempCanvas.width = DOWNSAMPLE_SIZE;
      tempCanvas.height = DOWNSAMPLE_SIZE;
      const tempCtx = tempCanvas.getContext('2d');
      
      if (!tempCtx) {
        console.error('无法创建临时 canvas 上下文');
        return;
      }
      
      // 使用高质量缩放
      tempCtx.imageSmoothingEnabled = true;
      tempCtx.imageSmoothingQuality = 'high';
      tempCtx.drawImage(canvas, 0, 0, DOWNSAMPLE_SIZE, DOWNSAMPLE_SIZE);
      
      await new Promise<void>((resolve, reject) => {
        // 使用降采样后的 canvas，质量 0.5
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

            // 从 store 获取参数值
            const currentParams = getPipelineValues();
            
            // 构建参数对象，使用用户配置的值或默认值
            const params: Record<string, any> = {
              prompt: currentParams.prompt || (pipelineParams?.prompt?.default || 'masterpiece,inflatable flowers,transparency,blue sky background,high quality,'),
              negative_prompt: currentParams.negative_prompt || (pipelineParams?.negative_prompt?.default || 'ng_deepnegative_v1_75t,(badhandv4:1.2),EasyNegative,(worst quality:2),balloon,,nsfw'),
              steps: currentParams.steps ?? (pipelineParams?.steps?.default ?? 2),
              cfg_scale: currentParams.cfg_scale ?? (pipelineParams?.cfg_scale?.default ?? 1.5),
              denoise: currentParams.denoise ?? (pipelineParams?.denoise?.default ?? 0.6),
              width: 512,
              height: 512,
              seed: currentParams.seed ?? (pipelineParams?.seed?.default ?? 502923423887318),
              lora_selection: currentParams.lora_selection || (pipelineParams?.lora_selection?.default || 'none')
            };
            
            // 如果配置了MultiControlNet，添加MultiControlNet参数
            if (multiControlNetConfig.length > 0) {
              // 构建MultiControlNet参数数组
              params.controlnets = multiControlNetConfig.map(cn => ({
                type: cn.type,
                image: cn.image,
                weight: Math.max(0, Math.min(2, cn.weight)),
                guidance_start: Math.max(0, Math.min(1, cn.guidanceStart)),
                guidance_end: Math.max(0, Math.min(1, cn.guidanceEnd))
              }));
              console.log(`🎮 MultiControlNet已启用: ${multiControlNetConfig.length}个ControlNet`);
            } else {
              console.log('🎮 MultiControlNet未配置，使用普通img2img模式');
            }
            
            // 使用streamdiffusion的协议：先发送next_frame，再发送params，最后发送blob
            // 步骤1: 发送 next_frame 消息
            wsManager.send(JSON.stringify({ status: 'next_frame' }));
            // 步骤2: 发送参数 JSON
            wsManager.send(JSON.stringify(params));
            // 步骤3: 发送图像 blob
            wsManager.send(blob);
            
            const totalTime = performance.now() - perfStart;
            console.log(`📊 发送完成: 降采样=${DOWNSAMPLE_SIZE}x${DOWNSAMPLE_SIZE}, 总耗时=${totalTime.toFixed(1)}ms`);
            
            
            // 性能优化：保存当前帧用于下次比较
            if (ctx && useDiffTransfer) {
              lastSentImageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            }
            
            resolve();
          } catch (error) {
            console.error('发送图像失败:', error);
            reject(error);
          }
        }, 'image/webp', 0.5);  // 性能优化：使用 WebP 格式，质量 0.5 以提高实时性能
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
    canvasChanged = true; // 标记画布已变化，确保发送初始状态
    
    // 初始化prompt跟踪
    const currentPrompt = $pipelineValues.prompt || '';
    const currentNegativePrompt = $pipelineValues.negative_prompt || '';
    lastPrompt = currentPrompt;
    lastNegativePrompt = currentNegativePrompt;
    
    // 立即发送第一帧
    requestAnimationFrame(() => {
      if (isSending && isConnected && wsManager && wsManager.isConnected()) {
        sendFrame();
        canvasChanged = false;
      }
    });
  }

  function stopSending() {
    isSending = false;
    
    // 清除防抖定时器和动画帧
    if (debounceTimer) {
      clearTimeout(debounceTimer);
      debounceTimer = null;
    }
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }
    
    canvasChanged = false;
  }

  function copyUserId() {
    if (userId) {
      navigator.clipboard.writeText(userId).then(() => {
        setError({
          type: ErrorType.API,
          message: 'User ID 已复制到剪贴板',
          details: '您可以使用此ID在viewer页面查看生成结果',
          recoverable: true,
          suggestions: []
        });
      }).catch((err) => {
        setError({
          type: ErrorType.API,
          message: '复制失败',
          details: err instanceof Error ? err.message : '无法访问剪贴板',
          recoverable: true,
          suggestions: ['请手动复制User ID']
        });
      });
    }
  }
  
  // CLIP反推功能
  function analyzeCanvas() {
    if (!canvas) {
      setError({
        type: ErrorType.VALIDATION,
        message: '画布未初始化',
        details: '无法获取画布内容',
        recoverable: true,
        suggestions: ['请刷新页面重试']
      });
      return;
    }
    // 将画布转换为base64图像
    const dataUrl = canvas.toDataURL('image/png');
    clipImageUrl = dataUrl;
    clipResult = null;
    clipError = '';
    showCLIPInterrogator = true;
  }
  
  function analyzeViewerImage() {
    if (!userId) {
      setError({
        type: ErrorType.VALIDATION,
        message: '请先连接服务器获取User ID',
        details: '需要User ID才能获取生成结果图像',
        recoverable: true,
        suggestions: ['点击"连接服务器"按钮建立连接']
      });
      return;
    }
    // 构建viewer页面的图像URL
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
    const viewerImageUrl = `${protocol}//${window.location.host}/api/stream/${userId}`;
    clipImageUrl = viewerImageUrl;
    clipResult = null;
    clipError = '';
    showCLIPInterrogator = true;
  }
  
  async function performCLIPInterrogation() {
    if (!clipImageUrl) {
      setError({
        type: ErrorType.VALIDATION,
        message: '请先选择要分析的图像',
        details: '需要选择画布图像或生成结果图像',
        recoverable: true,
        suggestions: ['点击"分析画布图像"或"分析生成结果"按钮']
      });
      return;
    }
    
    clipInterrogating = true;
    clipError = '';
    clipResult = null;
    
    try {
      // 准备图像数据
      let imageData = clipImageUrl;
      if (!imageData.startsWith('data:')) {
        // 如果不是base64格式，尝试转换
        try {
          const response = await fetch(imageData);
          const blob = await response.blob();
          const reader = new FileReader();
          imageData = await new Promise<string>((resolve, reject) => {
            reader.onloadend = () => resolve(reader.result as string);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
          });
        } catch (e) {
          throw new Error('无法加载图像');
        }
      }
      
      const response = await fetch('/api/clip/interrogate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image: imageData,
          mode: clipMode,
        }),
      });
      
      const data = await response.json();
      
      if (!data.success) {
        setError({
          type: ErrorType.API,
          message: 'CLIP反推失败',
          details: data.message || '未知错误',
          recoverable: true,
          suggestions: [
            '检查后端CLIP服务是否正常',
            '尝试使用不同的反推模式',
            '确认图像格式正确'
          ]
        });
        return;
      }
      
      clipResult = {
        prompt: data.prompt || '',
        negative_prompt: data.negative_prompt || '',
        flavors: data.flavors || [],
        mode: data.mode || clipMode,
      };
    } catch (err) {
      console.error('CLIP反推失败:', err);
      setError({
        type: ErrorType.API,
        message: 'CLIP反推失败',
        details: err instanceof Error ? err.message : '未知错误',
        recoverable: true,
        suggestions: [
          '检查网络连接',
          '确认后端服务正常运行',
          '查看浏览器控制台获取详细错误'
        ]
      });
    } finally {
      clipInterrogating = false;
    }
  }
  
  function applyCLIPPrompt() {
    if (clipResult) {
      // 更新pipelineValues store
      const currentValues = getPipelineValues();
      pipelineValues.set({
        ...currentValues,
        prompt: clipResult.prompt,
        negative_prompt: clipResult.negative_prompt,
      });
      // 提示用户
      setError({
        type: ErrorType.API,
        message: 'Prompt已应用到画板参数',
        details: '反推的Prompt和Negative Prompt已成功应用',
        recoverable: true,
        suggestions: []
      });
    }
  }
  
  function copyCLIPPrompt() {
    if (clipResult) {
      navigator.clipboard.writeText(clipResult.prompt).then(() => {
        setError({
          type: ErrorType.API,
          message: 'Prompt已复制到剪贴板',
          details: '您可以在其他地方粘贴使用',
          recoverable: true,
          suggestions: []
        });
      }).catch((err) => {
        setError({
          type: ErrorType.API,
          message: '复制失败',
          details: err instanceof Error ? err.message : '无法访问剪贴板',
          recoverable: true,
          suggestions: ['请手动复制Prompt文本']
        });
      });
    }
  }
  
  function copyCLIPNegativePrompt() {
    if (clipResult) {
      navigator.clipboard.writeText(clipResult.negative_prompt).then(() => {
        setError({
          type: ErrorType.API,
          message: 'Negative Prompt已复制到剪贴板',
          details: '您可以在其他地方粘贴使用',
          recoverable: true,
          suggestions: []
        });
      }).catch((err) => {
        setError({
          type: ErrorType.API,
          message: '复制失败',
          details: err instanceof Error ? err.message : '无法访问剪贴板',
          recoverable: true,
          suggestions: ['请手动复制Negative Prompt文本']
        });
      });
    }
  }

  onDestroy(() => {
    stopSending();
    
    // 停止帧捕获（照搬streamdiffusion的VideoInput核心逻辑）
    if (frameCaptureId) {
      cancelAnimationFrame(frameCaptureId);
      frameCaptureId = null;
    }
    
    // 清理所有定时器和动画帧
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
    }
    
    // 清理 WebSocketManager
    if (wsManager) {
      wsManager.destroy();
      wsManager = null;
    }
    
    // 取消注册快捷键
    unregisterShortcuts.forEach(unregister => unregister());
  });
</script>

<svelte:head>
  <title>画板 - ArtFlow</title>
</svelte:head>

<main class="min-h-screen bg-surface">
  <div class="container mx-auto max-w-7xl px-4 py-6">
    <ErrorHandler />
    
    <div class="mb-6">
      <h1 class="title">✏️ 画板</h1>
      <p class="subtitle">手绘输入，实时生成AI图像</p>
    </div>

    <div class="card">
    <!-- 工具栏 -->
    <div class="flex flex-wrap items-center gap-3 mb-6 pb-6 border-b border-border">
      <!-- 画笔工具组 -->
      <div class="flex items-center gap-3 p-2 bg-surface rounded-xl">
        <span class="text-sm text-text-secondary whitespace-nowrap">画笔颜色:</span>
        <input 
          type="color" 
          bind:value={color} 
          class="w-10 h-10 border border-border rounded-lg cursor-pointer bg-transparent"
          aria-label="画笔颜色"
        >
        <div class="flex items-center gap-2">
          <span class="text-sm text-text-secondary whitespace-nowrap">大小:</span>
          <input 
            type="range" 
            bind:value={brushSize} 
            min="1" 
            max="50" 
            class="w-20 h-2 bg-surface rounded-lg appearance-none cursor-pointer accent-primary"
            aria-label="画笔大小"
          >
          <span class="text-sm text-text-secondary w-8 font-mono">{brushSize}</span>
        </div>
      </div>
      
      <!-- 编辑工具组 -->
      <div class="flex items-center gap-2">
        <button
          on:click={undoCanvas}
          disabled={!canUndo}
          class="btn-secondary"
          title="撤销 (Ctrl+Z)"
        >
          ↶ 撤销
        </button>
        <button
          on:click={redoCanvas}
          disabled={!canRedo}
          class="btn-secondary"
          title="重做 (Ctrl+Shift+Z)"
        >
          ↷ 重做
        </button>
        <button
          on:click={clearCanvas}
          class="btn-secondary"
          title="清空画布 (Delete)"
        >
          清空
        </button>
      </div>
      
      <!-- MultiControlNet配置切换按钮 -->
      <div class="flex items-center gap-2">
        <button
          on:click={() => showMultiControlNet = !showMultiControlNet}
          class="btn-secondary {multiControlNetConfig.length > 0 ? 'border-primary' : ''}"
          title="配置多个ControlNet"
        >
          🎮 MultiControlNet {multiControlNetConfig.length > 0 ? `(${multiControlNetConfig.length})` : ''}
        </button>
      </div>
      
      <!-- 连接控制组 -->
      <div class="flex items-center gap-2">
        <button
          on:click={connectToServer}
          class="btn-primary"
        >
          {isConnected ? '断开连接' : '连接服务器'}
        </button>
        {#if isConnected && userId}
          <div class="flex items-center gap-2 px-3 py-2 bg-surface rounded-xl border border-border">
            <span class="text-xs text-text-tertiary">User ID:</span>
            <input
              type="text"
              value={userId}
              readonly
              class="px-2 py-1 bg-transparent text-text-primary text-xs font-mono w-40 border-0 focus:ring-0"
            />
            <button
              on:click={copyUserId}
              class="btn-ghost text-xs px-2 py-1"
            >
              复制
            </button>
          </div>
        {/if}
        <button
          on:click={startSending}
          disabled={!isConnected || isSending}
          class="btn-success"
        >
          开始发送
        </button>
        <button
          on:click={stopSending}
          disabled={!isSending}
          class="btn-danger"
        >
          停止发送
        </button>
      </div>
      
      <!-- 状态指示器 -->
      <div class="ml-auto flex items-center gap-2 px-3 py-2 bg-surface rounded-xl">
        <div class="status-dot {isConnected ? 'status-dot-online' : 'status-dot-offline'}"></div>
        <span class="text-sm text-text-secondary">{connectionStatus}</span>
      </div>
      
      <!-- 功能切换按钮 -->
      <div class="flex items-center gap-2">
        <button
          on:click={() => showParams = !showParams}
          class="btn-secondary"
        >
          {showParams ? '隐藏参数' : '显示参数'}
        </button>
        <button
          on:click={() => showCLIPInterrogator = !showCLIPInterrogator}
          class="btn-secondary"
        >
          {showCLIPInterrogator ? '隐藏CLIP' : 'CLIP反推'}
        </button>
      </div>
    </div>

    <!-- 模型管理区域 - 始终显示 -->
    <div class="card-compact mb-6">
      <ModelManager />
    </div>

    {#if showParams && pipelineParams}
      <div class="card-compact mb-6">
        <h3 class="heading">生成参数配置</h3>
        <PipelineOptions {pipelineParams}></PipelineOptions>
      </div>
    {/if}
    
    <!-- MultiControlNet配置面板 -->
    {#if showMultiControlNet}
      <div class="card-compact mb-6">
        <h3 class="heading">🎮 多ControlNet控制</h3>
        <MultiControlNetPanel bind:controlnets={multiControlNetConfig} />
      </div>
    {/if}
    
    <!-- CLIP反推面板 -->
    {#if showCLIPInterrogator}
      <div class="card-compact mb-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="heading mb-0">🔍 CLIP Prompt反推</h3>
          <button
            on:click={() => showCLIPInterrogator = false}
            class="btn-ghost text-sm px-2 py-1"
            title="关闭CLIP面板"
          >
            ✕
          </button>
        </div>
        
        <!-- 图像选择按钮 -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
          <button
            on:click={analyzeCanvas}
            class="btn-primary flex items-center justify-center gap-2"
            title="分析当前画布内容"
          >
            <span>🎨</span>
            <span>分析画布图像</span>
          </button>
          <button
            on:click={analyzeViewerImage}
            disabled={!userId}
            class="btn-success flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            title={!userId ? '请先连接服务器' : '分析生成的结果图像'}
          >
            <span>🖼️</span>
            <span>分析生成结果</span>
          </button>
        </div>
        
        {#if !userId}
          <div class="bg-warning/20 border border-warning/30 text-warning p-3 rounded-xl text-sm mb-4">
            <p class="font-semibold mb-1">💡 提示</p>
            <p>要分析生成结果，请先点击"连接服务器"按钮建立连接。</p>
          </div>
        {/if}
        
        {#if clipImageUrl}
          <!-- 预览图像 -->
          <div class="mb-4 bg-surface/50 p-4 rounded-xl border border-border">
            <div class="flex items-center justify-between mb-2">
              <span class="label mb-0">预览图像</span>
              <button
                on:click={() => { clipImageUrl = ''; clipResult = null; clipError = ''; }}
                class="btn-ghost text-xs px-2 py-1"
                title="清除图像"
              >
                清除
              </button>
            </div>
            <div class="flex justify-center">
              <img
                src={clipImageUrl}
                alt="预览图像"
                class="max-w-full h-auto max-h-64 border border-border rounded-xl shadow-medium"
              />
            </div>
          </div>
          
          <!-- 模式选择 -->
          <div class="mb-4">
            <label for="clipMode" class="label">反推模式</label>
            <select
              id="clipMode"
              bind:value={clipMode}
              class="input"
              disabled={clipInterrogating}
            >
              <option value="fast">⚡ 快速模式 (Fast)</option>
              <option value="classic">🎯 经典模式 (Classic)</option>
              <option value="negative">🚫 负面Prompt (Negative)</option>
            </select>
            <div class="mt-2 p-3 bg-surface/50 rounded-lg border border-border">
              <p class="text-xs text-text-secondary">
                {#if clipMode === 'fast'}
                  <span class="font-semibold text-text-primary">⚡ 快速模式：</span>使用BLIP快速生成图像描述，然后通过CLIP进行优化，速度快但可能不够详细。
                {:else if clipMode === 'classic'}
                  <span class="font-semibold text-text-primary">🎯 经典模式：</span>生成更详细和准确的Prompt描述，但处理时间较长，适合需要精确描述的场景。
                {:else}
                  <span class="font-semibold text-text-primary">🚫 负面Prompt：</span>专门生成负面提示词，用于排除不想要的元素和特征。
                {/if}
              </p>
            </div>
          </div>
          
          <!-- 反推按钮 -->
          <button
            on:click={performCLIPInterrogation}
            disabled={clipInterrogating}
            class="btn-primary w-full mb-4 relative overflow-hidden disabled:opacity-70"
          >
            {#if clipInterrogating}
              <span class="flex items-center justify-center gap-2">
                <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>正在分析图像...</span>
              </span>
            {:else}
              <span>🚀 开始反推</span>
            {/if}
          </button>
        {/if}
        
        {#if clipError}
          <div class="bg-danger/20 border border-danger/30 text-danger p-4 rounded-xl text-sm mb-4">
            <div class="flex items-start gap-2">
              <span class="text-lg">⚠️</span>
              <div class="flex-1">
                <p class="font-semibold mb-1">反推失败</p>
                <p>{clipError}</p>
              </div>
              <button
                on:click={() => clipError = ''}
                class="btn-ghost text-xs px-2 py-1"
              >
                ✕
              </button>
            </div>
          </div>
        {/if}
        
        {#if clipResult}
          <!-- 结果显示 -->
          <div class="space-y-4 bg-surface/50 p-4 rounded-xl border border-border">
            <div class="flex items-center justify-between">
              <h4 class="text-sm font-semibold text-text-primary flex items-center gap-2">
                <span>✨</span>
                <span>反推结果</span>
              </h4>
              <span class="text-xs text-text-tertiary px-2 py-1 bg-surface rounded-lg border border-border">
                模式: {clipResult.mode === 'fast' ? '⚡ 快速' : clipResult.mode === 'classic' ? '🎯 经典' : '🚫 负面'}
              </span>
            </div>
            
            <!-- Prompt -->
            <div class="bg-white/5 p-3 rounded-lg border border-border">
              <div class="flex justify-between items-center mb-2">
                <span class="label mb-0 text-xs font-semibold">Prompt</span>
                <div class="flex gap-2">
                  <button
                    on:click={copyCLIPPrompt}
                    class="btn-ghost text-xs px-2 py-1 hover:bg-surface"
                    title="复制Prompt"
                  >
                    📋 复制
                  </button>
                  <button
                    on:click={applyCLIPPrompt}
                    class="btn-success text-xs px-2 py-1"
                    title="应用到画板参数"
                  >
                    ✓ 应用
                  </button>
                </div>
              </div>
              <textarea
                value={clipResult.prompt}
                readonly
                class="input-textarea font-mono text-sm bg-transparent resize-none"
                rows="4"
                aria-label="Prompt"
              ></textarea>
            </div>
            
            <!-- Negative Prompt -->
            <div class="bg-white/5 p-3 rounded-lg border border-border">
              <div class="flex justify-between items-center mb-2">
                <span class="label mb-0 text-xs font-semibold">Negative Prompt</span>
                <button
                  on:click={copyCLIPNegativePrompt}
                  class="btn-ghost text-xs px-2 py-1 hover:bg-surface"
                  title="复制Negative Prompt"
                >
                  📋 复制
                </button>
              </div>
              <textarea
                value={clipResult.negative_prompt}
                readonly
                class="input-textarea font-mono text-sm bg-transparent resize-none"
                rows="3"
                aria-label="Negative Prompt"
              ></textarea>
            </div>
            
            <!-- 风格标签 -->
            {#if clipResult.flavors && clipResult.flavors.length > 0}
              <div class="bg-white/5 p-3 rounded-lg border border-border">
                <span class="label mb-2 text-xs font-semibold">🎨 风格标签</span>
                <div class="flex flex-wrap gap-2">
                  {#each clipResult.flavors as flavor}
                    <span class="px-3 py-1 bg-primary/10 border border-primary/30 text-primary rounded-full text-xs font-medium">
                      {flavor}
                    </span>
                  {/each}
                </div>
              </div>
            {/if}
            
            <!-- 操作提示 -->
            <div class="text-xs text-text-tertiary p-3 bg-surface/50 rounded-lg border border-border">
              <p class="font-semibold mb-1">💡 使用提示：</p>
              <ul class="list-disc list-inside space-y-1">
                <li>点击"应用"按钮将Prompt和Negative Prompt应用到画板参数</li>
                <li>点击"复制"按钮可以单独复制Prompt或Negative Prompt</li>
                <li>风格标签显示了图像的主要风格特征</li>
              </ul>
            </div>
          </div>
        {/if}
      </div>
    {/if}

    <!-- 画布和生成结果并排显示 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 my-6">
      <!-- 左侧：画布 -->
      <div class="card-compact">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-text-primary">✏️ 绘画区域</h3>
          <div class="flex items-center gap-2">
            <span class="text-xs text-text-tertiary">512 × 512</span>
          </div>
        </div>
        <canvas
          bind:this={canvas}
          width="512"
          height="512"
          class="border-2 border-primary rounded-2xl cursor-crosshair bg-white shadow-large w-full"
          style="max-width: 100%; height: auto;"
          on:mousedown={startDrawing}
          on:mousemove={draw}
          on:mouseup={stopDrawing}
          on:mouseleave={stopDrawing}
          on:touchstart={startDrawing}
          on:touchmove={draw}
          on:touchend={stopDrawing}
        ></canvas>
      </div>
      
      <!-- 右侧：生成结果 -->
      <div class="card-compact">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-text-primary">🎨 AI 生成结果</h3>
          {#if isSending}
            <div class="flex items-center gap-2">
              <div class="animate-pulse w-2 h-2 bg-success rounded-full"></div>
              <span class="text-xs text-success">实时生成中...</span>
            </div>
          {/if}
        </div>
        {#if userId}
          <ImagePlayer />
        {:else}
          <div class="flex flex-col items-center justify-center min-h-[512px] bg-surface-elevated rounded-lg border border-border p-4">
            <div class="text-6xl opacity-50 mb-4">🖼️</div>
            <p class="text-lg font-medium text-text-secondary mb-2">等待连接</p>
            <p class="text-sm text-text-tertiary text-center max-w-xs">
              点击"连接服务器"按钮建立连接，然后点击"开始发送"开始实时生成
            </p>
          </div>
        {/if}
      </div>
    </div>

    <!-- 提示信息 -->
    <div class="mt-6 text-xs text-text-tertiary text-center space-y-1">
      <p>💡 提示: 在左侧画布绘制，右侧实时显示 AI 生成结果</p>
      <p>🎨 操作: 连接服务器 → 开始发送 → 在画布上绘制 → 实时查看生成效果</p>
    </div>
  </div>
  
  <!-- 快捷键帮助面板 -->
  <KeyboardShortcuts bind:show={showShortcuts} />
  
  <!-- 快捷键提示按钮 -->
  <div class="fixed bottom-6 right-6">
    <button
      on:click={() => showShortcuts = true}
      class="btn-ghost shadow-medium"
      title="快捷键帮助 (Shift+?)"
    >
      ⌨️ 快捷键
    </button>
  </div>
</main>

