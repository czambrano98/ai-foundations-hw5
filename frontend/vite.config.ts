import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,      // the origin the backend allows for CORS
    open: true,      // `npm run dev` opens the React desk in the browser
  },
})
