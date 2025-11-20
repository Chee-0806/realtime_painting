/**
 * WebSocketManager 使用示例
 * 
 * 本文件展示了如何在不同场景下使用 WebSocketManager
 */

import { WebSocketManager, ConnectionStatus } from './websocket';

// ============================================
// 示例 1: 基本使用
// ============================================

function example1_BasicUsage() {
  // 创建 WebSocketManager 实例
  const wsManager = new WebSocketManager(
    {
      url: 'ws://localhost:8000/api/ws/user123',
      maxReconnectAttempts: 5,
      reconnectDelay: 1000
    },
    {
      onOpen: () => {
        console.log('连接成功！');
      },
      onClose: () => {
        console.log('连接关闭');
      },
      onError: (error) => {
        console.error('连接错误:', error);
      },
      onMessage: (event) => {
        console.log('收到消息:', event.data);
      }
    }
  );

  // 连接到服务器
  wsManager.connect();

  // 发送消息
  wsManager.send(JSON.stringify({ type: 'hello', data: 'world' }));

  // 断开连接
  wsManager.disconnect();

  // 清理资源
  wsManager.destroy();
}

// ============================================
// 示例 2: 在 Svelte 组件中使用
// ============================================

function example2_SvelteComponent() {
  /*
  <script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { WebSocketManager, ConnectionStatus } from '$lib/utils/websocket';
    
    let wsManager: WebSocketManager | null = null;
    let connectionStatus = '未连接';
    let isConnected = false;
    
    function connect() {
      const userId = generateUserId();
      const wsUrl = `ws://localhost:8000/api/ws/${userId}`;
      
      wsManager = new WebSocketManager(
        { url: wsUrl },
        {
          onOpen: () => {
            connectionStatus = '已连接';
            isConnected = true;
          },
          onClose: () => {
            connectionStatus = '未连接';
            isConnected = false;
          },
          onMessage: (event) => {
            handleMessage(event.data);
          },
          onReconnecting: (attempt, maxAttempts) => {
            connectionStatus = `重连中 (${attempt}/${maxAttempts})`;
          },
          onReconnectFailed: () => {
            connectionStatus = '连接失败';
            alert('无法连接到服务器，请刷新页面重试');
          }
        }
      );
      
      wsManager.connect();
    }
    
    function disconnect() {
      if (wsManager) {
        wsManager.disconnect();
        wsManager = null;
      }
    }
    
    function sendMessage(data: any) {
      if (wsManager && wsManager.isConnected()) {
        wsManager.send(JSON.stringify(data));
      } else {
        console.warn('未连接，消息已加入队列');
        wsManager?.send(JSON.stringify(data));
      }
    }
    
    onDestroy(() => {
      if (wsManager) {
        wsManager.destroy();
      }
    });
  </script>
  
  <button on:click={connect}>连接</button>
  <button on:click={disconnect}>断开</button>
  <p>状态: {connectionStatus}</p>
  */
}

// ============================================
// 示例 3: 自定义重连策略
// ============================================

function example3_CustomReconnectStrategy() {
  const wsManager = new WebSocketManager(
    {
      url: 'ws://localhost:8000/api/ws/user123',
      maxReconnectAttempts: 10,        // 最多重连10次
      reconnectDelay: 500,              // 初始延迟500ms
      maxReconnectDelay: 60000,         // 最大延迟60秒
      reconnectDecayRate: 2.0           // 每次延迟翻倍
    },
    {
      onReconnecting: (attempt, maxAttempts) => {
        console.log(`正在重连... (${attempt}/${maxAttempts})`);
        
        // 可以在这里添加自定义逻辑
        if (attempt === 3) {
          console.log('已尝试3次，建议检查网络连接');
        }
      },
      onReconnectFailed: () => {
        console.error('重连失败，请手动刷新页面');
        // 可以显示用户友好的错误提示
      }
    }
  );

  wsManager.connect();
}

// ============================================
// 示例 4: 处理不同类型的消息
// ============================================

