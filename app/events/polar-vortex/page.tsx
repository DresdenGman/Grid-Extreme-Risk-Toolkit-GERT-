'use client';

import { useState, useEffect, useRef } from 'react';
import { api } from '@/lib/api';
import { EventPlaybackResponse } from '@/lib/types';
import { Card } from '@/components/ui';
import { LoadingState } from '@/components/LoadingState';
import {
  Play,
  Pause,
  Rewind,
  Snowflake,
  Clock,
  Newspaper,
} from 'lucide-react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Area,
  ReferenceDot,
} from 'recharts';
import { clsx } from 'clsx';

export default function EventReplay() {
  const [data, setData] = useState<EventPlaybackResponse | null>(null);
  const [currentHour, setCurrentHour] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1000); // ms per step
  const [severityFilter, setSeverityFilter] = useState<'ALL' | 'INFO' | 'WARNING' | 'CRITICAL'>('ALL');
  
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Load Event Data
    api.fetchEventPlayback('polar-vortex').then(setData).catch(console.error);
  }, []);

  // Playback Logic
  useEffect(() => {
    if (isPlaying && data) {
      timerRef.current = setInterval(() => {
        setCurrentHour(prev => {
          if (prev >= data.total_hours - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, speed);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, data, speed]);

  const togglePlay = () => setIsPlaying(!isPlaying);
  
  const reset = () => {
    setIsPlaying(false);
    setCurrentHour(0);
  };

  if (!data) return <LoadingState label="Loading historical event data..." variant="full" />;

  const currentStep = data.steps[currentHour];
  
  // Slice data for chart to show history only up to current hour
  const chartData = data.steps.slice(0, currentHour + 1);
  
  // Filter logs that have happened up to this hour
  const visibleLogs = data.logs
    .filter(l => l.hour <= currentHour)
    .filter(l => severityFilter === 'ALL' ? true : l.severity === severityFilter)
    .reverse();

  const firstHighHour = data.steps.find(s => s.risk_score >= 75)?.hour;
  const firstExtremeHour = data.steps.find(s => s.risk_score >= 90)?.hour;
  const firstBreachHour = data.steps.find(s => s.gert_p99_load_mw > s.capacity_mw)?.hour;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      
      {/* Header with KPI Ticker */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <Snowflake className="h-6 w-6 text-indigo-400" />
            {data.title}
          </h1>
          <p className="text-slate-500 text-sm mt-1">Replaying: {currentStep.timestamp_label}</p>
        </div>
        
        <div className="flex gap-4">
          <Card className="px-4 py-2 flex flex-col items-center min-w-[100px] border-slate-800 bg-slate-900/50">
             <span className="text-xs text-slate-500 uppercase font-bold">Risk Score</span>
             <span className={clsx("text-2xl font-bold", 
                currentStep.risk_score > 90 ? "text-red-500 animate-pulse" : 
                currentStep.risk_score > 70 ? "text-orange-400" : "text-emerald-400"
             )}>
                {currentStep.risk_score.toFixed(0)}
             </span>
          </Card>
           <Card className="px-4 py-2 flex flex-col items-center min-w-[100px] border-slate-800 bg-slate-900/50">
             <span className="text-xs text-slate-500 uppercase font-bold">Temp</span>
             <span className="text-2xl font-bold text-white">
                {currentStep.temperature}°C
             </span>
          </Card>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Main Chart Area (Span 2) */}
        <div className="lg:col-span-2 space-y-6">
            <Card className="p-1 bg-slate-950 border-slate-800">
                <div className="h-[400px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={chartData} margin={{top: 20, right: 20, left: 0, bottom: 0}}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                            <XAxis dataKey="hour" stroke="#64748b" tick={false} />
                            <YAxis stroke="#64748b" domain={[40000, 80000]} tickFormatter={v => `${v/1000}k`} />
                            <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                            
                            {/* Areas */}
                            <Area type="monotone" dataKey="gert_p99_load_mw" stroke="#ef4444" strokeDasharray="5 5" fill="#ef4444" fillOpacity={0.1} name="GERT P99 (Predicted)" />
                            
                            {/* Lines */}
                            <Line type="monotone" dataKey="actual_load_mw" stroke="#fff" strokeWidth={2} dot={false} name="Actual Load" />
                            <Line type="step" dataKey="capacity_mw" stroke="#10b981" strokeWidth={2} dot={false} name="Available Capacity" />
                            
                            {/* Current Time Indicator */}
                            <ReferenceLine x={currentHour} stroke="#6366f1" strokeDasharray="3 3" />

                            {firstHighHour !== undefined && (
                              <ReferenceDot
                                x={firstHighHour}
                                y={currentStep.capacity_mw}
                                r={3}
                                stroke="#f97316"
                                fill="#f97316"
                              />
                            )}
                            {firstExtremeHour !== undefined && (
                              <ReferenceDot
                                x={firstExtremeHour}
                                y={currentStep.capacity_mw + 500}
                                r={3}
                                stroke="#ef4444"
                                fill="#ef4444"
                              />
                            )}
                            {firstBreachHour !== undefined && (
                              <ReferenceDot
                                x={firstBreachHour}
                                y={currentStep.capacity_mw - 500}
                                r={3}
                                stroke="#eab308"
                                fill="#eab308"
                              />
                            )}
                        </ComposedChart>
                    </ResponsiveContainer>
                </div>
            </Card>

            {/* Playback Controls */}
            <div className="flex items-center gap-4 bg-slate-900 p-4 rounded-lg border border-slate-800">
                <button onClick={togglePlay} className="p-3 bg-indigo-600 hover:bg-indigo-700 rounded-full text-white transition-colors">
                    {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5 ml-1" />}
                </button>
                
                <button onClick={reset} className="p-2 text-slate-400 hover:text-white">
                    <Rewind className="h-5 w-5" />
                </button>

                <div className="flex-1 mx-4">
                    <input 
                        type="range" 
                        min="0" 
                        max={data.total_hours - 1} 
                        value={currentHour}
                        onChange={(e) => {
                            setIsPlaying(false);
                            setCurrentHour(Number(e.target.value));
                        }}
                        className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                    />
                    <div className="flex justify-between text-xs text-slate-500 mt-1 font-mono">
                        <span>Start: Feb 14</span>
                        <span>End: Feb 16</span>
                    </div>
                </div>

                <div className="flex items-center gap-2 text-xs text-slate-400">
                    <Clock className="h-3 w-3" />
                    <span>Speed:</span>
                    <select 
                        value={speed} 
                        onChange={(e) => setSpeed(Number(e.target.value))}
                        className="bg-slate-800 border border-slate-700 rounded px-1 py-0.5"
                    >
                        <option value={2000}>0.5x</option>
                        <option value={1000}>1x</option>
                        <option value={500}>2x</option>
                        <option value={100}>Max</option>
                    </select>
                </div>
            </div>

            {/* Analysis Box */}
            <div className="grid grid-cols-2 gap-4">
                <Card className="bg-slate-900/50 border-slate-800">
                    <h3 className="text-sm font-semibold text-slate-400 mb-2">Capacity Margin</h3>
                    <div className={clsx("text-xl font-mono font-bold", (currentStep.capacity_mw - currentStep.actual_load_mw) < 2000 ? "text-red-500" : "text-emerald-400")}>
                        {((currentStep.capacity_mw - currentStep.actual_load_mw) / 1000).toFixed(1)} GW
                    </div>
                </Card>
                 <Card className="bg-slate-900/50 border-slate-800">
                    <h3 className="text-sm font-semibold text-slate-400 mb-2">GERT Accuracy</h3>
                    <div className="text-xl font-mono font-bold text-indigo-400">
                        +{(currentStep.gert_p99_load_mw - currentStep.actual_load_mw).toFixed(0)} MW
                    </div>
                    <div className="text-xs text-slate-500">P99 Buffer vs Actual</div>
                </Card>
            </div>
        </div>

        {/* Sidebar: Event Log (Span 1) */}
        <div className="space-y-4 h-[600px] flex flex-col">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold uppercase text-slate-500 flex items-center gap-2">
                  <Newspaper className="h-4 w-4" /> Control Room Feed
              </h3>
              <div className="flex gap-1 text-[10px]">
                {(['ALL','INFO','WARNING','CRITICAL'] as const).map(level => (
                  <button
                    key={level}
                    onClick={() => setSeverityFilter(level)}
                    className={clsx(
                      'px-2 py-0.5 rounded border text-[10px] font-mono',
                      severityFilter === level
                        ? 'bg-slate-800 border-slate-500 text-slate-100'
                        : 'bg-slate-900 border-slate-800 text-slate-500 hover:text-slate-200'
                    )}
                  >
                    {level}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto space-y-3 pr-2 scrollbar-thin scrollbar-thumb-slate-700">
                {visibleLogs.length === 0 && (
                    <div className="text-center text-slate-600 italic text-sm mt-10">No events yet...</div>
                )}
                {visibleLogs.map((log, idx) => (
                    <div 
                        key={`${log.hour}-${idx}`} 
                        className={clsx(
                            "p-3 rounded border text-sm animate-in slide-in-from-right-4 fade-in duration-300",
                            log.severity === 'CRITICAL' ? "bg-red-950/30 border-red-900 text-red-200" :
                            log.severity === 'WARNING' ? "bg-orange-950/30 border-orange-900 text-orange-200" :
                            "bg-slate-900 border-slate-800 text-slate-300"
                        )}
                    >
                        <div className="flex justify-between items-center mb-1">
                            <span className="font-mono text-xs opacity-70">T+{log.hour}h</span>
                            <span className="text-[10px] font-bold uppercase border px-1 rounded opacity-70">{log.source}</span>
                        </div>
                        <p>{log.message}</p>
                    </div>
                ))}
            </div>
        </div>

      </div>
    </div>
  );
}