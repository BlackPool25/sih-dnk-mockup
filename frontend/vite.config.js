import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
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
      '/transcribe': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      }
    }
  }
})
