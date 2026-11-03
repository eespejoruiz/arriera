import type { Metadata, Viewport } from "next";
import { Hanken_Grotesk, Special_Elite } from "next/font/google";
import "./globals.css";

const hanken = Hanken_Grotesk({ subsets: ["latin"], weight: ["300", "400", "500", "600"], variable: "--font-hanken", display: "swap" });
const elite = Special_Elite({ subsets: ["latin"], weight: "400", variable: "--font-elite", display: "swap" });

export const metadata: Metadata = {
  title: { default: "Arriera", template: "%s · Arriera" },
  description: "Gestión documental con IA",
  icons: { icon: "/favicon.svg" },
};
export const viewport: Viewport = { themeColor: "#0F110B", width: "device-width", initialScale: 1, viewportFit: "cover" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es-PE" className={`${hanken.variable} ${elite.variable}`}>
      <body>{children}</body>
    </html>
  );
}
