import { c as create_ssr_component, v as validate_component } from "../../../chunks/ssr.js";
const InpaintingTools = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  return `<div class="space-y-4" data-svelte-h="svelte-115vnzf"><div class="text-center py-12"><div class="text-6xl mb-4">🎨</div> <h3 class="text-xl font-semibold text-text-primary mb-2">局部重绘工具</h3> <p class="text-text-secondary">此功能正在开发中...</p></div></div>`;
});
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  return `${$$result.head += `<!-- HEAD_svelte-1jj9wzr_START -->${$$result.title = `<title>工具 - ArtFlow</title>`, ""}<!-- HEAD_svelte-1jj9wzr_END -->`, ""} <main class="min-h-screen bg-surface"><div class="container mx-auto max-w-6xl px-4 py-6"><div class="mb-6" data-svelte-h="svelte-wj1gyw"><h1 class="title">🛠️ 高级工具</h1> <p class="subtitle">图像编辑和处理工具集合</p></div> <div class="card">${validate_component(InpaintingTools, "InpaintingTools").$$render($$result, {}, {}, {})}</div></div></main>`;
});
export {
  Page as default
};
