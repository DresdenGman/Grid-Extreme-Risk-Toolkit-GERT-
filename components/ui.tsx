import React from 'react';

export const Card = ({ children, className = "" }: { children?: React.ReactNode; className?: string }) => (
  <div className={`hairline-panel rounded-2xl p-6 ${className}`}>
    {children}
  </div>
);

export const Badge = ({ level }: { level: string }) => {
  const colors: Record<string, string> = {
    LOW: "bg-transparent text-[#141414] border-[#141414]",
    MODERATE: "bg-amber-300 text-[#141414] border-[#141414]",
    HIGH: "bg-[#ff4d00] text-white border-[#141414]",
    EXTREME: "bg-[#c52f19] text-white border-[#141414] animate-pulse",
  };
  return (
    <span className={`technical-label border px-3 py-1 ${colors[level] || colors.LOW}`}>
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
