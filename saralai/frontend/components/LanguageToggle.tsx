"use client";

import { Language, LANGUAGES } from "@/lib/i18n";

interface LanguageToggleProps {
  value: Language;
  onChange: (lang: Language) => void;
  className?: string;
}

export default function LanguageToggle({ value, onChange, className = "" }: LanguageToggleProps) {
  return (
    <div className={`flex items-center gap-1 bg-[rgba(20,18,16,0.08)] rounded-full p-1 ${className}`}>
      {LANGUAGES.map((l) => (
        <button
          key={l.code}
          onClick={() => onChange(l.code)}
          className={`px-3 py-1 rounded-full text-[13px] font-semibold transition-all min-h-0 min-w-0 leading-none ${
            value === l.code
              ? "bg-white text-[#D9542B] shadow-sm"
              : "text-[#7A736C] hover:text-[#3D3A36]"
          }`}
        >
          {l.nativeLabel}
        </button>
      ))}
    </div>
  );
}
