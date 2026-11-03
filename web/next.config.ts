import type { NextConfig } from "next";
// Prototipo: exportación estática servida por nginx. En el sistema real se quita `output`.
const config: NextConfig = { output: "export", trailingSlash: true, images: { unoptimized: true } };
export default config;
