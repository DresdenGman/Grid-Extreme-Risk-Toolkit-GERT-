'use client';

import { PredictionOut } from '@/lib/types';

interface QuantileChartProps {
  prediction: PredictionOut;
}

const QUANTILES = [
  { key: 'q50_load_mw', label: 'P50', note: 'Expected', color: '#74e7dd' },
  { key: 'q90_load_mw', label: 'P90', note: 'Stress', color: '#c8ff3d' },
  { key: 'q95_load_mw', label: 'P95', note: 'Severe', color: '#ffd166' },
  { key: 'q99_load_mw', label: 'P99', note: 'Tail', color: '#ff6b57' },
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
    <div className="flex h-full flex-col justify-between gap-7">
      <div className="flex items-start justify-between gap-4">
        <div>
          <span className="technical-label text-slate-600">Forecast target</span>
          <span className="mt-1 block text-base font-medium text-[#f4f1e8]">{targetLabel}</span>
        </div>
        <div className="text-right">
          <span className="technical-label text-slate-600">Available capacity</span>
          <span className="mt-1 block font-mono text-sm text-[#c8ff3d]">{(capacity / 1000).toFixed(1)} GW</span>
        </div>
      </div>

      <div className="relative space-y-4">
        <div className="absolute bottom-0 top-0 w-px bg-[#c8ff3d]/70" style={{ left: `${capacityPosition}%` }}>
          <div className="absolute -top-1 h-2 w-2 -translate-x-1/2 rounded-full bg-[#c8ff3d] shadow-[0_0_12px_rgba(200,255,61,.7)]" />
        </div>
        {QUANTILES.map(({ key, label, note, color }, index) => {
          const value = prediction[key];
          return (
            <div key={key} className="grid grid-cols-[48px_1fr_76px] items-center gap-3">
              <div><span className="block text-xs font-semibold text-slate-200">{label}</span><span className="technical-label text-[8px] text-slate-600">{note}</span></div>
              <div className="relative h-7 overflow-hidden rounded-sm bg-white/[0.035]">
                <div
                  className="h-full rounded-sm transition-[width] duration-700"
                  style={{ width: `${Math.min(100, (value / maximum) * 100)}%`, background: `linear-gradient(90deg, ${color}20, ${color}${index === 3 ? 'd9' : 'a8'})` }}
                />
              </div>
              <span className="text-right font-mono text-xs text-[#f4f1e8]">
                {(value / 1000).toFixed(1)} GW
              </span>
            </div>
          );
        })}
      </div>

      <div className="flex items-start gap-3 border-t border-white/[0.08] pt-4">
        <div className="mt-1 h-2 w-2 rounded-full bg-[#c8ff3d]" />
        <div>
          <p className="text-xs text-slate-400">Capacity marker reveals where each confidence band meets the system boundary.</p>
          <p className="mt-1 text-[10px] text-slate-600">One-hour probability distribution. No synthetic multi-hour curve.</p>
        </div>
      </div>
    </div>
  );
};
