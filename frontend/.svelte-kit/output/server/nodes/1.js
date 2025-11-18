

export const index = 1;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/fallbacks/error.svelte.js')).default;
export const imports = ["_app/immutable/nodes/1.b0ce0628.js","_app/immutable/chunks/scheduler.ae4f2bff.js","_app/immutable/chunks/index.92b2b836.js","_app/immutable/chunks/stores.c0d5a966.js","_app/immutable/chunks/singletons.9f129248.js","_app/immutable/chunks/index.fa5aef85.js"];
export const stylesheets = [];
export const fonts = [];
