"use client";

import React, { memo } from "react";
import { motion } from "framer-motion";
import type { DemoHook } from "./demo-carousel";

interface DemoHookCardProps {
  hook: DemoHook;
  index: number;
  visible: boolean;
  isTop: boolean;
}

export const DemoHookCard = memo(function DemoHookCard({
  hook,
  index,
  visible,
  isTop,
}: DemoHookCardProps) {
  const circ = 2 * Math.PI * 14;
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={visible ? { opacity: 1, y: 0 } : { opacity: 0, y: 10 }}
      transition={{ delay: index * 0.08, duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
      className={`rounded-xl border bg-[#0f0f0f] p-3.5 flex flex-col gap-2.5 ${
        isTop ? "border-white/[0.09]" : "border-white/[0.04]"
      }`}
    >
      <div className="flex items-center gap-2.5">
        {/* Score ring */}
        <div className="relative shrink-0 w-9 h-9">
          <svg viewBox="0 0 32 32" className="w-full h-full -rotate-90" aria-hidden="true">
            <circle cx="16" cy="16" r="14" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="2.5" />
            <motion.circle
              cx="16" cy="16" r="14"
              fill="none" stroke={hook.color} strokeWidth="2.5" strokeLinecap="round"
              strokeDasharray={circ}
              initial={{ strokeDashoffset: circ }}
              animate={visible ? { strokeDashoffset: circ * (1 - hook.score / 10) } : { strokeDashoffset: circ }}
              transition={{ duration: 0.9, ease: "easeOut", delay: index * 0.07 + 0.15 }}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-[9px] font-bold font-mono" style={{ color: hook.color }}>{hook.score}</span>
          </div>
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span
              className="text-[7.5px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded"
              style={{ background: `${hook.color}18`, color: hook.color }}
            >
              {hook.type}
            </span>
            <span className="text-white/20 text-[9px] font-mono">{hook.time}</span>
          </div>
        </div>
      </div>

      <p className="text-white/65 text-[11.5px] leading-relaxed">{hook.text}</p>

      {isTop ? (
        <div className="border-t border-white/[0.05] pt-2.5 flex flex-col gap-1.5">
          {(
            [
              ["Platform", hook.platform, "text-white/20"],
              ["Psychology", hook.psychology, "text-white/20"],
              ["Tip", hook.tip, hook.color + "99"],
            ] as const
          ).map(([label, text, labelColor]) => (
            <div key={label} className="flex gap-1.5">
              <span className="text-[8px] font-bold uppercase tracking-wider pt-px shrink-0 w-16" style={{ color: labelColor }}>
                {label}
              </span>
              <p className="text-[10px] text-white/45 leading-relaxed">{text}</p>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-[9.5px] font-mono leading-relaxed border-t border-white/[0.04] pt-2 line-clamp-1" style={{ color: `${hook.color}60` }}>
          {hook.tip}
        </p>
      )}
    </motion.div>
  );
});
