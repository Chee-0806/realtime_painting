<script lang="ts">
  import { onMount } from 'svelte';
  import { setError, clearError, ErrorType } from '$lib/store';
  
  // 组件状态
  let sourceImage: string = '';
  let sourceImageElement: HTMLImageElement | null = null;
  
  // Canvas引用
  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D | null = null;
  
  // 编辑历史
  let editHistory: ImageData[] = [];
  let historyIndex: number = -1;
  const MAX_HISTORY = 20;
  
  // UI状态
  let loading: boolean = false;
  let imageLoaded: boolean = false;
  
  // 文件上传处理
  let fileInput: HTMLInputElement;
  
  // Canvas尺寸
  let canvasWidth: number = 512;
  let canvasHeight: number = 512;
  
  // 编辑工具状态
  let activeTool: 'none' | 'crop' | 'rotate' | 'scale' = 'none';
  
  // 裁剪工具状态
  let cropStartX: number = 0;
  let cropStartY: number = 0;
  let cropEndX: number = 0;
  let cropEndY: number = 0;
  let isCropping: boolean = false;
  let cropRect: { x: number; y: number; width: number; height: number } | null = null;
  
  // 旋转工具状态
  let rotationAngle: number = 0;
  let customRotationAngle: number = 0;
  
  // 缩放工具状态
  let scaleX: number = 1.0;
  let scaleY: number = 1.0;
  let maintainAspectRatio: boolean = true;
  
  // 颜色调整状态
  let brightness: number = 0;      // -100 到 100
  let contrast: number = 0;        // -100 到 100
  let saturation: number = 0;      // -100 到 100
  let originalImageData: ImageData | null = null;
  
  // 滤镜状态
  let selectedFilter: string = 'none';
  let filterStrength: number = 100;  // 0-100，滤镜强度百分比
  
  // 对比视图状态
  let comparisonMode: 'none' | 'split' | 'toggle' = 'none';
  let splitPosition: number = 50;  // 分屏位置百分比
  let showOriginal: boolean = false;  // 切换对比时显示原始图像
  let comparisonCanvas: HTMLCanvasElement;
  let comparisonCtx: CanvasRenderingContext2D | null = null;
  
  onMount(() => {
    if (canvas) {
      ctx = canvas.getContext('2d', { willReadFrequently: true });
      
      // 初始化画布
      if (ctx) {
        ctx.fillStyle = '#1a1a1a';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
      }
    }
    
    // 初始化对比画布
    if (comparisonCanvas) {
      comparisonCtx = comparisonCanvas.getContext('2d', { willReadFrequently: true });
    }
    
    // 添加键盘快捷键支持
    const handleKeyDown = (e: KeyboardEvent) => {
      // 空格键：在切换对比模式下切换图像
      if (e.code === 'Space' && comparisonMode === 'toggle') {
        e.preventDefault();
        toggleImage();
      }
      
      // Escape键：退出对比模式
      if (e.code === 'Escape' && comparisonMode !== 'none') {
        e.preventDefault();
        exitComparisonMode();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  });
  
  function handleFileSelect(event: Event) {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    
    if (!file) return;
    
    if (!file.type.startsWith('image/')) {
      setError({
        type: ErrorType.VALIDATION,
        message: '请选择图像文件',
        details: '只支持图像格式（PNG, JPG, WebP等）',
        recoverable: true,
        suggestions: ['选择一个有效的图像文件']
      });
      return;
    }
    
    loading = true;
    const reader = new FileReader();
    
    reader.onload = (e) => {
      const result = e.target?.result as string;
      sourceImage = result;
      loadImageToCanvas(result);
      clearError();
    };
    
    reader.onerror = () => {
      loading = false;
      setError({
        type: ErrorType.VALIDATION,
        message: '图像加载失败',
        details: '无法读取选择的文件',
        recoverable: true,
        suggestions: ['尝试选择其他图像文件']
      });
    };
    
    reader.readAsDataURL(file);
  }
  
  function loadImageToCanvas(imageSrc: string) {
    const img = new Image();
    
    img.onload = () => {
      sourceImageElement = img;
      
      // 调整canvas大小以匹配图像
      const maxWidth = 800;
      const maxHeight = 600;
      let width = img.width;
      let height = img.height;
      
      // 保持宽高比缩放
      if (width > maxWidth || height > maxHeight) {
        const ratio = Math.min(maxWidth / width, maxHeight / height);
        width = Math.floor(width * ratio);
        height = Math.floor(height * ratio);
      }
      
      canvasWidth = width;
      canvasHeight = height;
      canvas.width = width;
      canvas.height = height;
      
      // 绘制图像
      if (ctx) {
        ctx.clearRect(0, 0, width, height);
        ctx.drawImage(img, 0, 0, width, height);
        
        // 保存到历史记录
        saveToHistory();
        imageLoaded = true;
        loading = false;
      }
    };
    
    img.onerror = () => {
      loading = false;
      setError({
        type: ErrorType.VALIDATION,
        message: '图像加载失败',
        details: '无法加载图像到画布',
        recoverable: true,
        suggestions: ['尝试选择其他图像文件']
      });
    };
    
    img.src = imageSrc;
  }
  
  function saveToHistory() {
    if (!ctx) return;
    
    // 删除当前位置之后的历史
    editHistory = editHistory.slice(0, historyIndex + 1);
    
    // 保存当前状态
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    editHistory.push(imageData);
    
    // 限制历史记录大小
    if (editHistory.length > MAX_HISTORY) {
      editHistory.shift();
    } else {
      historyIndex++;
    }
  }
  
  function undo() {
    if (!canUndo() || !ctx) return;
    
    historyIndex--;
    const imageData = editHistory[historyIndex];
    ctx.putImageData(imageData, 0, 0);
  }
  
  function redo() {
    if (!canRedo() || !ctx) return;
    
    historyIndex++;
    const imageData = editHistory[historyIndex];
    ctx.putImageData(imageData, 0, 0);
  }
  
  function canUndo(): boolean {
    return historyIndex > 0;
  }
  
  function canRedo(): boolean {
    return historyIndex < editHistory.length - 1;
  }
  
  function reset() {
    if (!ctx) return;
    
    if (sourceImageElement) {
      // 重新加载原始图像
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(sourceImageElement, 0, 0, canvas.width, canvas.height);
      
      // 重置所有编辑参数
      rotationAngle = 0;
      customRotationAngle = 0;
      scaleX = 1.0;
      scaleY = 1.0;
      cropRect = null;
      activeTool = 'none';
      brightness = 0;
      contrast = 0;
      saturation = 0;
      originalImageData = null;
      selectedFilter = 'none';
      filterStrength = 100;
      
      // 清空历史并保存当前状态
      editHistory = [];
      historyIndex = -1;
      saveToHistory();
    } else {
      // 清空画布
      ctx.fillStyle = '#1a1a1a';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      editHistory = [];
      historyIndex = -1;
      imageLoaded = false;
    }
  }
  
  // ========== 裁剪工具 ==========
  function startCrop() {
    activeTool = 'crop';
    cropRect = null;
  }
  
  function handleCropMouseDown(e: MouseEvent) {
    if (activeTool !== 'crop') return;
    
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    
    cropStartX = (e.clientX - rect.left) * scaleX;
    cropStartY = (e.clientY - rect.top) * scaleY;
    isCropping = true;
  }
  
  function handleCropMouseMove(e: MouseEvent) {
    if (!isCropping || activeTool !== 'crop') return;
    
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    
    cropEndX = (e.clientX - rect.left) * scaleX;
    cropEndY = (e.clientY - rect.top) * scaleY;
    
    // 绘制裁剪框预览
    drawCropPreview();
  }
  
  function handleCropMouseUp() {
    if (!isCropping || activeTool !== 'crop') return;
    
    isCropping = false;
    
    // 计算裁剪区域
    const x = Math.min(cropStartX, cropEndX);
    const y = Math.min(cropStartY, cropEndY);
    const width = Math.abs(cropEndX - cropStartX);
    const height = Math.abs(cropEndY - cropStartY);
    
    if (width > 10 && height > 10) {
      cropRect = { x, y, width, height };
    }
  }
  
  function drawCropPreview() {
    if (!ctx || !imageLoaded) return;
    
    // 重绘当前图像
    const currentImageData = editHistory[historyIndex];
    if (currentImageData) {
      ctx.putImageData(currentImageData, 0, 0);
    }
    
    // 绘制裁剪框
    const x = Math.min(cropStartX, cropEndX);
    const y = Math.min(cropStartY, cropEndY);
    const width = Math.abs(cropEndX - cropStartX);
    const height = Math.abs(cropEndY - cropStartY);
    
    // 半透明遮罩
    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // 清除裁剪区域的遮罩
    ctx.clearRect(x, y, width, height);
    const imageData = editHistory[historyIndex];
    if (imageData) {
      ctx.putImageData(imageData, 0, 0, x, y, width, height);
    }
    
    // 绘制裁剪框边框
    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, width, height);
  }
  
  function applyCrop() {
    if (!ctx || !cropRect) return;
    
    const { x, y, width, height } = cropRect;
    
    // 获取裁剪区域的图像数据
    const croppedImageData = ctx.getImageData(x, y, width, height);
    
    // 调整canvas大小
    canvas.width = width;
    canvas.height = height;
    canvasWidth = width;
    canvasHeight = height;
    
    // 绘制裁剪后的图像
    ctx.putImageData(croppedImageData, 0, 0);
    
    // 保存到历史
    saveToHistory();
    
    // 重置裁剪状态
    cropRect = null;
    activeTool = 'none';
  }
  
  function cancelCrop() {
    cropRect = null;
    activeTool = 'none';
    
    // 重绘当前图像
    if (ctx && editHistory[historyIndex]) {
      ctx.putImageData(editHistory[historyIndex], 0, 0);
    }
  }
  
  // ========== 旋转工具 ==========
  function rotate90() {
    rotateImage(90);
  }
  
  function rotate180() {
    rotateImage(180);
  }
  
  function rotate270() {
    rotateImage(270);
  }
  
  function rotateCustom() {
    if (customRotationAngle !== 0) {
      rotateImage(customRotationAngle);
    }
  }
  
  function rotateImage(angle: number) {
    if (!ctx || !imageLoaded) return;
    
    // 获取当前图像数据
    const currentImageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    
    // 创建临时canvas
    const tempCanvas = document.createElement('canvas');
    const tempCtx = tempCanvas.getContext('2d');
    if (!tempCtx) return;
    
    // 对于90度的倍数，需要交换宽高
    const radians = (angle * Math.PI) / 180;
    const isOrthogonal = angle % 90 === 0 && angle % 180 !== 0;
    
    if (isOrthogonal) {
      tempCanvas.width = canvas.height;
      tempCanvas.height = canvas.width;
    } else {
      tempCanvas.width = canvas.width;
      tempCanvas.height = canvas.height;
    }
    
    // 设置旋转中心
    tempCtx.translate(tempCanvas.width / 2, tempCanvas.height / 2);
    tempCtx.rotate(radians);
    tempCtx.translate(-canvas.width / 2, -canvas.height / 2);
    
    // 绘制旋转后的图像
    tempCtx.putImageData(currentImageData, 0, 0);
    
    // 更新主canvas
    canvas.width = tempCanvas.width;
    canvas.height = tempCanvas.height;
    canvasWidth = tempCanvas.width;
    canvasHeight = tempCanvas.height;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(tempCanvas, 0, 0);
    
    // 保存到历史
    saveToHistory();
    
    // 更新旋转角度
    rotationAngle = (rotationAngle + angle) % 360;
  }
  
  // ========== 缩放工具 ==========
  function applyScale() {
    if (!ctx || !imageLoaded) return;
    
    if (scaleX <= 0 || scaleY <= 0) {
      setError({
        type: ErrorType.VALIDATION,
        message: '缩放比例无效',
        details: '缩放比例必须大于0',
        recoverable: true,
        suggestions: ['请输入有效的缩放比例']
      });
      return;
    }
    
    // 获取当前图像数据
    const currentImageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    
    // 创建临时canvas
    const tempCanvas = document.createElement('canvas');
    const tempCtx = tempCanvas.getContext('2d');
    if (!tempCtx) return;
    
    tempCanvas.width = canvas.width;
    tempCanvas.height = canvas.height;
    tempCtx.putImageData(currentImageData, 0, 0);
    
    // 计算新尺寸
    const newWidth = Math.floor(canvas.width * scaleX);
    const newHeight = Math.floor(canvas.height * scaleY);
    
    // 更新canvas尺寸
    canvas.width = newWidth;
    canvas.height = newHeight;
    canvasWidth = newWidth;
    canvasHeight = newHeight;
    
    // 绘制缩放后的图像
    ctx.clearRect(0, 0, newWidth, newHeight);
    ctx.drawImage(tempCanvas, 0, 0, newWidth, newHeight);
    
    // 保存到历史
    saveToHistory();
    
    // 重置缩放比例
    scaleX = 1.0;
    scaleY = 1.0;
  }
  
  function handleScaleXChange() {
    if (maintainAspectRatio) {
      scaleY = scaleX;
    }
  }
  
  function handleScaleYChange() {
    if (maintainAspectRatio) {
      scaleX = scaleY;
    }
  }
  
  // ========== 颜色调整工具 ==========
  function applyColorAdjustments() {
    if (!ctx || !imageLoaded) return;
    
    // 保存原始图像数据（如果还没有保存）
    if (!originalImageData && editHistory[historyIndex]) {
      originalImageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    }
    
    // 从原始图像开始调整
    const imageData = originalImageData ? 
      new ImageData(
        new Uint8ClampedArray(originalImageData.data),
        originalImageData.width,
        originalImageData.height
      ) : 
      ctx.getImageData(0, 0, canvas.width, canvas.height);
    
    const data = imageData.data;
    
    // 计算调整因子
    const brightnessFactor = brightness / 100;
    const contrastFactor = (contrast + 100) / 100;
    const saturationFactor = (saturation + 100) / 100;
    
    // 对每个像素应用调整
    for (let i = 0; i < data.length; i += 4) {
      let r = data[i];
      let g = data[i + 1];
      let b = data[i + 2];
      
      // 应用亮度调整
      r += brightnessFactor * 255;
      g += brightnessFactor * 255;
      b += brightnessFactor * 255;
      
      // 应用对比度调整
      r = ((r / 255 - 0.5) * contrastFactor + 0.5) * 255;
      g = ((g / 255 - 0.5) * contrastFactor + 0.5) * 255;
      b = ((b / 255 - 0.5) * contrastFactor + 0.5) * 255;
      
      // 应用饱和度调整
      // 转换为灰度值
      const gray = 0.299 * r + 0.587 * g + 0.114 * b;
      
      // 混合灰度和原始颜色
      r = gray + (r - gray) * saturationFactor;
      g = gray + (g - gray) * saturationFactor;
      b = gray + (b - gray) * saturationFactor;
      
      // 限制在0-255范围内
      data[i] = Math.max(0, Math.min(255, r));
      data[i + 1] = Math.max(0, Math.min(255, g));
      data[i + 2] = Math.max(0, Math.min(255, b));
    }
    
    // 绘制调整后的图像
    ctx.putImageData(imageData, 0, 0);
  }
  
  function handleBrightnessChange() {
    applyColorAdjustments();
  }
  
  function handleContrastChange() {
    applyColorAdjustments();
  }
  
  function handleSaturationChange() {
    applyColorAdjustments();
  }
  
  function resetColorAdjustments() {
    brightness = 0;
    contrast = 0;
    saturation = 0;
    
    // 恢复原始图像
    if (originalImageData && ctx) {
      ctx.putImageData(originalImageData, 0, 0);
    }
  }
  
  function applyColorAdjustmentsPermanently() {
    if (!ctx) return;
    
    // 保存当前调整后的状态到历史
    saveToHistory();
    
    // 更新原始图像数据为当前状态
    originalImageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    
    // 重置调整值
    brightness = 0;
    contrast = 0;
    saturation = 0;
  }
  
  // ========== 滤镜工具 ==========
  
  /**
   * 应用模糊滤镜
   */
  function applyBlurFilter(imageData: ImageData, strength: number): ImageData {
    const data = imageData.data;
    const width = imageData.width;
    const height = imageData.height;
    const result = new ImageData(width, height);
    const resultData = result.data;
    
    // 计算模糊半径（基于强度）
    const radius = Math.max(1, Math.floor(strength / 20));
    
    // 简单的盒式模糊
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        let r = 0, g = 0, b = 0, a = 0;
        let count = 0;
        
        // 对周围像素求平均
        for (let dy = -radius; dy <= radius; dy++) {
          for (let dx = -radius; dx <= radius; dx++) {
            const nx = x + dx;
            const ny = y + dy;
            
            if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
              const idx = (ny * width + nx) * 4;
              r += data[idx];
              g += data[idx + 1];
              b += data[idx + 2];
              a += data[idx + 3];
              count++;
            }
          }
        }
        
        const idx = (y * width + x) * 4;
        resultData[idx] = r / count;
        resultData[idx + 1] = g / count;
        resultData[idx + 2] = b / count;
        resultData[idx + 3] = a / count;
      }
    }
    
    return result;
  }
  
  /**
   * 应用锐化滤镜
   */
  function applySharpenFilter(imageData: ImageData, strength: number): ImageData {
    const data = imageData.data;
    const width = imageData.width;
    const height = imageData.height;
    const result = new ImageData(width, height);
    const resultData = result.data;
    
    // 锐化卷积核（基于强度调整）
    const factor = strength / 100;
    const kernel = [
      0, -factor, 0,
      -factor, 1 + 4 * factor, -factor,
      0, -factor, 0
    ];
    
    // 应用卷积
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        let r = 0, g = 0, b = 0;
        
        // 3x3卷积
        for (let ky = -1; ky <= 1; ky++) {
          for (let kx = -1; kx <= 1; kx++) {
            const nx = Math.min(Math.max(x + kx, 0), width - 1);
            const ny = Math.min(Math.max(y + ky, 0), height - 1);
            const idx = (ny * width + nx) * 4;
            const kernelIdx = (ky + 1) * 3 + (kx + 1);
            
            r += data[idx] * kernel[kernelIdx];
            g += data[idx + 1] * kernel[kernelIdx];
            b += data[idx + 2] * kernel[kernelIdx];
          }
        }
        
        const idx = (y * width + x) * 4;
        resultData[idx] = Math.max(0, Math.min(255, r));
        resultData[idx + 1] = Math.max(0, Math.min(255, g));
        resultData[idx + 2] = Math.max(0, Math.min(255, b));
        resultData[idx + 3] = data[idx + 3]; // 保持alpha通道
      }
    }
    
    return result;
  }
  
  /**
   * 应用灰度滤镜
   */
  function applyGrayscaleFilter(imageData: ImageData): ImageData {
    const data = imageData.data;
    const result = new ImageData(
      new Uint8ClampedArray(data),
      imageData.width,
      imageData.height
    );
    const resultData = result.data;
    
    // 使用标准的灰度转换公式
    for (let i = 0; i < resultData.length; i += 4) {
      const gray = 0.299 * resultData[i] + 0.587 * resultData[i + 1] + 0.114 * resultData[i + 2];
      resultData[i] = gray;
      resultData[i + 1] = gray;
      resultData[i + 2] = gray;
      // alpha通道保持不变
    }
    
    return result;
  }
  
  /**
   * 应用选中的滤镜
   */
  function applyFilter() {
    if (!ctx || !imageLoaded || selectedFilter === 'none') return;
    
    // 保存原始图像数据（如果还没有保存）
    if (!originalImageData && editHistory[historyIndex]) {
      originalImageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    }
    
    // 从原始图像开始应用滤镜
    const sourceData = originalImageData || ctx.getImageData(0, 0, canvas.width, canvas.height);
    let filteredData: ImageData;
    
    switch (selectedFilter) {
      case 'blur':
        filteredData = applyBlurFilter(sourceData, filterStrength);
        break;
      case 'sharpen':
        filteredData = applySharpenFilter(sourceData, filterStrength);
        break;
      case 'grayscale':
        filteredData = applyGrayscaleFilter(sourceData);
        break;
      default:
        return;
    }
    
    // 绘制滤镜后的图像
    ctx.putImageData(filteredData, 0, 0);
  }
  
  /**
   * 处理滤镜选择变化
   */
  function handleFilterChange() {
    if (selectedFilter === 'none') {
      // 恢复原始图像
      if (originalImageData && ctx) {
        ctx.putImageData(originalImageData, 0, 0);
      }
    } else {
      applyFilter();
    }
  }
  
  /**
   * 处理滤镜强度变化
   */
  function handleFilterStrengthChange() {
    if (selectedFilter !== 'none' && selectedFilter !== 'grayscale') {
      applyFilter();
    }
  }
  
  /**
   * 永久应用滤镜
   */
  function applyFilterPermanently() {
    if (!ctx || selectedFilter === 'none') return;
    
    // 保存当前滤镜后的状态到历史
    saveToHistory();
    
    // 更新原始图像数据为当前状态
    originalImageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    
    // 重置滤镜选择
    selectedFilter = 'none';
    filterStrength = 100;
  }
  
  /**
   * 重置滤镜
   */
  function resetFilter() {
    selectedFilter = 'none';
    filterStrength = 100;
    
    // 恢复原始图像
    if (originalImageData && ctx) {
      ctx.putImageData(originalImageData, 0, 0);
    }
  }
  
  // ========== 对比视图功能 ==========
  
  /**
   * 启用分屏对比模式
   */
  function enableSplitComparison() {
    if (!originalImageData || !ctx) return;
    
    comparisonMode = 'split';
    splitPosition = 50;
    updateSplitComparison();
  }
  
  /**
   * 更新分屏对比视图
   */
  function updateSplitComparison() {
    if (!ctx || !originalImageData || comparisonMode !== 'split') return;
    
    const currentImageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const splitX = Math.floor(canvas.width * (splitPosition / 100));
    
    // 创建临时画布用于合成
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = canvas.width;
    tempCanvas.height = canvas.height;
    const tempCtx = tempCanvas.getContext('2d');
    if (!tempCtx) return;
    
    // 左侧显示原始图像
    tempCtx.putImageData(originalImageData, 0, 0);
    
    // 右侧显示编辑后的图像
    tempCtx.putImageData(currentImageData, 0, 0, splitX, 0, canvas.width - splitX, canvas.height);
    
    // 绘制分割线
    tempCtx.strokeStyle = '#00ff00';
    tempCtx.lineWidth = 3;
    tempCtx.beginPath();
    tempCtx.moveTo(splitX, 0);
    tempCtx.lineTo(splitX, canvas.height);
    tempCtx.stroke();
    
    // 绘制分割线上的拖动手柄
    tempCtx.fillStyle = '#00ff00';
    tempCtx.beginPath();
    tempCtx.arc(splitX, canvas.height / 2, 10, 0, Math.PI * 2);
    tempCtx.fill();
    
    // 添加标签
    tempCtx.font = 'bold 14px sans-serif';
    tempCtx.fillStyle = '#ffffff';
    tempCtx.strokeStyle = '#000000';
    tempCtx.lineWidth = 3;
    
    // 左侧标签
    const leftLabel = '原始';
    tempCtx.strokeText(leftLabel, 10, 30);
    tempCtx.fillText(leftLabel, 10, 30);
    
    // 右侧标签
    const rightLabel = '编辑后';
    const rightLabelWidth = tempCtx.measureText(rightLabel).width;
    tempCtx.strokeText(rightLabel, canvas.width - rightLabelWidth - 10, 30);
    tempCtx.fillText(rightLabel, canvas.width - rightLabelWidth - 10, 30);
    
    // 更新主画布
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(tempCanvas, 0, 0);
  }
  
  /**
   * 处理分屏位置拖动
   */
  function handleSplitDrag(e: MouseEvent) {
    if (comparisonMode !== 'split') return;
    
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    splitPosition = Math.max(0, Math.min(100, (x / rect.width) * 100));
    updateSplitComparison();
  }
  
  /**
   * 启用切换对比模式
   */
  function enableToggleComparison() {
    if (!originalImageData || !ctx) return;
    
    comparisonMode = 'toggle';
    showOriginal = false;
  }
  
  /**
   * 切换显示原始/编辑后图像
   */
  function toggleImage() {
    if (!ctx || !originalImageData || comparisonMode !== 'toggle') return;
    
    showOriginal = !showOriginal;
    
    if (showOriginal) {
      // 显示原始图像
      ctx.putImageData(originalImageData, 0, 0);
    } else {
      // 显示编辑后的图像
      const currentImageData = editHistory[historyIndex];
      if (currentImageData) {
        ctx.putImageData(currentImageData, 0, 0);
      }
    }
  }
  
  /**
   * 退出对比模式
   */
  function exitComparisonMode() {
    comparisonMode = 'none';
    showOriginal = false;
    
    // 恢复编辑后的图像
    if (ctx && editHistory[historyIndex]) {
      ctx.putImageData(editHistory[historyIndex], 0, 0);
    }
  }
  
  /**
   * 导出对比图像
   */
  function exportComparison() {
    if (!canvas || comparisonMode === 'none') return;
    
    try {
      let exportCanvas: HTMLCanvasElement;
      
      if (comparisonMode === 'split') {
        // 导出当前的分屏对比视图
        exportCanvas = canvas;
      } else {
        // 对于切换模式，创建一个并排对比图
        exportCanvas = document.createElement('canvas');
        exportCanvas.width = canvas.width * 2;
        exportCanvas.height = canvas.height;
        const exportCtx = exportCanvas.getContext('2d');
        
        if (exportCtx && originalImageData) {
          // 左侧：原始图像
          const tempCanvas1 = document.createElement('canvas');
          tempCanvas1.width = canvas.width;
          tempCanvas1.height = canvas.height;
          const tempCtx1 = tempCanvas1.getContext('2d');
          if (tempCtx1) {
            tempCtx1.putImageData(originalImageData, 0, 0);
            exportCtx.drawImage(tempCanvas1, 0, 0);
          }
          
          // 右侧：编辑后的图像
          const currentImageData = editHistory[historyIndex];
          if (currentImageData) {
            const tempCanvas2 = document.createElement('canvas');
            tempCanvas2.width = canvas.width;
            tempCanvas2.height = canvas.height;
            const tempCtx2 = tempCanvas2.getContext('2d');
            if (tempCtx2) {
              tempCtx2.putImageData(currentImageData, 0, 0);
              exportCtx.drawImage(tempCanvas2, canvas.width, 0);
            }
          }
          
          // 添加分割线
          exportCtx.strokeStyle = '#00ff00';
          exportCtx.lineWidth = 3;
          exportCtx.beginPath();
          exportCtx.moveTo(canvas.width, 0);
          exportCtx.lineTo(canvas.width, canvas.height);
          exportCtx.stroke();
          
          // 添加标签
          exportCtx.font = 'bold 16px sans-serif';
          exportCtx.fillStyle = '#ffffff';
          exportCtx.strokeStyle = '#000000';
          exportCtx.lineWidth = 3;
          
          exportCtx.strokeText('原始', 10, 30);
          exportCtx.fillText('原始', 10, 30);
          
          const rightLabel = '编辑后';
          const rightLabelWidth = exportCtx.measureText(rightLabel).width;
          exportCtx.strokeText(rightLabel, canvas.width + 10, 30);
          exportCtx.fillText(rightLabel, canvas.width + 10, 30);
        }
      }
      
      const dataURL = exportCanvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.href = dataURL;
      link.download = `comparison_${Date.now()}.png`;
      link.click();
    } catch (e) {
      setError({
        type: ErrorType.VALIDATION,
        message: '对比图导出失败',
        details: e instanceof Error ? e.message : String(e),
        recoverable: true,
        suggestions: ['尝试重新导出']
      });
    }
  }
  
  function downloadImage() {
    if (!canvas) return;
    
    try {
      const dataURL = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.href = dataURL;
      link.download = `edited_image_${Date.now()}.png`;
      link.click();
    } catch (e) {
      setError({
        type: ErrorType.VALIDATION,
        message: '图像下载失败',
        details: e instanceof Error ? e.message : String(e),
        recoverable: true,
        suggestions: ['尝试重新下载']
      });
    }
  }
  
  function clearCanvas() {
    sourceImage = '';
    sourceImageElement = null;
    imageLoaded = false;
    editHistory = [];
    historyIndex = -1;
    
    if (ctx) {
      ctx.fillStyle = '#1a1a1a';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }
    
    clearError();
  }
  
  // 导出当前图像为Base64
  export function getImageDataURL(): string {
    return canvas.toDataURL('image/png');
  }
  
  // 导出当前图像元素（供其他组件使用）
  export function getCanvas(): HTMLCanvasElement {
    return canvas;
  }
