import type { Metadata } from "next";
import Script from "next/script";
import {
  Plus_Jakarta_Sans,
  JetBrains_Mono,
  Noto_Sans_Kannada,
  Noto_Sans_Devanagari,
} from "next/font/google";
import "@/styles/globals.css";
import dynamic from "next/dynamic";

const jakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-jakarta",
  display: "swap",
});
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});
const notoKannada = Noto_Sans_Kannada({
  subsets: ["kannada"],
  variable: "--font-kannada",
  display: "swap",
});
const notoDevanagari = Noto_Sans_Devanagari({
  subsets: ["devanagari"],
  variable: "--font-devanagari",
  display: "swap",
});

const DevLogger = process.env.NODE_ENV === "development"
  ? dynamic(() => import("@/components/DevLogger"), { ssr: false })
  : () => null;

export const metadata: Metadata = {
  title: "SaralAI — Find Government Schemes",
  description: "Photograph your Aadhaar, speak about your situation, get matched to welfare schemes you qualify for — offline, free.",
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${jakartaSans.variable} ${jetbrainsMono.variable} ${notoKannada.variable} ${notoDevanagari.variable}`}
    >
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="theme-color" content="#D9542B" />
        <link rel="icon" href="/icon-192.png" />
        <link rel="apple-touch-icon" href="/icon-192.png" />
      </head>
      <body className="min-h-screen bg-paper text-ink antialiased">
        {/* Redirect to onboarding before React boots — eliminates post-hydration flash */}
        <Script id="onboarding-check" strategy="beforeInteractive">
          {`try{if(!localStorage.getItem('saralai_lang')&&!location.pathname.startsWith('/onboarding'))location.replace('/onboarding');}catch(e){}`}
        </Script>
        <DevLogger />
        {children}
        <Script id="sw-register" strategy="afterInteractive">
          {`if('serviceWorker'in navigator)navigator.serviceWorker.register('/sw.js');`}
        </Script>
      </body>
    </html>
  );
}
