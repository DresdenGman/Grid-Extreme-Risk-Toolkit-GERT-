'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { ScenarioResponse, AIAnalysisResponse, RiskLevel } from '@/lib/types';
import { Card, Badge } from '@/components/ui';
import { ArrowRight, AlertTriangle, CloudSnow, Sun, CloudRain, BrainCircuit, Sparkles, RefreshCw } from 'lucide-react';

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
  
  // AI State
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<AIAnalysisResponse | null>(null);

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
    setAnalysis(null);
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
    } finally {
      setLoading(false);
    }
  };

  const runAIAnalysis = async () => {
      if (!result) return;
      setAnalyzing(true);
      try {
        const env = await api.analyze({
          region: 'ERCOT_SYSTEM',
          date: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
          weather_features: { 
              temperature: 20 - tempDrop,
              wind_speed: 10 + windChange,
              solar_irradiance: 500
          }
        });
        setAnalysis(env.data);
      } catch (e) {
        console.error(e);
        alert("AI Analysis failed.");
      } finally {
        setAnalyzing(false);
      }
    };

  return (
    <div className="mx-auto max-w-6xl space-y-7 pb-12">
      <header className="border-b border-white/[0.09] pb-7">
        <span className="technical-label text-[#c8ff3d]">Scenario lab / Controlled intervention</span>
        <h1 className="mt-3 text-4xl font-medium tracking-[-0.045em] text-white sm:text-6xl">Stress the system<br />before nature does.</h1>
        <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-400">Perturb physical drivers, preserve the baseline and expose the resulting tail-risk delta.</p>
      </header>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <button onClick={() => applyPreset('POLAR_VORTEX')} className="hairline-panel rounded-2xl p-5 text-left transition hover:border-[#74e7dd]/40">
          <div className="flex items-center gap-2 mb-2 text-indigo-400 group-hover:text-indigo-300">
            <CloudSnow className="h-5 w-5" />
            <span className="font-bold">Polar Vortex</span>
          </div>
          <p className="text-xs text-slate-500">Extreme cold (-15°C) with high heating demand.</p>
        </button>
        <button onClick={() => applyPreset('HEAT_WAVE')} className="hairline-panel rounded-2xl p-5 text-left transition hover:border-orange-400/40">
          <div className="flex items-center gap-2 mb-2 text-orange-400 group-hover:text-orange-300">
            <Sun className="h-5 w-5" />
            <span className="font-bold">Heat Wave</span>
          </div>
          <p className="text-xs text-slate-500">Extreme heat (+10°C) triggering A/C load.</p>
        </button>
        <button onClick={() => applyPreset('DUNKELFLAUTE')} className="hairline-panel rounded-2xl p-5 text-left transition hover:border-[#c8ff3d]/40">
          <div className="flex items-center gap-2 mb-2 text-slate-400 group-hover:text-slate-300">
            <CloudRain className="h-5 w-5" />
            <span className="font-bold">Dunkelflaute</span>
          </div>
          <p className="text-xs text-slate-500">"Dark Lull": Low wind/solar output scenario.</p>
        </button>
      </div>

      <Card className="mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-4">
              Temperature Adjustment (°C)
            </label>
            <div className="flex items-center gap-4">
              <input 
                type="range" min="-20" max="20" step="1"
                value={tempDrop}
                onChange={(e) => setTempDrop(Number(e.target.value))}
                className="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
              <span className="font-mono text-xl w-16 text-right">{tempDrop > 0 ? '-' : '+'}{Math.abs(tempDrop)}°C</span>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-4">
              Wind Speed Adjustment (m/s)
            </label>
            <div className="flex items-center gap-4">
              <input 
                type="range" min="-20" max="20" step="1"
                value={windChange}
                onChange={(e) => setWindChange(Number(e.target.value))}
                className="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
              <span className="font-mono text-xl w-16 text-right">{windChange > 0 ? '+' : ''}{windChange}</span>
            </div>
          </div>
        </div>
        
        <button
          onClick={runSimulation}
          disabled={loading}
          className="mt-6 w-full rounded-xl bg-[#c8ff3d] py-3 font-semibold text-[#07100a] transition-colors hover:bg-[#d5ff6a] disabled:opacity-50"
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
              <h3 className="text-sm uppercase tracking-wider text-slate-400 mb-2">Baseline Risk</h3>
              <div className="text-4xl font-bold text-slate-200">{result.baseline_risk_score}</div>
            </div>

            {/* Arrow */}
            <div className="flex justify-center text-slate-600 md:hidden">
              <ArrowRight className="h-8 w-8 rotate-90" />
            </div>
             <div className="hidden md:flex justify-center text-slate-600">
              <ArrowRight className="h-8 w-8" />
            </div>

            {/* After */}
            <Card className="border-indigo-500/50 bg-indigo-900/10">
              <div className="text-center">
                <h3 className="text-sm uppercase tracking-wider text-indigo-300 mb-2">Scenario Risk Score</h3>
                <div className="text-5xl font-bold text-white mb-2">{result.scenario_risk_score}</div>
                <div className="inline-flex items-center gap-2 text-indigo-400 bg-indigo-950/50 px-3 py-1 rounded-full text-sm">
                  <AlertTriangle className="h-4 w-4" />
                  Delta: +{result.risk_delta}
                </div>
                <div className="mt-3 text-xs text-slate-400 text-left max-w-md mx-auto">
                  <p className="font-semibold text-slate-300 mb-1">Why did risk change?</p>
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
            <Card className="bg-slate-900/50">
              <h4 className="text-xs font-bold uppercase text-slate-500 mb-2">Reserve Requirement</h4>
              <div className="text-2xl font-mono text-white">
                {result.reserve_shortfall_mw > 0 
                  ? <span className="text-red-400">-{result.reserve_shortfall_mw} MW</span> 
                  : <span className="text-emerald-400">Sufficient</span>}
              </div>
              <p className="text-xs text-slate-500 mt-1">Additional generation needed to meet P99 load.</p>
            </Card>

            <Card className="bg-slate-900/50">
              <h4 className="text-xs font-bold uppercase text-slate-500 mb-2">Projected Financial Impact</h4>
              <div className="text-2xl font-mono text-white">
                 ${(result.financial_impact.estimated_loss / 1000).toLocaleString()}k
              </div>
              <p className="text-xs text-slate-500 mt-1">Based on VOLL pricing.</p>
            </Card>
          </div>
          
           {/* AI Analysis Section */}
            {!analysis ? (
              <div className="flex justify-center">
                 <button 
                  onClick={runAIAnalysis}
                  disabled={analyzing}
                  className="group relative inline-flex items-center justify-center overflow-hidden rounded-lg bg-gradient-to-br from-purple-600 to-blue-500 p-0.5 font-medium text-gray-900 focus:outline-none focus:ring-4 focus:ring-blue-300 group-hover:from-purple-600 group-hover:to-blue-500 dark:text-white dark:focus:ring-blue-800"
                >
                  <span className="relative flex items-center gap-2 rounded-md bg-white px-5 py-2.5 transition-all duration-75 ease-in group-hover:bg-opacity-0 dark:bg-gray-900">
                     {analyzing ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                     {analyzing ? "AI: Explain This Scenario" : "AI: Explain This Scenario"}
                  </span>
                </button>
              </div>
            ) : (
              <Card className="border-purple-500/50 bg-slate-900/80">
                <div className="flex items-center justify-between mb-4 border-b border-purple-900/50 pb-3">
                  <div className="flex items-center gap-2 text-purple-400">
                    <BrainCircuit className="h-5 w-5" />
                    <span className="font-bold tracking-wide text-sm">SCENARIO ANALYSIS</span>
                  </div>
                  <Badge level={analysis.confidence === 'HIGH' ? 'HIGH' : 'MODERATE'} />
                </div>
                
                <h3 className="text-xl font-bold text-white mb-4">{analysis.headline}</h3>
                <p className="text-slate-300 mb-4">{analysis.uncertainty}</p>
                
                <h4 className="text-xs font-bold text-slate-500 uppercase mb-3">Implications</h4>
                 <ul className="space-y-2">
                      {analysis.drivers.map((d, i) => (
                        <li key={i} className="flex gap-2 text-sm text-slate-300">
                          <span className="text-purple-500 font-bold">•</span>
                          <span>
                            <span className="font-semibold text-white">{d.factor}:</span> {d.evidence}
                          </span>
                        </li>
                      ))}
                </ul>
              </Card>
            )}

        </div>
      )}
    </div>
  );
}
