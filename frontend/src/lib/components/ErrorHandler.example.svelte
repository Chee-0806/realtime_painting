<script lang="ts">
  import ErrorHandler from './ErrorHandler.svelte';
  import { setError, clearError, ErrorType } from '$lib/store';
  
  function testNetworkError() {
    setError({
      type: ErrorType.NETWORK,
      message: '网络连接失败',
      details: 'Failed to fetch from http://localhost:7860/api/settings',
      recoverable: true
    });
  }
  
  function testModelError() {
    setError({
      type: ErrorType.MODEL,
      message: '模型加载失败',
      details: 'CUDA out of memory (tried to allocate 2.00 GiB)',
      recoverable: true,
      suggestions: [
        '关闭其他占用显存的程序',
        '尝试使用较小的模型',
        '减少batch size'
      ]
    });
  }
  
  function testWebSocketError() {
    setError({
      type: ErrorType.WEBSOCKET,
      message: 'WebSocket连接断开',
      details: 'Connection closed unexpectedly',
      recoverable: true
    });
  }
  
  function testValidationError() {
    setError({
      type: ErrorType.VALIDATION,
      message: '参数验证失败',
      details: 'steps must be between 1 and 50, got 100',
      recoverable: true
    });
  }
  
  function testGenerationError() {
    setError({
      type: ErrorType.GENERATION,
      message: '图像生成失败',
      details: 'Invalid prompt: contains forbidden words',
      recoverable: true
    });
  }
  
  function testAPIError() {
    setError({
      type: ErrorType.API,
      message: 'API调用失败',
      details: 'HTTP 500: Internal Server Error',
      recoverable: true
    });
  }
  
  function testNonRecoverableError() {
    setError({
      type: ErrorType.MODEL,
      message: '严重错误：模型文件损坏',
      details: 'Checksum verification failed',
      recoverable: false
    });
  }
</script>

<div class="p-8 space-y-4">
  <h1 class="text-2xl font-bold mb-6">ErrorHandler Component Demo</h1>
  
  <div class="grid grid-cols-2 gap-4">
    <button
      on:click={testNetworkError}
      class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
    >
      Test Network Error
    </button>
    
    <button
      on:click={testModelError}
      class="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded"
    >
      Test Model Error
    </button>
    
    <button
      on:click={testWebSocketError}
      class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
    >
      Test WebSocket Error
    </button>
    
    <button
      on:click={testValidationError}
      class="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded"
    >
      Test Validation Error
    </button>
    
    <button
      on:click={testGenerationError}
      class="bg-pink-500 hover:bg-pink-600 text-white px-4 py-2 rounded"
    >
      Test Generation Error
    </button>
    
    <button
      on:click={testAPIError}
      class="bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded"
    >
      Test API Error
    </button>
    
    <button
      on:click={testNonRecoverableError}
      class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded"
    >
      Test Non-Recoverable Error
    </button>
    
    <button
      on:click={clearError}
      class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded"
    >
      Clear Error
    </button>
  </div>
  
  <div class="mt-8 p-4 bg-gray-100 rounded">
    <h2 class="font-semibold mb-2">Usage Example:</h2>
    <pre class="text-sm overflow-x-auto"><code>{`import { setError, ErrorType } from '$lib/store';

// In your component
try {
  await fetch('/api/generate', { ... });
} catch (error) {
  setError({
    type: ErrorType.API,
    message: '生成失败',
    details: error.message,
    recoverable: true
  });
}`}</code></pre>
  </div>
</div>

<ErrorHandler />
