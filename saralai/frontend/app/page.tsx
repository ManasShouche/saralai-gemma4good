"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, ScanLine, Mic, ClipboardList, Bell, HelpCircle, ChevronRight, ShieldCheck } from "lucide-react";
import { motion } from "framer-motion";
import { t, setLanguage } from "@/lib/i18n";
import type { Language } from "@/lib/i18n";
import TrustStrip from "@/components/TrustStrip";
import GiantCTA from "@/components/GiantCTA";
import LanguageToggle from "@/components/LanguageToggle";
import ListenFAB from "@/components/ListenFAB";

export default function Home() {
  const router = useRouter();
  const [lang, setLangState] = useState<Language>("en");
  const [userName, setUserName] = useState<string | null>(null);
  const [lastVisit, setLastVisit] = useState<{ count: number } | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem("saralai_lang") as Language | null;
    if (stored) {
      setLangState(stored);
      setLanguage(stored);
    } else {
      localStorage.setItem("saralai_lang", "en");
      setLanguage("en");
    }
    // Read name from most recent Aadhaar scan (stored by scan page)
    const savedName = localStorage.getItem("saralai_user_name");
    if (savedName) setUserName(savedName);
    // Read last visit data
    const lv = localStorage.getItem("saralai_last_visit");
    if (lv) {
      try { setLastVisit(JSON.parse(lv)); } catch {}
    }
  }, []);

  const handleLanguageChange = (newLang: Language) => {
    setLangState(newLang);
    setLanguage(newLang);
    localStorage.setItem("saralai_lang", newLang);
  };

  const [showNoNotif, setShowNoNotif] = useState(false);

  // Permissions pre-check — request camera + mic upfront so dialogs don't interrupt mid-flow
  type PermState = "unknown" | "pending" | "granted" | "denied";
  const [permState, setPermState] = useState<PermState>("unknown");

  const checkPermissions = useCallback(async () => {
    if (typeof window === "undefined" || !navigator.permissions) return;
    try {
      const [cam, mic] = await Promise.all([
        navigator.permissions.query({ name: "camera" as PermissionName }),
        navigator.permissions.query({ name: "microphone" as PermissionName }),
      ]);
      if (cam.state === "granted" && mic.state === "granted") {
        setPermState("granted");
      } else if (cam.state === "denied" || mic.state === "denied") {
        setPermState("denied");
      } else {
        setPermState("pending");
      }
    } catch {
      // Some browsers don't support querying camera/mic — hide banner
      setPermState("granted");
    }
  }, []);

  useEffect(() => { checkPermissions(); }, [checkPermissions]);

  const requestPermissions = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      stream.getTracks().forEach((t) => t.stop()); // release immediately
      setPermState("granted");
    } catch {
      setPermState("denied");
    }
  };

  // Detect ?demo=true and propagate it through the flow
  const [isDemo, setIsDemo] = useState(false);
  useEffect(() => {
    if (typeof window !== "undefined" && new URLSearchParams(window.location.search).get("demo") === "true") {
      setIsDemo(true);
    }
  }, []);
  const demoQ = isDemo ? "?demo=true" : "";

  const SECONDARY_ACTIONS = [
    { key: "home.actScan", icon: ScanLine, href: `/scan${demoQ}` },
    { key: "home.actSpeak", icon: Mic, href: `/speak${demoQ}` },
    { key: "home.actStatus", icon: ClipboardList, href: `/results${demoQ}` },
  ];

  return (
    <main className="relative min-h-screen bg-paper flex flex-col px-5 pt-5 pb-28 overflow-x-hidden">
      {/* Header */}
      <header className="relative flex items-center justify-between mb-8">
        <button className="w-10 h-10 rounded-full bg-[rgba(20,18,16,0.06)] flex items-center justify-center">
          <HelpCircle size={18} className="text-inkSoft" />
        </button>
        <TrustStrip lang={lang} />
        <button
          onClick={() => { setShowNoNotif(true); setTimeout(() => setShowNoNotif(false), 2500); }}
          className="w-10 h-10 rounded-full bg-[rgba(20,18,16,0.06)] flex items-center justify-center"
        >
          <Bell size={18} className="text-inkSoft" />
        </button>
        {showNoNotif && (
          <div className="absolute top-16 right-5 z-50 bg-ink text-white text-[13px] font-medium px-4 py-2 rounded-full shadow-lg">
            No new notifications
          </div>
        )}
      </header>

      {/* Language toggle */}
      <div className="flex justify-center mb-8">
        <LanguageToggle value={lang} onChange={handleLanguageChange} />
      </div>

      {/* Permissions banner — shown until camera + mic are granted */}
      {permState === "pending" && (
        <motion.button
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          onClick={requestPermissions}
          className="w-full flex items-center gap-3 bg-[#FBE9DD] border border-[#D9542B]/20 rounded-2xl px-4 py-3 mb-6 text-left"
        >
          <div className="w-9 h-9 rounded-xl bg-[#D9542B]/15 flex items-center justify-center shrink-0">
            <ShieldCheck size={18} className="text-[#D9542B]" />
          </div>
          <div className="flex-1">
            <p className="font-semibold text-ink text-[15px] leading-tight">Allow camera &amp; microphone</p>
            <p className="text-[12px] text-inkSoft">Tap to grant — needed for Aadhaar scan and voice</p>
          </div>
          <ChevronRight size={16} className="text-[#D9542B] shrink-0" />
        </motion.button>
      )}
      {permState === "denied" && (
        <div className="w-full flex items-center gap-3 bg-[rgba(199,122,32,0.1)] border border-[#C77A20]/30 rounded-2xl px-4 py-3 mb-6">
          <div className="w-9 h-9 rounded-xl bg-[#C77A20]/15 flex items-center justify-center shrink-0">
            <ShieldCheck size={18} className="text-[#C77A20]" />
          </div>
          <div className="flex-1">
            <p className="font-semibold text-ink text-[14px] leading-tight">Camera / mic blocked</p>
            <p className="text-[12px] text-inkSoft">Open browser site settings and allow both</p>
          </div>
        </div>
      )}

      {/* Greeting */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="mb-6"
      >
        <p className="text-[17px] text-muted">{t("home.hi", lang)}</p>
        <h1 className="text-[30px] font-bold text-ink leading-tight">
          {userName || t("home.greeting_generic", lang)}
        </h1>
      </motion.div>

      {/* Giant CTA */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
        className="mb-6"
      >
        <GiantCTA
          lang={lang}
          label={t("home.primaryFind", lang)}
          sub={t("home.primaryFindSub", lang)}
          icon={<Sparkles size={28} />}
          href={`/scan${demoQ}`}
        />
      </motion.div>

      {/* Recent visit strip — only shown if user has run a search before */}
      {lastVisit && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.18, ease: [0.22, 1, 0.36, 1] }}
          className="mb-6"
        >
          <button
            onClick={() => router.push("/results")}
            className="w-full flex items-center gap-3 bg-[#FBE9DD] rounded-2xl px-4 py-3"
          >
            <div className="w-10 h-10 rounded-xl bg-[#D9542B]/20 flex items-center justify-center">
              <ClipboardList size={18} className="text-[#D9542B]" />
            </div>
            <div className="flex-1 min-w-0 text-left">
              <p className="font-semibold text-ink text-[15px] leading-tight">{t("home.recents", lang)}</p>
              <p className="text-[13px] text-inkSoft">
                {lastVisit.count} {lang === "kn" ? "ಯೋಜನೆ ಸಿಕ್ಕವು" : lang === "hi" ? "योजनाएं मिलीं" : "schemes matched"}
              </p>
            </div>
            <ChevronRight size={16} className="text-muted shrink-0" />
          </button>
        </motion.div>
      )}

      {/* Secondary actions */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.25, ease: [0.22, 1, 0.36, 1] }}
      >
        <p className="font-mono text-[11px] tracking-widest text-muted uppercase mb-3">
          {t("home.smallActions", lang)}
        </p>
        <div className="flex flex-col">
          {SECONDARY_ACTIONS.map((action, i) => {
            const Icon = action.icon;
            return (
              <div key={action.key}>
                {i > 0 && <div className="h-px bg-[rgba(20,18,16,0.06)] mx-2" />}
                <button
                  onClick={() => router.push(action.href)}
                  className="flex items-center gap-3 py-4 px-2 w-full text-left transition-colors hover:bg-[rgba(20,18,16,0.03)] rounded-xl"
                >
                  <div className="w-8 h-8 rounded-lg bg-[rgba(20,18,16,0.06)] flex items-center justify-center">
                    <Icon size={16} className="text-inkSoft" />
                  </div>
                  <span className="text-[17px] text-ink font-medium flex-1">{t(action.key, lang)}</span>
                  <ChevronRight size={15} className="text-muted" />
                </button>
              </div>
            );
          })}
        </div>
      </motion.div>

      {/* Listen FAB */}
      <ListenFAB lang={lang} />

      {/* Bottom safe area */}
      <div className="h-4" />
    </main>
  );
}
