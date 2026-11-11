import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dev server forwards /api to FastAPI so the page can use relative URLs.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
