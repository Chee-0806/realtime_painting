<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  
  const dispatch = createEventDispatcher();
  
  // Props
  export let width: number = 512;
  export let height: number = 512;
  export let sourceImage: string = '';
  
  // Canvas引用
  let maskCanvas: HTMLCanvasElement;
  let previewCanvas: HTMLCanvasElement;
  let maskCtx: CanvasRenderingContext2D | null = null;
  let previewCtx: CanvasRenderingContext2D | null = null;
  
  // 工具状态
  export let tool: 'brush' | 'eraser' | 'fill' = 'brush';
  export let brushSize: number = 30;
  export let brushHardness: number = 0.8;
  
  // 绘制状态
  let isDrawing: boolean = false;
  let lastX: number = 0;
  let lastY: number = 0;
  
  // UI状态
  let showPreview: boolean = false;
  let invertMask: boolean = false;
  
  onMount(() => {
    if (maskCanvas && previewCanvas) {
      maskCtx = maskCanvas.getContext('2d', { willReadFrequently: true });
      previewCtx = previewCanvas.getContext('2d');
      
      // 设置canvas尺寸
      maskCanvas.width = width;
      maskCanvas.height = height;
      previewCanvas.width = width;
      previewCanvas.height = height;
      
      // 初始化蒙版为透明
      clearMask();
      
      // 如果有源图像，加载到预览
      if (sourceImage) {
        loadSourceImage();
      }
    }
  });
  
  // 监听尺寸变化
  $: if (maskCanvas && previewCanvas) {
    maskCanvas.width = width;
    maskCanvas.height = height;
    previewCanvas.width = width;
    previewCanvas.height = height;
    clearMask();
    if (sourceImage) {
      loadSourceImage();
    }
  }
  
  // 监听源图像变化
  $: if (sourceImage && previewCtx) {
    loadSourceImage();
  }
  
  function loadSourceImage() {
    if (!sourceImage || !previewCtx) return;
    
    const img = new Image();
    img.onload = () => {
      if (previewCtx) {
        previewCtx.clearRect(0, 0, width, height);
        previewCtx.drawImage(img, 0, 0, width, height);
      }
    };
    img.src = sourceImage;
  }
  
  function getMousePos(event: MouseEvent | TouchEvent): { x: number; y: number } {
    const rect = maskCanvas.getBoundingClientRect();
    const scaleX = maskCanvas.width / rect.width;
    const scaleY = maskCanvas.height / rect.height;
    
    let clientX: number, clientY: number;
    
    if (event instanceof MouseEvent) {
      clientX = event.clientX;
      clientY = event.clientY;
    } else {
      clientX = event.touches[0].clientX;
      clientY = event.touches[0].clientY;
    }
    
    return {
      x: (clientX - rect.left) * scaleX,
      y: (clientY - rect.top) * scaleY
    };
  }
  
  function startDrawing(event: MouseEvent | TouchEvent) {
    event.preventDefault();
    isDrawing = true;
    
    const pos = getMousePos(event);
    lastX = pos.x;
    lastY = pos.y;
    
    if (tool === 'fill') {
      floodFill(pos.x, pos.y);
      isDrawing = false;
    } else {
      draw(event);
    }
  }
  
  function stopDrawing() {
    if (isDrawing) {
      isDrawing = false;
      notifyChange();
    }
  }
  
  function draw(event: MouseEvent | TouchEvent) {
    if (!isDrawing || !maskCtx || tool === 'fill') return;
    
    event.preventDefault();
    const pos = getMousePos(event);
    
    // 使用线条连接上一个点和当前点，避免快速移动时出现断点
    maskCtx.lineWidth = brushSize;
    maskCtx.lineCap = 'round';
    maskCtx.lineJoin = 'round';
    
    if (tool === 'brush') {
      // 绘制白色蒙版
      maskCtx.globalCompositeOperation = 'source-over';
      maskCtx.strokeStyle = `rgba(255, 255, 255, ${brushHardness})`;
    } else if (tool === 'eraser') {
      // 橡皮擦：清除蒙版
      maskCtx.globalCompositeOperation = 'destination-out';
      maskCtx.strokeStyle = 'rgba(255, 255, 255, 1)';
    }
    
    maskCtx.beginPath();
    maskCtx.moveTo(lastX, lastY);
    maskCtx.lineTo(pos.x, pos.y);
    maskCtx.stroke();
    
    lastX = pos.x;
    lastY = pos.y;
    
    // 重置混合模式
    maskCtx.globalCompositeOperation = 'source-over';
  }
  
  function floodFill(startX: number, startY: number) {
    if (!maskCtx) return;
    
    const imageData = maskCtx.getImageData(0, 0, width, height);
    const pixels = imageData.data;
    const targetColor = getPixelColor(pixels, startX, startY);
    const fillColor = tool === 'brush' 
      ? { r: 255, g: 255, b: 255, a: Math.floor(brushHardness * 255) }
      : { r: 0, g: 0, b: 0, a: 0 };
    
    // 如果目标颜色和填充颜色相同，不需要填充
    if (colorsMatch(targetColor, fillColor)) return;
    
    const stack: Array<{ x: number; y: number }> = [{ x: Math.floor(startX), y: Math.floor(startY) }];
    const visited = new Set<string>();
    
    while (stack.length > 0) {
      const { x, y } = stack.pop()!;
      const key = `${x},${y}`;
      
      if (visited.has(key)) continue;
      if (x < 0 || x >= width || y < 0 || y >= height) continue;
      
      const currentColor = getPixelColor(pixels, x, y);
      if (!colorsMatch(currentColor, targetColor)) continue;
      
      visited.add(key);
      setPixelColor(pixels, x, y, fillColor);
      
      // 添加相邻像素到栈
      stack.push({ x: x + 1, y });
      stack.push({ x: x - 1, y });
      stack.push({ x, y: y + 1 });
      stack.push({ x, y: y - 1 });
    }
    
    maskCtx.putImageData(imageData, 0, 0);
    notifyChange();
  }
  
  function getPixelColor(pixels: Uint8ClampedArray, x: number, y: number) {
    const index = (Math.floor(y) * width + Math.floor(x)) * 4;
    return {
      r: pixels[index],
      g: pixels[index + 1],
      b: pixels[index + 2],
      a: pixels[index + 3]
    };
  }
  
  function setPixelColor(
    pixels: Uint8ClampedArray, 
    x: number, 
    y: number, 
    color: { r: number; g: number; b: number; a: number }
  ) {
    const index = (Math.floor(y) * width + Math.floor(x)) * 4;
    pixels[index] = color.r;
    pixels[index + 1] = color.g;
    pixels[index + 2] = color.b;
    pixels[index + 3] = color.a;
  }
  
  function colorsMatch(
    c1: { r: number; g: number; b: number; a: number },
    c2: { r: number; g: number; b: number; a: number },
    tolerance: number = 10
  ): boolean {
    return (
      Math.abs(c1.r - c2.r) <= tolerance &&
      Math.abs(c1.g - c2.g) <= tolerance &&
      Math.abs(c1.b - c2.b) <= tolerance &&
      Math.abs(c1.a - c2.a) <= tolerance
    );
  }
  
  export function clearMask() {
    if (!maskCtx) return;
    
    maskCtx.clearRect(0, 0, width, height);
    maskCtx.fillStyle = 'rgba(0, 0, 0, 0)';
    maskCtx.fillRect(0, 0, width, height);
    notifyChange();
  }
  
  export function invertMaskData() {
    if (!maskCtx) return;
    
    const imageData = maskCtx.getImageData(0, 0, width, height);
    const pixels = imageData.data;
    
    for (let i = 0; i < pixels.length; i += 4) {
      // 反转RGB值
      pixels[i] = 255 - pixels[i];
      pixels[i + 1] = 255 - pixels[i + 1];
      pixels[i + 2] = 255 - pixels[i + 2];
      // Alpha保持不变或反转
      if (pixels[i + 3] > 0) {
        pixels[i + 3] = 255 - pixels[i + 3];
      }
    }
    
    maskCtx.putImageData(imageData, 0, 0);
    invertMask = !invertMask;
    notifyChange();
  }
  
  export function getMaskDataURL(): string {
    return maskCanvas.toDataURL('image/png');
  }
  
  export function getMaskImageData(): ImageData | null {
    if (!maskCtx) return null;
    return maskCtx.getImageData(0, 0, width, height);
  }
  
  export function setMaskFromDataURL(dataURL: string) {
    if (!maskCtx) return;
    
    const img = new Image();
    img.onload = () => {
      maskCtx!.clearRect(0, 0, width, height);
      maskCtx!.drawImage(img, 0, 0, width, height);
      notifyChange();
    };
    img.src = dataURL;
  }
  
  function togglePreview() {
    showPreview = !showPreview;
  }
  
  function notifyChange() {
    dispatch('change', {
      dataURL: getMaskDataURL(),
      imageData: getMaskImageData()
    });
  }
  
  // 键盘快捷键
  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'b' || event.key === 'B') {
      tool = 'brush';
    } else if (event.key === 'e' || event.key === 'E') {
      tool = 'eraser';
    } else if (event.key === 'f' || event.key === 'F') {
      tool = 'fill';
    } else if (event.key === 'c' || event.key === 'C') {
      clearMask();
    } else if (event.key === 'i' || event.key === 'I') {
      invertMaskData();
    } else if (event.key === '[') {
      brushSize = Math.max(5, brushSize - 5);
    } else if (event.key === ']') {
      brushSize = Math.min(100, brushSize + 5);
    }
  }
