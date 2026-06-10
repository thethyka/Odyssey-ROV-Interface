import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ command }) => ({
  // GitHub Pages serves the build from /Odyssey-ROV-Interface/, but the dev
  // server should keep serving from the root.
  base: command === 'build' ? '/Odyssey-ROV-Interface/' : '/',
  plugins: [react(), tailwindcss()],
}))