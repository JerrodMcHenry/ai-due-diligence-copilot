import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import AppShell from "@/components/layout/AppShell";
import ThemeProvider from "@/components/providers/ThemeProvider";

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
  title: {
    default: "Startup Intelligence Engine",
    template: "%s | Startup Intelligence Engine",
  },
  description: "Startup intelligence powered by the Startup Power Score.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable}`}
    >
      <body className="min-h-screen bg-background font-sans text-foreground antialiased">
        <ThemeProvider>
          <AppShell>{children}</AppShell>
        </ThemeProvider>
      </body>
    </html>
  );
}
