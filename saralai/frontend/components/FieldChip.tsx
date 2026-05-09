"use client";

import { motion } from "framer-motion";
import { AlertTriangle } from "lucide-react";

interface FieldChipProps {
  fieldKey: string;
  label: string;
  value: string;
  confidence: number;
  native?: string;
}

export default function FieldChip({ label, value, confidence, native }: FieldChipProps) {
  const pct = Math.round(confidence * 100);
  const lowConf = confidence < 0.7;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className="flex items-center gap-3 bg-white rounded-2xl border border-[rgba(20,18,16,0.08)] px-4 py-3"
    >
      {/* Icon badge */}
      <div className="w-9 h-9 rounded-xl bg-[#FBE9DD] flex items-center justify-center shrink-0">
        <span className="text-[#D9542B] text-sm font-bold">{label.charAt(0).toUpperCase()}</span>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className="font-mono text-[11px] tracking-widest text-[#7A736C] uppercase">{label}</p>
        <p className="text-[19px] font-bold text-[#161513] leading-tight truncate">{value}</p>
        {native && (
          <p className="text-[13px] text-[#7A736C] font-kan">{native}</p>
        )}
      </div>

      {/* Confidence */}
      <div className={`flex items-center gap-1 shrink-0 ${lowConf ? "text-[#C77A20]" : "text-[#7A736C]"}`}>
        {lowConf && <AlertTriangle size={12} />}
        <span className="font-mono text-[12px]">{pct}%</span>
      </div>
    </motion.div>
  );
}
