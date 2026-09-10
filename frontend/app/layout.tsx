import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SOCIALIQ — Social Intelligence Platform",
  description: "From Social Signals to Actionable Intelligence.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
        <script
          dangerouslySetInnerHTML={{
            __html: `try{var t=localStorage.getItem("socialiq-theme");if(t==="light"){document.documentElement.classList.remove("dark");document.documentElement.classList.add("light")}}catch(e){}`,
          }}
        />
      </head>
      <body className="bg-[var(--bg-app)] font-sans text-[var(--text-primary)] antialiased selection:bg-[var(--primary)] selection:text-[var(--on-primary)]">
        {children}
      </body>
    </html>
  );
}
