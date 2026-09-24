import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

const root = fileURLToPath(new URL('.', import.meta.url));

export default defineConfig({
  // GitHub Pages serves under the repo-name path; Vercel serves at root (VITE_BASE=/).
  base: process.env.VITE_BASE || '/wisdomtwin-three-rooms/',
  plugins: [react(), tailwindcss()],
  build: {
    sourcemap: true,
    rollupOptions: {
      input: {
        main: resolve(root, 'index.html'),
        invest: resolve(root, 'invest/index.html'),
      },
    },
  },
});
