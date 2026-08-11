'use client';

import { clsx } from 'clsx';

interface LoadingStateProps {
  label?: string;
  variant?: 'full' | 'card';
}

export const LoadingState = ({ label = 'Loading…', variant = 'full' }: LoadingStateProps) => {
  if (variant === 'card') {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center gap-3 text-[#6d6b66]">
        <div className="h-10 w-10 animate-spin border-2 border-[#141414] border-t-[#ff4d00]" />
        <div className="text-xs font-mono">{label}</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center gap-3 p-12 text-[#6d6b66]">
      <div className="h-10 w-10 animate-spin border-2 border-[#141414] border-t-[#ff4d00]" />
      <div className="text-sm font-mono">{label}</div>
    </div>
  );
};
