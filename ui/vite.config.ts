import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

// The dashboard is served by `skills/_core/command_center/server.py`, which
// mounts the build output at the origin root and exposes `/api/*`. `base: './'`
// keeps every asset URL relative so the bundle works from any served root.
export default defineConfig({
  base: './',
  plugins: [react()],
  build: {
    outDir: '../skills/_core/command_center/static',
    emptyOutDir: true,
    sourcemap: false,
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['src/test/setup.ts'],
    globals: false,
    include: ['src/**/*.test.{ts,tsx}'],
  },
  server: {
    port: 5173,
    // Development only: `vite dev` proxies the API to a locally running
    // command center. The production build never makes a cross-origin call.
    // `changeOrigin` stays false so the backend sees Host and Origin
    // `localhost:5173` (the smoke POST compares them); start the backend with
    // `--allowed-host localhost:5173` so its Host allow-list accepts that.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: false,
      },
    },
  },
});
