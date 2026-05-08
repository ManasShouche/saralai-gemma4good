"use client";

import { useRouter } from "next/navigation";
import { ArrowRight } from "lucide-react";
import TrustStrip from "@/components/TrustStrip";
import type { Language } from "@/lib/i18n";

const OPTIONS: { code: Language; label: string; sub: string; primary: boolean }[] = [
  { code: "en", label: "English", sub: "English", primary: true },
  { code: "hi", label: "हिन्दी", sub: "Hindi", primary: false },
  { code: "kn", label: "ಕನ್ನಡ", sub: "Kannada", primary: false },
];

export default function OnboardingPage() {
  const router = useRouter();

  const choose = (lang: Language) => {
    localStorage.setItem("saralai_lang", lang);
    router.replace("/");
  };

  return (
    <main className="min-h-screen bg-paper flex flex-col px-6 pt-14 pb-10">
      {/* Header */}
      <div className="flex justify-center mb-10">
        <TrustStrip lang="en" />
      </div>

      {/* Heading */}
      <div className="mb-8">
        <p className="font-mono text-[11px] tracking-widest text-muted uppercase mb-2">SaralAI</p>
        <h1 className="text-[30px] font-bold text-ink leading-tight">
          Choose your language
        </h1>
        <p className="text-[17px] text-inkSoft mt-2">
          Touch the language you read best
        </p>
      </div>

      {/* Language options */}
      <div className="flex flex-col gap-4 flex-1">
        {OPTIONS.map((opt) => (
          <button
            key={opt.code}
            onClick={() => choose(opt.code)}
            className={`relative flex items-center justify-between rounded-[22px] px-6 py-5 h-[88px] transition-transform active:scale-[0.98] ${
              opt.primary
                ? "bg-ink text-white"
                : "bg-white border border-[rgba(20,18,16,0.1)] text-ink"
            }`}
          >
            <div className="text-left">
              <p className={`text-[26px] font-bold leading-none ${opt.code === "kn" ? "font-kan" : ""}`}>
                {opt.label}
              </p>
              {opt.primary && (
                <p className="text-white/50 text-[13px] mt-0.5">{opt.sub}</p>
              )}
            </div>
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center ${
                opt.primary ? "bg-[#D9542B]" : "bg-[rgba(20,18,16,0.06)]"
              }`}
            >
              <ArrowRight size={18} className={opt.primary ? "text-white" : "text-ink"} />
            </div>
          </button>
        ))}
      </div>

      {/* Footer */}
      <p className="mt-8 text-center font-mono text-[11px] text-muted tracking-wide">
        Nothing leaves this phone
      </p>
    </main>
  );
}
