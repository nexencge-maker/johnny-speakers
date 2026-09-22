import type { Metadata, Viewport } from "next";
import "./globals.css";
import AppRuntime from "./app-runtime";

export const viewport: Viewport = { themeColor: "#101112", width: "device-width", initialScale: 1, viewportFit: "cover" };

export const metadata: Metadata = {
  title: "Johnny Speakers — Beats by JDP",
  description: "Explore beats, original music and videos by John da Poet. Connect, collaborate and find your sound.",
  manifest: "/manifest.webmanifest",
  applicationName: "Johnny Speakers",
  appleWebApp: { capable: true, title: "Johnny Speakers", statusBarStyle: "black-translucent" },
  icons: {
    apple: "/icons/apple-touch-icon.png",
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}<AppRuntime/></body>
    </html>
  );
}
