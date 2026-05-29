import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom'
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return
          if (id.includes('katex')) return 'markmap-katex'
          if (id.includes('d3')) return 'markmap-d3'
          if (
            id.includes('markdown-it') ||
            id.includes('linkify-it') ||
            id.includes('mdurl') ||
            id.includes('uc.micro') ||
            id.includes('entities')
          ) {
            return 'markmap-markdown'
          }
          if (id.includes('highlight')) return 'markmap-highlight'
          if (id.includes('markmap-lib') || id.includes('markmap-view')) return 'markmap'
        }
      }
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