</script>

<div class="space-y-4">
  <div class="flex items-center justify-between mb-4">
    <h3 class="text-lg font-semibold text-text-primary">✂️ 图像编辑器</h3>
    <div class="flex gap-2">
      {#if imageLoaded}
        <button 
          on:click={downloadImage}
          class="px-3 py-1 text-sm bg-success hover:bg-success/90 text-white border border-success rounded-lg transition-colors"
          title="下载图像"
        >
          💾 下载
        </button>
      {/if}
      <button 
        on:click={clearCanvas}
        class="px-3 py-1 text-sm bg-surface-elevated hover:bg-surface-elevated/80 border border-border rounded-lg text-text-secondary transition-colors"
        title="清空画布"
      >
        🗑️ 清空
      </button>
    </div>
  </div>
  
  <!-- 图像上传 -->
  <div class="space-y-2">
    <label for="image-upload" class="block text-sm font-medium text-text-primary">
      选择图像
    </label>
    <input
      id="image-upload"
      type="file"
      bind:this={fileInput}
      on:change={handleFileSelect}
      accept="image/*"
      class="hidden"
    />
    <button
      on:click={() => fileInput.click()}
      disabled={loading}
      class="w-full px-4 py-3 bg-primary hover:bg-primary/90 disabled:bg-surface-elevated disabled:text-text-secondary text-white rounded-lg transition-colors font-medium disabled:cursor-not-allowed"
    >
      {#if loading}
        <span class="flex items-center justify-center gap-2">
          <div class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
          加载中...
        </span>
      {:else}
        {imageLoaded ? '更换图像' : '📁 选择图像'}
      {/if}
    </button>
  </div>
  
  {#if imageLoaded}
    <!-- 编辑工具栏 -->
    <div class="flex gap-2 p-3 bg-surface-elevated border border-border rounded-lg">
      <button
        on:click={undo}
        disabled={!canUndo()}
        class="flex-1 px-3 py-2 bg-surface hover:bg-surface/80 disabled:bg-surface-elevated disabled:text-text-secondary text-text-primary rounded-lg transition-colors font-medium disabled:cursor-not-allowed"
        title="撤销 (Ctrl+Z)"
      >
        ↶ 撤销
      </button>
      <button
        on:click={redo}
        disabled={!canRedo()}
        class="flex-1 px-3 py-2 bg-surface hover:bg-surface/80 disabled:bg-surface-elevated disabled:text-text-secondary text-text-primary rounded-lg transition-colors font-medium disabled:cursor-not-allowed"
        title="重做 (Ctrl+Shift+Z)"
      >
        ↷ 重做
      </button>
      <button
        on:click={reset}
        class="flex-1 px-3 py-2 bg-warning/10 hover:bg-warning/20 text-warning rounded-lg transition-colors font-medium"
        title="重置到原始图像"
      >
        🔄 重置
      </button>
    </div>
    
    <!-- 编辑工具面板 -->
    <div class="space-y-4 p-4 bg-surface-elevated border border-border rounded-lg">
      <h4 class="text-sm font-semibold text-text-primary mb-3">🛠️ 编辑工具</h4>
      
      <!-- 裁剪工具 -->
      <div class="space-y-2">
        <label class="text-sm font-medium text-text-primary">✂️ 裁剪</label>
        {#if activeTool === 'crop'}
          <div class="space-y-2">
            <p class="text-xs text-text-secondary">在画布上拖动鼠标选择裁剪区域</p>
            <div class="flex gap-2">
              <button
                on:click={applyCrop}
                disabled={!cropRect}
                class="flex-1 px-3 py-2 bg-success hover:bg-success/90 disabled:bg-surface-elevated disabled:text-text-secondary text-white rounded-lg transition-colors font-medium disabled:cursor-not-allowed"
              >
                ✓ 应用裁剪
              </button>
              <button
                on:click={cancelCrop}
                class="flex-1 px-3 py-2 bg-surface hover:bg-surface/80 text-text-primary rounded-lg transition-colors font-medium"
              >
                ✕ 取消
              </button>
            </div>
          </div>
        {:else}
          <button
            on:click={startCrop}
            class="w-full px-3 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg transition-colors font-medium"
          >
            开始裁剪
          </button>
        {/if}
      </div>
      
      <!-- 旋转工具 -->
      <div class="space-y-2">
        <label class="text-sm font-medium text-text-primary">🔄 旋转</label>
        <div class="grid grid-cols-3 gap-2">
          <button
            on:click={rotate90}
            class="px-3 py-2 bg-surface hover:bg-surface/80 text-text-primary rounded-lg transition-colors font-medium text-sm"
            title="顺时针旋转90度"
          >
            ↻ 90°
          </button>
          <button
            on:click={rotate180}
            class="px-3 py-2 bg-surface hover:bg-surface/80 text-text-primary rounded-lg transition-colors font-medium text-sm"
            title="旋转180度"
          >
            ↻ 180°
          </button>
          <button
            on:click={rotate270}
            class="px-3 py-2 bg-surface hover:bg-surface/80 text-text-primary rounded-lg transition-colors font-medium text-sm"
            title="顺时针旋转270度（逆时针90度）"
          >
            ↻ 270°
          </button>
        </div>
        
        <!-- 自定义旋转角度 -->
        <div class="space-y-2 mt-3">
          <label class="text-xs text-text-secondary">自定义角度</label>
          <div class="flex gap-2">
            <input
              type="number"
              bind:value={customRotationAngle}
              min="-360"
              max="360"
              step="1"
              class="flex-1 px-3 py-2 bg-surface border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="角度 (-360 到 360)"
            />
            <button
              on:click={rotateCustom}
              disabled={customRotationAngle === 0}
              class="px-4 py-2 bg-primary hover:bg-primary/90 disabled:bg-surface-elevated disabled:text-text-secondary text-white rounded-lg transition-colors font-medium text-sm disabled:cursor-not-allowed"
            >
              应用
            </button>
          </div>
          <p class="text-xs text-text-secondary">当前旋转: {rotationAngle}°</p>
        </div>
      </div>
      
      <!-- 缩放工具 -->
      <div class="space-y-2">
        <label class="text-sm font-medium text-text-primary">🔍 缩放</label>
        
        <div class="flex items-center gap-2 mb-2">
          <input
            type="checkbox"
            bind:checked={maintainAspectRatio}
            id="maintain-aspect-ratio"
            class="w-4 h-4 text-primary bg-surface border-border rounded focus:ring-primary"
          />
          <label for="maintain-aspect-ratio" class="text-xs text-text-secondary cursor-pointer">
            保持宽高比
          </label>
        </div>
        
        <div class="space-y-3">
          <div class="space-y-1">
            <div class="flex items-center justify-between">
              <label class="text-xs text-text-secondary">宽度缩放</label>
              <span class="text-xs text-text-primary font-mono">{scaleX.toFixed(2)}x</span>
            </div>
            <input
              type="range"
              bind:value={scaleX}
              on:input={handleScaleXChange}
              min="0.1"
              max="3.0"
              step="0.1"
              class="w-full h-2 bg-surface rounded-lg appearance-none cursor-pointer accent-primary"
            />
          </div>
          
          <div class="space-y-1">
            <div class="flex items-center justify-between">
              <label class="text-xs text-text-secondary">高度缩放</label>
              <span class="text-xs text-text-primary font-mono">{scaleY.toFixed(2)}x</span>
            </div>
            <input
              type="range"
              bind:value={scaleY}
              on:input={handleScaleYChange}
              min="0.1"
              max="3.0"
              step="0.1"
              class="w-full h-2 bg-surface rounded-lg appearance-none cursor-pointer accent-primary"
              disabled={maintainAspectRatio}
            />
          </div>
        </div>
        
        <button
          on:click={applyScale}
          disabled={scaleX === 1.0 && scaleY === 1.0}
          class="w-full px-3 py-2 bg-primary hover:bg-primary/90 disabled:bg-surface-elevated disabled:text-text-secondary text-white rounded-lg transition-colors font-medium disabled:cursor-not-allowed"
        >
          应用缩放
        </button>
      </div>
      
      <!-- 滤镜工具 -->
      <div class="space-y-2">
        <label class="text-sm font-medium text-text-primary">✨ 滤镜效果</label>
        
        <div class="space-y-3">
          <!-- 滤镜选择下拉菜单 -->
          <div class="space-y-1">
            <label class="text-xs text-text-secondary">选择滤镜</label>
            <select
              bind:value={selectedFilter}
              on:change={handleFilterChange}
              class="w-full px-3 py-2 bg-surface border border-border rounded-lg text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="none">无滤镜</option>
              <option value="blur">模糊</option>
              <option value="sharpen">锐化</option>
              <option value="grayscale">灰度</option>
            </select>
          </div>
          
          <!-- 滤镜强度（仅对模糊和锐化有效） -->
          {#if selectedFilter === 'blur' || selectedFilter === 'sharpen'}
            <div class="space-y-1">
              <div class="flex items-center justify-between">
                <label class="text-xs text-text-secondary">
                  {selectedFilter === 'blur' ? '模糊强度' : '锐化强度'}
                </label>
                <span class="text-xs text-text-primary font-mono">{filterStrength}%</span>
              </div>
              <input
                type="range"
                bind:value={filterStrength}
                on:input={handleFilterStrengthChange}
                min="0"
                max="100"
                step="5"
                class="w-full h-2 bg-surface rounded-lg appearance-none cursor-pointer accent-primary"
              />
            </div>
          {/if}
          
          <!-- 滤镜预览说明 -->
          {#if selectedFilter !== 'none'}
            <div class="p-2 bg-primary/10 border border-primary/30 rounded text-xs text-text-secondary">
              {#if selectedFilter === 'blur'}
                🌫️ 模糊滤镜：使图像变得柔和，减少细节
              {:else if selectedFilter === 'sharpen'}
                🔪 锐化滤镜：增强图像边缘，使细节更清晰
              {:else if selectedFilter === 'grayscale'}
                ⚫ 灰度滤镜：将图像转换为黑白
              {/if}
            </div>
          {/if}
        </div>
        
        <!-- 滤镜操作按钮 -->
        {#if selectedFilter !== 'none'}
          <div class="flex gap-2 mt-3">
            <button
              on:click={applyFilterPermanently}
              class="flex-1 px-3 py-2 bg-success hover:bg-success/90 text-white rounded-lg transition-colors font-medium text-sm"
            >
              ✓ 应用滤镜
            </button>
            <button
              on:click={resetFilter}
              class="flex-1 px-3 py-2 bg-surface hover:bg-surface/80 text-text-primary rounded-lg transition-colors font-medium text-sm"
            >
              ↶ 取消
            </button>
          </div>
        {/if}
        
        <p class="text-xs text-text-secondary mt-2">
          💡 实时预览：选择滤镜即可看到效果，点击"应用滤镜"保存更改
        </p>
      </div>
      
      <!-- 对比视图工具 -->
      <div class="space-y-2">
        <label class="text-sm font-medium text-text-primary">🔍 前后对比</label>
        
        {#if comparisonMode === 'none'}
          <div class="space-y-2">
            <p class="text-xs text-text-secondary">
              对比原始图像和编辑后的效果
            </p>
            <div class="grid grid-cols-2 gap-2">
              <button
                on:click={enableSplitComparison}
                disabled={!originalImageData}
                class="px-3 py-2 bg-primary hover:bg-primary/90 disabled:bg-surface-elevated disabled:text-text-secondary text-white rounded-lg transition-colors font-medium text-sm disabled:cursor-not-allowed"
                title="左右分屏对比"
              >
                ⬌ 分屏对比
              </button>
              <button
                on:click={enableToggleComparison}
                disabled={!originalImageData}
                class="px-3 py-2 bg-primary hover:bg-primary/90 disabled:bg-surface-elevated disabled:text-text-secondary text-white rounded-lg transition-colors font-medium text-sm disabled:cursor-not-allowed"
                title="点击切换原始/编辑后"
              >
                ⇄ 切换对比
              </button>
            </div>
            {#if !originalImageData}
              <p class="text-xs text-warning">
                ⚠️ 请先进行编辑操作才能使用对比功能
              </p>
            {/if}
          </div>
        {:else if comparisonMode === 'split'}
          <div class="space-y-3">
            <p class="text-xs text-text-secondary">
              拖动画布上的绿色分割线调整对比位置
            </p>
            
            <!-- 分屏位置滑块 -->
            <div class="space-y-1">
              <div class="flex items-center justify-between">
                <label class="text-xs text-text-secondary">分割位置</label>
                <span class="text-xs text-text-primary font-mono">{Math.round(splitPosition)}%</span>
              </div>
              <input
                type="range"
                bind:value={splitPosition}
                on:input={updateSplitComparison}
                min="0"
                max="100"
                step="1"
                class="w-full h-2 bg-surface rounded-lg appearance-none cursor-pointer accent-primary"
              />
            </div>
            
            <div class="flex gap-2">
              <button
                on:click={exportComparison}
                class="flex-1 px-3 py-2 bg-success hover:bg-success/90 text-white rounded-lg transition-colors font-medium text-sm"
              >
                💾 导出对比图
              </button>
              <button
                on:click={exitComparisonMode}
                class="flex-1 px-3 py-2 bg-surface hover:bg-surface/80 text-text-primary rounded-lg transition-colors font-medium text-sm"
              >
                ✕ 退出对比
              </button>
            </div>
          </div>
        {:else if comparisonMode === 'toggle'}
          <div class="space-y-3">
            <p class="text-xs text-text-secondary">
              点击按钮在原始图像和编辑后图像之间切换
            </p>
            
            <div class="p-3 bg-primary/10 border border-primary/30 rounded text-center">
              <p class="text-sm font-semibold text-text-primary">
                当前显示: {showOriginal ? '原始图像' : '编辑后图像'}
              </p>
            </div>
            
            <button
              on:click={toggleImage}
              class="w-full px-4 py-3 bg-primary hover:bg-primary/90 text-white rounded-lg transition-colors font-medium"
            >
              ⇄ 切换图像
            </button>
            
            <div class="flex gap-2">
              <button
                on:click={exportComparison}
                class="flex-1 px-3 py-2 bg-success hover:bg-success/90 text-white rounded-lg transition-colors font-medium text-sm"
              >
                💾 导出对比图
              </button>
              <button
                on:click={exitComparisonMode}
                class="flex-1 px-3 py-2 bg-surface hover:bg-surface/80 text-text-primary rounded-lg transition-colors font-medium text-sm"
              >
                ✕ 退出对比
              </button>
            </div>
          </div>
        {/if}
        
        <div class="p-2 bg-primary/10 border border-primary/30 rounded text-xs text-text-secondary">
          💡 <strong>提示:</strong> 
          {#if comparisonMode === 'none'}
            对比功能可以帮助你查看编辑前后的差异
          {:else if comparisonMode === 'split'}
            拖动分割线或使用滑块调整对比位置
          {:else}
            使用空格键快速切换图像
          {/if}
        </div>
      </div>
      
      <!-- 颜色调整工具 -->
      <div class="space-y-2">
        <label class="text-sm font-medium text-text-primary">🎨 颜色调整</label>
        
        <div class="space-y-3">
          <!-- 亮度调整 -->
          <div class="space-y-1">
            <div class="flex items-center justify-between">
              <label class="text-xs text-text-secondary">☀️ 亮度</label>
              <span class="text-xs text-text-primary font-mono">{brightness > 0 ? '+' : ''}{brightness}</span>
            </div>
            <input
              type="range"
              bind:value={brightness}
              on:input={handleBrightnessChange}
              min="-100"
              max="100"
              step="1"
              class="w-full h-2 bg-surface rounded-lg appearance-none cursor-pointer accent-primary"
            />
          </div>
          
          <!-- 对比度调整 -->
          <div class="space-y-1">
            <div class="flex items-center justify-between">
              <label class="text-xs text-text-secondary">◐ 对比度</label>
              <span class="text-xs text-text-primary font-mono">{contrast > 0 ? '+' : ''}{contrast}</span>
            </div>
            <input
              type="range"
              bind:value={contrast}
              on:input={handleContrastChange}
              min="-100"
              max="100"
              step="1"
              class="w-full h-2 bg-surface rounded-lg appearance-none cursor-pointer accent-primary"
            />
          </div>
          
          <!-- 饱和度调整 -->
          <div class="space-y-1">
            <div class="flex items-center justify-between">
              <label class="text-xs text-text-secondary">🌈 饱和度</label>
              <span class="text-xs text-text-primary font-mono">{saturation > 0 ? '+' : ''}{saturation}</span>
            </div>
            <input
              type="range"
              bind:value={saturation}
              on:input={handleSaturationChange}
              min="-100"
              max="100"
              step="1"
              class="w-full h-2 bg-surface rounded-lg appearance-none cursor-pointer accent-primary"
            />
          </div>
        </div>
        
        <div class="flex gap-2 mt-3">
          <button
            on:click={applyColorAdjustmentsPermanently}
            disabled={brightness === 0 && contrast === 0 && saturation === 0}
            class="flex-1 px-3 py-2 bg-success hover:bg-success/90 disabled:bg-surface-elevated disabled:text-text-secondary text-white rounded-lg transition-colors font-medium disabled:cursor-not-allowed text-sm"
          >
            ✓ 应用
          </button>
          <button
            on:click={resetColorAdjustments}
            disabled={brightness === 0 && contrast === 0 && saturation === 0}
            class="flex-1 px-3 py-2 bg-surface hover:bg-surface/80 disabled:bg-surface-elevated disabled:text-text-secondary text-text-primary rounded-lg transition-colors font-medium disabled:cursor-not-allowed text-sm"
          >
            ↶ 重置
          </button>
        </div>
        
        <p class="text-xs text-text-secondary mt-2">
          💡 实时预览：拖动滑块即可看到效果，点击"应用"保存更改
        </p>
      </div>
    </div>
  {/if}
  
  <!-- Canvas预览区域 -->
  <div class="relative border border-border rounded-lg overflow-hidden bg-surface-elevated">
    <div class="flex items-center justify-center min-h-[400px] p-4">
      <canvas
        bind:this={canvas}
        width={canvasWidth}
        height={canvasHeight}
        on:mousedown={(e) => {
          if (comparisonMode === 'split') {
            handleSplitDrag(e);
          } else {
            handleCropMouseDown(e);
          }
        }}
        on:mousemove={(e) => {
          if (comparisonMode === 'split' && e.buttons === 1) {
            handleSplitDrag(e);
          } else {
            handleCropMouseMove(e);
          }
        }}
        on:mouseup={handleCropMouseUp}
        on:mouseleave={handleCropMouseUp}
        on:click={() => {
          if (comparisonMode === 'toggle') {
            toggleImage();
          }
        }}
        class="max-w-full h-auto rounded-lg shadow-lg {
          comparisonMode === 'split' ? 'cursor-ew-resize' : 
          comparisonMode === 'toggle' ? 'cursor-pointer' :
          activeTool === 'crop' ? 'cursor-crosshair' : 
          'cursor-default'
        }"
        style="image-rendering: auto;"
      ></canvas>
    </div>
    
    {#if !imageLoaded}
      <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div class="text-center text-text-secondary">
          <div class="text-4xl mb-2">🖼️</div>
          <p class="text-sm">请选择一张图像开始编辑</p>
        </div>
      </div>
    {/if}
  </div>
  
  {#if imageLoaded}
    <!-- 图像信息 -->
    <div class="p-3 bg-surface-elevated border border-border rounded-lg">
      <div class="flex items-center justify-between text-sm">
        <span class="text-text-secondary">图像尺寸:</span>
        <span class="text-text-primary font-mono">{canvasWidth} × {canvasHeight}px</span>
      </div>
      <div class="flex items-center justify-between text-sm mt-2">
        <span class="text-text-secondary">历史记录:</span>
        <span class="text-text-primary">{historyIndex + 1} / {editHistory.length}</span>
      </div>
    </div>
    
    <!-- 提示信息 -->
    <div class="p-3 bg-primary/10 border border-primary/30 rounded-lg">
      <p class="text-xs text-text-secondary">
        💡 <strong>提示:</strong> 使用裁剪工具时，在画布上拖动鼠标选择区域。旋转和缩放工具会立即应用到整个图像。所有操作都支持撤销/重做。
      </p>
    </div>
  {/if}
</div>

<style>
  canvas {
    display: block;
  }
</style>
