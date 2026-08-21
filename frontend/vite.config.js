import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],  // 👈 ПЛАГИН ДОЛЖЕН БЫТЬ!
  server: {
    watch: {
      usePolling: true,
      interval: 1000,
    },
    hmr: {
      overlay: true, // показывать ошибки
      host: 'localhost',
      port: 5173,
      protocol: 'ws',
    }
  }
})