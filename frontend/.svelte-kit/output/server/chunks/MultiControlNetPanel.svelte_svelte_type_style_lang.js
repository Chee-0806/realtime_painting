import { c as create_ssr_component, e as each, d as escape, a as subscribe } from "./ssr.js";
import { e as errorState, E as ErrorType } from "./PromptTools.svelte_svelte_type_style_lang.js";
const KeyboardShortcuts = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { show = false } = $$props;
  const shortcuts = [
    {
      key: "Shift + ?",
      description: "显示/隐藏快捷键帮助"
    }
  ];
  if ($$props.show === void 0 && $$bindings.show && show !== void 0)
    $$bindings.show(show);
  return `${show ? `<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="dialog" aria-modal="true" aria-labelledby="shortcuts-title"><div class="card max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto" role="document"><div class="flex items-center justify-between mb-6"><h2 id="shortcuts-title" class="title" data-svelte-h="svelte-166uzre">⌨️ 快捷键</h2> <button class="btn-ghost" type="button" aria-label="关闭" data-svelte-h="svelte-1xeeokb">✕</button></div> <div class="space-y-4">${each(shortcuts, (shortcut) => {
    return `<div class="flex items-center justify-between py-2 border-b border-border"><span class="text-text-secondary">${escape(shortcut.description)}</span> <kbd class="px-3 py-1 bg-surface-elevated border border-border rounded-lg text-sm font-mono text-text-primary">${escape(shortcut.key)}</kbd> </div>`;
  })}</div> <div class="mt-6 pt-4 border-t border-border"><button class="btn-secondary w-full" type="button" data-svelte-h="svelte-1jm07t9">关闭</button></div></div></div>` : ``}`;
});
const ErrorHandler_svelte_svelte_type_style_lang = "";
const css = {
  code: "@keyframes svelte-1b6tmen-slide-in{from{transform:translateX(100%);opacity:0}to{transform:translateX(0);opacity:1}}.animate-slide-in.svelte-1b6tmen{animation:svelte-1b6tmen-slide-in 0.3s ease-out}",
  map: null
};
const ErrorHandler = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let suggestions;
  let errorIcon;
  let errorTitle;
  let $errorState, $$unsubscribe_errorState;
  $$unsubscribe_errorState = subscribe(errorState, (value) => $errorState = value);
  function getErrorSuggestions(error) {
    if (error.suggestions && error.suggestions.length > 0) {
      return error.suggestions;
    }
    switch (error.type) {
      case ErrorType.MODEL:
        return [
          "检查模型路径是否正确",
          "确保有足够的显存",
          "尝试重启服务"
        ];
      case ErrorType.WEBSOCKET:
        return [
          "检查网络连接",
          "刷新页面重新连接",
          "查看后端日志"
        ];
      case ErrorType.NETWORK:
        return [
          "检查网络连接",
          "确认后端服务正在运行",
          "检查防火墙设置"
        ];
      case ErrorType.API:
        return [
          "检查请求参数是否正确",
          "查看后端日志获取详细信息",
          "尝试重新提交请求"
        ];
      case ErrorType.VALIDATION:
        return [
          "检查输入参数是否符合要求",
          "确保所有必填字段已填写",
          "参考文档了解参数范围"
        ];
      case ErrorType.GENERATION:
        return [
          "尝试调整生成参数",
          "检查Prompt是否合理",
          "确保模型已正确加载"
        ];
      default:
        return ["请重试或联系技术支持"];
    }
  }
  function getErrorIcon(type) {
    switch (type) {
      case ErrorType.MODEL:
        return "🎨";
      case ErrorType.WEBSOCKET:
        return "🔌";
      case ErrorType.NETWORK:
        return "🌐";
      case ErrorType.API:
        return "⚙️";
      case ErrorType.VALIDATION:
        return "✏️";
      case ErrorType.GENERATION:
        return "🖼️";
      default:
        return "⚠️";
    }
  }
  function getErrorTitle(type) {
    switch (type) {
      case ErrorType.MODEL:
        return "模型错误";
      case ErrorType.WEBSOCKET:
        return "WebSocket连接错误";
      case ErrorType.NETWORK:
        return "网络错误";
      case ErrorType.API:
        return "API错误";
      case ErrorType.VALIDATION:
        return "参数验证错误";
      case ErrorType.GENERATION:
        return "生成错误";
      default:
        return "错误";
    }
  }
  $$result.css.add(css);
  suggestions = $errorState.error ? getErrorSuggestions($errorState.error) : [];
  errorIcon = $errorState.error ? getErrorIcon($errorState.error.type) : "⚠️";
  errorTitle = $errorState.error ? getErrorTitle($errorState.error.type) : "错误";
  $$unsubscribe_errorState();
  return `${$errorState.hasError && $errorState.error ? `<div class="fixed top-4 right-4 z-50 max-w-md animate-slide-in svelte-1b6tmen"><div class="bg-red-50 border-l-4 border-red-500 rounded-lg shadow-lg p-4"><div class="flex items-start gap-3"><span class="text-2xl flex-shrink-0">${escape(errorIcon)}</span> <div class="flex-1 min-w-0"><div class="flex items-start justify-between gap-2 mb-2"><h4 class="font-semibold text-red-800">${escape(errorTitle)}</h4> <button class="text-red-500 hover:text-red-700 transition-colors flex-shrink-0" aria-label="关闭错误提示" data-svelte-h="svelte-146heoo"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></button></div> <p class="text-red-700 text-sm mb-2">${escape($errorState.error.message)}</p> ${$errorState.error.details ? `<p class="text-red-600 text-xs mb-3 font-mono bg-red-100 p-2 rounded">${escape($errorState.error.details)}</p>` : ``} ${suggestions.length > 0 ? `<div class="mt-3 pt-3 border-t border-red-200"><p class="text-xs font-semibold text-red-800 mb-2" data-svelte-h="svelte-9nlrif">💡 建议:</p> <ul class="text-xs text-red-700 space-y-1">${each(suggestions, (suggestion) => {
    return `<li class="flex items-start gap-2"><span class="text-red-400 flex-shrink-0" data-svelte-h="svelte-1rlqugl">•</span> <span>${escape(suggestion)}</span> </li>`;
  })}</ul></div>` : ``} ${$errorState.error.recoverable ? `<div class="mt-3 pt-3 border-t border-red-200"><button class="text-xs bg-red-500 hover:bg-red-600 text-white px-3 py-1.5 rounded transition-colors" data-svelte-h="svelte-153fhqe">我知道了</button></div>` : ``}</div></div></div></div>` : ``}`;
});
const ControlNetItem_svelte_svelte_type_style_lang = "";
const MultiControlNetPanel_svelte_svelte_type_style_lang = "";
export {
  ErrorHandler as E,
  KeyboardShortcuts as K
};
