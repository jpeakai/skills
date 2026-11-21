import { readFileSync } from "node:fs";
import { fileURLToPath, URL } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

const src = (path: string) => fileURLToPath(new URL(path, import.meta.url));

// The shell is the only file that carries {{...}} placeholders. It is authored
// here and emitted beside the bundle, so all three viewer files are generated.
function emitShell(): Plugin {
  const shell = src("./src/viewer/shell.html");
  return {
    name: "richdocs-emit-shell",
    buildStart() {
      this.addWatchFile(shell);
    },
    generateBundle() {
      this.emitFile({ type: "asset", fileName: "viewer.html", source: readFileSync(shell, "utf-8") });
    },
  };
}

// md2html.py inlines the output text verbatim into a classic <script>, so the
// bundle is a self-contained IIFE: no ES modules, no code-splitting, no asset
// URLs. It lands in the skill's assets as committed Generated Files, so
// emptyOutDir stays off: that directory holds hand-written files too.
export default defineConfig({
  plugins: [react(), tailwindcss(), emitShell()],
  resolve: {
    alias: { "@": src("./src") },
  },
  define: { "process.env.NODE_ENV": JSON.stringify("production") },
  // The dev page (src/dev.ts) reads the skill's classic helpers from the repo.
  server: { fs: { allow: [src("../..")] } },
  build: {
    outDir: src("../../skills/richdocs/assets"),
    emptyOutDir: false,
    copyPublicDir: false,
    cssCodeSplit: false,
    lib: {
      entry: src("./src/viewer/main.tsx"),
      name: "RichdocsViewer",
      formats: ["iife"],
      fileName: () => "viewer.bundle.js",
      cssFileName: "viewer.bundle",
    },
  },
});
