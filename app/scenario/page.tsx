'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { ScenarioResponse, AIAnalysisResponse } from '@/lib/types';
import { Card, Badge } from '@/components/ui';
import { ArrowRight, AlertTriangle, CloudSnow, Sun, CloudRain, BrainCircuit, Sparkles, RefreshCw } from 'lucide-react';

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
      const res = await api.scenario({
        baseline_request: {
          region: 'ERCOT_NORTH',
          date: new Date().toISOString(),
          weather_features: { temperature: 20, wind_speed: 10, solar_irradiance: 500 }
        },
        perturbations: {
          temperature: 20 - tempDrop,
          wind_speed: 10 + windChange
        }
      });
      setResult(res);
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
        // Construct a PredictRequest from the scenario result to feed into the analyzer
        // In a real app, we might have a specific endpoint for analyzing scenario diffs,
        // but re-using the analyze endpoint works if we pass the perturbed state.
        const res = await api.analyze({
          region: 'ERCOT_NORTH',
          date: new Date().toISOString(),
          weather_features: { 
              temperature: 20 - tempDrop,
              wind_speed: 10 + windChange,
              solar_irradiance: 500
          }
        });
        setAnalysis(res);
      } catch (e) {
        console.error(e);
        alert("AI Analysis failed.");
      } finally {
        setAnalyzing(false);
      }
    };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Scenario Stress Test</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <button onClick={() => applyPreset('POLAR_VORTEX')} className="bg-slate-900 border border-slate-800 p-4 rounded hover:border-indigo-500 transition-colors text-left group">
          <div className="flex items-center gap-2 mb-2 text-indigo-400 group-hover:text-indigo-300">
            <CloudSnow className="h-5 w-5" />
            <span className="font-bold">Polar Vortex</span>
          </div>
          <p className="text-xs text-slate-500">Extreme cold (-15°C) with high heating demand.</p>
        </button>
        <button onClick={() => applyPreset('HEAT_WAVE')} className="bg-slate-900 border border-slate-800 p-4 rounded hover:border-orange-500 transition-colors text-left group">
          <div className="flex items-center gap-2 mb-2 text-orange-400 group-hover:text-orange-300">
            <Sun className="h-5 w-5" />
            <span className="font-bold">Heat Wave</span>
          </div>
          <p className="text-xs text-slate-500">Extreme heat (+10°C) triggering A/C load.</p>
        </button>
        <button onClick={() => applyPreset('DUNKELFLAUTE')} className="bg-slate-900 border border-slate-800 p-4 rounded hover:border-slate-500 transition-colors text-left group">
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
          className="mt-6 w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded font-medium disabled:opacity-50 transition-colors"
        >
          {loading ? 'Running Simulation...' : 'Run Analysis'}
        </button>
      </Card>

      {result && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          
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