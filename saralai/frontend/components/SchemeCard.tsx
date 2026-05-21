"use client";

import { motion } from "framer-motion";
import { CheckCircle2, AlertCircle, ArrowRight } from "lucide-react";
import { Language } from "@/lib/i18n";
import Link from "next/link";

interface SchemeResult {
  id: string;
  title_kn?: string;
  title_hi?: string;
  title_en: string;
  qualifies: boolean;
  reason_kn?: string;
  reason_hi?: string;
  reason_en?: string;
  benefit?: string;
  documents_needed?: string[];
  confidence?: number;
}

interface SchemeCardProps {
  scheme: SchemeResult;
  index: number;
  lang?: Language;
  isSolid?: boolean;
}

export default function SchemeCard({ scheme, index, lang = "kn", isSolid = false }: SchemeCardProps) {
  if (!scheme) return null;
  const isDemo = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("demo") === "true";
  const demoQ = isDemo ? "?demo=true" : "";
  const title = lang === "kn" ? (scheme.title_kn || scheme.title_en) :
                lang === "hi" ? (scheme.title_hi || scheme.title_en) :
                scheme.title_en;
  const reason = lang === "kn" ? (scheme.reason_kn || scheme.reason_en || "") :
                 lang === "hi" ? (scheme.reason_hi || scheme.reason_en || "") :
                 (scheme.reason_en || "");

  if (isSolid) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: index * 0.08, ease: [0.22, 1, 0.36, 1] }}
      >
        <Link href={`/scheme/${scheme.id}${demoQ}`}>
          <div className="relative overflow-hidden rounded-[22px] bg-[#161513] p-5">
            <div className="absolute -top-8 -right-8 w-32 h-32 rounded-full bg-[#D9542B] opacity-20 blur-xl pointer-events-none" />
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <p className="text-white/50 font-mono text-[11px] tracking-widest uppercase mb-1">
                  Scheme {index + 1}
                </p>
                <p className="text-white text-[21px] font-bold leading-tight">{title}</p>
              </div>
              <CheckCircle2 size={20} className="text-[#2F7D4F] shrink-0 mt-1" />
            </div>
            {scheme.benefit && (
              <p className="mt-3 text-[26px] font-bold text-white">{scheme.benefit}</p>
            )}
            {reason && (
              <p className="mt-2 text-white/60 text-[14px] leading-snug line-clamp-2">{reason}</p>
            )}
            {scheme.documents_needed && scheme.documents_needed.length > 0 && (
              <div className="mt-3 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#C77A20]/20">
                <AlertCircle size={11} className="text-[#C77A20]" />
                <span className="text-[#C77A20] font-mono text-[11px]">
                  {scheme.documents_needed.length} doc needed
                </span>
              </div>
            )}
            <div className="mt-4 flex justify-end">
              <ArrowRight size={16} className="text-white/40" />
            </div>
          </div>
        </Link>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.07, ease: [0.22, 1, 0.36, 1] }}
    >
      <Link href={`/scheme/${scheme.id}${demoQ}`}>
        <div className="flex items-center gap-3 bg-white rounded-2xl border border-[rgba(20,18,16,0.08)] px-4 py-4">
          <div className="w-10 h-10 rounded-xl bg-[#FBE9DD] flex items-center justify-center text-xl shrink-0">
            🏛
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[16px] font-semibold text-[#161513] leading-tight">{title}</p>
            {scheme.benefit && (
              <p className="text-[14px] text-[#7A736C] mt-0.5">{scheme.benefit}</p>
            )}
          </div>
          {scheme.qualifies
            ? <CheckCircle2 size={18} className="text-[#2F7D4F] shrink-0" />
            : <AlertCircle size={18} className="text-[#C77A20] shrink-0" />
          }
        </div>
      </Link>
    </motion.div>
  );
}
