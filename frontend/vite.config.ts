import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/campaigns': 'http://localhost:8000',
      '/knowledgebases': 'http://localhost:8000',
      '/query': 'http://localhost:8000',
    },
  },
})
