import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/kit/vite';
/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess({ postcss: true }),
  kit: {
    adapter: adapter({
      pages: 'public',
      assets: 'public',
      // 设置 fallback 以支持单页应用（SPA）的客户端路由
      // 所有未匹配的路由将回退到 index.html，由客户端路由处理
      fallback: 'index.html',
      precompress: false,
      // 对于 SPA，不需要严格模式
      strict: false
    })
  }
};

export default config;
