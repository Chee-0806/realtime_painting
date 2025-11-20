import { writable } from 'svelte/store';

export enum LCMLiveStatus {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RUNNING = 'running',
  TIMEOUT = 'timeout',
  ERROR = 'error',
}

export const lcmLiveStatus = writable<LCMLiveStatus>(LCMLiveStatus.DISCONNECTED);
export const userIdStore = writable<string | null>(null);

type StreamDataGetter = () => [Record<string, any>, Blob | null] | [Record<string, any>];

let ws: WebSocket | null = null;
let userId: string | null = null;
let streamDataGetter: StreamDataGetter | null = null;
let isRunning = false;
let isSendingFrame = false; // 防止并发发送帧
let sendInterval: number | null = null; // 定时发送帧的定时器

// 导出 userId 供 ImagePlayer 使用（使用 store）
export function getUserId(): string | null {
  let value: string | null = null;
  userIdStore.subscribe((v) => {
    value = v;
  })();
  console.log('getUserId() 被调用，返回:', value);
  return value;
}

function generateUserId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

// 高性能方案：使用二进制 WebSocket 传输（避免 Base64 编码）
async function sendFrame(): Promise<void> {
  // 防止并发发送
  if (isSendingFrame) {
    console.warn('sendFrame: 正在发送中，跳过本次请求');
    return;
  }

  if (!ws || ws.readyState !== WebSocket.OPEN || !streamDataGetter) {
    console.warn('sendFrame: WebSocket 未就绪或 streamDataGetter 未设置', {
      ws: !!ws,
      readyState: ws?.readyState,
      hasGetter: !!streamDataGetter
    });
    return;
  }

  isSendingFrame = true;
  const startTime = performance.now();
  
  try {
    const data = streamDataGetter();
    const params = data[0];
    const imageBlob = data.length > 1 ? data[1] : null;
    
    console.log('sendFrame: 准备发送数据', {
      hasParams: !!params,
      hasImage: !!imageBlob,
      paramsKeys: params ? Object.keys(params) : []
    });

    // 清理参数，确保所有值都是有效的 JSON 类型
    const cleanParams: Record<string, any> = {};
    for (const [key, value] of Object.entries(params)) {
      // 过滤掉 undefined 值
      if (value !== undefined) {
        // 确保数字不是 NaN 或 Infinity
        if (typeof value === 'number') {
          if (isNaN(value) || !isFinite(value)) {
            console.warn(`参数 ${key} 的值 ${value} 不是有效数字，跳过`);
            continue;
          }
        }
        cleanParams[key] = value;
      }
    }

    // 高性能方案：使用二进制传输协议
    // 格式：[JSON长度(4字节)] + [JSON数据] + [图像数据]
    if (imageBlob) {
      const encodeStart = performance.now();
      
      // 1. 准备 JSON 数据
      const jsonStr = JSON.stringify({
        status: 'next_frame',
        params: cleanParams
      });
      const jsonBytes = new TextEncoder().encode(jsonStr);
      const jsonLength = jsonBytes.length;
      
      // 2. 准备图像数据
      const imageBuffer = await imageBlob.arrayBuffer();
      const imageBytes = new Uint8Array(imageBuffer);
      
      // 3. 构建二进制消息：[4字节长度] + [JSON] + [图像]
      const totalLength = 4 + jsonLength + imageBytes.length;
      const binaryMessage = new Uint8Array(totalLength);
      
      // 写入 JSON 长度（大端序）
      const view = new DataView(binaryMessage.buffer);
      view.setUint32(0, jsonLength, false);
      
      // 写入 JSON 数据
      binaryMessage.set(jsonBytes, 4);
      
      // 写入图像数据
      binaryMessage.set(imageBytes, 4 + jsonLength);
      
      // 4. 发送二进制消息
      ws.send(binaryMessage.buffer);
      
      const encodeTime = performance.now() - encodeStart;
      console.log(`二进制打包耗时: ${encodeTime.toFixed(2)}ms, 总大小: ${(totalLength / 1024).toFixed(2)}KB (JSON: ${(jsonLength / 1024).toFixed(2)}KB, 图像: ${(imageBytes.length / 1024).toFixed(2)}KB)`);
    } else {
      // 没有图像，只发送 JSON
      const message = {
        status: 'next_frame',
        params: cleanParams
      };
      ws.send(JSON.stringify(message));
    }
    
    const totalTime = performance.now() - startTime;
    console.log('sendFrame: 数据发送完成', {
      sentParams: true,
      sentImage: !!imageBlob,
      totalTime: totalTime.toFixed(2) + 'ms',
      method: imageBlob ? 'binary' : 'json'
    });
  } catch (error) {
    console.error('发送帧失败:', error);
    throw error;
  } finally {
    isSendingFrame = false;
  }
}

export const lcmLiveActions = {
  async start(getStreamData: StreamDataGetter): Promise<void> {
    if (isRunning) {
      return;
    }

    streamDataGetter = getStreamData;
    userId = generateUserId();
    userIdStore.set(userId); // 更新 store
    console.log('设置 userId:', userId);
    isRunning = true;
    lcmLiveStatus.set(LCMLiveStatus.CONNECTING);

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/api/ws/${userId}`;

      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        lcmLiveStatus.set(LCMLiveStatus.CONNECTED);
        console.log('WebSocket连接成功');
      };

      ws.onmessage = async (event) => {
        try {
          if (typeof event.data === 'string') {
            const message = JSON.parse(event.data);
            console.log('收到WebSocket消息:', message);
            
            if (message.status === 'send_frame') {
              // 后端请求发送帧
              console.log('收到 send_frame 请求，准备发送数据');
              // 使用 setTimeout 确保异步执行，避免阻塞消息处理
              setTimeout(async () => {
                try {
                  await sendFrame();
                  console.log('数据已发送');
                  lcmLiveStatus.set(LCMLiveStatus.RUNNING);
                } catch (error) {
                  console.error('发送帧时出错:', error);
                }
              }, 0);
            } else if (message.status === 'connected' || message.status === 'wait') {
              // 连接成功或等待消息，不做处理
              console.log('WebSocket状态:', message.status);
            }
          }
        } catch (error) {
          console.error('处理WebSocket消息失败:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
        lcmLiveStatus.set(LCMLiveStatus.ERROR);
        isRunning = false;
      };

      ws.onclose = () => {
        lcmLiveStatus.set(LCMLiveStatus.DISCONNECTED);
        isRunning = false;
        ws = null;
        userId = null;
        userIdStore.set(null); // 清除 store
      };
    } catch (error) {
      lcmLiveStatus.set(LCMLiveStatus.ERROR);
      isRunning = false;
      throw error;
    }
  },

  stop(): void {
    if (ws) {
      ws.close();
      ws = null;
    }
    userId = null;
    userIdStore.set(null); // 清除 store
    streamDataGetter = null;
    isRunning = false;
    lcmLiveStatus.set(LCMLiveStatus.DISCONNECTED);
  },
};

