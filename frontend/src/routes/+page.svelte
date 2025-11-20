<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import type { Fields, PipelineInfo } from '$lib/types';
  import { PipelineMode } from '$lib/types';
  import ImagePlayer from '$lib/components/ImagePlayer.svelte';
  import VideoInput from '$lib/components/VideoInput.svelte';
  import Button from '$lib/components/Button.svelte';
  import PipelineOptions from '$lib/components/PipelineOptions.svelte';
  import KeyboardShortcuts from '$lib/components/KeyboardShortcuts.svelte';
  import Spinner from '$lib/icons/spinner.svelte';
  import Warning from '$lib/components/Warning.svelte';
  import ModelManager from '$lib/components/ModelManager.svelte';
  import ErrorHandler from '$lib/components/ErrorHandler.svelte';
  import InpaintingPanel from '$lib/components/InpaintingPanel.svelte';
  import OutpaintingPanel from '$lib/components/OutpaintingPanel.svelte';
  import HiresFixPanel from '$lib/components/HiresFixPanel.svelte';
  import UpscalePanel from '$lib/components/UpscalePanel.svelte';
  import FaceRestorePanel from '$lib/components/FaceRestorePanel.svelte';
  import MultiControlNetPanel from '$lib/components/MultiControlNetPanel.svelte';
  import ImageEditor from '$lib/components/ImageEditor.svelte';
  import XYZPlotPanel from '$lib/components/XYZPlotPanel.svelte';
  import CLIPInterrogatorPanel from '$lib/components/CLIPInterrogatorPanel.svelte';
  import { lcmLiveStatus, lcmLiveActions, LCMLiveStatus } from '$lib/lcmLive';
  import { mediaStreamActions, onFrameChangeStore } from '$lib/mediaStream';
  import { getPipelineValues, getDebouncedPipelineValues, pipelineValues, setError, ErrorType } from '$lib/store';
  import { keyboardManager } from '$lib/utils/keyboard';
  
  let showShortcuts = false;
  let showParamsPanel = false;
  let showModelManager = true;
  let showInputSource = true;
  let showControls = true;
  let showAdvancedFeatures = false;
  let showInpaintingPanel = false;
  let showOutpaintingPanel = false;
  let showHiresFixPanel = false;
  let showUpscalePanel = false;
  let showFaceRestorePanel = false;
  let showMultiControlNetPanel = false;
  let showImageEditorPanel = false;
  let showXYZPlotPanel = false;
  let showCLIPInterrogatorPanel = false;

  let pipelineParams: Fields;
  let pipelineInfo: PipelineInfo;
  let pageContent: string;
  let isImageMode: boolean = false;
  let maxQueueSize: number = 0;
  let currentQueueSize: number = 0;
  let queueCheckerRunning: boolean = false;
  let warningMessage: string = '';
  let unregisterShortcuts: (() => void)[] = [];

  onMount(() => {
    getSettings();
    
    const unregisterHelp = keyboardManager.register(
      { key: '?', shift: true },
      (e) => {
        showShortcuts = !showShortcuts;
        return false;
      }
    );
    
    unregisterShortcuts = [unregisterHelp];
  });
  
  onDestroy(() => {
    unregisterShortcuts.forEach(unregister => unregister());
  });

  async function getSettings() {
    const settings = await fetch('/api/settings').then((r) => r.json());
    pipelineParams = settings.input_params.properties;
    pipelineInfo = settings.info.properties;
    isImageMode = pipelineInfo.input_mode.default === PipelineMode.IMAGE;
    maxQueueSize = settings.max_queue_size;
    pageContent = settings.page_content;
    
    const initialValues: Record<string, any> = {};
    for (const [key, field] of Object.entries(pipelineParams)) {
      initialValues[key] = field.default;
    }
    pipelineValues.set(initialValues);
    
    toggleQueueChecker(true);
  }
  
  function toggleQueueChecker(start: boolean) {
    queueCheckerRunning = start && maxQueueSize > 0;
    if (start) {
      getQueueSize();
    }
  }
  
  async function getQueueSize() {
    if (!queueCheckerRunning) {
      return;
    }
    const data = await fetch('/api/queue').then((r) => r.json());
    currentQueueSize = data.queue_size;
    setTimeout(getQueueSize, 10000);
  }

  function getStreamData() {
    if (isImageMode) {
      const blob = $onFrameChangeStore?.blob;
      if (!blob) {
        return [getPipelineValues(), null];
      }
      return [getPipelineValues(), blob];
    } else {
      return [getDebouncedPipelineValues()];
    }
  }

  $: isLCMRunning = $lcmLiveStatus !== LCMLiveStatus.DISCONNECTED;
  $: if ($lcmLiveStatus === LCMLiveStatus.TIMEOUT) {
    warningMessage = 'Session timed out. Please try again.';
  }
  
  let disabled = false;
  async function toggleLcmLive() {
    try {
      if (!isLCMRunning) {
        if (isImageMode) {
          const blob = $onFrameChangeStore?.blob;
          if (!blob) {
            setError({
              type: ErrorType.VALIDATION,
              message: '请先启动摄像头',
              details: '点击"输入源"区域中的"启动摄像头"按钮。',
              recoverable: true,
              suggestions: ['启动摄像头后再开始生成']
            });
            return;
          }
        }
        disabled = true;
        await lcmLiveActions.start(getStreamData);
        disabled = false;
        toggleQueueChecker(false);
        warningMessage = ''; // 清除之前的警告
      } else {
        lcmLiveActions.stop();
        toggleQueueChecker(true);
      }
    } catch (e) {
      setError({
        type: ErrorType.GENERATION,
        message: '生成失败',
        details: e instanceof Error ? e.message : '未知错误',
        recoverable: true,
        suggestions: ['检查后端服务是否正常运行', '查看浏览器控制台获取更多信息']
      });
      disabled = false;
      toggleQueueChecker(true);
    }
  }