function example4_MessageHandling() {
  const wsManager = new WebSocketManager(
    {
      url: 'ws://localhost:8000/api/ws/user123'
    },
    {
      onMessage: (event) => {
        // 处理文本消息
        if (typeof event.data === 'string') {
          try {
            const data = JSON.parse(event.data);
            handleJsonMessage(data);
          } catch (e) {
            handleTextMessage(event.data);
          }
        }
        // 处理二进制消息
        else if (event.data instanceof Blob) {
          handleBlobMessage(event.data);
        }
        else if (event.data instanceof ArrayBuffer) {
          handleArrayBufferMessage(event.data);
        }
      }
    }
  );

  function handleJsonMessage(data: any) {
    switch (data.type) {
      case 'status':
        console.log('状态更新:', data.status);
        break;
      case 'result':
        console.log('收到结果:', data.result);
        break;
      default:
        console.log('未知消息类型:', data);
    }
  }

  function handleTextMessage(text: string) {
    console.log('收到文本消息:', text);
  }

  function handleBlobMessage(blob: Blob) {
    console.log('收到Blob消息，大小:', blob.size);
    // 可以转换为其他格式
    blob.arrayBuffer().then(buffer => {
      console.log('转换为ArrayBuffer:', buffer);
    });
  }

  function handleArrayBufferMessage(buffer: ArrayBuffer) {
    console.log('收到ArrayBuffer消息，大小:', buffer.byteLength);
  }

  wsManager.connect();
}

// ============================================
// 示例 5: 发送不同类型的数据
// ============================================

function example5_SendingDifferentTypes() {
  const wsManager = new WebSocketManager(
    { url: 'ws://localhost:8000/api/ws/user123' },
    {
      onOpen: () => {
        // 发送JSON数据
        wsManager.send(JSON.stringify({
          type: 'command',
          action: 'start'
        }));

        // 发送文本数据
        wsManager.send('Hello, Server!');

        // 发送二进制数据（ArrayBuffer）
        const buffer = new ArrayBuffer(8);
        const view = new Uint8Array(buffer);
        view[0] = 1;
        view[1] = 2;
        wsManager.send(buffer);

        // 发送Blob数据
        const blob = new Blob(['Hello'], { type: 'text/plain' });
        wsManager.send(blob);
      }
    }
  );

  wsManager.connect();
}

// ============================================
// 示例 6: 状态监控
// ============================================

function example6_StatusMonitoring() {
  const wsManager = new WebSocketManager(
    { url: 'ws://localhost:8000/api/ws/user123' },
    {}
  );

  wsManager.connect();

  // 定期检查连接状态
  const statusInterval = setInterval(() => {
    const status = wsManager.getStatus();
    const isConnected = wsManager.isConnected();
    
    console.log('当前状态:', status);
    console.log('是否已连接:', isConnected);
    
    switch (status) {
      case ConnectionStatus.CONNECTED:
        console.log('✅ 连接正常');
        break;
      case ConnectionStatus.RECONNECTING:
        console.log('🔄 正在重连...');
        break;
      case ConnectionStatus.FAILED:
        console.log('❌ 连接失败');
        clearInterval(statusInterval);
        break;
    }
  }, 1000);

  // 清理
  setTimeout(() => {
    clearInterval(statusInterval);
    wsManager.destroy();
  }, 10000);
}

// ============================================
// 示例 7: 动态更新配置
// ============================================

function example7_DynamicConfiguration() {
  const wsManager = new WebSocketManager(
    {
      url: 'ws://localhost:8000/api/ws/user123',
      maxReconnectAttempts: 5
    },
    {}
  );

  wsManager.connect();

  // 稍后更新配置
  setTimeout(() => {
    wsManager.updateConfig({
      maxReconnectAttempts: 10,
      reconnectDelay: 2000
    });
    console.log('配置已更新');
  }, 5000);
}

// ============================================
// 示例 8: 手动重置重连计数器
// ============================================

function example8_ManualReconnect() {
  const wsManager = new WebSocketManager(
    {
      url: 'ws://localhost:8000/api/ws/user123',
      maxReconnectAttempts: 3
    },
    {
      onReconnectFailed: () => {
        console.log('重连失败，但用户可以手动重试');
        
        // 显示重试按钮
        showRetryButton(() => {
          // 重置重连计数器
          wsManager.resetReconnectAttempts();
          // 重新连接
          wsManager.connect();
        });
      }
    }
  );

  function showRetryButton(onRetry: () => void) {
    // 在UI中显示重试按钮
    console.log('显示重试按钮');
    // 用户点击后调用 onRetry()
  }

  wsManager.connect();
}

