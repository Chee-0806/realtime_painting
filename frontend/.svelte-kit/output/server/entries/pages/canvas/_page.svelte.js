import { c as create_ssr_component, e as each, b as add_attribute, d as escape, a as subscribe, o as onDestroy, v as validate_component } from "../../../chunks/ssr.js";
import { p as pipelineValues } from "../../../chunks/PromptTools.svelte_svelte_type_style_lang.js";
import { E as ErrorHandler, K as KeyboardShortcuts } from "../../../chunks/MultiControlNetPanel.svelte_svelte_type_style_lang.js";
const ModelManager = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let models = [];
  let vaes = [];
  let schedulers = [];
  return `<div class="space-y-4"> ${``}  ${``}  <div class="space-y-2"><label for="model-select" class="block text-sm font-medium text-text-primary" data-svelte-h="svelte-1ptzy1b">模型</label> <select id="model-select" ${""} class="w-full px-3 py-2 bg-surface-elevated border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50">${each(models, (model) => {
    return `<option${add_attribute("value", model.id, 0)}>${escape(model.name)} ${escape(model.loaded ? "(当前)" : "")} </option>`;
  })}</select></div>  <div class="space-y-2"><label for="vae-select" class="block text-sm font-medium text-text-primary" data-svelte-h="svelte-13pu0rc">VAE</label> <select id="vae-select" ${""} class="w-full px-3 py-2 bg-surface-elevated border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50">${each(vaes, (vae) => {
    return `<option${add_attribute("value", vae.id, 0)}>${escape(vae.name)} ${escape(vae.loaded ? "(当前)" : "")} </option>`;
  })}</select></div>  <div class="space-y-2"><label for="scheduler-select" class="block text-sm font-medium text-text-primary" data-svelte-h="svelte-jehhn9">采样器</label> <select id="scheduler-select" ${""} class="w-full px-3 py-2 bg-surface-elevated border border-border rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50">${each(schedulers, (scheduler) => {
    return `<option${add_attribute("value", scheduler.id, 0)}>${escape(scheduler.name)} ${escape(scheduler.loaded ? "(当前)" : "")} </option>`;
  })}</select> ${``}</div>  ${``}</div>`;
});
const DEBOUNCE_DELAY = 100;
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $pipelineValues, $$unsubscribe_pipelineValues;
  $$unsubscribe_pipelineValues = subscribe(pipelineValues, (value) => $pipelineValues = value);
  let showShortcuts = false;
  let canvas;
  let color = "#000000";
  let brushSize = 5;
  let multiControlNetConfig = [];
  let isSending = false;
  let connectionStatus = "未连接";
  let isConnected = false;
  let canvasChanged = false;
  let debounceTimer = null;
  let animationFrameId = null;
  let lastPrompt = "";
  let lastNegativePrompt = "";
  function scheduleSend() {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }
    debounceTimer = setTimeout(
      () => {
        animationFrameId = requestAnimationFrame(() => {
          if (isSending && isConnected && canvasChanged) {
            sendFrame();
            canvasChanged = false;
          }
          animationFrameId = null;
        });
        debounceTimer = null;
      },
      DEBOUNCE_DELAY
    );
  }
  let unregisterShortcuts = [];
  async function sendFrame() {
    {
      return;
    }
  }
  function stopSending() {
    isSending = false;
    if (debounceTimer) {
      clearTimeout(debounceTimer);
      debounceTimer = null;
    }
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }
    canvasChanged = false;
  }
  onDestroy(() => {
    stopSending();
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
    }
    unregisterShortcuts.forEach((unregister) => unregister());
  });
  let $$settled;
  let $$rendered;
  let previous_head = $$result.head;
  do {
    $$settled = true;
    $$result.head = previous_head;
    {
      {
        if (multiControlNetConfig.length > 0) {
          console.log(`🎮 MultiControlNet状态: ${multiControlNetConfig.length}个ControlNet已配置`);
          multiControlNetConfig.forEach((cn, index) => {
            console.log(`  - ControlNet ${index + 1}: 类型=${cn.type}, 权重=${cn.weight}`);
          });
        }
      }
    }
    {
      {
        const currentPrompt = $pipelineValues.prompt || "";
        const currentNegativePrompt = $pipelineValues.negative_prompt || "";
        if (isSending && isConnected && (currentPrompt !== lastPrompt || currentNegativePrompt !== lastNegativePrompt)) {
          lastPrompt = currentPrompt;
          lastNegativePrompt = currentNegativePrompt;
          canvasChanged = true;
          scheduleSend();
        } else {
          if (!lastPrompt && currentPrompt) {
            lastPrompt = currentPrompt;
          }
          if (!lastNegativePrompt && currentNegativePrompt) {
            lastNegativePrompt = currentNegativePrompt;
          }
        }
      }
    }
    $$rendered = `${$$result.head += `<!-- HEAD_svelte-xwmalx_START -->${$$result.title = `<title>画板 - ArtFlow</title>`, ""}<!-- HEAD_svelte-xwmalx_END -->`, ""} <main class="min-h-screen bg-surface"><div class="container mx-auto max-w-7xl px-4 py-6">${validate_component(ErrorHandler, "ErrorHandler").$$render($$result, {}, {}, {})} <div class="mb-6" data-svelte-h="svelte-1wroi24"><h1 class="title">✏️ 画板</h1> <p class="subtitle">手绘输入，实时生成AI图像</p></div> <div class="card"> <div class="flex flex-wrap items-center gap-3 mb-6 pb-6 border-b border-border"> <div class="flex items-center gap-3 p-2 bg-surface rounded-xl"><span class="text-sm text-text-secondary whitespace-nowrap" data-svelte-h="svelte-1oo0j11">画笔颜色:</span> <input type="color" class="w-10 h-10 border border-border rounded-lg cursor-pointer bg-transparent" aria-label="画笔颜色"${add_attribute("value", color, 0)}> <div class="flex items-center gap-2"><span class="text-sm text-text-secondary whitespace-nowrap" data-svelte-h="svelte-1u1wdtu">大小:</span> <input type="range" min="1" max="50" class="w-20 h-2 bg-surface rounded-lg appearance-none cursor-pointer accent-primary" aria-label="画笔大小"${add_attribute("value", brushSize, 0)}> <span class="text-sm text-text-secondary w-8 font-mono">${escape(brushSize)}</span></div></div>  <div class="flex items-center gap-2"><button ${"disabled"} class="btn-secondary" title="撤销 (Ctrl+Z)">↶ 撤销</button> <button ${"disabled"} class="btn-secondary" title="重做 (Ctrl+Shift+Z)">↷ 重做</button> <button class="btn-secondary" title="清空画布 (Delete)" data-svelte-h="svelte-de72k8">清空</button></div>  <div class="flex items-center gap-2"><button class="${"btn-secondary " + escape(multiControlNetConfig.length > 0 ? "border-primary" : "", true)}" title="配置多个ControlNet">🎮 MultiControlNet ${escape(multiControlNetConfig.length > 0 ? `(${multiControlNetConfig.length})` : "")}</button></div>  <div class="flex items-center gap-2"><button class="btn-primary">${escape("连接服务器")}</button> ${``} <button ${"disabled"} class="btn-success">开始发送</button> <button ${!isSending ? "disabled" : ""} class="btn-danger">停止发送</button></div>  <div class="ml-auto flex items-center gap-2 px-3 py-2 bg-surface rounded-xl"><div class="${"status-dot " + escape("status-dot-offline", true)}"></div> <span class="text-sm text-text-secondary">${escape(connectionStatus)}</span></div>  <div class="flex items-center gap-2"><button class="btn-secondary">${escape("显示参数")}</button> <button class="btn-secondary">${escape("CLIP反推")}</button></div></div>  <div class="card-compact mb-6">${validate_component(ModelManager, "ModelManager").$$render($$result, {}, {}, {})}</div> ${``}  ${``}  ${``}  <div class="flex justify-center my-6"><canvas width="512" height="512" class="border-2 border-primary rounded-2xl cursor-crosshair bg-white shadow-large"${add_attribute("this", canvas, 0)}></canvas></div>  <div class="mt-6 text-xs text-text-tertiary text-center space-y-1"><p data-svelte-h="svelte-2vhs38">提示: 绘制完成后点击&quot;连接服务器&quot;，然后点击&quot;开始发送&quot;以实时发送画布内容到 AI 生成服务</p> <p>查看结果: 
        <a href="${"/viewer?userId=" + escape("", true)}" class="text-primary hover:text-primary-light underline">/viewer?userId=${escape("你的UserID")}</a></p></div></div>  ${validate_component(KeyboardShortcuts, "KeyboardShortcuts").$$render(
      $$result,
      { show: showShortcuts },
      {
        show: ($$value) => {
          showShortcuts = $$value;
          $$settled = false;
        }
      },
      {}
    )}  <div class="fixed bottom-6 right-6"><button class="btn-ghost shadow-medium" title="快捷键帮助 (Shift+?)" data-svelte-h="svelte-1lbjoky">⌨️ 快捷键</button></div></div></main>`;
  } while (!$$settled);
  $$unsubscribe_pipelineValues();
  return $$rendered;
});
export {
  Page as default
};
