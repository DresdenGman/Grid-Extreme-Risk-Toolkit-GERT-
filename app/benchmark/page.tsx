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
      .then((env) => setData(env.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="h-6 w-64 rounded bg-[#d0cfca] animate-pulse" />
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
  if (!data) return <div className="p-8 text-[#b42318]">Failed to load benchmark data.</div>;

  return (
    <div className="space-y-8">
      <div className="border-b border-white/[0.09] pb-7">
        <span className="technical-label text-[#175a73]">Evidence layer / Model governance</span>
        <h1 className="display-serif mt-3 text-4xl tracking-[-0.045em] text-[#141414] sm:text-6xl">Trust is a measured<br />property.</h1>
        <p className="text-[#454545] text-sm mb-1">
          Compare tail coverage, loss and reliability before any artifact earns production authority.
        </p>
        <p className="text-[#6d6b66] text-sm">
          Validating GERT's probabilistic guarantees using historical backtests.
        </p>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {data.metrics.map((model) => (
          <Card key={model.model_name} className={model.model_name.includes("GERT") ? "border-[#141414] bg-[#ff4d00]/10" : "opacity-80"}>
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl font-semibold text-[#141414]">{model.model_name}</h2>
              {model.model_name.includes("GERT") && <Trophy className="h-5 w-5 text-yellow-500" />}
            </div>
            
            <p className="text-sm text-[#4f4e4a] mb-6 h-10">{model.description}</p>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-[#deddd9]/50 p-3 rounded">
                <div className="text-xs text-[#6d6b66] flex items-center gap-1">
                  <ShieldCheck className="h-3 w-3" /> P99 Coverage
                </div>
                <div className={`text-2xl font-bold ${model.coverage_p99 >= 99 ? 'text-[#2f6b4f]' : 'text-[#b42318]'}`}>
                  {model.coverage_p99}%
                </div>
                <div className="text-[10px] text-[#87847e]">Target: ≥99%</div>
              </div>

              <div className="bg-[#deddd9]/50 p-3 rounded">
                <div className="text-xs text-[#6d6b66] flex items-center gap-1">
                  <TrendingDown className="h-3 w-3" /> Pinball Loss
                </div>
                <div className="text-2xl font-bold text-[#141414]">
                  {model.pinball_loss}
                </div>
                <div className="text-[10px] text-[#87847e]">Lower is better</div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Visualization: Time Series */}
        <Card>
            <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                <TrendingDown className="h-5 w-5 text-[#ff4d00]"/>
                Extreme Event Performance
            </h3>
            <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={data.time_series}>
                <CartesianGrid strokeDasharray="3 3" stroke="#b9b6af" />
                <XAxis dataKey="hour" stroke="#6d6b66" />
                <YAxis stroke="#6d6b66" />
                <Tooltip contentStyle={{ backgroundColor: '#e4e3e0', borderColor: '#141414', color: '#141414' }} />
                <Legend />
                
                <Line type="monotone" dataKey="actual_load" stroke="#141414" strokeWidth={2} dot={false} name="Actual" />
                <Line type="step" dataKey="baseline_p99" stroke="#6d6b66" strokeDasharray="5 5" name="Baseline P99" />
                <Area type="monotone" dataKey="gert_p99" stroke="#ff4d00" fill="#ff4d00" fillOpacity={0.18} name="GERT P99" />
                </ComposedChart>
            </ResponsiveContainer>
            </div>
        </Card>

        {/* Visualization: Calibration / Reliability */}
        <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Target className="h-5 w-5 text-[#2f6b4f]"/>
                  Reliability Diagram (Calibration)
              </h3>
              <div className="flex items-center gap-2 text-xs text-[#4f4e4a]">
                <span className="text-[10px] uppercase tracking-wide">Bucket Mode</span>
                <select
                  value={bucketMode}
                  onChange={(e) => setBucketMode(e.target.value as typeof bucketMode)}
                  className="bg-[#e4e3e0] border border-[#141414] rounded px-2 py-1 text-xs"
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
                <CartesianGrid strokeDasharray="3 3" stroke="#b9b6af" />
                <XAxis dataKey="prob_bucket" stroke="#6d6b66" tick={{fontSize: 10}} />
                <YAxis stroke="#6d6b66" domain={[0, 1]} />
                <Tooltip 
                    cursor={{fill: '#1e293b'}}
                    contentStyle={{ backgroundColor: '#e4e3e0', borderColor: '#141414', color: '#141414' }}
                />
                <Legend />
                <Bar dataKey="observed_freq" name="Observed Frequency" fill="#10b981" />
                <Bar dataKey="ideal_freq" name="Ideal Frequency" fill="#334155" />
                </BarChart>
            </ResponsiveContainer>
            </div>
            <p className="text-xs text-[#6d6b66] mt-2 text-center">
                A perfectly calibrated model has Observed Frequency matching Ideal Frequency (bars are equal height).
            </p>
        </Card>
      </div>
    </div>
  );
}
