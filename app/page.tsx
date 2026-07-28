'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '@/lib/api';
import { WeatherFeatures, PredictionOut, Region, ApiClientError, Provenance } from '@/lib/types';
import { Card, Badge } from '@/components/ui';
import { QuantileChart } from '@/components/Charts';
import GridMap from '@/components/GridMap';
import {
  Thermometer,
  Wind,
  Sun,
  RefreshCw,
  Zap,
  AlertTriangle,
  ShieldCheck,
  Activity,
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
  const [draftInputs, setDraftInputs] = useState<WeatherFeatures>({
    temperature: 32,
    wind_speed: 15,
    solar_irradiance: 800
  });
  const [liveSnapshot, setLiveSnapshot] = useState<WeatherFeatures | null>(null);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<PredictionOut | null>(null);
  const [prevData, setPrevData] = useState<PredictionOut | null>(null);
  const [showWhy, setShowWhy] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const [provenance, setProvenance] = useState<Provenance | null>(null);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  // Sync Live Weather on mount and region change
  useEffect(() => {
    const syncWeather = async () => {
        try {
            const envelope = await api.liveWeather(region);
            if (mountedRef.current) {
              setInputs(envelope.data);
              setDraftInputs(envelope.data);
              setLiveSnapshot(envelope.data);
            }
        } catch(e) { console.error(e); }
    };
    syncWeather();
  }, [region]);

  useEffect(() => {
    setLastUpdated(new Date().toLocaleTimeString());
  }, [data]);

  const fetchPrediction = useCallback(
    async (featuresOverride?: WeatherFeatures) => {
      const featuresToUse = featuresOverride ?? inputs;
    setLoading(true);
    try {
      const envelope = await api.predict({
        region: region,
        date: new Date().toISOString(),
          weather_features: featuresToUse
      });
        if (mountedRef.current) {
          setPrevData((prev) => data ?? prev);
          setData(envelope.data);
          setProvenance(envelope.source);
          setError(null);
        }
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError('Prediction failed.');
      }
      console.error(err);
    } finally {
      if (mountedRef.current) setLoading(false);
    }
    },
    [inputs, region, data]
  );

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

  const riskDelta = data && prevData ? data.risk_score - prevData.risk_score : null;
  const capacityUsed = (data?.diagnostics?.capacity_used ?? 60000);
  const marginMw = data ? capacityUsed - data.q99_load_mw : null;
  const marginLabel =
    marginMw === null
      ? null
      : marginMw < 0
        ? 'OVER CAPACITY'
        : marginMw < 2000
          ? 'TIGHT'
          : 'COMFORTABLE';

  const handleApplyScenario = () => {
    setInputs(draftInputs);
    fetchPrediction(draftInputs);
  };

  const handleResetScenario = () => {
    if (liveSnapshot) {
      setDraftInputs(liveSnapshot);
    } else {
      setDraftInputs(inputs);
    }
  };

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
             {region.replace('_', ' ')} • Last Updated: {lastUpdated}
          </p>
          {provenance && (
            <span className={clsx(
              "text-[10px] px-2 py-0.5 rounded font-mono inline-block mt-1",
              provenance === 'live_api'
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
            )}>
              {provenance === 'live_api' ? '✓ LIVE API' : '⚠ SIMULATED DEMO DATA — Not for operational use'}
            </span>
          )}
          {error && !data && (
            <div className="mt-2 text-xs text-red-400 font-mono">
              DATA UNAVAILABLE — {error}
            </div>
          )}
          {error && data && (
            <div className="mt-1 text-xs text-amber-400 font-mono">
              STALE DATA — {error}
            </div>
          )}
          {data?.diagnostics?.data_source && (
            <div className="mt-1 flex items-center gap-2">
              <span className={clsx(
                "text-[10px] px-2 py-0.5 rounded font-mono",
                data.diagnostics.data_source === 'real_time' 
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                  : "bg-slate-700/50 text-slate-400 border border-slate-600/30"
              )}>
                {data.diagnostics.data_source === 'real_time' ? '✓ Real-Time Data' : '⚠ Simulated Data'}
              </span>
              {data && (
                <button
                  type="button"
                  onClick={() => setShowWhy((v) => !v)}
                  className="text-[10px] font-mono text-slate-400 underline-offset-2 hover:text-slate-200 hover:underline"
                >
                  Why?
                </button>
              )}
            </div>
          )}
        </div>
        <div className="flex gap-3">
             <button 
                onClick={() => fetchPrediction()}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 rounded text-sm font-medium transition-colors"
             >
                <RefreshCw className={clsx("h-4 w-4", loading && "animate-spin")} />
                Refresh Model
             </button>
        </div>
      </div>

      {showWhy && data && (
        <div className="border border-slate-800 bg-slate-900/80 rounded-lg p-3 text-xs text-slate-300 space-y-1">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-slate-200">Why this risk level?</span>
            <span className="font-mono text-[10px] text-slate-500">
              Risk {data.risk_score.toFixed(1)}/100 • Margin {marginMw !== null ? (marginMw / 1000).toFixed(2) : '--'} GW
            </span>
          </div>
          <ul className="list-disc list-inside space-y-0.5">
            {marginMw !== null && (
              <li>
                P99 load is {marginMw < 0 ? 'above' : 'below'} capacity by{' '}
                <span className={marginMw < 0 ? 'text-red-400 font-mono' : 'text-emerald-400 font-mono'}>
                  {Math.abs(marginMw / 1000).toFixed(2)} GW
                </span>
                .
              </li>
            )}
            <li>
              Ambient temperature at{' '}
              <span className="font-mono">
                {inputs.temperature.toFixed(1)}°C
              </span>{' '}
              with wind{' '}
              <span className="font-mono">
                {inputs.wind_speed.toFixed(1)} m/s
              </span>{' '}
              is driving {' '}
              {inputs.temperature < 0 ? 'heating' : inputs.temperature > 30 ? 'cooling' : 'moderate'}
              {' '}load.
            </li>
            <li>
              Risk trend vs last run:{' '}
              {riskDelta === null ? (
                <span className="text-slate-400">no prior snapshot.</span>
              ) : riskDelta > 0 ? (
                <span className="text-red-400 font-mono">↗ +{riskDelta.toFixed(1)} points (worsening)</span>
              ) : riskDelta < 0 ? (
                <span className="text-emerald-400 font-mono">↘ {riskDelta.toFixed(1)} points (improving)</span>
              ) : (
                <span className="text-slate-400 font-mono">no change</span>
              )}
            </li>
          </ul>
        </div>
      )}

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
                {riskDelta !== null && (
                  <div className="mt-1 text-[11px] font-mono text-slate-400">
                    <span className={riskDelta > 0 ? 'text-red-400' : riskDelta < 0 ? 'text-emerald-400' : 'text-slate-400'}>
                      {riskDelta > 0 ? '↗ +' : riskDelta < 0 ? '↘ ' : '— '}
                      {Math.abs(riskDelta).toFixed(1)}
                    </span>
                    <span className="ml-1">vs last run</span>
                  </div>
                )}
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
                        {marginMw !== null ? (marginMw / 1000).toFixed(2) : '--'}
                    </span>
                    <span className="text-slate-500 text-sm">GW</span>
                </div>
                {marginLabel && (
                  <div className="mt-1 text-[11px] font-mono">
                    <span
                      className={clsx(
                        marginMw !== null && marginMw < 0
                          ? 'text-red-400'
                          : marginMw !== null && marginMw < 2000
                            ? 'text-amber-300'
                            : 'text-emerald-400'
                      )}
                    >
                      {marginLabel}
                    </span>
                    <span className="ml-1 text-slate-500">vs capacity</span>
                  </div>
                )}
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
                    value={draftInputs.temperature}
                    onChange={(e) => setDraftInputs({...draftInputs, temperature: Number(e.target.value)})}
                    className="w-full h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
              <div className="text-[10px] font-mono text-slate-500 w-28">
                <div>Now: {draftInputs.temperature.toFixed(1)}°C</div>
                {liveSnapshot && (
                  <div className="text-slate-600">Live: {liveSnapshot.temperature.toFixed(1)}°C</div>
                )}
              </div>
            </div>
             <div className="flex items-center gap-4">
                <Wind className="h-4 w-4 text-slate-500" />
                <input 
                    type="range" min="0" max="40" step="0.1"
                    value={draftInputs.wind_speed}
                    onChange={(e) => setDraftInputs({...draftInputs, wind_speed: Number(e.target.value)})}
                    className="w-full h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
                <div className="text-[10px] font-mono text-slate-500 w-28">
                  <div>Now: {draftInputs.wind_speed.toFixed(1)} m/s</div>
                  {liveSnapshot && (
                    <div className="text-slate-600">Live: {liveSnapshot.wind_speed.toFixed(1)} m/s</div>
                  )}
                </div>
            </div>
             <div className="flex items-center gap-4">
                <Sun className="h-4 w-4 text-slate-500" />
                <input 
                    type="range" min="0" max="1200" step="10"
                    value={draftInputs.solar_irradiance}
                    onChange={(e) => setDraftInputs({...draftInputs, solar_irradiance: Number(e.target.value)})}
                    className="w-full h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
                <div className="text-[10px] font-mono text-slate-500 w-32">
                  <div>Now: {draftInputs.solar_irradiance.toFixed(0)} W/m²</div>
                  {liveSnapshot && (
                    <div className="text-slate-600">Live: {liveSnapshot.solar_irradiance.toFixed(0)} W/m²</div>
                  )}
                </div>
            </div>
         </div>
         
         <div className="flex flex-col items-end gap-2 text-xs">
            <div className="text-xs font-mono text-slate-500 whitespace-nowrap">
              Auto-Sync: <span className="text-emerald-500">ON</span>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleResetScenario}
                className="px-3 py-1 rounded border border-slate-700 text-slate-300 hover:bg-slate-800 text-xs"
              >
                Reset to Live
              </button>
              <button
                type="button"
                onClick={handleApplyScenario}
                disabled={loading}
                className="px-3 py-1 rounded bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs"
              >
                Apply Scenario
              </button>
            </div>
         </div>
      </div>

    </div>
  );
}