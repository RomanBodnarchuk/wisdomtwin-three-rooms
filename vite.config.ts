import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  base: '/wisdomtwin-three-rooms/',
  plugins: [react(), tailwindcss()],
  build: {
    sourcemap: true,
  },
});
