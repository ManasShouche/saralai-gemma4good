"use client";

import { useState, useRef, useCallback, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft, RotateCcw } from "lucide-react";
import { t } from "@/lib/i18n";
import type { Language } from "@/lib/i18n";
import { transcribeAudio } from "@/lib/api";
import HoldToTalk from "@/components/HoldToTalk";
import Waveform from "@/components/Waveform";

// Demo transcript for Rukmini persona — used when ?demo=true is in the URL
const DEMO_TRANSCRIPT = "My husband passed away two years ago. I have two children. No income.";

function SpeakPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const isDemo = searchParams.get("demo") === "true";
  const [lang, setLangState] = useState<Language>(() => {
    if (typeof window === "undefined") return "en";
    return (localStorage.getItem("saralai_lang") as Language) || "en";
  });
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState(isDemo ? DEMO_TRANSCRIPT : "");
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [hasRecorded, setHasRecorded] = useState(isDemo);
  const [seconds, setSeconds] = useState(0);
  const [micError, setMicError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recordingStartRef = useRef<number>(0);

  // Demo mode: set English as language
  useEffect(() => {
    if (isDemo) {
      setLangState("en");
      localStorage.setItem("saralai_lang", "en");
    }
  }, [isDemo]);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      mediaRecorderRef.current?.stop();
      streamRef.current?.getTracks().forEach((t) => t.stop());
      audioCtxRef.current?.close();
    };
  }, []);

  const startRecording = useCallback(async () => {
    setMicError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Waveform analyser
      const ctx = new AudioContext();
      audioCtxRef.current = ctx;
      const src = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      src.connect(analyser);
      analyserRef.current = analyser;

      // MediaRecorder — prefer opus for small file size; fall through to
      // audio/mp4 for Safari / some Android browsers that lack WebM support.
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : MediaRecorder.isTypeSupported("audio/ogg")
        ? "audio/ogg"
        : "audio/mp4";

      chunksRef.current = [];
      const recorder = new MediaRecorder(stream, { mimeType });
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        // Clean up audio pipeline
        streamRef.current?.getTracks().forEach((t) => t.stop());
        audioCtxRef.current?.close().catch(() => {});
        analyserRef.current = null;
        if (timerRef.current) clearInterval(timerRef.current);
        setIsRecording(false);
        setSeconds(0);

        const durationMs = Date.now() - recordingStartRef.current;
        const blob = new Blob(chunksRef.current, { type: mimeType });
        if (blob.size === 0 || durationMs < 1500 || blob.size < 1000) {
          // Too short or empty — tap-release too fast, or silent
          setMicError(
            lang === "kn"
              ? "ಸಾಕಷ್ಟು ಧ್ವನಿ ರೆಕಾರ್ಡ್ ಆಗಲಿಲ್ಲ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ."
              : lang === "hi"
              ? "पर्याप्त आवाज़ रिकॉर्ड नहीं हुई। दोबारा प्रयास करें।"
              : "Not enough audio recorded. Hold longer and speak clearly."
          );
          setHasRecorded(false);
          return;
        }

        setIsTranscribing(true);
        try {
          const result = await transcribeAudio(blob, lang);
          setTranscript(result.transcript || "");
          setHasRecorded(true);
        } catch (err) {
          console.error("[Speak] transcription failed:", err);
          setMicError(
            lang === "kn"
              ? "ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಷನ್ ವಿಫಲವಾಗಿದೆ. ಬ್ಯಾಕೆಂಡ್ ಚಾಲನೆಯಲ್ಲಿದೆಯೇ?"
              : lang === "hi"
              ? "ट्रांसक्रिप्शन विफल। क्या बैकएंड चल रहा है?"
              : "Transcription failed. Is the backend running on port 8000?"
          );
          setHasRecorded(true);
        } finally {
          setIsTranscribing(false);
        }
      };

      mediaRecorderRef.current = recorder;
      recorder.start(250); // collect chunks every 250 ms
      recordingStartRef.current = Date.now();
      setIsRecording(true);
      setSeconds(0);
      timerRef.current = setInterval(() => setSeconds((s) => s + 1), 1000);
    } catch (err) {
      console.error("[Speak] mic access failed:", err);
      setMicError(
        lang === "kn"
          ? "ಮೈಕ್ ಅನುಮತಿ ಬೇಕು"
          : lang === "hi"
          ? "माइक की अनुमति चाहिए"
          : "Microphone access denied."
      );
    }
  }, [lang]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
  }, []);

  const handleConfirm = () => {
    localStorage.setItem("saralai_narrative", transcript);
    router.push(isDemo ? "/results?demo=true" : "/results");
  };

  return (
    <main className="min-h-screen bg-paper flex flex-col pb-10">
      {/* Top bar */}
      <div className="flex items-center gap-3 px-4 pt-5 pb-4">
        <button
          onClick={() => router.back()}
          className="w-10 h-10 rounded-full bg-[rgba(20,18,16,0.06)] flex items-center justify-center"
        >
          <ArrowLeft size={18} className="text-inkSoft" />
        </button>
        {/* Progress bar - step 2 of 3 */}
        <div className="flex-1 flex items-center gap-2">
          <div className="flex-1 h-1.5 rounded-full bg-[rgba(20,18,16,0.08)] overflow-hidden">
            <div className="h-full bg-[#D9542B] rounded-full" style={{ width: "66%" }} />
          </div>
          <span className="font-mono text-[11px] text-muted">2/3</span>
        </div>
      </div>

      <div className="px-5 flex-1 flex flex-col">
        {/* Heading */}
        <div className="mb-8 mt-4">
          <h1 className="text-[30px] font-bold text-ink leading-tight">
            {t("speak.voicePrompt", lang)}
          </h1>
          <p className="text-[17px] text-inkSoft mt-2">
            {t("speak.speakInLang", lang)}
          </p>
        </div>

        {/* Transcribing indicator */}
        {isTranscribing && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 rounded-[22px] bg-[rgba(20,18,16,0.04)] border border-[rgba(20,18,16,0.08)] p-5 flex items-center gap-3"
          >
            <div className="w-5 h-5 border-2 border-[#D9542B]/40 border-t-[#D9542B] rounded-full animate-spin shrink-0" />
            <p className="font-mono text-[13px] text-muted tracking-wide">
              gemma-4-e4b · transcribing…
            </p>
          </motion.div>
        )}

        {/* Transcript box */}
        {transcript && !isTranscribing && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 rounded-[22px] bg-[#FBE9DD] border-2 border-[#D9542B]/30 p-5 min-h-[100px]"
          >
            <p className="text-[17px] text-ink leading-relaxed">{transcript}</p>
          </motion.div>
        )}

        {/* Waveform */}
        <div className="flex justify-center mb-8">
          <Waveform isRecording={isRecording} analyserRef={analyserRef} />
        </div>

        {/* Hold to Talk */}
        <div className="flex flex-col items-center gap-4 flex-1 justify-center">
          <HoldToTalk
            isRecording={isRecording}
            onPointerDown={() => { setMicError(null); startRecording(); }}
            onPointerUp={stopRecording}
          />
          {isRecording && (
            <p className="font-mono text-[17px] text-ink">
              {String(Math.floor(seconds / 60)).padStart(2, "0")}:{String(seconds % 60).padStart(2, "0")}
            </p>
          )}
          {micError && (
            <p className="text-[14px] text-[#D9542B] text-center px-6">{micError}</p>
          )}
          {!isRecording && !isTranscribing && !transcript && !micError && (
            <p className="text-[15px] text-muted text-center">
              {t("speak.hold", lang)}
            </p>
          )}
        </div>
      </div>

      {/* Actions */}
      {hasRecorded && !isTranscribing && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="px-5 mt-6 flex flex-col gap-3"
        >
          <button
            onClick={handleConfirm}
            disabled={!transcript}
            className="w-full h-[68px] rounded-[22px] bg-ink text-white font-bold text-[17px] transition-transform active:scale-[0.98] disabled:opacity-40"
          >
            {t("scan.contStep", lang)}
          </button>
          <button
            onClick={() => { setTranscript(""); setHasRecorded(false); setSeconds(0); setMicError(null); }}
            className="flex items-center justify-center gap-2 py-3 text-muted text-[15px] w-full"
          >
            <RotateCcw size={14} />
            {t("speak.re_record", lang)}
          </button>
        </motion.div>
      )}
    </main>
  );
}

export default function SpeakPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-paper" />}>
      <SpeakPageInner />
    </Suspense>
  );
}
