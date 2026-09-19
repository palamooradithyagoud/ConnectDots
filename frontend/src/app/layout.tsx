import type { Metadata } from "next";
import Navbar from "@/components/Navbar";
import AppContainer from "@/components/AppContainer";
import SmoothScroll from "@/components/SmoothScroll";
import "./globals.css";

export const metadata: Metadata = {
  title: "ConnectDots | AI Crime Intelligence Platform",
  description: "India's First AI-Powered Crime & Telecom Intelligence Platform",
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
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className="min-h-screen bg-[#030307] text-foreground antialiased selection:bg-brand selection:text-white"
        suppressHydrationWarning
      >
        <SmoothScroll>
          <Navbar />
          <AppContainer>{children}</AppContainer>
        </SmoothScroll>
      </body>
    </html>
  );
}
