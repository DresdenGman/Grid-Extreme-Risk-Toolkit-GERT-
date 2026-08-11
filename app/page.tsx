'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { clsx } from 'clsx';
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  Braces,
  Check,
  ChevronRight,
  CircleDotDashed,
  Cpu,
  Database,
  Gauge,
  Layers3,
  Radio,
  RefreshCw,
  RotateCcw,
  ShieldCheck,
  Sun,
  Thermometer,
  Wind,
  Zap,
} from 'lucide-react';
import { api } from '@/lib/api';
import { ApiClientError, PredictionOut, Provenance, Region, WeatherFeatures } from '@/lib/types';
import { Badge, Card } from '@/components/ui';
import { QuantileChart } from '@/components/Charts';
import GridMap from '@/components/GridMap';

const REGION: Region = 'ERCOT_SYSTEM';

function sourceLabel(provenance: Provenance | null) {
  if (provenance === 'live_api') return 'LIVE API';
  if (provenance === 'simulated_demo') return 'SIMULATED DEMO DATA — Not for operational use';
  return 'AWAITING SOURCE';
}

export default function Home() {
  const [inputs, setInputs] = useState<WeatherFeatures>({ temperature: 32, wind_speed: 15, solar_irradiance: 800 });
  const [draftInputs, setDraftInputs] = useState<WeatherFeatures>({ temperature: 32, wind_speed: 15, solar_irradiance: 800 });
  const [liveSnapshot, setLiveSnapshot] = useState<WeatherFeatures | null>(null);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<PredictionOut | null>(null);
  const [prevData, setPrevData] = useState<PredictionOut | null>(null);
  const [showWhy, setShowWhy] = useState(false);
  const [lastUpdated, setLastUpdated] = useState('—');
  const [provenance, setProvenance] = useState<Provenance | null>(null);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => () => { mountedRef.current = false; }, []);

  useEffect(() => {
    api.liveWeather(REGION)
      .then((envelope) => {
        if (!mountedRef.current) return;
        setInputs(envelope.data);
        setDraftInputs(envelope.data);
        setLiveSnapshot(envelope.data);
      })
      .catch((err) => console.warn('Weather sync failed', err));
  }, []);

  const fetchPrediction = useCallback(async (featuresOverride?: WeatherFeatures) => {
    const features = featuresOverride ?? inputs;
    setLoading(true);
    try {
      const envelope = await api.predict({
        region: REGION,
        date: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
        weather_features: features,
      });
      if (!mountedRef.current) return;
      setData((current) => {
        if (current) setPrevData(current);
        return envelope.data;
      });
      setProvenance(envelope.source);
      setLastUpdated(new Date(envelope.fetchedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : 'Prediction failed.');
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, [inputs]);

  useEffect(() => { fetchPrediction(); }, [fetchPrediction]);

  const capacity = data?.diagnostics.capacity_used ?? 60000;
  const marginMw = data ? capacity - data.q99_load_mw : null;
  const riskDelta = data && prevData ? data.risk_score - prevData.risk_score : null;
  const riskLevel = data?.risk_level ?? 'LOW';
  const danger = riskLevel === 'HIGH' || riskLevel === 'EXTREME';
  const marginState = marginMw === null ? 'AWAITING MODEL' : marginMw < 0 ? 'CAPACITY BREACH' : marginMw < 2000 ? 'TIGHT MARGIN' : 'BUFFER INTACT';
  const backendReal = data?.diagnostics.backend_type === 'real';
  const officialLoad = data?.diagnostics.load_data_source === 'official_live';
  const officialCapacity = data?.diagnostics.capacity_data_source === 'official_adequacy';

  const applyScenario = () => setInputs({ ...draftInputs });
  const resetScenario = () => {
    const next = liveSnapshot ?? inputs;
    setDraftInputs(next);
    setInputs({ ...next });
  };

  return (
    <div className="space-y-5 pb-10">
      <header className="reveal flex flex-col justify-between gap-5 border-b border-white/[0.09] pb-6 lg:flex-row lg:items-end">
        <div>
          <div className="mb-3 flex items-center gap-2 text-[#c8ff3d]">
            <Radio className="h-3.5 w-3.5" />
            <span className="technical-label">ERCOT / Operational tail-risk intelligence</span>
          </div>
          <h1 className="max-w-4xl text-[clamp(2.1rem,4.6vw,4.9rem)] font-medium leading-[0.93] tracking-[-0.055em] text-[#f4f1e8]">
            See the grid edge<br />before it becomes the event.
          </h1>
        </div>
        <div className="max-w-sm lg:text-right">
          <p className="text-sm leading-6 text-slate-400">
            A decision surface for rare-demand tails, capacity stress and evidence-backed intervention.
          </p>
          <div className="mt-3 flex items-center gap-3 lg:justify-end">
            <span className="technical-label text-slate-600">Target</span>
            <span className="font-mono text-xs text-slate-300">T+01:00</span>
            <span className="h-3 w-px bg-white/15" />
            <span className="font-mono text-xs text-slate-300">Updated {lastUpdated}</span>
          </div>
        </div>
      </header>

      <section className="reveal reveal-delay-1 grid gap-5 xl:grid-cols-12">
        <div className="relative min-h-[430px] overflow-hidden rounded-[28px] border border-white/[0.1] bg-[#0b1212] p-6 sm:p-8 xl:col-span-8">
          <div className={clsx('absolute inset-x-0 top-0 h-1', danger ? 'bg-[#ff6b57]' : 'bg-[#c8ff3d]')} />
          <div className="absolute -right-24 -top-24 h-80 w-80 rounded-full border border-white/[0.04]" />
          <div className="absolute -right-12 -top-12 h-56 w-56 rounded-full border border-white/[0.05]" />

          <div className="relative flex h-full flex-col justify-between gap-10">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <span className="technical-label text-slate-500">01 / Decision signal</span>
                <div className="mt-3 flex items-center gap-3">
                  <Badge level={riskLevel} />
                  <span className="technical-label text-slate-600">Next-hour system risk</span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => fetchPrediction()}
                disabled={loading}
                className="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-xs text-slate-300 transition hover:border-white/20 hover:bg-white/[0.06] disabled:opacity-50"
              >
                <RefreshCw className={clsx('h-3.5 w-3.5', loading && 'animate-spin')} /> Refresh inference
              </button>
            </div>

            <div className="grid items-end gap-8 lg:grid-cols-[1fr_0.9fr]">
              <div>
                <div className="flex items-end gap-3">
                  <span className={clsx('font-mono text-[clamp(5.3rem,12vw,10rem)] font-light leading-[0.72] tracking-[-0.09em]', danger ? 'text-[#ff7663]' : 'text-[#f4f1e8]')}>
                    <span className={clsx(!data && 'text-[0.42em] tracking-[-0.03em] text-slate-700')}>
                      {data ? data.risk_score.toFixed(0) : 'N/A'}
                    </span>
                  </span>
                  <span className="mb-1 font-mono text-sm text-slate-600">/100</span>
                </div>
                <div className="mt-6 flex flex-wrap items-center gap-3">
                  <span className={clsx('technical-label rounded-full px-3 py-1.5', marginMw !== null && marginMw < 0 ? 'bg-[#ff6b57]/10 text-[#ff8878]' : 'bg-[#c8ff3d]/10 text-[#c8ff3d]')}>
                    {marginState}
                  </span>
                  {riskDelta !== null && (
                    <span className={clsx('flex items-center gap-1 font-mono text-xs', riskDelta > 0 ? 'text-[#ff8878]' : 'text-[#c8ff3d]')}>
                      {riskDelta > 0 ? <ArrowUpRight className="h-3.5 w-3.5" /> : <ArrowDownRight className="h-3.5 w-3.5" />}
                      {Math.abs(riskDelta).toFixed(1)} vs prior run
                    </span>
                  )}
                </div>
              </div>

              <div className="border-l border-white/[0.1] pl-5 sm:pl-7">
                <span className="technical-label text-slate-500">Operator brief</span>
                <h2 className="mt-3 text-2xl font-medium leading-tight tracking-tight text-white">
                  {data
                    ? marginMw !== null && marginMw < 0
                      ? 'Tail demand crosses the stated capacity boundary.'
                      : 'Capacity remains above the modeled extreme-demand tail.'
                    : 'The decision layer is waiting for a compatible prediction service.'}
                </h2>
                <p className="mt-3 text-sm leading-6 text-slate-400">
                  {data
                    ? `P99 demand is ${(data.q99_load_mw / 1000).toFixed(2)} GW against ${(capacity / 1000).toFixed(2)} GW of capacity context.`
                    : 'No forecast is substituted or fabricated while the live service is unavailable.'}
                </p>
                <button type="button" onClick={() => setShowWhy((value) => !value)} disabled={!data} className="mt-5 flex items-center gap-2 text-xs font-medium text-[#c8ff3d] disabled:text-slate-700">
                  Inspect decision logic <ChevronRight className={clsx('h-3.5 w-3.5 transition', showWhy && 'rotate-90')} />
                </button>
              </div>
            </div>
          </div>
        </div>

        <Card className="flex min-h-[430px] flex-col justify-between overflow-hidden p-0 xl:col-span-4">
          <div className="border-b border-white/[0.08] p-6">
            <span className="technical-label text-slate-500">02 / System boundary</span>
            <div className="mt-4 flex items-end justify-between">
              <div><p className="text-sm text-slate-500">P99 capacity margin</p><p className="mt-1 font-mono text-4xl tracking-tight text-white">{marginMw === null ? '—' : `${(marginMw / 1000).toFixed(2)}`} <span className="text-sm text-slate-600">GW</span></p></div>
              <Gauge className={clsx('h-10 w-10', marginMw !== null && marginMw < 0 ? 'text-[#ff6b57]' : 'text-[#c8ff3d]')} />
            </div>
          </div>
          <div className="grid flex-1 grid-cols-2">
            <MetricCell label="Expected / P50" value={data ? `${(data.q50_load_mw / 1000).toFixed(1)} GW` : '—'} icon={<Activity />} />
            <MetricCell label="Extreme / P99" value={data ? `${(data.q99_load_mw / 1000).toFixed(1)} GW` : '—'} icon={<Zap />} />
            <MetricCell label="Temperature" value={`${inputs.temperature.toFixed(1)}°C`} icon={<Thermometer />} />
            <MetricCell label="Wind signal" value={`${inputs.wind_speed.toFixed(1)} m/s`} icon={<Wind />} />
          </div>
          <div className="border-t border-white/[0.08] px-6 py-4">
            <div className={clsx('flex items-center gap-2 technical-label', error ? 'text-[#ff8878]' : 'text-slate-500')}>
              <span className={clsx('h-1.5 w-1.5 rounded-full', error ? 'bg-[#ff6b57]' : 'signal-dot bg-[#c8ff3d]')} />
              {error ? (data ? `STALE DATA — ${error}` : `DATA UNAVAILABLE — ${error}`) : sourceLabel(provenance)}
            </div>
          </div>
        </Card>
      </section>

      {showWhy && data && (
        <section className="reveal grid gap-px overflow-hidden rounded-2xl border border-white/[0.09] bg-white/[0.09] md:grid-cols-3">
          <LogicStep index="A" title="Tail distance" body={`P99 sits ${Math.abs((marginMw ?? 0) / 1000).toFixed(2)} GW ${marginMw !== null && marginMw < 0 ? 'above' : 'below'} capacity.`} />
          <LogicStep index="B" title="Weather pressure" body={`${inputs.temperature.toFixed(1)}°C and ${inputs.wind_speed.toFixed(1)} m/s shape the next-hour load tail.`} />
          <LogicStep index="C" title="Run-to-run motion" body={riskDelta === null ? 'A prior comparable snapshot is not yet available.' : `Risk moved ${riskDelta > 0 ? 'up' : 'down'} ${Math.abs(riskDelta).toFixed(1)} points.`} />
        </section>
      )}

      <section className="reveal reveal-delay-2 grid gap-5 xl:grid-cols-12">
        <Card className="p-6 sm:p-7 xl:col-span-8">
          <div className="mb-8 flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
            <div><span className="technical-label text-slate-500">03 / Uncertainty geometry</span><h2 className="mt-2 text-2xl font-medium tracking-tight text-white">One forecast. Four confidence boundaries.</h2></div>
            <div className="flex items-center gap-2 rounded-full border border-white/[0.08] px-3 py-1.5"><CircleDotDashed className="h-3.5 w-3.5 text-[#74e7dd]" /><span className="technical-label text-slate-500">Quantile engine</span></div>
          </div>
          <div className="min-h-[330px]">{data ? <QuantileChart prediction={data} /> : <EmptyForecast loading={loading} />}</div>
        </Card>

        <Card className="overflow-hidden p-0 xl:col-span-4">
          <div className="flex items-center justify-between border-b border-white/[0.08] px-6 py-5">
            <div><span className="technical-label text-slate-500">04 / Grid context</span><h2 className="mt-1 text-lg font-medium text-white">ERCOT interconnection</h2></div>
            <span className="technical-label rounded-full border border-[#c8ff3d]/20 bg-[#c8ff3d]/5 px-2.5 py-1 text-[#c8ff3d]">System</span>
          </div>
          <GridMap selectedRegion={REGION} onSelect={() => undefined} className="min-h-[300px] border-0 bg-transparent" />
          <div className="border-t border-white/[0.08] px-6 py-4 text-xs leading-5 text-slate-500">Spatial context only. The active forecast is system-wide, not a fabricated weather-zone estimate.</div>
        </Card>
      </section>

      <section className="reveal reveal-delay-3 grid overflow-hidden rounded-[28px] border border-white/[0.1] bg-[#0b1212] lg:grid-cols-[0.7fr_1.3fr]">
        <div className="border-b border-white/[0.08] p-6 sm:p-8 lg:border-b-0 lg:border-r">
          <span className="technical-label text-slate-500">05 / Controlled intervention</span>
          <h2 className="mt-3 text-3xl font-medium leading-tight tracking-tight text-white">Stress the weather.<br />Keep the evidence.</h2>
          <p className="mt-4 max-w-sm text-sm leading-6 text-slate-400">Adjust the physical drivers, rerun the same decision pipeline and compare against the live snapshot.</p>
          <div className="mt-6 flex gap-2">
            <button onClick={resetScenario} className="flex items-center gap-2 rounded-full border border-white/10 px-4 py-2 text-xs text-slate-300 hover:bg-white/[0.04]"><RotateCcw className="h-3.5 w-3.5" /> Reset live</button>
            <button onClick={applyScenario} disabled={loading} className="flex items-center gap-2 rounded-full bg-[#c8ff3d] px-4 py-2 text-xs font-semibold text-[#07100a] transition hover:bg-[#d5ff6a] disabled:opacity-50">Run scenario <ArrowUpRight className="h-3.5 w-3.5" /></button>
          </div>
        </div>
        <div className="grid gap-px bg-white/[0.08] sm:grid-cols-3">
          <ScenarioControl icon={<Thermometer />} label="Temperature" value={`${draftInputs.temperature.toFixed(1)}°C`} live={liveSnapshot ? `${liveSnapshot.temperature.toFixed(1)}°C live` : 'sync pending'} min={-10} max={45} step={0.1} input={draftInputs.temperature} onChange={(temperature) => setDraftInputs({ ...draftInputs, temperature })} />
          <ScenarioControl icon={<Wind />} label="Wind speed" value={`${draftInputs.wind_speed.toFixed(1)} m/s`} live={liveSnapshot ? `${liveSnapshot.wind_speed.toFixed(1)} m/s live` : 'sync pending'} min={0} max={40} step={0.1} input={draftInputs.wind_speed} onChange={(wind_speed) => setDraftInputs({ ...draftInputs, wind_speed })} />
          <ScenarioControl icon={<Sun />} label="Solar input" value={`${draftInputs.solar_irradiance.toFixed(0)} W/m²`} live={liveSnapshot ? `${liveSnapshot.solar_irradiance.toFixed(0)} W/m² live` : 'sync pending'} min={0} max={1200} step={10} input={draftInputs.solar_irradiance} onChange={(solar_irradiance) => setDraftInputs({ ...draftInputs, solar_irradiance })} />
        </div>
      </section>

      <section className="grid gap-px overflow-hidden rounded-2xl border border-white/[0.09] bg-white/[0.09] md:grid-cols-4">
        <EvidenceCell icon={<Database />} title="Load context" value={officialLoad ? 'Official live' : 'Estimated fallback'} verified={officialLoad} />
        <EvidenceCell icon={<ShieldCheck />} title="Capacity basis" value={officialCapacity ? 'ERCOT adequacy' : 'Configured reference'} verified={officialCapacity} />
        <EvidenceCell icon={<Cpu />} title="Model artifact" value={backendReal ? data?.diagnostics.model_version ?? 'Trained' : 'Stub / demo'} verified={backendReal} />
        <EvidenceCell icon={<Braces />} title="Decision contract" value="P50 → P99 + provenance" verified />
      </section>
    </div>
  );
}

function MetricCell({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
  return <div className="border-b border-r border-white/[0.07] p-5 last:border-b-0 [&_svg]:h-3.5 [&_svg]:w-3.5 [&_svg]:text-slate-600"><div className="flex items-center gap-2 text-slate-600">{icon}<span className="technical-label text-[9px]">{label}</span></div><p className="mt-3 font-mono text-lg text-[#f4f1e8]">{value}</p></div>;
}

function LogicStep({ index, title, body }: { index: string; title: string; body: string }) {
  return <div className="bg-[#091010] p-5"><div className="flex items-center gap-3"><span className="font-mono text-xs text-[#c8ff3d]">{index}</span><span className="technical-label text-slate-500">{title}</span></div><p className="mt-3 text-sm leading-6 text-slate-300">{body}</p></div>;
}

function EmptyForecast({ loading }: { loading: boolean }) {
  return <div className="grid h-[330px] place-items-center rounded-xl border border-dashed border-white/[0.1] bg-white/[0.015] text-center"><div><Layers3 className="mx-auto h-8 w-8 text-slate-700" /><p className="mt-4 text-sm text-slate-400">{loading ? 'Initializing probability boundaries…' : 'Forecast boundaries unavailable'}</p><p className="mt-1 text-xs text-slate-600">The interface will not invent a distribution.</p></div></div>;
}

function ScenarioControl({ icon, label, value, live, min, max, step, input, onChange }: { icon: React.ReactNode; label: string; value: string; live: string; min: number; max: number; step: number; input: number; onChange: (value: number) => void }) {
  return <div className="bg-[#0b1212] p-6 sm:p-7"><div className="flex items-center justify-between text-slate-500"><span className="flex items-center gap-2 technical-label [&_svg]:h-3.5 [&_svg]:w-3.5">{icon}{label}</span><span className="font-mono text-[10px] text-slate-600">{live}</span></div><p className="mt-8 font-mono text-2xl text-white">{value}</p><input aria-label={label} type="range" min={min} max={max} step={step} value={input} onChange={(event) => onChange(Number(event.target.value))} className="mt-6 h-1 w-full cursor-pointer appearance-none rounded bg-white/10 accent-[#c8ff3d]" /></div>;
}

function EvidenceCell({ icon, title, value, verified }: { icon: React.ReactNode; title: string; value: string; verified: boolean }) {
  return <div className="bg-[#080e0e] p-5"><div className="flex items-center justify-between"><span className="text-slate-600 [&_svg]:h-4 [&_svg]:w-4">{icon}</span>{verified ? <Check className="h-3.5 w-3.5 text-[#c8ff3d]" /> : <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />}</div><p className="technical-label mt-5 text-slate-600">{title}</p><p className="mt-1 text-xs text-slate-300">{value}</p></div>;
}
