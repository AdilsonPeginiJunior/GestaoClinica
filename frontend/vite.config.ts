import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Proxy opcional: use baseURL '/api' no frontend se preferir evitar CORS
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
