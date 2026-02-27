'use client';

import { clsx } from 'clsx';

interface LoadingStateProps {
  label?: string;
  variant?: 'full' | 'card';
}

export const LoadingState = ({ label = 'Loading…', variant = 'full' }: LoadingStateProps) => {
  if (variant === 'card') {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center gap-3 text-slate-500">
        <div className="w-10 h-10 border-2 border-slate-700 border-t-indigo-500 rounded-full animate-spin" />
        <div className="text-xs font-mono">{label}</div>
      </div>
    );
  }

  return (
    <div className="p-12 flex flex-col items-center justify-center gap-3 text-slate-500">
      <div className="w-10 h-10 border-2 border-slate-700 border-t-indigo-500 rounded-full animate-spin" />
      <div className="text-sm font-mono">{label}</div>
    </div>
  );
};

