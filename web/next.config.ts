import type { NextConfig } from "next";
// Prototipo: exportación estática servida por nginx. En el sistema real se quita `output`.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || undefined;
const config: NextConfig = { output: "export", trailingSlash: true, images: { unoptimized: true }, basePath };
export default config;
