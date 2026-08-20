import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  resolve: {
    dedupe: ['react', 'react-dom'],
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8006',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://localhost:8006',
        changeOrigin: true,
      },
      '/orders': {
        target: 'http://localhost:8006',
        changeOrigin: true,
      },
      '/pricing': {
        target: 'http://localhost:8006',
        changeOrigin: true,
      },
      '/messages': {
        target: 'http://127.0.0.1:8006',
        changeOrigin: true,
        ws: true,
      },
      '/quotes': {
        target: 'http://127.0.0.1:8006',
        changeOrigin: true,
      },
      '/verify': {
        target: 'http://127.0.0.1:8006',
        changeOrigin: true,
      },
      '/trust': {
        target: 'http://127.0.0.1:8006',
        changeOrigin: true,
      },
      '/bindings': {
        target: 'http://127.0.0.1:8006',
        changeOrigin: true,
      },
      '/profile': {
        target: 'http://127.0.0.1:8006',
        changeOrigin: true,
      },
      '/guidance': {
        target: 'http://127.0.0.1:8006',
        changeOrigin: true,
      },
      '/tracking': {
        target: 'http://127.0.0.1:8006',
        changeOrigin: true,
      },
      '/payments': {
        target: 'http://127.0.0.1:8006',
        changeOrigin: true,
      },
    }
  }
})
