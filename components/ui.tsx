import React from 'react';

export const Card = ({ children, className = "" }: { children?: React.ReactNode; className?: string }) => (
  <div className={`hairline-panel rounded-2xl p-6 ${className}`}>
    {children}
  </div>
);

export const Badge = ({ level }: { level: string }) => {
  const colors: Record<string, string> = {
    LOW: "bg-[#c8ff3d]/10 text-[#c8ff3d] border-[#c8ff3d]/25",
    MODERATE: "bg-amber-400/10 text-amber-300 border-amber-300/25",
    HIGH: "bg-orange-500/10 text-orange-300 border-orange-400/25",
    EXTREME: "bg-[#ff6b57]/10 text-[#ff8878] border-[#ff6b57]/30 animate-pulse",
  };
  return (
    <span className={`technical-label rounded-full border px-3 py-1 ${colors[level] || colors.LOW}`}>
      {level}
    </span>
  );
};

export const SkeletonCard = ({ className = "" }: { className?: string }) => (
  <div className={`hairline-panel rounded-2xl p-6 animate-pulse ${className}`}>
    <div className="h-4 w-1/3 rounded bg-slate-800 mb-3" />
    <div className="h-6 w-1/2 rounded bg-slate-800 mb-2" />
    <div className="h-3 w-2/3 rounded bg-slate-800" />
  </div>
);
