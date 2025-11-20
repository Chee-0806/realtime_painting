<script lang="ts">
  import { errorState, clearError, ErrorType, type AppError } from '$lib/store';
  
  function dismissError() {
    clearError();
  }
  
  function getErrorSuggestions(error: AppError): string[] {
    if (error.suggestions && error.suggestions.length > 0) {
      return error.suggestions;
    }
    
    switch (error.type) {
      case ErrorType.MODEL:
        return [
          '检查模型路径是否正确',
          '确保有足够的显存',
          '尝试重启服务'
        ];
      case ErrorType.WEBSOCKET:
        return [
          '检查网络连接',
          '刷新页面重新连接',
          '查看后端日志'
        ];
      case ErrorType.NETWORK:
        return [
          '检查网络连接',
          '确认后端服务正在运行',
          '检查防火墙设置'
        ];
      case ErrorType.API:
        return [
          '检查请求参数是否正确',
          '查看后端日志获取详细信息',
          '尝试重新提交请求'
        ];
      case ErrorType.VALIDATION:
        return [
          '检查输入参数是否符合要求',
          '确保所有必填字段已填写',
          '参考文档了解参数范围'
        ];
      case ErrorType.GENERATION:
        return [
          '尝试调整生成参数',
          '检查Prompt是否合理',
          '确保模型已正确加载'
        ];
      default:
        return ['请重试或联系技术支持'];
    }
  }
  
  function getErrorIcon(type: ErrorType): string {
    switch (type) {
      case ErrorType.MODEL:
        return '🎨';
      case ErrorType.WEBSOCKET:
        return '🔌';
      case ErrorType.NETWORK:
        return '🌐';
      case ErrorType.API:
        return '⚙️';
      case ErrorType.VALIDATION:
        return '✏️';
      case ErrorType.GENERATION:
        return '🖼️';
      default:
        return '⚠️';
    }
  }
  
  function getErrorTitle(type: ErrorType): string {
    switch (type) {
      case ErrorType.MODEL:
        return '模型错误';
      case ErrorType.WEBSOCKET:
        return 'WebSocket连接错误';
      case ErrorType.NETWORK:
        return '网络错误';
      case ErrorType.API:
        return 'API错误';
      case ErrorType.VALIDATION:
        return '参数验证错误';
      case ErrorType.GENERATION:
        return '生成错误';
      default:
        return '错误';
    }
  }
  
  $: suggestions = $errorState.error ? getErrorSuggestions($errorState.error) : [];
  $: errorIcon = $errorState.error ? getErrorIcon($errorState.error.type) : '⚠️';
  $: errorTitle = $errorState.error ? getErrorTitle($errorState.error.type) : '错误';
</script>

{#if $errorState.hasError && $errorState.error}
  <div class="fixed top-4 right-4 z-50 max-w-md animate-slide-in">
    <div class="bg-red-50 border-l-4 border-red-500 rounded-lg shadow-lg p-4">
      <div class="flex items-start gap-3">
        <span class="text-2xl flex-shrink-0">{errorIcon}</span>
        <div class="flex-1 min-w-0">
          <div class="flex items-start justify-between gap-2 mb-2">
            <h4 class="font-semibold text-red-800">{errorTitle}</h4>
            <button
              on:click={dismissError}
              class="text-red-500 hover:text-red-700 transition-colors flex-shrink-0"
              aria-label="关闭错误提示"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <p class="text-red-700 text-sm mb-2">{$errorState.error.message}</p>
          
          {#if $errorState.error.details}
            <p class="text-red-600 text-xs mb-3 font-mono bg-red-100 p-2 rounded">
              {$errorState.error.details}
            </p>
          {/if}
          
          {#if suggestions.length > 0}
            <div class="mt-3 pt-3 border-t border-red-200">
              <p class="text-xs font-semibold text-red-800 mb-2">💡 建议:</p>
              <ul class="text-xs text-red-700 space-y-1">
                {#each suggestions as suggestion}
                  <li class="flex items-start gap-2">
                    <span class="text-red-400 flex-shrink-0">•</span>
                    <span>{suggestion}</span>
                  </li>
                {/each}
              </ul>
            </div>
          {/if}
          
          {#if $errorState.error.recoverable}
            <div class="mt-3 pt-3 border-t border-red-200">
              <button
                on:click={dismissError}
                class="text-xs bg-red-500 hover:bg-red-600 text-white px-3 py-1.5 rounded transition-colors"
              >
                我知道了
              </button>
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  @keyframes slide-in {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  .animate-slide-in {
    animation: slide-in 0.3s ease-out;
  }
</style>