</script>

<svelte:head>
  <title>实时生成 - ArtFlow</title>
  <script
    src="https://cdnjs.cloudflare.com/ajax/libs/iframe-resizer/4.3.9/iframeResizer.contentWindow.min.js"
  ></script>
</svelte:head>

<main class="min-h-screen bg-surface">
  <div class="container mx-auto max-w-7xl px-3 sm:px-4 py-4 sm:py-6">
    <ErrorHandler />
    <Warning bind:message={warningMessage} />
    
    {#if pageContent}
      <section class="mb-4 sm:mb-6 text-center">
        <div class="max-w-none text-text-primary">
          {@html pageContent}
        </div>
      </section>
    {/if}
    
    {#if maxQueueSize > 0}
      <div class="card-compact mb-4 sm:mb-6 bg-warning/10 border-warning/30">
        <p class="text-sm text-text-secondary">
          队列状态: <span class="font-semibold text-text-primary">{currentQueueSize}/{maxQueueSize}</span>
          {#if currentQueueSize > 0}
            <span class="text-warning ml-2">可能影响实时性能</span>
          {/if}
        </p>
      </div>
    {/if}
    
    {#if pipelineParams}
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-6">
        <!-- 左侧：输入和控制 -->
        <div class="lg:col-span-1 space-y-4">
          <!-- 快捷操作栏 -->
          <div class="flex justify-end mb-2">
            <button
              on:click={() => {
                const allExpanded = showInputSource && showModelManager && showControls && showAdvancedFeatures;
                const newState = !allExpanded;
                showInputSource = newState;
                showModelManager = newState;
                showControls = newState;
                showAdvancedFeatures = newState;
              }}
              class="text-xs text-text-tertiary hover:text-text-secondary transition-colors"
              title="全部折叠/展开"
            >
              {(showInputSource && showModelManager && showControls && showAdvancedFeatures) ? '全部折叠' : '全部展开'}
            </button>
          </div>
          <!-- 输入源面板 -->
          <div class="card">
            <button
              on:click={() => showInputSource = !showInputSource}
              class="collapsible-header mb-3"
              aria-expanded={showInputSource}
            >
              <h3 class="heading mb-0">📷 输入源</h3>
              <span class="collapsible-icon {showInputSource ? 'expanded' : 'collapsed'}">
                ▼
              </span>
            </button>
            
            {#if showInputSource}
              <div class="pt-2">
                {#if isImageMode}
                  <VideoInput
                    width={Number(pipelineParams?.width?.default ?? 512)}
                    height={Number(pipelineParams?.height?.default ?? 512)}
                  />
                {:else}
                  <div class="flex flex-col items-center justify-center min-h-[180px] w-full bg-surface-elevated rounded-lg border border-border p-4">
                    <div class="text-4xl mb-2">🎥</div>
                    <p class="text-sm text-text-secondary mb-2">视频模式：无需摄像头输入</p>
                    <p class="text-xs text-text-tertiary text-center">实时生成将使用参数配置进行生成</p>
                  </div>
                {/if}
              </div>
            {/if}
          </div>
          
          <!-- 模型管理面板 -->
          <div class="card">
            <button
              on:click={() => showModelManager = !showModelManager}
              class="collapsible-header mb-3"
              aria-expanded={showModelManager}
            >
              <h3 class="heading mb-0">🎨 模型管理</h3>
              <span class="collapsible-icon {showModelManager ? 'expanded' : 'collapsed'}">
                ▼
              </span>
            </button>
            
            {#if showModelManager}
              <div class="pt-2">
                <ModelManager />
              </div>
            {/if}
          </div>
          
          <!-- 控制面板 -->
          <div class="card">
            <button
              on:click={() => showControls = !showControls}
              class="collapsible-header mb-3"
              aria-expanded={showControls}
            >
              <h3 class="heading mb-0">🎮 控制</h3>
              <span class="collapsible-icon {showControls ? 'expanded' : 'collapsed'}">
                ▼
              </span>
            </button>
            
            {#if showControls}
              <div class="pt-2 flex flex-col gap-3">
                <Button 
                  on:click={toggleLcmLive} 
                  {disabled} 
                  variant={isLCMRunning ? 'danger' : 'success'}
                  classList={'w-full text-lg py-3'}
                >
                  {#if isLCMRunning}
                    ⏹ 停止生成
                  {:else}
                    ▶ 开始生成
                  {/if}
                </Button>
                
                {#if isLCMRunning}
                  <div class="flex items-center gap-2 px-3 py-2 bg-success/10 border border-success/30 rounded-lg">
                    <div class="status-dot status-dot-online"></div>
                    <span class="text-sm text-text-secondary">生成中...</span>
                  </div>
                {/if}
                
                <button
                  on:click={() => showParamsPanel = !showParamsPanel}
                  class="btn-secondary w-full"
                >
                  {showParamsPanel ? '隐藏参数' : '显示参数'}
                </button>
              </div>
            {/if}
          </div>
          
          <!-- 生成参数面板 -->
          {#if showParamsPanel}
            <div class="card">
              <h3 class="heading mb-4">⚙️ 生成参数</h3>
              <PipelineOptions {pipelineParams} />
            </div>
          {/if}
          
          <!-- 高级功能面板 -->
          <div class="card">
            <button
              on:click={() => showAdvancedFeatures = !showAdvancedFeatures}
              class="collapsible-header mb-3"
              aria-expanded={showAdvancedFeatures}
            >
              <h3 class="heading mb-0">🎯 高级功能</h3>
              <span class="collapsible-icon {showAdvancedFeatures ? 'expanded' : 'collapsed'}">
                ▼
              </span>
            </button>
            
            {#if showAdvancedFeatures}
              <div class="pt-2 flex flex-col gap-2">
                <button
                  on:click={() => showInpaintingPanel = !showInpaintingPanel}
                  class="btn-secondary w-full flex items-center justify-center gap-2"
                >
                  <span>🎨</span>
                  <span>{showInpaintingPanel ? '隐藏局部重绘' : '局部重绘'}</span>
                </button>
                
                {#if showInpaintingPanel}
                  <div class="mt-2 p-3 bg-surface-elevated rounded-lg border border-border">
                    <p class="text-xs text-text-tertiary mb-2">
                      💡 提示：局部重绘功能允许您修复或替换图像的特定区域
                    </p>
                  </div>
                {/if}
                
                <button
                  on:click={() => showOutpaintingPanel = !showOutpaintingPanel}
                  class="btn-secondary w-full flex items-center justify-center gap-2"
                >
                  <span>🖼️</span>
                  <span>{showOutpaintingPanel ? '隐藏画布扩展' : '画布扩展'}</span>
                </button>
                
                {#if showOutpaintingPanel}
                  <div class="mt-2 p-3 bg-surface-elevated rounded-lg border border-border">
                    <p class="text-xs text-text-tertiary mb-2">
                      💡 提示：画布扩展功能允许您向任意方向扩展图像边界
                    </p>
                  </div>
                {/if}
                
                <button
                  on:click={() => showHiresFixPanel = !showHiresFixPanel}
                  class="btn-secondary w-full flex items-center justify-center gap-2"
                >
                  <span>🔍</span>
                  <span>{showHiresFixPanel ? '隐藏高分辨率修复' : '高分辨率修复'}</span>
                </button>
                
                {#if showHiresFixPanel}
                  <div class="mt-2 p-3 bg-surface-elevated rounded-lg border border-border">
                    <p class="text-xs text-text-tertiary mb-2">
                      💡 提示：高分辨率修复通过两阶段生成提升图像质量和分辨率
                    </p>
                  </div>
                {/if}
                
                <button
                  on:click={() => showUpscalePanel = !showUpscalePanel}
                  class="btn-secondary w-full flex items-center justify-center gap-2"
                >
                  <span>📐</span>
                  <span>{showUpscalePanel ? '隐藏图像放大' : '图像放大'}</span>
                </button>
                
                {#if showUpscalePanel}
                  <div class="mt-2 p-3 bg-surface-elevated rounded-lg border border-border">
                    <p class="text-xs text-text-tertiary mb-2">
                      💡 提示：使用Real-ESRGAN等算法放大图像并增强细节
                    </p>
                  </div>
                {/if}
                
                <button
                  on:click={() => showFaceRestorePanel = !showFaceRestorePanel}
                  class="btn-secondary w-full flex items-center justify-center gap-2"
                >
                  <span>👤</span>
                  <span>{showFaceRestorePanel ? '隐藏面部修复' : '面部修复'}</span>
                </button>
                
                {#if showFaceRestorePanel}
                  <div class="mt-2 p-3 bg-surface-elevated rounded-lg border border-border">
                    <p class="text-xs text-text-tertiary mb-2">
                      💡 提示：使用CodeFormer或GFPGAN修复和增强面部细节
                    </p>
                  </div>
                {/if}
                
                <button
                  on:click={() => showMultiControlNetPanel = !showMultiControlNetPanel}
                  class="btn-secondary w-full flex items-center justify-center gap-2"
                >
                  <span>🎮</span>
                  <span>{showMultiControlNetPanel ? '隐藏多ControlNet' : '多ControlNet'}</span>
                </button>
                
                {#if showMultiControlNetPanel}
                  <div class="mt-2 p-3 bg-surface-elevated rounded-lg border border-border">
                    <p class="text-xs text-text-tertiary mb-2">
                      💡 提示：同时使用多个ControlNet（最多3个）精确控制图像生成
                    </p>
                  </div>
                {/if}
                
                <button
                  on:click={() => showImageEditorPanel = !showImageEditorPanel}
                  class="btn-secondary w-full flex items-center justify-center gap-2"
                >
                  <span>✂️</span>
                  <span>{showImageEditorPanel ? '隐藏图像编辑' : '图像编辑'}</span>
                </button>
                
                {#if showImageEditorPanel}
                  <div class="mt-2 p-3 bg-surface-elevated rounded-lg border border-border">
                    <p class="text-xs text-text-tertiary mb-2">
                      💡 提示：裁剪、旋转、调整颜色和应用滤镜等图像编辑工具
                    </p>
                  </div>
                {/if}
                
                <button
                  on:click={() => showXYZPlotPanel = !showXYZPlotPanel}
                  class="btn-secondary w-full flex items-center justify-center gap-2"
                >
                  <span>📊</span>
                  <span>{showXYZPlotPanel ? '隐藏参数对比' : '参数对比'}</span>
                </button>
                
                {#if showXYZPlotPanel}
                  <div class="mt-2 p-3 bg-surface-elevated rounded-lg border border-border">
                    <p class="text-xs text-text-tertiary mb-2">
                      💡 提示：XYZ Plot功能允许您对比不同参数组合的生成效果
                    </p>
                  </div>
                {/if}
                
                <button
                  on:click={() => showCLIPInterrogatorPanel = !showCLIPInterrogatorPanel}
                  class="btn-secondary w-full flex items-center justify-center gap-2"
                >
                  <span>🔍</span>
                  <span>{showCLIPInterrogatorPanel ? '隐藏Prompt反推' : 'Prompt反推'}</span>
                </button>
                
                {#if showCLIPInterrogatorPanel}
                  <div class="mt-2 p-3 bg-surface-elevated rounded-lg border border-border">
                    <p class="text-xs text-text-tertiary mb-2">
                      💡 提示：CLIP Interrogator可以从图像中反推生成Prompt
                    </p>
                  </div>
                {/if}
              </div>
            {/if}
          </div>
          
          <!-- Inpainting面板 -->
          {#if showInpaintingPanel}
            <div class="card">
              <div class="flex items-center justify-between mb-4">
                <h3 class="heading mb-0">🎨 局部重绘 (Inpainting)</h3>
                <button
                  on:click={() => showInpaintingPanel = false}
                  class="text-text-tertiary hover:text-text-primary transition-colors"
                  title="关闭"
                >
                  ✕
                </button>
              </div>
              <InpaintingPanel />
            </div>
          {/if}
          
          <!-- Outpainting面板 -->
          {#if showOutpaintingPanel}
            <div class="card">
              <div class="flex items-center justify-between mb-4">
                <h3 class="heading mb-0">🖼️ 画布扩展 (Outpainting)</h3>
                <button
                  on:click={() => showOutpaintingPanel = false}
                  class="text-text-tertiary hover:text-text-primary transition-colors"
                  title="关闭"
                >
                  ✕
                </button>
              </div>
              <OutpaintingPanel />
            </div>
          {/if}
          
          <!-- HiresFix面板 -->
          {#if showHiresFixPanel}
            <div class="card">
              <div class="flex items-center justify-between mb-4">
                <h3 class="heading mb-0">🔍 高分辨率修复 (Hires.fix)</h3>
                <button
                  on:click={() => showHiresFixPanel = false}
                  class="text-text-tertiary hover:text-text-primary transition-colors"
                  title="关闭"
                >
                  ✕
                </button>
              </div>
              <HiresFixPanel />
            </div>
          {/if}
          
          <!-- Upscale面板 -->
          {#if showUpscalePanel}
            <div class="card">
              <div class="flex items-center justify-between mb-4">
                <h3 class="heading mb-0">📐 图像放大 (Upscale)</h3>
                <button
                  on:click={() => showUpscalePanel = false}
                  class="text-text-tertiary hover:text-text-primary transition-colors"
                  title="关闭"
                >
                  ✕
                </button>
              </div>
              <UpscalePanel />
            </div>
          {/if}
          
          <!-- FaceRestore面板 -->
          {#if showFaceRestorePanel}
            <div class="card">
              <div class="flex items-center justify-between mb-4">
                <h3 class="heading mb-0">👤 面部修复 (Face Restore)</h3>
                <button
                  on:click={() => showFaceRestorePanel = false}
                  class="text-text-tertiary hover:text-text-primary transition-colors"
                  title="关闭"
                >
                  ✕
                </button>
              </div>
              <FaceRestorePanel />
            </div>
          {/if}
          
          <!-- MultiControlNet面板 -->
          {#if showMultiControlNetPanel}
            <div class="card">
              <div class="flex items-center justify-between mb-4">
                <h3 class="heading mb-0">🎮 多ControlNet控制</h3>
                <button
                  on:click={() => showMultiControlNetPanel = false}
                  class="text-text-tertiary hover:text-text-primary transition-colors"
                  title="关闭"
                >
                  ✕
                </button>
              </div>
              <MultiControlNetPanel />
            </div>
          {/if}
          
          <!-- ImageEditor面板 -->
          {#if showImageEditorPanel}
            <div class="card">
              <div class="flex items-center justify-between mb-4">
                <h3 class="heading mb-0">✂️ 图像编辑</h3>
                <button
                  on:click={() => showImageEditorPanel = false}
                  class="text-text-tertiary hover:text-text-primary transition-colors"
                  title="关闭"
                >
                  ✕
                </button>
              </div>
              <ImageEditor />
            </div>
          {/if}
          
          <!-- XYZPlot面板 -->
          {#if showXYZPlotPanel}
            <div class="card">
              <div class="flex items-center justify-between mb-4">
                <h3 class="heading mb-0">📊 参数对比 (XYZ Plot)</h3>
                <button
                  on:click={() => showXYZPlotPanel = false}
                  class="text-text-tertiary hover:text-text-primary transition-colors"
                  title="关闭"
                >
                  ✕
                </button>
              </div>
              <XYZPlotPanel />
            </div>
          {/if}
          
          <!-- CLIPInterrogator面板 -->
          {#if showCLIPInterrogatorPanel}
            <div class="card">
              <CLIPInterrogatorPanel
                showCloseButton={false}
                on:close={() => showCLIPInterrogatorPanel = false}
                on:apply={() => {
                  // Prompt已自动应用到pipelineValues
                  console.log('CLIP Prompt已应用');
                }}
              />
              <button
                on:click={() => showCLIPInterrogatorPanel = false}
                class="btn-secondary w-full mt-4"
              >
                关闭面板
              </button>
            </div>
          {/if}
        </div>
        
        <!-- 右侧：输出结果 -->
        <div class="lg:col-span-2">
          <div class="card h-full">
            <h3 class="heading mb-4">✨ 生成结果</h3>
            <ImagePlayer />
          </div>
        </div>
      </div>
    {:else}
      <div class="flex items-center justify-center gap-4 py-48">
        <Spinner classList={'animate-spin opacity-50'} />
        <p class="text-xl text-text-secondary">加载中...</p>
      </div>
    {/if}
  </div>
  
  <KeyboardShortcuts bind:show={showShortcuts} />
  
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
