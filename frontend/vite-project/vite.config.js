import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // 把 /ask 请求代理到后端 8000 端口
      '/ask': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});