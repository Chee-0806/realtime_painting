import { writable, derived } from 'svelte/store';

// Error handling types
export enum ErrorType {
  NETWORK = 'network',
  API = 'api',
  VALIDATION = 'validation',
  MODEL = 'model',
  GENERATION = 'generation',
  WEBSOCKET = 'websocket'
}

export interface AppError {
  type: ErrorType;
  message: string;
  details?: string;
  recoverable: boolean;
  suggestions?: string[];
}

export interface ErrorState {
  hasError: boolean;
  error: AppError | null;
}

// Error state store
export const errorState = writable<ErrorState>({
  hasError: false,
  error: null
});

// Helper functions for error state
export function setError(error: AppError) {
  errorState.set({
    hasError: true,
    error
  });
}

export function clearError() {
  errorState.set({
    hasError: false,
    error: null
  });
}

export const pipelineValues = writable<Record<string, any>>({});

export function getPipelineValues(): Record<string, any> {
  let values: Record<string, any> = {};
  pipelineValues.subscribe((v) => {
    values = v;
  })();
  return values;
}

export function getDebouncedPipelineValues(): Record<string, any> {
  let values: Record<string, any> = {};
  deboucedPipelineValues.subscribe((v) => {
    values = v;
  })();
  return values;
}

// 防抖的管道值，用于实时生成时减少请求频率
let debounceTimer: ReturnType<typeof setTimeout> | null = null;
let debouncedValue: Record<string, any> = {};

export const deboucedPipelineValues = derived(
  pipelineValues,
  ($pipelineValues, set) => {
    // 立即更新当前值
    debouncedValue = $pipelineValues;
    
    // 清除之前的定时器
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    
    // 设置新的定时器，300ms后更新store
    debounceTimer = setTimeout(() => {
      set(debouncedValue);
    }, 300);
  },
  {}
);

