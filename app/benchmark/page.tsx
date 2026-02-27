'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { BacktestResponse } from '@/lib/types';
import { Card, SkeletonCard } from '@/components/ui';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Area,
  ReferenceLine
} from 'recharts';
import { Trophy, TrendingDown, ShieldCheck, Target } from 'lucide-react';

export default function BenchmarkPage() {
  const [data, setData] = useState<BacktestResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [bucketMode, setBucketMode] = useState<'OVERALL' | 'TEMP' | 'REGION'>('OVERALL');

  useEffect(() => {
    api.backtest()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="h-6 w-64 rounded bg-slate-800 animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <SkeletonCard />
          <SkeletonCard />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    );
  }
  if (!data) return <div className="p-8 text-red-500">Failed to load benchmark data.</div>;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">Model Benchmark & Calibration</h1>
        <p className="text-slate-300 text-sm mb-1">
          GERT maintains near-nominal P99 coverage during extreme spikes, while mean models under-cover tail events.
        </p>
        <p className="text-slate-500 text-sm">
          Validating GERT's probabilistic guarantees using historical backtests.
        </p>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {data.metrics.map((model) => (
          <Card key={model.model_name} className={model.model_name.includes("GERT") ? "border-indigo-500/50 bg-indigo-900/10" : "opacity-80"}>
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl font-semibold text-white">{model.model_name}</h2>
              {model.model_name.includes("GERT") && <Trophy className="h-5 w-5 text-yellow-500" />}
            </div>
            
            <p className="text-sm text-slate-400 mb-6 h-10">{model.description}</p>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-950/50 p-3 rounded">
                <div className="text-xs text-slate-500 flex items-center gap-1">
                  <ShieldCheck className="h-3 w-3" /> P99 Coverage
                </div>
                <div className={`text-2xl font-bold ${model.coverage_p99 >= 99 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {model.coverage_p99}%
                </div>
                <div className="text-[10px] text-slate-600">Target: ≥99%</div>
              </div>

              <div className="bg-slate-950/50 p-3 rounded">
                <div className="text-xs text-slate-500 flex items-center gap-1">
                  <TrendingDown className="h-3 w-3" /> Pinball Loss
                </div>
                <div className="text-2xl font-bold text-white">
                  {model.pinball_loss}
                </div>
                <div className="text-[10px] text-slate-600">Lower is better</div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Visualization: Time Series */}
        <Card>
            <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                <TrendingDown className="h-5 w-5 text-indigo-400"/>
                Extreme Event Performance
            </h3>
            <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={data.time_series}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="hour" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                <Legend />
                
                <Line type="monotone" dataKey="actual_load" stroke="#f8fafc" strokeWidth={2} dot={false} name="Actual" />
                <Line type="step" dataKey="baseline_p99" stroke="#94a3b8" strokeDasharray="5 5" name="Baseline P99" />
                <Area type="monotone" dataKey="gert_p99" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} name="GERT P99" />
                </ComposedChart>
            </ResponsiveContainer>
            </div>
        </Card>

        {/* Visualization: Calibration / Reliability */}
        <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Target className="h-5 w-5 text-emerald-400"/>
                  Reliability Diagram (Calibration)
              </h3>
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span className="text-[10px] uppercase tracking-wide">Bucket Mode</span>
                <select
                  value={bucketMode}
                  onChange={(e) => setBucketMode(e.target.value as typeof bucketMode)}
                  className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs"
                >
                  <option value="OVERALL">Overall</option>
                  <option value="TEMP">By Temperature (planned)</option>
                  <option value="REGION">By Region (planned)</option>
                </select>
              </div>
            </div>
            <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.calibration_curve}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="prob_bucket" stroke="#64748b" tick={{fontSize: 10}} />
                <YAxis stroke="#64748b" domain={[0, 1]} />
                <Tooltip 
                    cursor={{fill: '#1e293b'}}
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} 
                />
                <Legend />
                <Bar dataKey="observed_freq" name="Observed Frequency" fill="#10b981" />
                <Bar dataKey="ideal_freq" name="Ideal Frequency" fill="#334155" />
                </BarChart>
            </ResponsiveContainer>
            </div>
            <p className="text-xs text-slate-500 mt-2 text-center">
                A perfectly calibrated model has Observed Frequency matching Ideal Frequency (bars are equal height).
            </p>
        </Card>
      </div>
    </div>
  );
}