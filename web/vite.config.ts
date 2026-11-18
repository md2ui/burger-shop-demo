import { defineConfig } from "vite";

// The backend (FastAPI on :8000) serves the shop's API, the theme and md2ui's socket; the
// dev server proxies all three, so the page, its API and the socket share one origin (the
// one the backend's ALLOWED_ORIGINS names; `pnpm dev --port N` changes it). @md2ui/dom's
// pipeline Worker is built as an ES module so its code-block grammars stay lazy chunks.
const BACKEND = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

export default defineConfig({
  server: {
    port: 5173,
    proxy: { "/api": BACKEND, "/theme": BACKEND, "/md2ui": { target: BACKEND, ws: true } },
  },
  preview: { proxy: { "/api": BACKEND, "/theme": BACKEND, "/md2ui": { target: BACKEND, ws: true } } },
  worker: { format: "es" },
});
