<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import {
    onFrameChangeStore,
  } from '$lib/mediaStream';
  
  export let width = 512;
  export let height = 512;
  const size = { width, height };

  let canvasEl: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D | null = null;
  let animationFrameId: number | null = null;
  
  // 调整节流时间以适应你的需求
  const THROTTLE = 1000 / 120; // 120fps
  let lastMillis = 0;
  
  // 画板绘制相关
  let isDrawing = false;
  let lastX = 0;
  let lastY = 0;
  export let color = '#000000';
  export let brushSize = 5;

  onMount(() => {
    ctx = canvasEl.getContext('2d') as CanvasRenderingContext2D;
    if (ctx) {
      canvasEl.width = size.width;
      canvasEl.height = size.height;
      // 初始化画布为白色
      ctx.fillStyle = 'white';
      ctx.fillRect(0, 0, canvasEl.width, canvasEl.height);
      ctx.fillStyle = color;
    }
    // 开始捕获帧
    startFrameCapture();
  });

  onDestroy(() => {
    stopFrameCapture();
  });

  function startFrameCapture() {
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
    }
    lastMillis = performance.now();
    onFrameChange(performance.now());
  }

  function stopFrameCapture() {
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }
  }

  async function onFrameChange(now: DOMHighResTimeStamp) {
    if (now - lastMillis < THROTTLE) {
      animationFrameId = requestAnimationFrame(onFrameChange);
      return;
    }
    
    if (!ctx || !canvasEl) {
      animationFrameId = requestAnimationFrame(onFrameChange);
      return;
    }

    // 将画布转换为blob
    const blob = await new Promise<Blob>((resolve) => {
      canvasEl.toBlob(
        (blob) => {
          resolve(blob as Blob);
        },
        'image/jpeg',
        0.95
      );
    });
    
    onFrameChangeStore.set({ blob });
    lastMillis = now;
    animationFrameId = requestAnimationFrame(onFrameChange);
  }

  // 画板绘制函数
  function startDrawing(e: MouseEvent | TouchEvent) {
    isDrawing = true;
    const rect = canvasEl.getBoundingClientRect();
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
    lastX = clientX - rect.left;
    lastY = clientY - rect.top;
  }

  function draw(e: MouseEvent | TouchEvent) {
    if (!isDrawing || !ctx) return;
    
    const rect = canvasEl.getBoundingClientRect();
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
  }

  function stopDrawing() {
    isDrawing = false;
  }

  function clearCanvas() {
    if (ctx) {
      ctx.fillStyle = 'white';
      ctx.fillRect(0, 0, canvasEl.width, canvasEl.height);
      ctx.fillStyle = color;
    }
  }

  // 导出方法供父组件调用
  export function setColor(newColor: string) {
    color = newColor;
    if (ctx) {
      ctx.strokeStyle = color;
      ctx.fillStyle = color;
    }
  }

  export function setBrushSize(size: number) {
    brushSize = size;
  }

  export function clear() {
    clearCanvas();
  }
  
  // 响应式更新颜色和画笔大小
  $: if (ctx && color) {
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
  }
  
  $: if (brushSize) {
    // brushSize 变化时不需要特殊处理，在draw函数中使用
  }
</script>

<div class="relative mx-auto max-w-lg overflow-hidden rounded-lg border border-slate-300">
  <div class="relative z-10 aspect-square w-full object-cover">
    <canvas
      bind:this={canvasEl}
      class="aspect-square w-full object-cover cursor-crosshair bg-white"
      on:mousedown={startDrawing}
      on:mousemove={draw}
      on:mouseup={stopDrawing}
      on:mouseleave={stopDrawing}
      on:touchstart={startDrawing}
      on:touchmove={draw}
      on:touchend={stopDrawing}
    ></canvas>
  </div>
</div>

