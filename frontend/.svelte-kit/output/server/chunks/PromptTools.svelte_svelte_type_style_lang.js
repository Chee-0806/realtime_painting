import { d as derived, w as writable } from "./index.js";
var ErrorType = /* @__PURE__ */ ((ErrorType2) => {
  ErrorType2["NETWORK"] = "network";
  ErrorType2["API"] = "api";
  ErrorType2["VALIDATION"] = "validation";
  ErrorType2["MODEL"] = "model";
  ErrorType2["GENERATION"] = "generation";
  ErrorType2["WEBSOCKET"] = "websocket";
  return ErrorType2;
})(ErrorType || {});
const errorState = writable({
  hasError: false,
  error: null
});
const pipelineValues = writable({});
let debounceTimer = null;
let debouncedValue = {};
derived(
  pipelineValues,
  ($pipelineValues, set) => {
    debouncedValue = $pipelineValues;
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    debounceTimer = setTimeout(() => {
      set(debouncedValue);
    }, 300);
  },
  {}
);
const PromptTools_svelte_svelte_type_style_lang = "";
export {
  ErrorType as E,
  errorState as e,
  pipelineValues as p
};
