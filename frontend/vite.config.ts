import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Backend port - use 8001 for retail, 8000 for todo
const BACKEND_PORT = process.env.BACKEND_PORT || '8001'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // Proxy API requests to the Python backend
      '/chatkit': {
        target: `http://localhost:${BACKEND_PORT}`,
        changeOrigin: true,
      },
      '/api': {
        target: `http://localhost:${BACKEND_PORT}`,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../static/dist',
    emptyOutDir: true,
  },
})
