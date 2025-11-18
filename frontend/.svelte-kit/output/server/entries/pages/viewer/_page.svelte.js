import { c as create_ssr_component, o as onDestroy, b as add_attribute, d as escape } from "../../../chunks/ssr.js";
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let imageUrl = "";
  let userIdInput = "";
  let connectionStatus = "未连接";
  onDestroy(() => {
  });
  return `${$$result.head += `<!-- HEAD_svelte-1v8oqjv_START -->${$$result.title = `<title>实时图像生成查看器 - ArtFlow</title>`, ""}<!-- HEAD_svelte-1v8oqjv_END -->`, ""} <main class="min-h-screen bg-surface"><div class="container mx-auto max-w-7xl px-4 py-6"><div class="mb-6" data-svelte-h="svelte-t0puq1"><h1 class="title">👁️ 查看器</h1> <p class="subtitle">实时查看画板生成的AI图像结果</p></div> <div class="card">${`<div class="card-compact mb-6"><label for="userIdInput" class="label" data-svelte-h="svelte-525t44">请输入画板应用的 User ID：</label> <div class="flex gap-3"><input id="userIdInput" type="text" placeholder="从画板应用复制 User ID" class="input flex-1"${add_attribute("value", userIdInput, 0)}> <button ${!userIdInput.trim() || !!imageUrl ? "disabled" : ""} class="btn-primary">连接</button></div> <p class="text-xs text-text-tertiary mt-3" data-svelte-h="svelte-1wqhgxw">提示：在画板应用中连接服务器后，会显示 User ID，请复制并粘贴到这里</p></div>`} <div class="flex items-center justify-between mb-6 pb-6 border-b border-border"><div class="flex items-center gap-4"><div class="flex items-center gap-2 px-3 py-2 bg-surface rounded-xl"><div class="${"status-dot " + escape(
    "status-dot-offline",
    true
  )}"></div> <span class="text-sm text-text-secondary">${escape(connectionStatus)}</span></div> ${``}</div> <div class="flex gap-2">${`${``}`}</div></div> ${``} <div class="relative w-full aspect-square bg-black rounded-2xl overflow-hidden border border-border shadow-large">${`<div class="flex items-center justify-center h-full" data-svelte-h="svelte-oh6fzp"><div class="text-center"><p class="text-lg text-text-secondary mb-2">未连接</p> <p class="text-sm text-text-tertiary">请输入 User ID 并连接</p></div></div>`}</div> <div class="mt-6 text-xs text-text-tertiary text-center" data-svelte-h="svelte-3fzpkr"><p>提示: 确保画板应用已连接并开始发送，图像将实时显示在这里</p></div></div></div></main>`;
});
export {
  Page as default
};
