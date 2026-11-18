import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";

// The Flutter app's embedded page (embed.html), built with relative URLs into the app's
// assets, where its local server serves it: `pnpm vite build -c vite.embed.config.ts`
// (app/tool/sync_md2ui.sh runs it). The theme and its fonts are copied beside it by that
// script; the pipeline Worker is an ES module, so code grammars stay lazy chunks.

export default defineConfig({
  base: "./",
  publicDir: false,
  build: {
    outDir: process.env.EMBED_OUT ?? "../app/assets/md2ui",
    emptyOutDir: true,
    rollupOptions: { input: { index: fileURLToPath(new URL("embed.html", import.meta.url)) } },
  },
  worker: { format: "es" },
});
