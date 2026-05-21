"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, RotateCcw } from "lucide-react";
import { t } from "@/lib/i18n";
import type { Language } from "@/lib/i18n";
import { extractDocument } from "@/lib/api";
import CameraView from "@/components/CameraView";
import FieldChip from "@/components/FieldChip";
import ListenFAB from "@/components/ListenFAB";

type ScanState = "camera" | "extracting" | "confirm";

interface ExtractedField {
  key: string;
  value: string;
  confidence: number;
}

const FIELD_LABELS: Record<string, Record<Language, string>> = {
  name:           { en: "Name",           hi: "नाम",         kn: "ಹೆಸರು" },
  dob:            { en: "Date of birth",  hi: "जन्म तिथि",   kn: "ಜನ್ಮ ದಿನ" },
  gender:         { en: "Gender",         hi: "लिंग",         kn: "ಲಿಂಗ" },
  district:       { en: "District",       hi: "ज़िला",        kn: "ಜಿಲ್ಲೆ" },
  state:          { en: "State",          hi: "राज्य",        kn: "ರಾಜ್ಯ" },
  aadhaar_number: { en: "Aadhaar",        hi: "आधार",         kn: "ಆಧಾರ್" },
};

// Demo data for Rukmini persona — used when ?demo=true is in the URL
const DEMO_FIELDS: ExtractedField[] = [
  { key: "name", value: "Rukmini Devi", confidence: 0.96 },
  { key: "dob", value: "1973-04-15", confidence: 0.93 },
  { key: "gender", value: "F", confidence: 0.99 },
  { key: "district", value: "Tumkur", confidence: 0.91 },
  { key: "state", value: "Karnataka", confidence: 0.94 },
  { key: "aadhaar_number", value: "XXXX XXXX 4521", confidence: 0.97 },
];

function ScanPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const isDemo = searchParams.get("demo") === "true";
  const [lang, setLangState] = useState<Language>(() => {
    if (typeof window === "undefined") return "en";
    return (localStorage.getItem("saralai_lang") as Language) || "en";
  });
  const [scanState, setScanState] = useState<ScanState>(isDemo ? "confirm" : "camera");
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [fields, setFields] = useState<ExtractedField[]>([]);
  const [elapsed, setElapsed] = useState(0);
  const [rawText, setRawText] = useState<string | null>(null);
  const [showRaw, setShowRaw] = useState(false);
  const [extractError, setExtractError] = useState<string | null>(null);

  // Demo mode: pre-fill Rukmini's fields on mount
  useEffect(() => {
    if (isDemo) {
      setFields(DEMO_FIELDS);
      setElapsed(2.8);
    }
  }, [isDemo]);

  const handleCapture = async (blob: Blob, docType: string = "aadhaar") => {
    if (scanState !== "camera") return; // prevent double-capture
    // Revoke previous blob URL to prevent memory leak
    setCapturedImage((prev) => { if (prev) URL.revokeObjectURL(prev); return prev; });
    const url = URL.createObjectURL(blob);
    setCapturedImage(url);
    setScanState("extracting");
    setFields([]);
    setRawText(null);
    setShowRaw(false);
    setExtractError(null);
    const start = Date.now();

    try {
      await extractDocument(
        blob,
        docType,
        (field) => setFields((prev) => {
          const idx = prev.findIndex((f) => f.key === field.key);
          if (idx >= 0) {
            const next = [...prev];
            next[idx] = field;
            return next;
          }
          return [...prev, field];
        }),
        () => {
          setElapsed(Math.round((Date.now() - start) / 100) / 10);
          setScanState("confirm");
        },
        (errMsg) => {
          console.error("[Scan] extraction error:", errMsg);
          setExtractError(errMsg || "Extraction failed");
          setScanState("confirm");
        },
        (text) => setRawText(text)
      );
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      console.error("[Scan] fetch failed:", msg);
      setExtractError("Could not reach the backend. Is it running on port 8000?");
      setScanState("confirm");
    }
  };

  const handleConfirm = () => {
    const profile = Object.fromEntries(fields.map((f) => [f.key, f.value]));
    localStorage.setItem("saralai_profile", JSON.stringify(profile));
    // Persist name so home screen can greet the user by name
    if (profile.name) localStorage.setItem("saralai_user_name", profile.name);
    router.push(isDemo ? "/speak?demo=true" : "/speak");
  };

  if (scanState === "camera") {
    return (
      <CameraView
        lang={lang}
        onCapture={handleCapture}
        onClose={() => router.back()}
      />
    );
  }

  return (
    <main className="min-h-screen bg-paper flex flex-col pb-28">
      {/* Top bar */}
      <div className="flex items-center gap-3 px-4 pt-5 pb-4">
        <button
          onClick={() => { setScanState("camera"); setFields([]); setExtractError(null); setCapturedImage((prev) => { if (prev) URL.revokeObjectURL(prev); return null; }); }}
          className="w-10 h-10 rounded-full bg-[rgba(20,18,16,0.06)] flex items-center justify-center"
        >
          <ArrowLeft size={18} className="text-inkSoft" />
        </button>
        {/* Progress bar */}
        <div className="flex-1 flex items-center gap-2">
          <div className="flex-1 h-1.5 rounded-full bg-[rgba(20,18,16,0.08)] overflow-hidden">
            <div className="h-full bg-[#D9542B] rounded-full" style={{ width: "33%" }} />
          </div>
          <span className="font-mono text-[11px] text-muted">1/3</span>
        </div>
      </div>

      <div className="px-5 flex-1">
        {/* Document thumbnail */}
        {capturedImage && (
          <div className="mb-5">
            <img
              src={capturedImage}
              alt="Captured document"
              className="w-full h-36 object-cover rounded-[22px] opacity-80"
            />
          </div>
        )}

        {/* Error banner */}
        {extractError && scanState === "confirm" && (
          <div className="mb-4 rounded-2xl bg-[rgba(199,122,32,0.12)] border border-[#C77A20]/30 px-4 py-3">
            <p className="text-[13px] font-semibold text-[#C77A20]">Extraction failed</p>
            <p className="text-[12px] text-inkSoft mt-0.5">{extractError}</p>
          </div>
        )}

        {/* Heading */}
        <div className="mb-5">
          <h2 className="text-[22px] font-bold text-ink">
            {scanState === "extracting"
              ? t("scan.extracting", lang)
              : extractError
              ? (lang === "kn" ? "ದೋಷ ಸಂಭವಿಸಿದೆ" : lang === "hi" ? "कुछ गलत हुआ" : "Something went wrong")
              : t("scan.confirm", lang)}
          </h2>
          {scanState === "extracting" && (
            <p className="font-mono text-[12px] text-muted mt-1 tracking-wide">
              gemma-4-e4b · reading…
            </p>
          )}
          {scanState === "confirm" && elapsed > 0 && (
            <p className="font-mono text-[12px] text-muted mt-1 tracking-wide">
              gemma-4-e4b · {elapsed}s
            </p>
          )}
        </div>

        {/* Field chips */}
        <div className="flex flex-col gap-3">
          <AnimatePresence>
            {fields.map((field) => (
              <FieldChip
                key={field.key}
                fieldKey={field.key}
                label={FIELD_LABELS[field.key]?.[lang] ?? field.key}
                value={field.value}
                confidence={field.confidence}
              />
            ))}
          </AnimatePresence>

          {/* Loading placeholder */}
          {scanState === "extracting" && fields.length === 0 && (
            <div className="flex flex-col gap-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-16 rounded-2xl bg-[rgba(20,18,16,0.04)] animate-pulse" />
              ))}
            </div>
          )}

          {/* Raw OCR text — collapsible verification panel */}
          {rawText && scanState === "confirm" && (
            <div className="mt-4">
              <button
                onClick={() => setShowRaw((v) => !v)}
                className="flex items-center gap-2 w-full py-2 text-left"
              >
                <span className="font-mono text-[11px] tracking-widest text-muted uppercase">
                  Raw OCR output
                </span>
                <span className="font-mono text-[11px] text-muted ml-auto">
                  {showRaw ? "▲ hide" : "▼ show"}
                </span>
              </button>
              {showRaw && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="rounded-2xl bg-[rgba(20,18,16,0.04)] border border-[rgba(20,18,16,0.08)] px-4 py-3 overflow-hidden"
                >
                  <pre className="font-mono text-[11px] text-inkSoft whitespace-pre-wrap break-words leading-relaxed">
                    {rawText}
                  </pre>
                </motion.div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      {scanState === "confirm" && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="px-5 pt-4 flex flex-col gap-3"
        >
          <button
            onClick={handleConfirm}
            className="w-full h-[68px] rounded-[22px] bg-ink text-white font-bold text-[17px] transition-transform active:scale-[0.98]"
          >
            {t("scan.contStep", lang)}
          </button>
          <button
            onClick={() => { setScanState("camera"); setFields([]); setExtractError(null); setCapturedImage((prev) => { if (prev) URL.revokeObjectURL(prev); return null; }); }}
            className="w-full flex items-center justify-center gap-2 py-3 text-muted text-[15px]"
          >
            <RotateCcw size={14} />
            {t("scan.retake", lang)}
          </button>
        </motion.div>
      )}

      <ListenFAB lang={lang} bottom={100} />
    </main>
  );
}

export default function ScanPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-paper" />}>
      <ScanPageInner />
    </Suspense>
  );
}
