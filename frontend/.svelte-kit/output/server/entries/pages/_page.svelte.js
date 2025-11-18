import { c as create_ssr_component, d as escape, a as subscribe, o as onDestroy, v as validate_component } from "../../chunks/ssr.js";
import { w as writable } from "../../chunks/index.js";
import "../../chunks/PromptTools.svelte_svelte_type_style_lang.js";
import { E as ErrorHandler, K as KeyboardShortcuts } from "../../chunks/MultiControlNetPanel.svelte_svelte_type_style_lang.js";
import { S as Spinner } from "../../chunks/spinner.js";
var LCMLiveStatus = /* @__PURE__ */ ((LCMLiveStatus2) => {
  LCMLiveStatus2["DISCONNECTED"] = "disconnected";
  LCMLiveStatus2["CONNECTING"] = "connecting";
  LCMLiveStatus2["CONNECTED"] = "connected";
  LCMLiveStatus2["RUNNING"] = "running";
  LCMLiveStatus2["TIMEOUT"] = "timeout";
  LCMLiveStatus2["ERROR"] = "error";
  return LCMLiveStatus2;
})(LCMLiveStatus || {});
const lcmLiveStatus = writable(
  "disconnected"
  /* DISCONNECTED */
);
const onFrameChangeStore = writable({
  blob: null,
  timestamp: 0
});
const Warning = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let show;
  let { message = "" } = $$props;
  if ($$props.message === void 0 && $$bindings.message && message !== void 0)
    $$bindings.message(message);
  show = message.length > 0;
  return `${show ? `<div class="card-compact mb-6 bg-warning/10 border-warning/30"><div class="flex items-center gap-2"><span class="text-warning text-lg" data-svelte-h="svelte-1gude3d">⚠️</span> <p class="text-sm text-text-primary">${escape(message)}</p></div></div>` : ``}`;
});
const InpaintingPanel_svelte_svelte_type_style_lang = "";
const OutpaintingPanel_svelte_svelte_type_style_lang = "";
const HiresFixPanel_svelte_svelte_type_style_lang = "";
const UpscalePanel_svelte_svelte_type_style_lang = "";
const FaceRestorePanel_svelte_svelte_type_style_lang = "";
const ImageEditor_svelte_svelte_type_style_lang = "";
const XYZPlotResult_svelte_svelte_type_style_lang = "";
const XYZPlotPanel_svelte_svelte_type_style_lang = "";
const CLIPInterrogatorPanel_svelte_svelte_type_style_lang = "";
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$unsubscribe_onFrameChangeStore;
  let $lcmLiveStatus, $$unsubscribe_lcmLiveStatus;
  $$unsubscribe_onFrameChangeStore = subscribe(onFrameChangeStore, (value) => value);
  $$unsubscribe_lcmLiveStatus = subscribe(lcmLiveStatus, (value) => $lcmLiveStatus = value);
  let showShortcuts = false;
  let warningMessage = "";
  let unregisterShortcuts = [];
  onDestroy(() => {
    unregisterShortcuts.forEach((unregister) => unregister());
  });
  let $$settled;
  let $$rendered;
  let previous_head = $$result.head;
  do {
    $$settled = true;
    $$result.head = previous_head;
    $lcmLiveStatus !== LCMLiveStatus.DISCONNECTED;
    {
      if ($lcmLiveStatus === LCMLiveStatus.TIMEOUT) {
        warningMessage = "Session timed out. Please try again.";
      }
    }
    $$rendered = `${$$result.head += `<!-- HEAD_svelte-1mxwd5t_START -->${$$result.title = `<title>实时生成 - ArtFlow</title>`, ""}<script src="https://cdnjs.cloudflare.com/ajax/libs/iframe-resizer/4.3.9/iframeResizer.contentWindow.min.js" data-svelte-h="svelte-1oi43ze"><\/script><!-- HEAD_svelte-1mxwd5t_END -->`, ""} <main class="min-h-screen bg-surface"><div class="container mx-auto max-w-7xl px-3 sm:px-4 py-4 sm:py-6">${validate_component(ErrorHandler, "ErrorHandler").$$render($$result, {}, {}, {})} ${validate_component(Warning, "Warning").$$render(
      $$result,
      { message: warningMessage },
      {
        message: ($$value) => {
          warningMessage = $$value;
          $$settled = false;
        }
      },
      {}
    )} ${``} ${``} ${`<div class="flex items-center justify-center gap-4 py-48">${validate_component(Spinner, "Spinner").$$render($$result, { classList: "animate-spin opacity-50" }, {}, {})} <p class="text-xl text-text-secondary" data-svelte-h="svelte-bqbwh1">加载中...</p></div>`}</div> ${validate_component(KeyboardShortcuts, "KeyboardShortcuts").$$render(
      $$result,
      { show: showShortcuts },
      {
        show: ($$value) => {
          showShortcuts = $$value;
          $$settled = false;
        }
      },
      {}
    )} <div class="fixed bottom-6 right-6"><button class="btn-ghost shadow-medium" title="快捷键帮助 (Shift+?)" data-svelte-h="svelte-1lbjoky">⌨️ 快捷键</button></div></main>`;
  } while (!$$settled);
  $$unsubscribe_onFrameChangeStore();
  $$unsubscribe_lcmLiveStatus();
  return $$rendered;
});
export {
  Page as default
};
