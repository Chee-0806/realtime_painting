import { c as create_ssr_component, v as validate_component } from "../../../chunks/ssr.js";
import "../../../chunks/PromptTools.svelte_svelte_type_style_lang.js";
import { S as Spinner } from "../../../chunks/spinner.js";
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  return `${$$result.head += `<!-- HEAD_svelte-bjuu77_START -->${$$result.title = `<title>设置 - ArtFlow</title>`, ""}<!-- HEAD_svelte-bjuu77_END -->`, ""} <main class="min-h-screen bg-surface"><div class="container mx-auto max-w-6xl px-4 py-6"><div class="mb-6" data-svelte-h="svelte-xiiswp"><h1 class="title">⚙️ 设置</h1> <p class="subtitle">管理模型和生成参数</p></div> ${`<div class="flex items-center justify-center gap-4 py-48">${validate_component(Spinner, "Spinner").$$render($$result, { classList: "animate-spin opacity-50" }, {}, {})} <p class="text-xl text-text-secondary" data-svelte-h="svelte-bqbwh1">加载中...</p></div>`}</div></main>`;
});
export {
  Page as default
};
