import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/ask': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/ask-stream': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/upload': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/history': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/analyze': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/exercise': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
  },
});