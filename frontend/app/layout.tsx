import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Navegacion } from "@/components/navegacion";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "BalanceApp — Prueba Técnica Esguerra JHR",
  description: "Aplicación contable: comprobantes, libro mayor e información exógena",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="es"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col bg-slate-50 text-slate-900">
        <Navegacion />
        <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-8">{children}</main>
        <footer className="border-t border-sky-100 bg-white">
          <div className="mx-auto max-w-6xl px-6 py-4 text-center text-xs text-slate-400">
            BalanceApp — Prueba técnica Esguerra JHR · Santiago Sierra · {new Date().getFullYear()}
          </div>
        </footer>
      </body>
    </html>
  );
}
