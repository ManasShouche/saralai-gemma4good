"use client";

import { type ReactNode } from "react";
import { ArrowRight } from "lucide-react";
import type { Language } from "@/lib/i18n";

interface GiantCTAProps {
  lang?: Language;
  label: string;
  sub: string;
  icon: ReactNode;
  onClick?: () => void;
  href?: string;
  className?: string;
}

export default function GiantCTA({ label, sub, icon, onClick, href, className = "" }: GiantCTAProps) {
  const inner = (
    <div className={`relative overflow-hidden rounded-[28px] bg-[#161513] p-6 flex flex-col justify-between min-h-[220px] ${className}`}>
      {/* Accent circle overlay top-right */}
      <div className="absolute -top-10 -right-10 w-40 h-40 rounded-full bg-[#D9542B] opacity-30 blur-2xl pointer-events-none" />
      {/* Bottom accent dot */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 w-24 h-1 rounded-full bg-[#D9542B] opacity-20 pointer-events-none" />

      {/* Icon badge */}
      <div className="w-14 h-14 rounded-2xl bg-[#D9542B] flex items-center justify-center text-white">
        {icon}
      </div>

      {/* Text */}
      <div className="mt-4 flex-1">
        <p className="text-white text-[22px] font-bold leading-tight whitespace-pre-line">{label}</p>
        <p className="text-white/60 text-[14px] mt-2 leading-snug whitespace-pre-line">{sub}</p>
      </div>

      {/* Time pill + arrow */}
      <div className="mt-6 flex items-center justify-between">
        <span className="font-mono text-[11px] tracking-widest text-white/40 uppercase">~ 2 minutes</span>
        <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center">
          <ArrowRight size={18} className="text-[#161513]" />
        </div>
      </div>
    </div>
  );

  if (href) {
    return <a href={href} className="block">{inner}</a>;
  }
  return <button onClick={onClick} className="block w-full text-left">{inner}</button>;
}
