import { c as create_ssr_component, a as subscribe, e as each, b as add_attribute, d as escape, v as validate_component } from "../../chunks/ssr.js";
import { p as page } from "../../chunks/stores.js";
const app = "";
const Navigation_svelte_svelte_type_style_lang = "";
const css = {
  code: "nav.svelte-16hnsr2{box-shadow:0 2px 8px rgba(0, 0, 0, 0.15)}",
  map: null
};
const Navigation = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $page, $$unsubscribe_page;
  $$unsubscribe_page = subscribe(page, (value) => $page = value);
  const navItems = [
    {
      path: "/",
      label: "🎨 实时生成",
      icon: "🎨"
    },
    {
      path: "/canvas",
      label: "✏️ 画板",
      icon: "✏️"
    },
    {
      path: "/settings",
      label: "⚙️ 设置",
      icon: "⚙️"
    },
    {
      path: "/tools",
      label: "🛠️ 工具",
      icon: "🛠️"
    }
  ];
  function isActive(path) {
    if (path === "/") {
      return $page.url.pathname === "/";
    }
    return $page.url.pathname.startsWith(path);
  }
  $$result.css.add(css);
  $$unsubscribe_page();
  return `<nav class="bg-surface-elevated border-b border-border sticky top-0 z-50 svelte-16hnsr2"><div class="container mx-auto max-w-7xl px-4"><div class="flex items-center justify-between h-16"> <div class="flex items-center gap-4"><button class="text-xl font-bold text-text-primary hover:text-primary transition-colors cursor-pointer" type="button" data-svelte-h="svelte-17zx8kh">ArtFlow</button></div>  <div class="flex items-center gap-1">${each(navItems, (item) => {
    return `<a${add_attribute("href", item.path, 0)} class="${"px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 " + escape(
      isActive(item.path) ? "bg-primary text-white" : "text-text-secondary hover:text-text-primary hover:bg-surface-hover",
      true
    )}">${escape(item.label)} </a>`;
  })}</div>  <div class="flex items-center gap-2">${slots.actions ? slots.actions({}) : ``}</div></div></div> </nav>`;
});
const Layout = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  return `${validate_component(Navigation, "Navigation").$$render($$result, {}, {}, {
    default: () => {
      return `${slots.actions ? slots.actions({}) : ``}`;
    }
  })} ${slots.default ? slots.default({}) : ``}`;
});
export {
  Layout as default
};
