import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, "src/widget.js"),
      name: "InquisiWidget",
      fileName: "widget",
      formats: ["iife"],
    },
    outDir: "../inquisitool/static",
    emptyOutDir: false,
    rollupOptions: {
      output: { inlineDynamicImports: true },
    },
  },
});
