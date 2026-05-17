"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Volume2, VolumeX } from "lucide-react";
import { Language } from "@/lib/i18n";

const LABELS: Record<Language, string> = {
  en: "Listen",
  hi: "सुनें",
  kn: "ಕೇಳಿ",
};

const LANG_CODE: Record<Language, string> = {
  en: "en-IN",
  hi: "hi-IN",
  kn: "kn-IN",
};

interface ListenFABProps {
  lang?: Language;
  text?: string;
  onClick?: () => void;
  dark?: boolean;
  bottom?: number;
  right?: number;
  className?: string;
}

export default function ListenFAB({
  lang = "en",
  text,
  onClick,
  dark = false,
  bottom = 24,
  right = 24,
  className = "",
}: ListenFABProps) {
  const [mounted, setMounted] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => { setMounted(true); }, []);

  // Stop speech when component unmounts
  useEffect(() => {
    return () => {
      if (typeof window !== "undefined") window.speechSynthesis?.cancel();
    };
  }, []);

  const handleClick = () => {
    if (onClick) { onClick(); return; }

    if (!("speechSynthesis" in window)) return;

    if (speaking) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
      return;
    }

    // Read provided text or fall back to visible page text (first 500 chars)
    const content = text || document.body.innerText.slice(0, 500);
    if (!content.trim()) return;

    const utt = new SpeechSynthesisUtterance(content);
    utt.lang = LANG_CODE[lang];
    utt.rate = 0.9;
    utt.onend = () => setSpeaking(false);
    utt.onerror = () => setSpeaking(false);
    utteranceRef.current = utt;

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utt);
    setSpeaking(true);
  };

  const btn = (
    <button
      onClick={handleClick}
      aria-label={speaking ? "Stop listening" : LABELS[lang]}
      style={{ bottom, right }}
      className={`fixed z-50 flex items-center gap-2 px-5 h-[64px] rounded-full shadow-lg transition-transform active:scale-95 ${
        dark
          ? "bg-white text-[#161513]"
          : "bg-[#D9542B] text-white"
      } ${className}`}
    >
      <div
        className={`flex items-center justify-center w-8 h-8 rounded-full ${
          dark ? "bg-[#D9542B]" : "bg-white/20"
        }`}
      >
        {speaking
          ? <VolumeX size={16} className="text-white" />
          : <Volume2 size={16} className="text-white" />
        }
      </div>
      <span className="font-semibold text-[15px]">{speaking ? "Stop" : LABELS[lang]}</span>
    </button>
  );

  if (!mounted) return null;
  return createPortal(btn, document.body);
}