// ============================================
// 示例 9: 与错误处理系统集成
// ============================================

function example9_ErrorHandling() {
  // 假设有一个全局错误处理函数
  function setError(error: {
    type: string;
    message: string;
    details: string;
    recoverable: boolean;
    suggestions: string[];
  }) {
    console.error('错误:', error);
    // 显示错误提示给用户
  }

  const wsManager = new WebSocketManager(
    { url: 'ws://localhost:8000/api/ws/user123' },
    {
      onError: (error) => {
        setError({
          type: 'WEBSOCKET',
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
      onReconnecting: (attempt, maxAttempts) => {
        setError({
          type: 'WEBSOCKET',
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
        setError({
          type: 'WEBSOCKET',
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

  wsManager.connect();
}

// ============================================
// 示例 10: 完整的实时绘画应用
// ============================================

function example10_RealtimeDrawing() {
  /*
  这是一个完整的实时绘画应用示例，展示了如何：
  1. 连接到WebSocket服务器
  2. 实时发送画布数据
  3. 处理断线重连
  4. 优雅地清理资源
  
  <script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { WebSocketManager } from '$lib/utils/websocket';
    
    let canvas: HTMLCanvasElement;
    let ctx: CanvasRenderingContext2D | null = null;
    let wsManager: WebSocketManager | null = null;
    let isDrawing = false;
    let isSending = false;
    
    function connectToServer() {
      const userId = crypto.randomUUID();
      const wsUrl = `ws://localhost:8000/api/ws/${userId}`;
      
      wsManager = new WebSocketManager(
        {
          url: wsUrl,
          maxReconnectAttempts: 5,
          reconnectDelay: 1000
        },
        {
          onOpen: () => {
            console.log('✅ 连接成功');
            // 连接成功后自动开始发送
            startSending();
          },
          onClose: () => {
            console.log('🔌 连接关闭');
            if (isSending) {
              stopSending();
            }
          },
          onMessage: (event) => {
            // 处理服务器消息
            try {
              const data = JSON.parse(event.data);
              if (data.status === 'send_frame') {
                sendFrame();
              }
            } catch (e) {
              console.error('解析消息失败:', e);
            }
          },
          onReconnecting: (attempt, maxAttempts) => {
            console.log(`🔄 重连中 (${attempt}/${maxAttempts})`);
          }
        }
      );
      
      wsManager.connect();
    }
    
    function startSending() {
      if (!wsManager || !wsManager.isConnected()) {
        console.warn('未连接到服务器');
        return;
      }
      isSending = true;
      sendFrame();
    }
    
    function stopSending() {
      isSending = false;
    }
    
    function sendFrame() {
      if (!canvas || !wsManager || !isSending) return;
      
      canvas.toBlob((blob) => {
        if (blob && wsManager && wsManager.isConnected()) {
          // 发送帧数据
          wsManager.send(JSON.stringify({ status: 'next_frame' }));
          wsManager.send(JSON.stringify({ prompt: 'a beautiful painting' }));
          blob.arrayBuffer().then(buffer => {
            wsManager.send(buffer);
          });
        }
      }, 'image/webp', 0.8);
    }
    
    function draw(e: MouseEvent) {
      if (!isDrawing || !ctx) return;
      
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      ctx.lineTo(x, y);
      ctx.stroke();
      
      // 绘画时触发发送
      if (isSending) {
        sendFrame();
      }
    }
    
    onMount(() => {
      if (canvas) {
        ctx = canvas.getContext('2d');
      }
    });
    
    onDestroy(() => {
      if (wsManager) {
        wsManager.destroy();
      }
    });
  </script>
  
  <canvas
    bind:this={canvas}
    width="512"
    height="512"
    on:mousedown={() => isDrawing = true}
    on:mousemove={draw}
    on:mouseup={() => isDrawing = false}
  />
  <button on:click={connectToServer}>连接服务器</button>
  */
}

// 导出示例函数（仅用于文档目的）
export {
  example1_BasicUsage,
  example2_SvelteComponent,
  example3_CustomReconnectStrategy,
  example4_MessageHandling,
  example5_SendingDifferentTypes,
  example6_StatusMonitoring,
  example7_DynamicConfiguration,
  example8_ManualReconnect,
  example9_ErrorHandling,
  example10_RealtimeDrawing
};
