import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Served from https://sacharias.github.io/morning-brief/
export default defineConfig({
  base: "/morning-brief/",
  plugins: [react(), tailwindcss()],
});
