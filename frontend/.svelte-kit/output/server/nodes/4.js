

export const index = 4;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/settings/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/4.ebb3a608.js","_app/immutable/chunks/scheduler.ae4f2bff.js","_app/immutable/chunks/index.92b2b836.js","_app/immutable/chunks/ModelManager.36413409.js","_app/immutable/chunks/each.fa7c727b.js","_app/immutable/chunks/index.fa5aef85.js","_app/immutable/chunks/spinner.471702df.js"];
export const stylesheets = ["_app/immutable/assets/ModelManager.58a99713.css"];
export const fonts = [];
