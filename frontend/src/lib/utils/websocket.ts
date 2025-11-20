/**
 * WebSocketManager - WebSocket连接管理器
 * 
 * 功能：
 * - 自动重连机制
 * - 重连次数限制
 * - 指数退避策略
 * - 连接状态管理
 * - 消息队列（可选）
 */

export interface WebSocketConfig {
  url: string;
  maxReconnectAttempts?: number;
  reconnectDelay?: number;
  maxReconnectDelay?: number;
  reconnectDecayRate?: number;
  connectionTimeout?: number; // 连接超时时间（毫秒），默认10秒
}

export interface WebSocketCallbacks {
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  onMessage?: (event: MessageEvent) => void;
  onReconnecting?: (attempt: number, maxAttempts: number) => void;
  onReconnectFailed?: () => void;
}

export enum ConnectionStatus {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  FAILED = 'failed'
}

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private callbacks: WebSocketCallbacks;
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private connectionTimeoutTimer: ReturnType<typeof setTimeout> | null = null;
  private status: ConnectionStatus = ConnectionStatus.DISCONNECTED;
  private shouldReconnect = true;
  private messageQueue: any[] = [];
  private isManualClose = false;

  constructor(config: WebSocketConfig, callbacks: WebSocketCallbacks = {}) {
    this.config = {
      url: config.url,
      maxReconnectAttempts: config.maxReconnectAttempts ?? 5,
      reconnectDelay: config.reconnectDelay ?? 1000,
      maxReconnectDelay: config.maxReconnectDelay ?? 30000,
      reconnectDecayRate: config.reconnectDecayRate ?? 1.5,
      connectionTimeout: config.connectionTimeout ?? 10000 // 默认10秒超时
    };
    this.callbacks = callbacks;
  }

  /**
   * 连接到WebSocket服务器
   */
  connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('WebSocket已连接，无需重复连接');
      return;
    }

    if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
      console.log('WebSocket正在连接中...');
      return;
    }

    this.isManualClose = false;
    this.shouldReconnect = true;
    this.status = this.reconnectAttempts > 0 
      ? ConnectionStatus.RECONNECTING 
      : ConnectionStatus.CONNECTING;

    try {
      console.log(`🔌 连接WebSocket: ${this.config.url} (尝试 ${this.reconnectAttempts + 1}/${this.config.maxReconnectAttempts})`);
      
      // 清除之前的连接超时定时器
      if (this.connectionTimeoutTimer) {
        clearTimeout(this.connectionTimeoutTimer);
        this.connectionTimeoutTimer = null;
      }
      
      this.ws = new WebSocket(this.config.url);

      // 设置连接超时定时器
      this.connectionTimeoutTimer = setTimeout(() => {
        if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
          console.error(`⏱️ WebSocket连接超时 (${this.config.connectionTimeout}ms)`);
          this.ws.close();
          this.ws = null;
          
          // 清除超时定时器
          if (this.connectionTimeoutTimer) {
            clearTimeout(this.connectionTimeoutTimer);
            this.connectionTimeoutTimer = null;
          }
          
          // 触发错误回调
          if (this.callbacks.onError) {
            // 创建一个自定义错误事件，标记为超时
            const timeoutError = new Event('timeout') as any;
            timeoutError.isTimeout = true;
            this.callbacks.onError(timeoutError);
          }
          
          // 如果不是手动关闭，尝试重连
          if (!this.isManualClose && this.shouldReconnect) {
            this.scheduleReconnect();
          } else {
            this.status = ConnectionStatus.FAILED;
          }
        }
      }, this.config.connectionTimeout);

      this.ws.onopen = () => {
        console.log('✅ WebSocket连接成功');
        
        // 清除连接超时定时器
        if (this.connectionTimeoutTimer) {
          clearTimeout(this.connectionTimeoutTimer);
          this.connectionTimeoutTimer = null;
        }
        
        this.status = ConnectionStatus.CONNECTED;
        this.reconnectAttempts = 0;
        
        // 发送队列中的消息
        this.flushMessageQueue();
        
        if (this.callbacks.onOpen) {
          this.callbacks.onOpen();
        }
      };

      this.ws.onerror = (error) => {
        console.error('❌ WebSocket错误:', error);
        
        // 清除连接超时定时器
        if (this.connectionTimeoutTimer) {
          clearTimeout(this.connectionTimeoutTimer);
          this.connectionTimeoutTimer = null;
        }
        
        if (this.callbacks.onError) {
          this.callbacks.onError(error);
        }
      };

      this.ws.onclose = (event) => {
        console.log(`🔌 WebSocket连接关闭 (code: ${event.code}, reason: ${event.reason})`);
        
        // 清除连接超时定时器
        if (this.connectionTimeoutTimer) {
          clearTimeout(this.connectionTimeoutTimer);
          this.connectionTimeoutTimer = null;
        }
        
        this.ws = null;
        
        if (this.callbacks.onClose) {
          this.callbacks.onClose();
        }

        // 如果不是手动关闭且应该重连，则尝试重连
        if (!this.isManualClose && this.shouldReconnect) {
          this.scheduleReconnect();
        } else {
          this.status = ConnectionStatus.DISCONNECTED;
        }
      };

      this.ws.onmessage = (event) => {
        if (this.callbacks.onMessage) {
          this.callbacks.onMessage(event);
        }
      };

    } catch (error) {
      console.error('❌ WebSocket连接失败:', error);
      
      // 清除连接超时定时器
      if (this.connectionTimeoutTimer) {
        clearTimeout(this.connectionTimeoutTimer);
        this.connectionTimeoutTimer = null;
      }
      
      this.status = ConnectionStatus.FAILED;
      
      if (this.callbacks.onError) {
        this.callbacks.onError(error as Event);
      }
      
      if (this.shouldReconnect) {
        this.scheduleReconnect();
      }
    }
  }

  /**
   * 调度重连 - 使用指数退避策略
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.error(`❌ 达到最大重连次数 (${this.config.maxReconnectAttempts})，停止重连`);
      this.status = ConnectionStatus.FAILED;
      this.shouldReconnect = false;
      
      if (this.callbacks.onReconnectFailed) {
        this.callbacks.onReconnectFailed();
      }
      return;
    }

    // 计算重连延迟 - 指数退避
    const delay = Math.min(
      this.config.reconnectDelay * Math.pow(this.config.reconnectDecayRate, this.reconnectAttempts),
      this.config.maxReconnectDelay
    );

    this.reconnectAttempts++;
    this.status = ConnectionStatus.RECONNECTING;

    console.log(`🔄 将在 ${(delay / 1000).toFixed(1)}秒 后重连 (尝试 ${this.reconnectAttempts}/${this.config.maxReconnectAttempts})`);

    if (this.callbacks.onReconnecting) {
      this.callbacks.onReconnecting(this.reconnectAttempts, this.config.maxReconnectAttempts);
    }

    // 清除之前的定时器
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    // 设置新的重连定时器
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }

  /**
   * 手动断开连接
   */
  disconnect(): void {
    console.log('🔌 手动断开WebSocket连接');
    
    this.isManualClose = true;
    this.shouldReconnect = false;
    
    // 清除重连定时器
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    // 清除连接超时定时器
    if (this.connectionTimeoutTimer) {
      clearTimeout(this.connectionTimeoutTimer);
      this.connectionTimeoutTimer = null;
    }

    // 关闭WebSocket连接
    if (this.ws) {
      if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
        this.ws.close();
      }
      this.ws = null;
    }

    this.status = ConnectionStatus.DISCONNECTED;
    this.reconnectAttempts = 0;
    this.messageQueue = [];
  }

  /**
   * 发送消息
   * 如果连接未建立，消息将被加入队列
   */
  send(data: string | ArrayBuffer | Blob): boolean {
    if (!this.ws) {
      console.warn('⚠️ WebSocket未连接，消息已加入队列');
      this.messageQueue.push(data);
      return false;
    }

    if (this.ws.readyState !== WebSocket.OPEN) {
      console.warn('⚠️ WebSocket未就绪，消息已加入队列');
      this.messageQueue.push(data);
      return false;
    }

    try {
      this.ws.send(data);
      return true;
    } catch (error) {
      console.error('❌ 发送消息失败:', error);
      this.messageQueue.push(data);
      return false;
    }
  }

  /**
   * 发送队列中的消息
   */
  private flushMessageQueue(): void {
    if (this.messageQueue.length === 0) {
      return;
    }

    console.log(`📤 发送队列中的 ${this.messageQueue.length} 条消息`);

    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message) {
        this.send(message);
      }
    }
  }

  /**
   * 获取当前连接状态
   */
  getStatus(): ConnectionStatus {
    return this.status;
  }

  /**
   * 检查是否已连接
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * 获取WebSocket实例（用于特殊情况）
   */
  getWebSocket(): WebSocket | null {
    return this.ws;
  }

  /**
   * 重置重连计数器（用于手动重试）
   */
  resetReconnectAttempts(): void {
    this.reconnectAttempts = 0;
    this.shouldReconnect = true;
  }

  /**
   * 更新配置
   */
  updateConfig(config: Partial<WebSocketConfig>): void {
    this.config = {
      ...this.config,
      ...config
    };
  }

  /**
   * 清理资源
   */
  destroy(): void {
    // 清除所有定时器
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.connectionTimeoutTimer) {
      clearTimeout(this.connectionTimeoutTimer);
      this.connectionTimeoutTimer = null;
    }
    
    this.disconnect();
    this.callbacks = {};
  }
}
