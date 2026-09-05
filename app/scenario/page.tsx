'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { ScenarioResponse, RiskLevel } from '@/lib/types';
import { Card, Badge } from '@/components/ui';
import { ArrowRight, AlertTriangle, CloudSnow, Sun, CloudRain } from 'lucide-react';

function scoreToLevel(score: number): RiskLevel {
  if (score >= 90) return 'EXTREME';
  if (score >= 75) return 'HIGH';
  if (score >= 40) return 'MODERATE';
  return 'LOW';
}

export default function ScenarioLab() {
  // Scenario Parameters
  const [tempDrop, setTempDrop] = useState(5);
  const [windChange, setWindChange] = useState(0);
  
  const [result, setResult] = useState<ScenarioResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    if (new URLSearchParams(window.location.search).get('demo') !== '1') return;

    const request = {
      region: 'ERCOT_SYSTEM',
      date: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
      weather_features: { temperature: 15, wind_speed: 10, solar_irradiance: 500 },
    };
    setLoading(true);
    api.scenario({ baseline_request: request, perturbations: { temperature: 15, wind_speed: 10 } })
      .then((scenario) => setResult(scenario.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  // Presets
  const applyPreset = (type: 'POLAR_VORTEX' | 'HEAT_WAVE' | 'DUNKELFLAUTE') => {
    if (type === 'POLAR_VORTEX') {
      setTempDrop(15);
      setWindChange(5);
    } else if (type === 'HEAT_WAVE') {
      setTempDrop(-10); // Negative drop = Increase
      setWindChange(-2);
    } else if (type === 'DUNKELFLAUTE') {
      setTempDrop(2);
      setWindChange(-15); // Low wind
    }
  };

  const runSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const env = await api.scenario({
        baseline_request: {
          region: 'ERCOT_SYSTEM',
          date: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
          weather_features: { temperature: 20, wind_speed: 10, solar_irradiance: 500 }
        },
        perturbations: {
          temperature: 20 - tempDrop,
          wind_speed: 10 + windChange
        }
      });
      setResult(env.data);
    } catch (e) {
      console.error(e);
      setError(e instanceof Error ? e.message : 'Scenario analysis is currently unavailable.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl space-y-7 pb-12">
      <header className="border-b border-white/[0.09] pb-7">
        <span className="technical-label text-[#9a6200]">Scenario lab / Controlled intervention</span>
        <h1 className="display-serif mt-3 text-4xl tracking-[-0.045em] text-[#141414] sm:text-6xl">Stress the system<br />before nature does.</h1>
        <p className="mt-4 max-w-2xl text-sm leading-6 text-[#4f4e4a]">Perturb physical drivers, preserve the baseline and expose the resulting tail-risk delta.</p>
      </header>

      {error && (
        <div className="border border-[#b42318] bg-[#f5dfdc] px-5 py-4 text-sm text-[#7d1a13]" role="alert">
          <strong>Scenario unavailable.</strong> {error}
          <Link href="/benchmark#evidence-rehearsal" className="ml-2 font-semibold underline underline-offset-4">
            Run the evidence rehearsal instead.
          </Link>
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <button onClick={() => applyPreset('POLAR_VORTEX')} className="hairline-panel scenario-cold rounded-2xl p-5 text-left transition hover:-translate-y-0.5">
          <div className="mb-2 flex items-center gap-2 text-[#175a73]">
            <CloudSnow className="h-5 w-5" />
            <span className="font-bold">Polar Vortex</span>
          </div>
          <p className="text-xs text-[#6d6b66]">Extreme cold (-15°C) with high heating demand.</p>
        </button>
        <button onClick={() => applyPreset('HEAT_WAVE')} className="hairline-panel scenario-heat rounded-2xl p-5 text-left transition hover:-translate-y-0.5">
          <div className="flex items-center gap-2 mb-2 text-orange-400 group-hover:text-orange-300">
            <Sun className="h-5 w-5" />
            <span className="font-bold">Heat Wave</span>
          </div>
          <p className="text-xs text-[#6d6b66]">Extreme heat (+10°C) triggering A/C load.</p>
        </button>
        <button onClick={() => applyPreset('DUNKELFLAUTE')} className="hairline-panel scenario-renewables rounded-2xl p-5 text-left transition hover:-translate-y-0.5">
          <div className="flex items-center gap-2 mb-2 text-[#4f4e4a] group-hover:text-[#454545]">
            <CloudRain className="h-5 w-5" />
            <span className="font-bold">Dunkelflaute</span>
          </div>
          <p className="text-xs text-[#6d6b66]">"Dark Lull": Low wind/solar output scenario.</p>
        </button>
      </div>

      <Card className="mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <label className="block text-sm font-medium text-[#454545] mb-4">
              Temperature Adjustment (°C)
            </label>
            <div className="flex items-center gap-4">
              <input 
                type="range" min="-20" max="20" step="1"
                value={tempDrop}
                onChange={(e) => setTempDrop(Number(e.target.value))}
                className="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-[#ff4d00]"
              />
              <span className="font-mono text-xl w-16 text-right">{tempDrop > 0 ? '-' : '+'}{Math.abs(tempDrop)}°C</span>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-[#454545] mb-4">
              Wind Speed Adjustment (m/s)
            </label>
            <div className="flex items-center gap-4">
              <input 
                type="range" min="-20" max="20" step="1"
                value={windChange}
                onChange={(e) => setWindChange(Number(e.target.value))}
                className="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-[#ff4d00]"
              />
              <span className="font-mono text-xl w-16 text-right">{windChange > 0 ? '+' : ''}{windChange}</span>
            </div>
          </div>
        </div>
        
        <button
          onClick={runSimulation}
          disabled={loading}
          className="technical-label mt-6 w-full border border-[#141414] bg-[#141414] py-3 text-[#e4e3e0] shadow-[4px_4px_0_#ff4d00] transition-colors hover:bg-[#ff4d00] hover:text-[#141414] disabled:opacity-50"
        >
          {loading ? 'Running Simulation...' : 'Run Analysis'}
        </button>
      </Card>

      {result && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {(() => {
            const baselineLevel = scoreToLevel(result.baseline_risk_score);
            const scenarioLevel = scoreToLevel(result.scenario_risk_score);
            const order: RiskLevel[] = ['LOW', 'MODERATE', 'HIGH', 'EXTREME'];
            const escalated =
              order.indexOf(scenarioLevel) > order.indexOf(baselineLevel);
            return (
              escalated && (
                <div className="flex justify-center">
                  <div className="inline-flex items-center gap-2 rounded-full bg-amber-950/40 border border-amber-500/60 px-3 py-1 text-xs font-mono text-amber-200">
                    <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
                    Escalation: {baselineLevel} → {scenarioLevel}
                  </div>
                </div>
              )
            );
          })()}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
            {/* Before */}
            <div className="text-center opacity-50">
              <h3 className="text-sm uppercase tracking-wider text-[#4f4e4a] mb-2">Baseline Risk</h3>
              <div className="text-4xl font-bold text-[#141414]">{result.baseline_risk_score}</div>
            </div>

            {/* Arrow */}
            <div className="flex justify-center text-[#87847e] md:hidden">
              <ArrowRight className="h-8 w-8 rotate-90" />
            </div>
             <div className="hidden md:flex justify-center text-[#87847e]">
              <ArrowRight className="h-8 w-8" />
            </div>

            {/* After */}
            <Card className="border-[#141414] bg-[#ff4d00]/10">
              <div className="text-center">
                <h3 className="text-sm uppercase tracking-wider text-[#ff4d00] mb-2">Scenario Risk Score</h3>
                <div className="text-5xl font-bold text-[#141414] mb-2">{result.scenario_risk_score}</div>
                <div className="inline-flex items-center gap-2 border border-[#141414] bg-[#141414] px-3 py-1 text-sm text-[#e4e3e0]">
                  <AlertTriangle className="h-4 w-4" />
                  Delta: +{result.risk_delta}
                </div>
                <div className="mt-3 text-xs text-[#4f4e4a] text-left max-w-md mx-auto">
                  <p className="font-semibold text-[#454545] mb-1">Why did risk change?</p>
                  <ul className="space-y-1">
                    {tempDrop !== 0 && (
                      <li>
                        • Temperature {tempDrop > 0 ? '↓' : '↑'}{' '}
                        {Math.abs(tempDrop)}°C → load tail{' '}
                        {tempDrop > 0 ? 'increases (heating demand)' : 'shifts with cooling demand'}
                      </li>
                    )}
                    {windChange !== 0 && (
                      <li>
                        • Wind {windChange > 0 ? '↑' : '↓'} {Math.abs(windChange)} m/s →{' '}
                        {windChange < 0
                          ? 'lower renewables & higher uncertainty'
                          : 'potentially higher renewable contribution'}
                      </li>
                    )}
                    <li>
                      • P99 vs capacity gap reflected as reserve shortfall and financial impact below
                    </li>
                  </ul>
                </div>
              </div>
            </Card>
          </div>

          {/* Actionable Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="bg-[#e4e3e0]/50">
              <h4 className="text-xs font-bold uppercase text-[#6d6b66] mb-2">Reserve Requirement</h4>
              <div className="text-2xl font-mono text-[#141414]">
                {result.reserve_shortfall_mw > 0 
                  ? <span className="text-[#b42318]">-{result.reserve_shortfall_mw} MW</span>
                  : <span className="text-[#2f6b4f]">Sufficient</span>}
              </div>
              <p className="text-xs text-[#6d6b66] mt-1">Additional generation needed to meet P99 load.</p>
            </Card>

            <Card className="bg-[#e4e3e0]/50">
              <h4 className="text-xs font-bold uppercase text-[#6d6b66] mb-2">Projected Financial Impact</h4>
              <div className="text-2xl font-mono text-[#141414]">
                 ${(result.financial_impact.estimated_loss / 1000).toLocaleString()}k
              </div>
              <p className="text-xs text-[#6d6b66] mt-1">Based on VOLL pricing.</p>
            </Card>
          </div>
          
        </div>
      )}
    </div>
  );
}
