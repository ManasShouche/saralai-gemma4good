"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Sparkles, SlidersHorizontal } from "lucide-react";
import { t } from "@/lib/i18n";
import type { Language } from "@/lib/i18n";
import { findSchemes } from "@/lib/api";
import ReasoningStream, { Thought, ThoughtType } from "@/components/ReasoningStream";
import SchemeCard from "@/components/SchemeCard";
import ListenFAB from "@/components/ListenFAB";

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

export default function ResultsPage() {
  const router = useRouter();
  const [lang, setLangState] = useState<Language>("en");
  const [phase, setPhase] = useState<"searching" | "results" | "error">("searching");
  const [thoughts, setThoughts] = useState<Thought[]>([]);
  const [schemes, setSchemes] = useState<SchemeResult[]>([]);
  const [evaluated, setEvaluated] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [liveToken, setLiveToken] = useState("");
  const idCountRef = useRef(0);
  const langRef = useRef<Language>("en");
  const liveBufferRef = useRef("");
  const flushTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const classifyText = (text: string): ThoughtType => {
    const lower = text.toLowerCase();
    if (text.startsWith("⟳") || lower.includes("tool:") || lower.includes("checking")) return "tool";
    if (text.includes("✓") || lower.includes("match") || lower.includes("qualif") || lower.includes("eligible")) return "match";
    if (text.includes("✗") || lower.includes("skip") || lower.includes("not eligible") || lower.includes("does not qualify")) return "skip";
    return "profile";
  };

  const flushBuffer = useRef(() => {
    const text = liveBufferRef.current.trim();
    liveBufferRef.current = "";
    setLiveToken("");
    if (text.length < 4) return;
    idCountRef.current++;
    const type = classifyText(text);
    setThoughts((p) => [...p, { id: String(idCountRef.current), type, text }]);
  });

  useEffect(() => {
    const stored = localStorage.getItem("saralai_lang") as Language | null;
    if (stored) {
      setLangState(stored);
      langRef.current = stored as Language;
    }
  }, []);

  useEffect(() => {
    let profile: Record<string, string> = {};
    let narrative = "";
    try {
      profile = JSON.parse(localStorage.getItem("saralai_profile") || "{}");
      narrative = localStorage.getItem("saralai_narrative") || "";
    } catch {}

    const start = Date.now();

    findSchemes(
      profile,
      narrative,
      langRef.current,
      (text: string) => {
        // Accumulate tokens into buffer — flush on sentence boundaries or newlines
        liveBufferRef.current += text;
        setLiveToken(liveBufferRef.current);
        setEvaluated((n) => n + 1);

        const hasBoundary = /[\n.!?]/.test(text);
        if (flushTimerRef.current) clearTimeout(flushTimerRef.current);
        flushTimerRef.current = setTimeout(
          flushBuffer.current,
          hasBoundary ? 60 : 280,
        );
      },
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (scheme: any) => {
        // Flush any pending buffer when a scheme result arrives
        if (flushTimerRef.current) clearTimeout(flushTimerRef.current);
        flushBuffer.current();
        setSchemes((p) => {
          if (p.find((s) => s.id === scheme.id)) return p;
          return [...p, {
            id: scheme.id,
            title_kn: scheme.title_kn,
            title_hi: scheme.title_hi,
            title_en: scheme.title_en || scheme.id,
            qualifies: scheme.qualifies ?? true,
            reason_kn: scheme.reason_kn,
            reason_hi: scheme.reason_hi,
            reason_en: scheme.reason_en,
            benefit: scheme.benefit,
            documents_needed: scheme.documents_needed,
            confidence: scheme.confidence,
          }];
        });
      },
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (summary: any) => {
        if (flushTimerRef.current) clearTimeout(flushTimerRef.current);
        flushBuffer.current();
        setElapsed(Math.round((Date.now() - start) / 100) / 10);
        setTimeout(() => {
          setPhase("results");
          // Save last visit so home screen shows the strip
          setSchemes((current) => {
            localStorage.setItem("saralai_last_visit", JSON.stringify({ count: current.length }));
            return current;
          });
        }, 800);
      },
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (err: any) => {
        console.error(err);
        if (flushTimerRef.current) clearTimeout(flushTimerRef.current);
        flushBuffer.current();
        setSchemes((current) => {
          setPhase(current.length > 0 ? "results" : "error");
          return current;
        });
      }
    );
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (phase === "searching") {
    return (
      <main className="min-h-screen bg-paper flex flex-col px-5 pt-5 pb-10">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <button
            onClick={() => router.back()}
            className="w-10 h-10 rounded-full bg-[rgba(20,18,16,0.06)] flex items-center justify-center"
          >
            <ArrowLeft size={18} className="text-inkSoft" />
          </button>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#FBE9DD]">
            <Sparkles size={13} className="text-[#D9542B]" />
            <span className="font-mono text-[11px] tracking-widest text-[#D9542B] uppercase">{t("results.thinking", lang)}</span>
          </div>
        </div>

        {/* Title */}
        <h1 className="text-[30px] font-bold text-ink mb-6">
          {t("results.findingSchemes", lang)}
        </h1>

        {/* Progress bar */}
        <div className="mb-2 flex items-center justify-between">
          <div className="flex-1 h-1.5 rounded-full bg-[rgba(20,18,16,0.08)] overflow-hidden mr-4">
            <motion.div
              className="h-full bg-[#D9542B] rounded-full"
              animate={{ width: `${Math.min(95, (evaluated / 50) * 100)}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
          <span className="font-mono text-[12px] text-muted">{evaluated}/50</span>
        </div>

        {/* Stat pills */}
        <div className="flex gap-3 mb-6 mt-4">
          <div className="flex-1 bg-[#FBE9DD] rounded-2xl px-4 py-3">
            <p className="font-mono text-[10px] tracking-widest text-muted uppercase">Matched</p>
            <p className="text-[22px] font-bold text-[#D9542B]">{schemes.length}</p>
          </div>
          <div className="flex-1 bg-white rounded-2xl border border-[rgba(20,18,16,0.08)] px-4 py-3">
            <p className="font-mono text-[10px] tracking-widest text-muted uppercase">Yearly</p>
            <p className="text-[22px] font-bold text-ink">₹–</p>
          </div>
        </div>

        {/* Reasoning stream */}
        <ReasoningStream thoughts={thoughts} isStreaming liveToken={liveToken} />

        <ListenFAB lang={lang} />
      </main>
    );
  }

  if (phase === "error") {
    return (
      <main className="min-h-screen bg-paper flex flex-col items-center justify-center px-5 gap-6">
        <div className="text-center">
          <p className="text-[22px] font-bold text-ink mb-2">{t("common.error", lang)}</p>
          <p className="text-[15px] text-muted">{t("common.retry", lang)}</p>
        </div>
        <button
          onClick={() => router.push("/scan")}
          className="h-[60px] px-8 rounded-[18px] bg-ink text-white font-bold text-[16px]"
        >
          {t("common.backToHome", lang)}
        </button>
      </main>
    );
  }


  return (
    <main className="min-h-screen bg-paper flex flex-col px-5 pt-5 pb-28">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={() => router.back()}
          className="w-10 h-10 rounded-full bg-[rgba(20,18,16,0.06)] flex items-center justify-center"
        >
          <ArrowLeft size={18} className="text-inkSoft" />
        </button>
        <div className="flex-1">
          <span className="font-mono text-[11px] text-muted">{elapsed}s · 50 schemes</span>
        </div>
        <button className="w-10 h-10 rounded-full bg-[rgba(20,18,16,0.06)] flex items-center justify-center">
          <SlidersHorizontal size={16} className="text-inkSoft" />
        </button>
      </div>

      {/* Title */}
      <h1 className="text-[30px] font-bold text-ink mb-1">
        {t("results.fourMatches", lang).replace("{n}", String(schemes.length))}
      </h1>
      <p className="text-[15px] text-muted mb-6">{t("results.resultsSub", lang)}</p>

      {/* Scheme cards */}
      <div className="flex flex-col gap-4">
        <AnimatePresence>
          {schemes.map((scheme, i) => (
            <SchemeCard
              key={scheme.id}
              scheme={scheme}
              index={i}
              lang={lang}
              isSolid={i === 0}
            />
          ))}
        </AnimatePresence>

        {schemes.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <p className="text-muted text-[17px]">No schemes found. Try speaking more about your situation.</p>
          </div>
        )}
      </div>

      <ListenFAB lang={lang} />
    </main>
  );
}
