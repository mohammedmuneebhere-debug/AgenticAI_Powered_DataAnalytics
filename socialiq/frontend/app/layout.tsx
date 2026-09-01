import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SOCIALIQ — Social Intelligence Platform",
  description: "From Social Signals to Actionable Intelligence.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
