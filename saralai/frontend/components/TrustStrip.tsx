"use client";

import { useEffect, useState } from "react";
import { Lock } from "lucide-react";
import { Language } from "@/lib/i18n";

const LABELS: Record<Language, string> = {
  en: "Nothing leaves this phone",
  hi: "कुछ भी फोन से बाहर नहीं जाता",
  kn: "ಏನೂ ಈ ಫೋನ್‌ನಿಂದ ಹೊರಹೋಗುವುದಿಲ್ಲ",
};

interface TrustStripProps {
  lang?: Language;
  dark?: boolean;
  className?: string;
}

export default function TrustStrip({ lang = "en", dark = false, className = "" }: TrustStripProps) {
  const [mounted, setMounted] = useState(false);
  const [resolvedLang, setResolvedLang] = useState<Language>(lang);

  useEffect(() => {
    setMounted(true);
    const stored = (typeof window !== "undefined"
      ? (localStorage.getItem("saralai_lang") as Language | null)
      : null);
    setResolvedLang(stored ?? lang);
  }, [lang]);

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[12px] font-medium backdrop-blur-[10px] ${
        dark
          ? "bg-white/10 text-white/80"
          : "bg-[rgba(20,18,16,0.06)] text-[#3D3A36]"
      } ${className}`}
      suppressHydrationWarning
    >
      <Lock size={11} strokeWidth={2.5} />
      <span suppressHydrationWarning>{mounted ? LABELS[resolvedLang] : " "}</span>
    </div>
  );
}
