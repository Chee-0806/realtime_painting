

export const index = 6;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/viewer/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/6.d44bc0bf.js","_app/immutable/chunks/scheduler.ae4f2bff.js","_app/immutable/chunks/index.92b2b836.js"];
export const stylesheets = [];
export const fonts = [];
