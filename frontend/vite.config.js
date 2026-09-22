import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 本地开发：/api 代理到后端；生产构建由 FastAPI 直接托管
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
  build: {
    outDir: "dist",
  },
});
