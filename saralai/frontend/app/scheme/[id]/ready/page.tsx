"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { X, CheckCircle2, MapPin, FileText, Share2, AlertCircle, Camera } from "lucide-react";
import { t } from "@/lib/i18n";
import type { Language } from "@/lib/i18n";
import { generateForm } from "@/lib/api";

export default function ReadyPage() {
  const params = useParams();
  const router = useRouter();
  const [lang, setLangState] = useState<Language>("en");
  const [downloading, setDownloading] = useState(false);
  const id = params.id as string;

  useEffect(() => {
    const stored = localStorage.getItem("saralai_lang") as Language | null;
    if (stored) setLangState(stored);
  }, []);

  const handleDownload = async () => {
    if (downloading) return;
    setDownloading(true);
    try {
      let profile: Record<string, string> = {};
      try { profile = JSON.parse(sessionStorage.getItem("saralai_profile") || "{}"); } catch {}
      const blob = await generateForm(id, profile);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `form_${id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // silently fail — form generation is best-effort
    } finally {
      setDownloading(false);
    }
  };

  const handleShare = async () => {
    if (navigator.share) {
      await navigator.share({ title: "SaralAI form", text: "I found a welfare scheme that I qualify for!" });
    }
  };

  return (
    <main className="min-h-screen bg-paper flex flex-col px-5 pt-5 pb-10">
      {/* Top row */}
      <div className="flex items-center justify-between mb-8">
        <button
          onClick={() => router.push("/")}
          className="w-10 h-10 rounded-full bg-[rgba(20,18,16,0.06)] flex items-center justify-center"
        >
          <X size={18} className="text-inkSoft" />
        </button>
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#2F7D4F]/15">
          <span className="font-mono text-[11px] tracking-widest text-[#2F7D4F] uppercase">Ready · 1/1</span>
        </div>
        <div className="w-10" />
      </div>

      {/* Success indicator */}
      <motion.div
        initial={{ scale: 0.6, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5, type: "spring", bounce: 0.4 }}
        className="flex flex-col items-center mb-8"
      >
        <div className="relative flex items-center justify-center">
          <div className="absolute w-24 h-24 rounded-full bg-[#2F7D4F]/10 animate-ping" style={{ animationDuration: "2s" }} />
          <div className="absolute w-20 h-20 rounded-full bg-[#2F7D4F]/15" />
          <div className="w-[76px] h-[76px] rounded-full bg-[#2F7D4F] flex items-center justify-center z-10">
            <CheckCircle2 size={36} color="white" />
          </div>
        </div>
      </motion.div>

      {/* Title */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="text-center mb-8"
      >
        <h1 className="text-[32px] font-bold text-ink mb-2">{t("ready.formReady", lang)}</h1>
        <p className="text-[17px] text-inkSoft">{t("ready.formReadySub", lang)}</p>
      </motion.div>

      <div className="flex flex-col gap-4 flex-1">
        {/* Form preview card */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-[22px] border border-[rgba(20,18,16,0.08)] px-5 py-4 flex items-center gap-4"
        >
          <div className="w-12 h-12 rounded-xl bg-[#FBE9DD] flex items-center justify-center">
            <FileText size={22} className="text-[#D9542B]" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-ink text-[15px] truncate">form_{id}.pdf</p>
            <p className="text-[13px] text-muted">Pre-filled · ready to print</p>
          </div>
        </motion.div>

        {/* Office card */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.38 }}
          className="bg-[#FBE9DD] rounded-[22px] px-5 py-4 flex items-start gap-3"
        >
          <MapPin size={18} className="text-[#D9542B] shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-ink text-[15px]">{t("ready.takeTo", lang)}</p>
            <p className="text-[13px] text-inkSoft mt-0.5">{t("ready.openOffice", lang)}</p>
          </div>
        </motion.div>

        {/* What to bring */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.46 }}
        >
          <p className="font-mono text-[11px] tracking-widest text-muted uppercase mb-3">
            {t("ready.bring", lang)}
          </p>
          <div className="flex flex-col gap-2">
            <div className="flex items-start gap-3 bg-white rounded-2xl border border-[#C77A20]/30 px-4 py-3">
              <AlertCircle size={15} className="text-[#C77A20] shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-ink text-[14px]">{t("ready.bringDeath", lang)}</p>
                <p className="text-[12px] text-muted">{t("ready.bringDeathHint", lang)}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 bg-white rounded-2xl border border-[rgba(20,18,16,0.08)] px-4 py-3">
              <Camera size={15} className="text-inkSoft shrink-0" />
              <p className="text-[14px] text-ink">{t("ready.bringPhoto", lang)}</p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Action buttons */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.55 }}
        className="mt-6 flex flex-col gap-3"
      >
        <button
          onClick={handleDownload}
          disabled={downloading}
          className="w-full h-[68px] rounded-[22px] bg-[#D9542B] text-white font-bold text-[17px] flex items-center justify-center gap-2 shadow-[0_8px_32px_rgba(217,84,43,0.28)] active:scale-[0.98] transition-transform disabled:opacity-60"
        >
          <FileText size={20} />
          {downloading ? "..." : t("ready.open", lang)}
        </button>
        <button
          onClick={handleShare}
          className="w-full h-[68px] rounded-[22px] bg-ink text-white font-bold text-[17px] flex items-center justify-center gap-2 active:scale-[0.98] transition-transform"
        >
          <Share2 size={20} />
          {t("ready.share", lang)}
        </button>
      </motion.div>
    </main>
  );
}
