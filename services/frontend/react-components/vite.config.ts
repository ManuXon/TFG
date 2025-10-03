import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Export Vite config
export default defineConfig({
  plugins: [react()],
  build: {
    lib: {
      entry: "src/wc.tsx",   // Your Web Component entry
      name: "FacultySelector",
      fileName: "faculty-selector",
      formats: ["iife"],     // Needed so browser can run directly
    },
    rollupOptions: {
      output: {
        inlineDynamicImports: true,
        entryFileNames: "faculty-selector.iife.js",  // Force clear filename
        assetFileNames: "style.css"                  // Force CSS name
      },
    },
    outDir: "../assets/faculty_selector",  // Send build straight into Dash assets
    emptyOutDir: true,
  },
});
