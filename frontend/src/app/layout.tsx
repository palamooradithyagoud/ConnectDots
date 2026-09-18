import type { Metadata } from "next";
import Navbar from "@/components/Navbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "ConnectDots | AI Crime Intelligence Platform",
  description: "ConnectDots - Phase 1: Data Collection & Preprocessing Platform powered by FastAPI and PostgreSQL/PostGIS.",
  icons: {
    icon: "/logo.png",
    shortcut: "/logo.png",
    apple: "/logo.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-midnight text-foreground antialiased selection:bg-brand selection:text-white">
        <Navbar />
        <main className="mx-auto max-w-7xl px-6 py-8 lg:px-12">
          {children}
        </main>
      </body>
    </html>
  );
}
