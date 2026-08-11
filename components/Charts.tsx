'use client';

import { PredictionOut } from '@/lib/types';

interface QuantileChartProps {
  prediction: PredictionOut;
}

const QUANTILES = [
  { key: 'q50_load_mw', label: 'P50', color: 'bg-indigo-400' },
  { key: 'q90_load_mw', label: 'P90', color: 'bg-blue-400' },
  { key: 'q95_load_mw', label: 'P95', color: 'bg-amber-400' },
  { key: 'q99_load_mw', label: 'P99', color: 'bg-red-400' },
] as const;

export const QuantileChart = ({ prediction }: QuantileChartProps) => {
  const capacity = Number(prediction.diagnostics.capacity_used ?? 60000);
  const maximum = Math.max(capacity, prediction.q99_load_mw) * 1.08;
  const capacityPosition = Math.min(100, (capacity / maximum) * 100);
  const targetLabel = new Date(prediction.timestamp).toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });

  return (
    <div className="h-full flex flex-col justify-center gap-6 px-2 md:px-6">
      <div className="flex flex-col gap-1">
        <span className="text-xs font-mono text-slate-500">Target hour</span>
        <span className="text-sm font-semibold text-slate-200">{targetLabel}</span>
      </div>

      <div className="space-y-5">
        {QUANTILES.map(({ key, label, color }) => {
          const value = prediction[key];
          return (
            <div key={key} className="grid grid-cols-[42px_1fr_78px] items-center gap-3">
              <span className="text-xs font-bold text-slate-400">{label}</span>
              <div className="relative h-3 rounded-full bg-slate-800 overflow-visible">
                <div
                  className={`h-3 rounded-full ${color}`}
                  style={{ width: `${Math.min(100, (value / maximum) * 100)}%` }}
                />
                <div
                  className="absolute -top-2 h-7 w-px bg-emerald-300"
                  style={{ left: `${capacityPosition}%` }}
                  title={`Capacity ${(capacity / 1000).toFixed(1)} GW`}
                />
              </div>
              <span className="text-right text-xs font-mono text-slate-200">
                {(value / 1000).toFixed(1)} GW
              </span>
            </div>
          );
        })}
      </div>

      <div className="flex items-center justify-between border-t border-slate-800 pt-4 text-xs">
        <span className="text-slate-500">Green marker: available capacity</span>
        <span className="font-mono text-emerald-300">{(capacity / 1000).toFixed(1)} GW</span>
      </div>
      <p className="text-[11px] text-slate-600">
        One-hour target distribution. No synthetic multi-hour curve is displayed.
      </p>
    </div>
  );
};
