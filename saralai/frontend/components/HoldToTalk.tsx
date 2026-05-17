"use client";

import { Mic, MicOff } from "lucide-react";

interface HoldToTalkProps {
  isRecording: boolean;
  onPointerDown: () => void;
  onPointerUp: () => void;
}

export default function HoldToTalk({ isRecording, onPointerDown, onPointerUp }: HoldToTalkProps) {
  return (
    <div className="relative flex items-center justify-center">
      {/* Outer halo — only shown while recording */}
      {isRecording && (
        <>
          <div
            className="absolute rounded-full bg-[#D9542B] animate-ping"
            style={{ width: 160, height: 160, opacity: 0.12 }}
          />
          <div
            className="absolute rounded-full bg-[#D9542B]"
            style={{ width: 148, height: 148, opacity: 0.22 }}
          />
        </>
      )}

      <button
        onPointerDown={(e) => {
          (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
          onPointerDown();
        }}
        onPointerUp={onPointerUp}
        onPointerLeave={onPointerUp}
        onPointerCancel={onPointerUp}
        style={{
          width: 124,
          height: 124,
          borderRadius: "50%",
          background: isRecording ? "#D9542B" : "#161513",
          boxShadow: isRecording
            ? "0 14px 36px rgba(217,84,43,0.47)"
            : "0 8px 24px rgba(0,0,0,0.18)",
          transition: "background 0.2s, box-shadow 0.2s, transform 0.1s",
          transform: isRecording ? "scale(1.04)" : "scale(1)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          border: "none",
          cursor: "pointer",
          touchAction: "none",
          userSelect: "none",
          WebkitUserSelect: "none",
        }}
        className="relative z-10 select-none"
        aria-label={isRecording ? "Recording — release to stop" : "Hold to talk"}
      >
        {isRecording
          ? <MicOff size={36} color="white" />
          : <Mic size={36} color="white" />
        }
      </button>
    </div>
  );
}
