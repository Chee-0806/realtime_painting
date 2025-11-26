import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

const API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://localhost:8000';
const HOST = process.env.HOST || '127.0.0.1';
const PORT = parseInt(process.env.PORT || '6006');

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    host: HOST === '0.0.0.0' ? '0.0.0.0' : HOST,
    port: PORT,
    proxy: {
      '/api': {
        target: API_BASE_URL,
        changeOrigin: true,
        ws: true,  // 启用 WebSocket 代理
        secure: false,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, res) => {
            // 只在非连接错误时记录，避免启动时的噪音
            if (err.code !== 'ECONNREFUSED') {
              console.error('proxy error', err);
            }
          });
          proxy.on('proxyReqWs', (proxyReq, req, socket) => {
            console.log('WebSocket proxy request:', req.url);
          });
        }
      }
    },
  },
  build: {
    target: 'es2020',
    outDir: 'build',
    assetsDir: 'assets',
    sourcemap: process.env.NODE_ENV === 'development',
    minify: process.env.NODE_ENV === 'production' ? 'terser' : false,
    terserOptions: {
      compress: {
        drop_console: process.env.NODE_ENV === 'production',
        drop_debugger: process.env.NODE_ENV === 'production'
      }
    }
  },
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0')
  }
});