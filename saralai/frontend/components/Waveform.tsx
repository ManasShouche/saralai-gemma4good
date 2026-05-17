"use client";

import { useEffect, useRef } from "react";

interface WaveformProps {
  isRecording: boolean;
  analyserRef?: React.RefObject<AnalyserNode | null>;
  accent?: string;
}

const BAR_COUNT = 20;

export default function Waveform({ isRecording, analyserRef, accent = "#D9542B" }: WaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef<number>(0);
  const dataRef = useRef<Uint8Array>(new Uint8Array(BAR_COUNT));

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const draw = () => {
      if (analyserRef?.current && isRecording) {
        const buf = new Uint8Array(analyserRef.current.frequencyBinCount);
        analyserRef.current.getByteFrequencyData(buf);
        // Downsample to BAR_COUNT bars
        const step = Math.floor(buf.length / BAR_COUNT);
        for (let i = 0; i < BAR_COUNT; i++) {
          dataRef.current[i] = buf[i * step] ?? 0;
        }
      } else if (!isRecording) {
        // Animate to flat line
        for (let i = 0; i < BAR_COUNT; i++) {
          dataRef.current[i] = Math.max(0, (dataRef.current[i] ?? 0) - 8);
        }
      } else {
        // Idle random animation
        for (let i = 0; i < BAR_COUNT; i++) {
          dataRef.current[i] = Math.floor(30 + Math.random() * 60);
        }
      }

      const W = canvas.width;
      const H = canvas.height;
      ctx.clearRect(0, 0, W, H);

      const barW = 5;
      const gap = (W - BAR_COUNT * barW) / (BAR_COUNT - 1);

      for (let i = 0; i < BAR_COUNT; i++) {
        const val = dataRef.current[i] ?? 0;
        const barH = Math.max(4, (val / 255) * H);
        const x = i * (barW + gap);
        const y = (H - barH) / 2;

        ctx.fillStyle = isRecording ? accent : "rgba(20,18,16,0.12)";
        ctx.beginPath();
        if (typeof ctx.roundRect === "function") {
          ctx.roundRect(x, y, barW, barH, 99);
        } else {
          const r = Math.min(barW / 2, barH / 2);
          ctx.moveTo(x + r, y);
          ctx.arcTo(x + barW, y, x + barW, y + barH, r);
          ctx.arcTo(x + barW, y + barH, x, y + barH, r);
          ctx.arcTo(x, y + barH, x, y, r);
          ctx.arcTo(x, y, x + barW, y, r);
          ctx.closePath();
        }
        ctx.fill();
      }

      rafRef.current = requestAnimationFrame(draw);
    };

    rafRef.current = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(rafRef.current);
  }, [isRecording, analyserRef, accent]);

  return (
    <canvas
      ref={canvasRef}
      width={200}
      height={48}
      className="w-full max-w-[200px] h-12"
    />
  );
}
