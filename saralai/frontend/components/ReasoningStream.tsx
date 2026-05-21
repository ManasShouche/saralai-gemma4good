"use client";

import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, XCircle, Wrench, User } from "lucide-react";

export type ThoughtType = "profile" | "tool" | "match" | "skip";

export interface Thought {
  id: string;
  type: ThoughtType;
  text: string;
  amount?: string;
}

interface ReasoningStreamProps {
  thoughts: Thought[];
  isStreaming?: boolean;
  liveToken?: string;
}

function ThoughtLine({ thought }: { thought: Thought }) {
  if (thought.type === "match") {
    return (
      <div className="flex items-start gap-2">
        <div className="flex items-center gap-1.5 shrink-0 mt-0.5 px-2 py-0.5 rounded-full bg-[#2F7D4F]/20">
          <CheckCircle2 size={11} className="text-[#2F7D4F]" />
          <span className="font-mono text-[10px] text-[#2F7D4F] uppercase tracking-wide">Match</span>
        </div>
        <span className="text-white/80 text-[13px] leading-relaxed flex-1">{thought.text}</span>
        {thought.amount && (
          <span className="font-mono text-[12px] text-[#2F7D4F] shrink-0">{thought.amount}</span>
        )}
      </div>
    );
  }

  if (thought.type === "skip") {
    return (
      <div className="flex items-start gap-2 opacity-50">
        <div className="flex items-center gap-1.5 shrink-0 mt-0.5 px-2 py-0.5 rounded-full bg-white/10">
          <XCircle size={11} className="text-white/50" />
          <span className="font-mono text-[10px] text-white/50 uppercase tracking-wide">Skip</span>
        </div>
        <span className="text-white/50 text-[13px] leading-relaxed line-through">{thought.text}</span>
      </div>
    );
  }

  if (thought.type === "tool") {
    return (
      <div className="flex items-start gap-2">
        <Wrench size={12} className="text-[#C77A20] shrink-0 mt-1" />
        <span className="font-mono text-[12px] text-[#C77A20] leading-relaxed">{thought.text}</span>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-2">
      <User size={12} className="text-white/40 shrink-0 mt-1" />
      <span className="text-white/70 text-[13px] leading-relaxed">{thought.text}</span>
    </div>
  );
}

export default function ReasoningStream({ thoughts, isStreaming = false, liveToken = "" }: ReasoningStreamProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [thoughts, liveToken]);

  return (
    <div className="rounded-[22px] bg-[#19181A] p-5 max-h-72 overflow-y-auto">
      <p className="font-mono text-[10px] tracking-widest text-white/30 uppercase mb-4">
        Gemma 4 · Reasoning live
      </p>
      <div className="flex flex-col gap-3">
        <AnimatePresence initial={false}>
          {thoughts.filter(Boolean).map((thought) => (
            <motion.div
              key={thought.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8, transition: { duration: 0.2 } }}
              transition={{ duration: 0.3 }}
            >
              <ThoughtLine thought={thought} />
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Live token — streams in character by character */}
        {(liveToken || isStreaming) && (
          <motion.div
            key="live"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-start gap-2"
          >
            <User size={12} className="text-white/30 shrink-0 mt-1" />
            <span className="text-white/50 text-[13px] leading-relaxed">
              {liveToken}
              <span className="inline-block w-[7px] h-[14px] bg-white/50 rounded-sm ml-0.5 align-middle blink" />
            </span>
          </motion.div>
        )}
      </div>
      <div ref={bottomRef} />
    </div>
  );
}
