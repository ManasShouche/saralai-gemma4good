"use client";

import { useEffect, useRef, useState } from "react";
import { X, Zap, ZapOff, CameraOff } from "lucide-react";
import TrustStrip from "./TrustStrip";
import { Language, t } from "@/lib/i18n";

const DOC_TABS: Record<Language, string[]> = {
  kn: ["ಆಧಾರ್", "ಪಡಿತರ", "ಇನ್ನಿತರ"],
  hi: ["आधार", "राशन", "अन्य"],
  en: ["Aadhaar", "Ration", "Other"],
};

interface CameraViewProps {
  onCapture: (blob: Blob) => void;
  onClose?: () => void;
  lang?: Language;
  docStatus?: "idle" | "detected";
}

export default function CameraView({
  onCapture,
  onClose,
  lang = "en",
  docStatus = "idle",
}: CameraViewProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [flash, setFlash] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [streamReady, setStreamReady] = useState(false);
  const [camDenied, setCamDenied] = useState(false);

  useEffect(() => {
    let stream: MediaStream | null = null;
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: "environment", width: 1280, height: 720 } })
      .then((s) => {
        stream = s;
        streamRef.current = s;
        if (videoRef.current) {
          videoRef.current.srcObject = s;
          videoRef.current.play().catch((err) => {
            console.error("[CameraView] video.play() rejected:", err);
          });
          setStreamReady(true);
        }
      })
      .catch((err: Error) => {
        console.error("[CameraView] getUserMedia failed:", err.name, err.message);
        setCamDenied(true);
        setStreamReady(false);
      });

    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    };
  }, []);

  const handleCapture = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d")?.drawImage(video, 0, 0);
    canvas.toBlob((blob) => {
      if (blob) onCapture(blob);
    }, "image/jpeg", 0.92);
  };

  const tabs = DOC_TABS[lang];

  if (camDenied) {
    return (
      <div className="fixed inset-0 z-40 bg-black flex flex-col items-center justify-center gap-4 px-8">
        <button
          onClick={onClose}
          className="absolute top-4 left-4 w-10 h-10 rounded-full bg-white/10 flex items-center justify-center"
        >
          <X size={18} color="white" />
        </button>
        <CameraOff size={40} color="#D9542B" />
        <p className="text-white text-center text-[16px] font-medium">
          {lang === "kn"
            ? "ಕ್ಯಾಮೆರಾ ಅನುಮತಿ ನಿರಾಕರಿಸಲಾಗಿದೆ. ಬ್ರೌಸರ್ ಸೆಟ್ಟಿಂಗ್‌ಗಳಲ್ಲಿ ಅನುಮತಿಸಿ."
            : lang === "hi"
            ? "कैमरा अनुमति अस्वीकृत है। ब्राउज़र सेटिंग्स में अनुमति दें।"
            : "Camera permission denied. Please allow camera access in browser settings."}
        </p>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-40 bg-black flex flex-col">
      {/* Top chrome */}
      <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-4 pt-safe-top pt-4 pb-3">
        <button
          onClick={onClose}
          className="w-10 h-10 rounded-full bg-black/40 flex items-center justify-center"
        >
          <X size={18} color="white" />
        </button>
        <TrustStrip lang={lang} dark />
        <button
          onClick={() => setFlash((f) => !f)}
          className="w-10 h-10 rounded-full bg-black/40 flex items-center justify-center"
        >
          {flash ? <Zap size={18} color="#D9542B" /> : <ZapOff size={18} color="white" />}
        </button>
      </div>

      {/* Camera feed */}
      <video
        ref={videoRef}
        className="absolute inset-0 w-full h-full object-cover"
        muted
        playsInline
        autoPlay
      />
      <canvas ref={canvasRef} className="hidden" />

      {/* Corner brackets */}
      {["top-left", "top-right", "bottom-left", "bottom-right"].map((pos) => {
        const isTop = pos.includes("top");
        const isLeft = pos.includes("left");
        return (
          <div
            key={pos}
            className="absolute w-8 h-8 pointer-events-none"
            style={{
              top: isTop ? "20%" : undefined,
              bottom: !isTop ? "20%" : undefined,
              left: isLeft ? "10%" : undefined,
              right: !isLeft ? "10%" : undefined,
              borderTop: isTop ? "3px solid #D9542B" : undefined,
              borderBottom: !isTop ? "3px solid #D9542B" : undefined,
              borderLeft: isLeft ? "3px solid #D9542B" : undefined,
              borderRight: !isLeft ? "3px solid #D9542B" : undefined,
              borderRadius: isTop && isLeft ? "6px 0 0 0" : isTop && !isLeft ? "0 6px 0 0" :
                             !isTop && isLeft ? "0 0 0 6px" : "0 0 6px 0",
            }}
          />
        );
      })}

      {/* Hint text — translated */}
      {!streamReady && !camDenied && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-white/40 border-t-white rounded-full animate-spin" />
        </div>
      )}
      <div className="absolute bottom-48 left-0 right-0 flex justify-center pointer-events-none" suppressHydrationWarning>
        <span className="text-white/70 text-[13px] font-medium text-center px-4">
          {t("scan.aadhaarHint", lang)}
        </span>
      </div>

      {/* Doc status pill */}
      {docStatus === "detected" && (
        <div className="absolute top-1/2 -translate-y-1/2 left-1/2 -translate-x-1/2">
          <div className="px-4 py-2 rounded-full bg-[#2F7D4F]/80 backdrop-blur-sm">
            <span className="text-white font-semibold text-[14px]" suppressHydrationWarning>
              {lang === "kn" ? "ಆಧಾರ್ ಕಂಡುಬಂತು" : lang === "hi" ? "आधार मिला" : "Aadhaar found"}
            </span>
          </div>
        </div>
      )}

      {/* Bottom area */}
      <div className="absolute bottom-0 left-0 right-0 pb-safe-bottom pb-8 flex flex-col items-center gap-4">
        {/* Native script doc tabs */}
        <div className="flex items-center gap-2">
          {tabs.map((tab, i) => (
            <button
              key={i}
              onClick={() => setActiveTab(i)}
              className={`px-4 py-1.5 rounded-full text-[14px] font-medium transition-all min-h-0 min-w-0 ${
                activeTab === i
                  ? "bg-white text-[#161513]"
                  : "bg-white/20 text-white/80"
              }`}
              suppressHydrationWarning
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Shutter button */}
        <button
          onClick={handleCapture}
          disabled={!streamReady}
          className="w-[88px] h-[88px] rounded-full bg-white border-4 border-[#D9542B] flex items-center justify-center disabled:opacity-50 transition-transform active:scale-95"
          aria-label="Capture document"
        >
          <div className="w-[68px] h-[68px] rounded-full bg-[#D9542B]" />
        </button>
      </div>
    </div>
  );
}