</script>

<svelte:window on:keydown={handleKeyDown} />

<div class="mask-editor space-y-3">
  <!-- 工具栏 -->
  <div class="flex gap-2 flex-wrap">
    <button
      on:click={() => tool = 'brush'}
      class="flex-1 min-w-[80px] px-3 py-2 rounded-lg font-medium transition-colors {tool === 'brush' ? 'bg-primary text-white' : 'bg-surface hover:bg-surface/80 text-text-secondary'}"
      title="画笔 (B)"
    >
      🖌️ 画笔
    </button>
    <button
      on:click={() => tool = 'eraser'}
      class="flex-1 min-w-[80px] px-3 py-2 rounded-lg font-medium transition-colors {tool === 'eraser' ? 'bg-primary text-white' : 'bg-surface hover:bg-surface/80 text-text-secondary'}"
      title="橡皮擦 (E)"
    >
      🧹 橡皮擦
    </button>
    <button
      on:click={() => tool = 'fill'}
      class="flex-1 min-w-[80px] px-3 py-2 rounded-lg font-medium transition-colors {tool === 'fill' ? 'bg-primary text-white' : 'bg-surface hover:bg-surface/80 text-text-secondary'}"
      title="填充 (F)"
    >
      🪣 填充
    </button>
  </div>
  
  <!-- 操作按钮 -->
  <div class="flex gap-2 flex-wrap">
    <button
      on:click={clearMask}
      class="flex-1 min-w-[100px] px-3 py-2 bg-danger/10 hover:bg-danger/20 text-danger rounded-lg font-medium transition-colors"
      title="清除蒙版 (C)"
    >
      清除
    </button>
    <button
      on:click={invertMaskData}
      class="flex-1 min-w-[100px] px-3 py-2 bg-surface hover:bg-surface/80 text-text-secondary rounded-lg font-medium transition-colors"
      title="反转蒙版 (I)"
    >
      反转
    </button>
    <button
      on:click={togglePreview}
      class="flex-1 min-w-[100px] px-3 py-2 rounded-lg font-medium transition-colors {showPreview ? 'bg-primary text-white' : 'bg-surface hover:bg-surface/80 text-text-secondary'}"
    >
      {showPreview ? '👁️ 隐藏预览' : '👁️ 显示预览'}
    </button>
  </div>
  
  <!-- Canvas区域 -->
  <div class="relative border border-border rounded-lg overflow-hidden bg-surface-elevated">
    <!-- 预览Canvas（源图像） -->
    {#if showPreview}
      <canvas
        bind:this={previewCanvas}
        class="absolute inset-0 w-full h-full pointer-events-none"
        style="opacity: 0.5;"
      ></canvas>
    {/if}
    
    <!-- 蒙版Canvas（可交互） -->
    <canvas
      bind:this={maskCanvas}
      on:mousedown={startDrawing}
      on:mousemove={draw}
      on:mouseup={stopDrawing}
      on:mouseleave={stopDrawing}
      on:touchstart={startDrawing}
      on:touchmove={draw}
      on:touchend={stopDrawing}
      on:touchcancel={stopDrawing}
      class="relative w-full h-full cursor-crosshair touch-none"
      style="mix-blend-mode: {showPreview ? 'multiply' : 'normal'}; background-color: rgba(255, 0, 0, 0.3);"
    ></canvas>
    
    <!-- 画笔光标指示器 -->
    {#if tool !== 'fill'}
      <div 
        class="pointer-events-none absolute top-2 right-2 bg-surface-elevated/90 border border-border rounded-lg px-3 py-2 text-xs text-text-secondary"
      >
        画笔大小: {brushSize}px
      </div>
    {/if}
  </div>
  
  <!-- 画笔参数 -->
  <div class="space-y-3 p-4 bg-surface-elevated border border-border rounded-lg">
    <h4 class="text-sm font-semibold text-text-primary">画笔设置</h4>
    
    <!-- 画笔大小 -->
    <div class="space-y-2">
      <div class="flex justify-between items-center">
        <label for="brush-size" class="text-sm font-medium text-text-primary">
          画笔大小
        </label>
        <span class="text-sm text-text-secondary">{brushSize}px</span>
      </div>
      <input
        id="brush-size"
        type="range"
        bind:value={brushSize}
        min="5"
        max="100"
        step="5"
        class="w-full"
      />
      <p class="text-xs text-text-secondary">
        快捷键: [ 减小 / ] 增大
      </p>
    </div>
    
    <!-- 画笔硬度 -->
    <div class="space-y-2">
      <div class="flex justify-between items-center">
        <label for="brush-hardness" class="text-sm font-medium text-text-primary">
          画笔硬度
        </label>
        <span class="text-sm text-text-secondary">{(brushHardness * 100).toFixed(0)}%</span>
      </div>
      <input
        id="brush-hardness"
        type="range"
        bind:value={brushHardness}
        min="0.1"
        max="1.0"
        step="0.1"
        class="w-full"
      />
      <p class="text-xs text-text-secondary">
        值越高，边缘越清晰
      </p>
    </div>
  </div>
  
  <!-- 提示信息 -->
  <div class="p-3 bg-surface-elevated border border-border rounded-lg">
    <p class="text-xs text-text-secondary">
      💡 <strong>快捷键:</strong> B-画笔 | E-橡皮擦 | F-填充 | C-清除 | I-反转 | [-减小画笔 | ]-增大画笔
    </p>
    <p class="text-xs text-text-secondary mt-1">
      💡 在图像上绘制白色区域标记需要处理的部分
    </p>
  </div>
</div>

<style>
  canvas {
    image-rendering: pixelated;
    image-rendering: -moz-crisp-edges;
    image-rendering: crisp-edges;
  }
  
  .touch-none {
    touch-action: none;
  }
</style>
