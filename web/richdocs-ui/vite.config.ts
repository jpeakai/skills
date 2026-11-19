import { fileURLToPath, URL } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// One entry per build. md2html.py inlines the output text verbatim into a
// classic <script>, so the bundle is a self-contained IIFE: no ES modules, no
// code-splitting, no asset URLs. M0 writes to dist/; M1 retargets
// skills/richdocs/assets/.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  define: { "process.env.NODE_ENV": JSON.stringify("production") },
  build: {
    outDir: "dist",
    emptyOutDir: true,
    cssCodeSplit: false,
    lib: {
      entry: fileURLToPath(new URL("./src/viewer/main.tsx", import.meta.url)),
      name: "RichdocsViewer",
      formats: ["iife"],
      fileName: () => "viewer.bundle.js",
      cssFileName: "viewer.bundle",
    },
  },
});
