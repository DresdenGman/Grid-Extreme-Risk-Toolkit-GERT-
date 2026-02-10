'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '@/lib/api';
import { WeatherFeatures, PredictionOut, Region, AIAnalysisResponse } from '@/lib/types';
import { Card, Badge } from '@/components/ui';
import { QuantileChart } from '@/components/Charts';
import GridMap from '@/components/GridMap';
import { 
  Thermometer, Wind, Sun, RefreshCw, Zap, 
  MapPin, Clock, CloudLightning, Activity, 
  ArrowUpRight, AlertTriangle, ShieldCheck 
} from 'lucide-react';
import { clsx } from 'clsx';

const REGIONS: Region[] = ['ERCOT_NORTH', 'CAISO', 'PJM', 'NYISO'];

export default function Home() {
  const [region, setRegion] = useState<Region>('ERCOT_NORTH');
  const [inputs, setInputs] = useState<WeatherFeatures>({
    temperature: 32,
    wind_speed: 15,
    solar_irradiance: 800
  });
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<PredictionOut | null>(null);
  const mountedRef = useRef(true);

  // Sync Live Weather on mount and region change
  useEffect(() => {
    const syncWeather = async () => {
        try {
            const realWeather = await api.liveWeather(region);
            if (mountedRef.current) setInputs(realWeather);
        } catch(e) { console.error(e); }
    };
    syncWeather();
  }, [region]);

  const fetchPrediction = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.predict({
        region: region,
        date: new Date().toISOString(),
        weather_features: inputs
      });
      if (mountedRef.current) setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, [inputs, region]);

  useEffect(() => {
    fetchPrediction();
  }, [fetchPrediction]);

  // Derived state for KPI colors
  const riskColor = data?.risk_level === 'EXTREME' ? 'text-red-500' 
                  : data?.risk_level === 'HIGH' ? 'text-orange-500' 
                  : 'text-emerald-500';
  
  const riskBg = data?.risk_level === 'EXTREME' ? 'bg-red-500/10 border-red-500/20' 
               : data?.risk_level === 'HIGH' ? 'bg-orange-500/10 border-orange-500/20' 
               : 'bg-emerald-500/10 border-emerald-500/20';

  return (
    <div className="space-y-6">
      
      {/* 1. Header Row (Status Bar) */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            Regional Grid Monitor
            <Badge level={data?.risk_level || 'LOW'} />
          </h1>
          <p className="text-slate-500 text-sm mt-1 font-mono">
             {region.replace('_', ' ')} • Last Updated: {new Date().toLocaleTimeString()}
          </p>
        </div>
        <div className="flex gap-3">
             <button 
                onClick={fetchPrediction}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 rounded text-sm font-medium transition-colors"
             >
                <RefreshCw className={clsx("h-4 w-4", loading && "animate-spin")} />
                Refresh Model
             </button>
        </div>
      </div>

      {/* 2. KPI Cards (Conclusion First) */}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            
            {/* Risk Score */}
            <Card className={clsx("p-4 border-l-4", riskBg)}>
                <div className="text-slate-500 text-xs font-bold uppercase mb-1 flex items-center gap-2">
                    <AlertTriangle className="h-3 w-3" /> System Risk
                </div>
                <div className="flex items-baseline gap-2">
                    <span className={clsx("text-3xl font-bold tracking-tighter", riskColor)}>
                        {data.risk_score.toFixed(1)}
                    </span>
                    <span className="text-slate-500 text-sm">/ 100</span>
                </div>
            </Card>

            {/* P99 Load */}
            <Card className="p-4 bg-slate-900 border border-slate-800">
                <div className="text-slate-500 text-xs font-bold uppercase mb-1 flex items-center gap-2">
                    <Zap className="h-3 w-3 text-yellow-500" /> P99 Peak Load
                </div>
                <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold text-white tracking-tighter">
                        {(data.q99_load_mw / 1000).toFixed(2)}
                    </span>
                    <span className="text-slate-500 text-sm">GW</span>
                </div>
            </Card>

            {/* Margin */}
            <Card className="p-4 bg-slate-900 border border-slate-800">
                <div className="text-slate-500 text-xs font-bold uppercase mb-1 flex items-center gap-2">
                    <ShieldCheck className="h-3 w-3 text-emerald-500" /> Capacity Margin
                </div>
                <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold text-white tracking-tighter">
                        {((60000 - data.q99_load_mw) / 1000).toFixed(2)}
                    </span>
                    <span className="text-slate-500 text-sm">GW</span>
                </div>
            </Card>

            {/* Weather Driver */}
            <Card className="p-4 bg-slate-900 border border-slate-800">
                <div className="text-slate-500 text-xs font-bold uppercase mb-1 flex items-center gap-2">
                    <Thermometer className="h-3 w-3 text-blue-500" /> Ambient Temp
                </div>
                <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold text-white tracking-tighter">
                        {inputs.temperature.toFixed(1)}
                    </span>
                    <span className="text-slate-500 text-sm">°C</span>
                </div>
            </Card>
        </div>
      )}

      {/* 3. Main Split View (Map + Chart) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[500px]">
        
        {/* Map Column */}
        <div className="lg:col-span-4 flex flex-col gap-4">
            <Card className="flex-1 p-0 overflow-hidden bg-slate-900 border-slate-800 flex flex-col">
                <div className="p-3 border-b border-slate-800 bg-slate-950/50 flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-400 uppercase">Interconnection View</span>
                    <div className="flex gap-2">
                        {REGIONS.map(r => (
                            <div 
                                key={r} 
                                className={clsx("w-2 h-2 rounded-full", region === r ? "bg-indigo-500 animate-pulse" : "bg-slate-700")}
                            />
                        ))}
                    </div>
                </div>
                <div className="flex-1 relative">
                    <GridMap 
                        selectedRegion={region} 
                        onSelect={setRegion} 
                        className="h-full w-full border-none rounded-none bg-slate-900"
                    />
                </div>
            </Card>
        </div>

        {/* Chart Column */}
        <div className="lg:col-span-8">
            <Card className="h-full p-0 bg-slate-900 border-slate-800 flex flex-col">
                 <div className="p-3 border-b border-slate-800 bg-slate-950/50 flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-400 uppercase flex items-center gap-2">
                        <Activity className="h-3 w-3" />
                        Probabilistic Forecast Horizon (24h)
                    </span>
                     <span className="text-xs font-mono text-slate-500">
                        Model: GERT-Quantile-v1
                    </span>
                </div>
                <div className="flex-1 p-4 min-h-0">
                    {data ? (
                        <QuantileChart prediction={data} />
                    ) : (
                        <div className="h-full flex items-center justify-center text-slate-600 animate-pulse">
                            Initializing Analytics...
                        </div>
                    )}
                </div>
            </Card>
        </div>
      </div>

      {/* 4. Controls & Input Strip */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 flex flex-col md:flex-row gap-8 items-center">
         <div className="text-xs font-bold text-slate-500 uppercase whitespace-nowrap">
            Scenario Overrides
         </div>
         
         <div className="flex-1 w-full grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex items-center gap-4">
                <Thermometer className="h-4 w-4 text-slate-500" />
                <input 
                    type="range" min="-10" max="45" step="0.1"
                    value={inputs.temperature}
                    onChange={(e) => setInputs({...inputs, temperature: Number(e.target.value)})}
                    className="w-full h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
            </div>
             <div className="flex items-center gap-4">
                <Wind className="h-4 w-4 text-slate-500" />
                <input 
                    type="range" min="0" max="40" step="0.1"
                    value={inputs.wind_speed}
                    onChange={(e) => setInputs({...inputs, wind_speed: Number(e.target.value)})}
                    className="w-full h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
            </div>
             <div className="flex items-center gap-4">
                <Sun className="h-4 w-4 text-slate-500" />
                <input 
                    type="range" min="0" max="1200" step="10"
                    value={inputs.solar_irradiance}
                    onChange={(e) => setInputs({...inputs, solar_irradiance: Number(e.target.value)})}
                    className="w-full h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
            </div>
         </div>
         
         <div className="text-xs font-mono text-slate-500 whitespace-nowrap">
            Auto-Sync: <span className="text-emerald-500">ON</span>
         </div>
      </div>

    </div>
  );
}