import React from 'react';

export const Card = ({ children, className = "" }: { children?: React.ReactNode; className?: string }) => (
  <div className={`bg-slate-900 border border-slate-800 rounded-lg p-6 shadow-xl ${className}`}>
    {children}
  </div>
);

export const Badge = ({ level }: { level: string }) => {
  const colors: Record<string, string> = {
    LOW: "bg-emerald-900 text-emerald-200 border-emerald-700",
    MODERATE: "bg-yellow-900 text-yellow-200 border-yellow-700",
    HIGH: "bg-orange-900 text-orange-200 border-orange-700",
    EXTREME: "bg-red-900 text-red-200 border-red-700 animate-pulse",
  };
  return (
    <span className={`px-3 py-1 rounded-full text-xs font-bold border ${colors[level] || colors.LOW}`}>
      {level}
    </span>
  );
};

export const SkeletonCard = ({ className = "" }: { className?: string }) => (
  <div className={`bg-slate-900 border border-slate-800 rounded-lg p-6 shadow-xl animate-pulse ${className}`}>
    <div className="h-4 w-1/3 rounded bg-slate-800 mb-3" />
    <div className="h-6 w-1/2 rounded bg-slate-800 mb-2" />
    <div className="h-3 w-2/3 rounded bg-slate-800" />
  </div>
);