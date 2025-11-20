<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { mediaStreamActions } from '$lib/mediaStream';
  
  export let width: number = 512;
  export let height: number = 512;
  
  let videoElement: HTMLVideoElement;
  let stream: MediaStream | null = null;
  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D | null = null;
  let animationFrameId: number | null = null;
  let isActive = false;
  let errorMessage: string = '';
  let isLoading = false; // 初始状态不加载，等待用户点击

  $: if (canvas && !ctx) {
    ctx = canvas.getContext('2d');
    // 如果已经有 stream，立即开始捕获
    if (stream && videoElement && videoElement.readyState >= 1 && !isActive) {
      isActive = true;
      startCapture();
      isLoading = false;
    }
  }
  
  // 当 videoElement 绑定后，如果已经有 stream，立即设置
  $: if (videoElement && stream && !videoElement.srcObject) {
    videoElement.srcObject = stream;
    videoElement.play().then(() => {
      if (videoElement.readyState >= 1) {
        if (canvas && !ctx) {
          ctx = canvas.getContext('2d');
        }
        isActive = true;
        startCapture();
        isLoading = false;
      }
    });
  }

  async function initializeCamera() {
    isLoading = true;
    errorMessage = '';
    
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('浏览器不支持摄像头访问');
      }
      
      stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: width },
          height: { ideal: height },
        },
      });
      
      // stream 获取成功，先更新状态
      isLoading = false;
      
      const setupVideo = () => {
        if (!videoElement || !stream) return false;
        
        videoElement.srcObject = stream;
        videoElement.play().then(() => {
          const checkReady = () => {
            if (videoElement.readyState >= 1) { // HAVE_METADATA
              if (canvas && !ctx) {
                ctx = canvas.getContext('2d');
              }
              if (ctx && canvas && videoElement) {
                isActive = true;
                startCapture();
              }
              return true;
            }
            return false;
          };
          
          // 立即检查
          if (!checkReady()) {
            // 等待 loadedmetadata 事件
            videoElement.addEventListener('loadedmetadata', checkReady, { once: true });
            
            // 超时保护
            setTimeout(() => {
              if (!isActive && stream) {
                checkReady();
              }
            }, 1000);
          }
        }).catch((err) => {
          console.error('播放视频失败:', err);
        });
        
        return true;
      };
      
      // 如果 videoElement 已经绑定，立即设置
      if (!setupVideo()) {
        // 如果还没有绑定，等待绑定
        const checkInterval = setInterval(() => {
          if (setupVideo()) {
            clearInterval(checkInterval);
          }
        }, 50);
        
        // 最多等待 1 秒
        setTimeout(() => {
          clearInterval(checkInterval);
        }, 1000);
      }
    } catch (error) {
      console.error('无法访问摄像头:', error);
      isLoading = false;
      if (error instanceof Error) {
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
          errorMessage = '摄像头权限被拒绝，请在浏览器设置中允许访问摄像头';
        } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
          errorMessage = '未找到摄像头设备';
        } else {
          errorMessage = `无法访问摄像头: ${error.message}`;
        }
      } else {
        errorMessage = '无法访问摄像头';
      }
    }
  }

  // 不在 onMount 时自动启动，让用户手动点击按钮
  // onMount(() => {
  //   initializeCamera();
  // });

  onDestroy(() => {
    stopCapture();
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
  });

  function startCapture() {
    if (!canvas || !ctx || !videoElement) return;
    
    const captureFrame = () => {
      if (!isActive || !videoElement || videoElement.readyState !== videoElement.HAVE_ENOUGH_DATA) {
        animationFrameId = requestAnimationFrame(captureFrame);
        return;
      }

      ctx?.drawImage(videoElement, 0, 0, width, height);
      
      canvas.toBlob((blob) => {
        if (blob) {
          mediaStreamActions.updateFrame(blob);
        }
      }, 'image/png');
      
      animationFrameId = requestAnimationFrame(captureFrame);
    };
    
    captureFrame();
  }

  function stopCapture() {
    isActive = false;
    if (animationFrameId !== null) {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }
  }
</script>

<div class="flex flex-col items-center gap-4 w-full">
  <video
    bind:this={videoElement}
    width={width}
    height={height}
    autoplay
    playsinline
    muted
    class="rounded-lg bg-surface-elevated border border-border"
    style="display: none;"
  ></video>
  
  {#if isLoading}
    <div class="flex flex-col items-center justify-center min-h-[200px] w-full bg-surface-elevated rounded-lg border border-border p-4">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-2"></div>
      <p class="text-sm text-text-secondary">正在请求摄像头权限...</p>
      <p class="text-xs text-text-tertiary mt-2">请允许浏览器访问您的摄像头</p>
    </div>
  {:else if errorMessage}
    <div class="flex flex-col items-center justify-center min-h-[200px] w-full bg-surface-elevated rounded-lg border border-border p-4">
      <div class="text-4xl mb-2">📷</div>
      <p class="text-sm text-text-secondary text-center mb-4">{errorMessage}</p>
      <button
        class="btn-primary mt-2"
        on:click={initializeCamera}
        type="button"
      >
        启动摄像头
      </button>
    </div>
  {:else if stream}
    <canvas
      bind:this={canvas}
      width={width}
      height={height}
      class="rounded-lg bg-surface-elevated border border-border w-full"
      style="max-width: 100%; height: auto;"
    ></canvas>
    <div class="flex items-center justify-between w-full mt-2">
      <p class="text-xs text-text-tertiary">摄像头已连接</p>
      <button
        class="btn-secondary text-xs px-3 py-1"
        on:click={() => {
          stopCapture();
          if (stream) {
            stream.getTracks().forEach((track) => track.stop());
            stream = null;
          }
          isLoading = false;
          errorMessage = '';
        }}
        type="button"
      >
        停止摄像头
      </button>
    </div>
  {:else}
    <div class="flex flex-col items-center justify-center min-h-[200px] w-full bg-surface-elevated rounded-lg border border-border p-4">
      <div class="text-4xl mb-2">📷</div>
      <p class="text-sm text-text-secondary mb-4">摄像头未启动</p>
      <button
        class="btn-primary"
        on:click={initializeCamera}
        type="button"
      >
        启动摄像头
      </button>
    </div>
  {/if}
</div>

