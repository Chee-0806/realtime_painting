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

  let pipelineParams: Fields | null = null;
  let pipelineInfo: PipelineInfo | null = null;
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
    // 使用实时生成专用接口
    const settings = await fetch('/api/realtime/settings').then((r) => r.json());
    const params = settings.input_params.properties as Fields;
    pipelineParams = params;
    const info = settings.info.properties as PipelineInfo;
    pipelineInfo = info;
    isImageMode = info.input_mode.default === PipelineMode.IMAGE;
    maxQueueSize = settings.max_queue_size;
    pageContent = settings.page_content;
    
    const initialValues: Record<string, any> = {};
    for (const key of Object.keys(params)) {
      const field = params[key];
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
    // 使用实时生成专用接口
    const data = await fetch('/api/realtime/queue').then((r) => r.json());
    currentQueueSize = data.queue_size;
    setTimeout(getQueueSize, 10000);
  }

  function buildParams(source: Record<string, any>, defaults: Fields) {
    const params: Record<string, any> = {};
    for (const key of Object.keys(defaults)) {
      const field = defaults[key];
      params[key] = source[key] ?? field.default;
    }
    return params;
  }

  function getStreamPayload() {
    const defaults = pipelineParams;
    if (!defaults) {
      throw new Error('Pipeline settings not ready.');
    }
    const values = isImageMode ? getPipelineValues() : getDebouncedPipelineValues();
    const params = buildParams(values, defaults);
    const blob = isImageMode ? $onFrameChangeStore?.blob ?? null : null;
    return { params, blob };
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
        await lcmLiveActions.start(getStreamPayload);
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
          
          <!-- 高级功能面板 - 已禁用 -->
          <div class="card opacity-50">
            <button
              disabled
              class="collapsible-header mb-3 cursor-not-allowed"
              title="高级功能已禁用"
            >
              <h3 class="heading mb-0 text-text-tertiary">🎯 高级功能</h3>
              <span class="text-xs text-text-tertiary">(已禁用)</span>
            </button>

            <div class="pt-2">
              <div class="p-3 bg-surface-elevated/50 rounded-lg border border-border text-center">
                <p class="text-sm text-text-tertiary">
                  ⚠️ 所有高级功能已暂时禁用
                </p>
                <p class="text-xs text-text-tertiary mt-1">
                  包括局部重绘、画布扩展、高分辨率修复等功能
                </p>
              </div>
            </div>
          </div>
          <!-- 高级功能面板已全部禁用，不再显示任何高级功能界面 -->
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
