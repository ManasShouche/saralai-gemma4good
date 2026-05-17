"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft, Download, MapPin, CheckCircle2, AlertCircle, Volume2, MoreVertical } from "lucide-react";
import { t } from "@/lib/i18n";
import type { Language } from "@/lib/i18n";
import { getSchemeDetails, generateForm } from "@/lib/api";
import ListenFAB from "@/components/ListenFAB";

interface SchemeData {
  id: string;
  title_kn?: string;
  title_hi?: string;
  title_en: string;
  ministry?: string;
  scope?: string;
  category?: string;
  benefit_en?: string;
  benefit_kn?: string;
  benefit_hi?: string;
  eligibility_reason?: string;
  docs_have?: string[];
  docs_need?: string[];
  office?: string;
  application_url?: string;
}

export default function SchemeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [lang, setLangState] = useState<Language>("en");
  const id = params.id as string;
  const [scheme, setScheme] = useState<SchemeData | null>(null);
  const [schemeError, setSchemeError] = useState(false);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("saralai_lang") as Language | null;
    if (stored) setLangState(stored);
  }, []);

  useEffect(() => {
    getSchemeDetails(id)
      .then((data: Record<string, string>) => {
        let docs: string[] = [];
        try { docs = JSON.parse(data.documents || "[]"); } catch {}
        const half = Math.ceil(docs.length / 2);
        setScheme({
          id,
          title_kn: data.title_kn || data.title_en,
          title_hi: data.title_hi || data.title_en,
          title_en: data.title_en,
          ministry: data.ministry || "Government of India",
          scope: data.scope,
          category: data.category,
          benefit_en: data.benefit_en,
          benefit_kn: data.benefit_kn,
          eligibility_reason: data.eligibility_reason || "Based on your profile, you may qualify for this scheme.",
          docs_have: docs.slice(0, half),
          docs_need: docs.slice(half),
          office: data.office_template || "Local Government Office",
          application_url: data.application_url,
        });
      })
      .catch((err) => { console.error(err); setSchemeError(true); });
  }, [id]);

  const handleDownload = async () => {
    if (!scheme) return;
    setDownloading(true);
    try {
      let profile: Record<string, string> = {};
      profile = JSON.parse(sessionStorage.getItem("saralai_profile") || "{}");
      const blob = await generateForm(id, profile);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `form_${id}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      router.push(`/scheme/${id}/ready`);
    } catch {
      alert("Failed to generate form.");
    } finally {
      setDownloading(false);
    }
  };

  const handleListen = () => {
    if (!scheme) return;
    const text = (lang === "kn" ? scheme.benefit_kn : lang === "hi" ? scheme.benefit_hi : scheme.benefit_en) || scheme.benefit_en || "";
    if (!("speechSynthesis" in window) || !text) return;
    window.speechSynthesis.cancel();
    const utt = new SpeechSynthesisUtterance(text);
    utt.lang = lang === "kn" ? "kn-IN" : lang === "hi" ? "hi-IN" : "en-IN";
    window.speechSynthesis.speak(utt);
  };

  if (schemeError) {
    return (
      <div className="min-h-screen bg-paper flex flex-col items-center justify-center gap-4 px-6">
        <p className="text-[17px] text-ink text-center">{t("common.error", lang)}</p>
        <button
          onClick={() => router.back()}
          className="h-[52px] px-6 rounded-[16px] bg-ink text-white font-semibold text-[15px]"
        >
          {t("scheme.back", lang)}
        </button>
      </div>
    );
  }

  if (!scheme) {
    return (
      <div className="min-h-screen bg-paper flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-2 border-[#D9542B] border-t-transparent animate-spin" />
      </div>
    );
  }

  const title = lang === "kn" ? (scheme.title_kn || scheme.title_en) :
                lang === "hi" ? (scheme.title_hi || scheme.title_en) :
                scheme.title_en;
  const benefit = lang === "kn" ? (scheme.benefit_kn || scheme.benefit_en) : lang === "hi" ? (scheme.benefit_hi || scheme.benefit_en) : scheme.benefit_en;
  const catLabel = [scheme.scope?.toUpperCase(), scheme.category?.toUpperCase().replace("_", " ")]
    .filter(Boolean).join(" · ");

  return (
    <main className="min-h-screen bg-paper flex flex-col pb-28">
      {/* Dark hero header */}
      <div className="relative overflow-hidden bg-[#161513] px-5 pt-12 pb-8">
        {/* Accent glow */}
        <div className="absolute -top-12 -right-12 w-48 h-48 rounded-full bg-[#D9542B] opacity-20 blur-3xl pointer-events-none" />

        {/* Top row */}
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={() => router.back()}
            className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center"
          >
            <ArrowLeft size={18} color="white" />
          </button>
          <span className="font-mono text-[11px] text-white/40 tracking-widest">Scheme 1 of 4</span>
          <button className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center">
            <MoreVertical size={18} color="white" />
          </button>
        </div>

        {/* Category badge */}
        {catLabel && (
          <div className="inline-flex items-center px-3 py-1 rounded-full bg-[#C77A20]/20 mb-3">
            <span className="font-mono text-[11px] tracking-widest text-[#C77A20] uppercase">{catLabel}</span>
          </div>
        )}

        {/* Title */}
        <h1 className="text-white text-[26px] font-bold leading-tight mb-4">{title}</h1>

        {/* Benefit row */}
        <div className="flex items-center gap-3">
          {benefit && (
            <span className="text-white text-[22px] font-bold">{benefit}</span>
          )}
          <button
            onClick={handleListen}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/10"
          >
            <div className="w-5 h-5 rounded-full bg-[#D9542B] flex items-center justify-center">
              <Volume2 size={11} color="white" />
            </div>
            <span className="text-white/80 text-[13px] font-medium">
              {t("scheme.listenSimple", lang)}
            </span>
          </button>
        </div>
      </div>

      {/* Body (paper bg, scrollable) */}
      <div className="flex-1 px-5 pt-6 flex flex-col gap-6">
        {/* Why you qualify */}
        <section>
          <p className="font-mono text-[11px] tracking-widest text-muted uppercase mb-3">
            {t("scheme.eligibility", lang)}
          </p>
          <p className="text-[17px] text-inkSoft leading-relaxed">{scheme.eligibility_reason}</p>
        </section>

        {/* Documents */}
        <section>
          <p className="font-mono text-[11px] tracking-widest text-muted uppercase mb-3">
            {t("scheme.documents_needed", lang)}
          </p>
          <div className="grid grid-cols-2 gap-3">
            {(scheme.docs_have || []).map((doc) => (
              <div key={doc} className="flex items-center gap-2 bg-white rounded-2xl border border-[rgba(20,18,16,0.08)] px-3 py-3">
                <CheckCircle2 size={14} className="text-[#2F7D4F] shrink-0" />
                <span className="text-[13px] text-ink leading-tight">{doc}</span>
              </div>
            ))}
            {(scheme.docs_need || []).map((doc) => (
              <div key={doc} className="flex items-center gap-2 bg-white rounded-2xl border border-[#C77A20]/30 px-3 py-3">
                <AlertCircle size={14} className="text-[#C77A20] shrink-0" />
                <span className="text-[13px] text-ink leading-tight">{doc}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Office */}
        {scheme.office && (
          <section>
            <p className="font-mono text-[11px] tracking-widest text-muted uppercase mb-3">
              {t("scheme.nearestOffice", lang)}
            </p>
            <div className="flex items-start gap-3 bg-[#FBE9DD] rounded-2xl px-4 py-4">
              <MapPin size={16} className="text-[#D9542B] shrink-0 mt-0.5" />
              <p className="text-[15px] text-ink">{scheme.office}</p>
            </div>
          </section>
        )}
      </div>

      {/* Download CTA */}
      <div className="px-5 pt-4">
        <button
          onClick={handleDownload}
          disabled={downloading}
          className="w-full h-[68px] rounded-[22px] bg-[#D9542B] text-white font-bold text-[17px] flex items-center justify-center gap-2 shadow-[0_8px_32px_rgba(217,84,43,0.35)] transition-transform active:scale-[0.98] disabled:opacity-70"
        >
          <Download size={20} />
          {downloading ? "Generating…" : t("scheme.download", lang)}
        </button>
      </div>

      <ListenFAB lang={lang} />
    </main>
  );
}
