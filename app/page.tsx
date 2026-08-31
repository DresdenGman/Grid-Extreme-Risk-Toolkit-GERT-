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
import { createPresentationPrediction, createPresentationPrior, PRESENTATION_WEATHER } from '@/lib/presentation';
import { ApiClientError, GridLoadResponse, PredictionOut, Provenance, Region, WeatherFeatures } from '@/lib/types';
import { Badge, Card } from '@/components/ui';
import { QuantileChart } from '@/components/Charts';
import GridMap from '@/components/GridMap';

const REGION: Region = 'ERCOT_SYSTEM';

function sourceLabel(provenance: Provenance | null) {
  if (provenance === 'live_api') return 'LIVE API';
  if (provenance === 'simulated_demo') return 'SIMULATED DEMO DATA — Not for operational use';
  return 'AWAITING SOURCE';
}

function gridSourceLabel(context: GridLoadResponse | null, contextError: string | null) {
  if (context?.data_source === 'official_live') return 'OFFICIAL ERCOT SYSTEM CONTEXT';
  if (context) return 'ESTIMATED GRID CONTEXT';
  if (contextError) return `GRID CONTEXT UNAVAILABLE — ${contextError}`;
  return 'GRID CONTEXT SYNCING';
}

export default function Home() {
  const [inputs, setInputs] = useState<WeatherFeatures>({ temperature: 32, wind_speed: 15, solar_irradiance: 800 });
  const [draftInputs, setDraftInputs] = useState<WeatherFeatures>({ temperature: 32, wind_speed: 15, solar_irradiance: 800 });
  const [liveSnapshot, setLiveSnapshot] = useState<WeatherFeatures | null>(null);
  const [gridContext, setGridContext] = useState<GridLoadResponse | null>(null);
  const [contextError, setContextError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<PredictionOut | null>(null);
  const [prevData, setPrevData] = useState<PredictionOut | null>(null);
  const [showWhy, setShowWhy] = useState(false);
  const [lastUpdated, setLastUpdated] = useState('—');
  const [provenance, setProvenance] = useState<Provenance | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [modeResolved, setModeResolved] = useState(false);
  const [presentationMode, setPresentationMode] = useState(false);
  const mountedRef = useRef(true);

  useEffect(() => () => { mountedRef.current = false; }, []);

  useEffect(() => {
    const enabled = new URLSearchParams(window.location.search).get('demo') === '1';
    setPresentationMode(enabled);
    setModeResolved(true);
  }, []);

  const syncLiveContext = useCallback(async () => {
    if (presentationMode) {
      setInputs(PRESENTATION_WEATHER);
      setDraftInputs(PRESENTATION_WEATHER);
      setLiveSnapshot(PRESENTATION_WEATHER);
      setContextError(null);
      return;
    }

    const [weatherResult, loadResult] = await Promise.allSettled([
      api.liveWeather(REGION),
      api.getCurrentLoad(REGION),
    ]);
    if (!mountedRef.current) return;

    const failures: string[] = [];
    if (weatherResult.status === 'fulfilled') {
      setInputs(weatherResult.value.data);
      setDraftInputs(weatherResult.value.data);
      setLiveSnapshot(weatherResult.value.data);
    } else {
      failures.push('weather');
    }

    if (loadResult.status === 'fulfilled') {
      setGridContext(loadResult.value.data);
      setLastUpdated(new Date(loadResult.value.data.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    } else {
      failures.push('load');
    }

    setContextError(failures.length ? `${failures.join(' and ')} sync failed` : null);
  }, [presentationMode]);

  useEffect(() => {
    if (modeResolved) syncLiveContext();
  }, [modeResolved, syncLiveContext]);

  const fetchPrediction = useCallback(async (featuresOverride?: WeatherFeatures) => {
    const features = featuresOverride ?? inputs;
    setLoading(true);
    if (presentationMode) {
      const snapshot = createPresentationPrediction(features);
      setData((current) => {
        setPrevData(current ?? createPresentationPrior());
        return snapshot;
      });
      setProvenance('simulated_demo');
      setLastUpdated('DEMO SNAPSHOT');
      setShowWhy(true);
      setError(null);
      setLoading(false);
      return;
    }
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
  }, [inputs, presentationMode]);

  useEffect(() => {
    if (modeResolved) fetchPrediction();
  }, [fetchPrediction, modeResolved]);

  const capacity = data?.diagnostics.capacity_used ?? gridContext?.capacity_mw ?? null;
  const marginMw = data && capacity !== null ? capacity - data.q99_load_mw : null;
  const riskDelta = data && prevData ? data.risk_score - prevData.risk_score : null;
  const riskLevel = data?.risk_level ?? 'LOW';
  const danger = riskLevel === 'HIGH' || riskLevel === 'EXTREME';
  const marginState = marginMw === null ? 'AWAITING MODEL' : marginMw < 0 ? 'CAPACITY BREACH' : marginMw < 2000 ? 'TIGHT MARGIN' : 'BUFFER INTACT';
  const backendReal = data?.diagnostics.backend_type === 'real';
  const officialLoad = data?.diagnostics.load_data_source === 'official_live' || gridContext?.data_source === 'official_live';
  const officialCapacity = data?.diagnostics.capacity_data_source === 'official_adequacy' || gridContext?.capacity_source === 'official_adequacy';

  const refreshProduct = async () => {
    await Promise.allSettled([syncLiveContext(), fetchPrediction()]);
  };

  const applyScenario = () => setInputs({ ...draftInputs });
  const resetScenario = () => {
    const next = liveSnapshot ?? inputs;
    setDraftInputs(next);
    setInputs({ ...next });
  };

  return (
    <div className="space-y-5 pb-10">
      <header className="reveal flex flex-col justify-between gap-5 border-b border-black/[0.09] pb-6 lg:flex-row lg:items-end">
        <div>
          <div className="mb-3 flex items-center gap-2 text-[#ff4d00]">
            <Radio className="h-3.5 w-3.5" />
            <span className="technical-label">ERCOT / Operational tail-risk intelligence</span>
          </div>
          <h1 className="display-serif max-w-4xl text-[clamp(2.1rem,4.6vw,4.9rem)] leading-[0.93] tracking-[-0.055em] text-[#141414]">
            See the grid edge<br />before it becomes the event.
          </h1>
        </div>
        <div className="max-w-sm lg:text-right">
          <p className="text-sm leading-6 text-[#4f4e4a]">
            A decision surface for rare-demand tails, capacity stress and evidence-backed intervention.
          </p>
          <div className="mt-3 flex items-center gap-3 lg:justify-end">
            <span className="technical-label text-[#87847e]">Target</span>
            <span className="font-mono text-xs text-[#454545]">T+01:00</span>
            <span className="h-3 w-px bg-black/15" />
            <span className="font-mono text-xs text-[#454545]">Updated {lastUpdated}</span>
          </div>
        </div>
      </header>

      {!presentationMode && error && (
        <div role="status" className="reveal flex items-start gap-3 border border-[#9a6200]/45 bg-[#9a6200]/10 px-4 py-3 text-sm text-[#5f4700]">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />
          <p><strong>Prediction layer gated.</strong> {error} Official grid context remains visible independently when available.</p>
        </div>
      )}

      <section className="reveal reveal-delay-1 grid gap-5 xl:grid-cols-12">
        <div className="relative min-h-[430px] overflow-hidden border border-[#141414] bg-[#f1efe9] p-6 shadow-[7px_7px_0_#ff4d00] sm:p-8 xl:col-span-8">
          <div className={clsx('absolute inset-x-0 top-0 h-1', danger ? 'bg-[#ff6b57]' : 'bg-[#ff4d00]')} />
          <div className="relative flex h-full flex-col justify-between gap-10">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <span className="technical-label text-[#6d6b66]">01 / Decision signal</span>
                <div className="mt-3 flex items-center gap-3">
                  <Badge level={riskLevel} />
                  <span className="technical-label text-[#87847e]">Next-hour system risk</span>
                </div>
              </div>
              <button
                type="button"
                onClick={refreshProduct}
                disabled={loading}
                className="technical-label flex items-center gap-2 border border-[#141414] bg-transparent px-4 py-2 text-[#141414] transition hover:bg-[#141414] hover:text-[#e4e3e0] disabled:opacity-50"
              >
                <RefreshCw className={clsx('h-3.5 w-3.5', loading && 'animate-spin')} /> {presentationMode ? 'Replay snapshot' : 'Refresh system'}
              </button>
            </div>

            <div className="grid items-end gap-8 lg:grid-cols-[1fr_0.9fr]">
              <div>
                <div className="flex items-end gap-3">
                  <span className={clsx('font-mono text-[clamp(5.3rem,12vw,10rem)] font-light leading-[0.72] tracking-[-0.09em]', danger ? 'text-[#ff7663]' : 'text-[#141414]')}>
                    <span className={clsx(!data && 'text-[0.42em] tracking-[-0.03em] text-[#a29f98]')}>
                      {data ? data.risk_score.toFixed(0) : 'N/A'}
                    </span>
                  </span>
                  <span className="mb-1 font-mono text-sm text-[#87847e]">/100</span>
                </div>
                <div className="mt-6 flex flex-wrap items-center gap-3">
                  <span className={clsx('technical-label border border-[#141414] px-3 py-1.5', marginMw !== null && marginMw < 0 ? 'bg-[#c52f19] text-white' : 'bg-[#ff4d00] text-[#141414]')}>
                    {marginState}
                  </span>
                  {riskDelta !== null && (
                    <span className={clsx('flex items-center gap-1 font-mono text-xs', riskDelta > 0 ? 'text-[#ff8878]' : 'text-[#ff4d00]')}>
                      {riskDelta > 0 ? <ArrowUpRight className="h-3.5 w-3.5" /> : <ArrowDownRight className="h-3.5 w-3.5" />}
                      {Math.abs(riskDelta).toFixed(1)} vs prior run
                    </span>
                  )}
                </div>
              </div>

              <div className="border-l border-black/[0.1] pl-5 sm:pl-7">
                <span className="technical-label text-[#6d6b66]">Operator brief</span>
                <h2 className="display-serif mt-3 text-2xl leading-tight tracking-tight text-[#141414]">
                  {data
                    ? marginMw !== null && marginMw < 0
                      ? 'Tail demand crosses the stated capacity boundary.'
                      : 'Capacity remains above the modeled extreme-demand tail.'
                    : 'The decision layer is waiting for a compatible prediction service.'}
                </h2>
                <p className="mt-3 text-sm leading-6 text-[#4f4e4a]">
                  {data
                    ? capacity !== null
                      ? `P99 demand is ${(data.q99_load_mw / 1000).toFixed(2)} GW against ${(capacity / 1000).toFixed(2)} GW of capacity context.`
                      : `P99 demand is ${(data.q99_load_mw / 1000).toFixed(2)} GW; verified capacity context is not available.`
                    : 'No forecast is substituted or fabricated while the live service is unavailable.'}
                </p>
                <button type="button" onClick={() => setShowWhy((value) => !value)} disabled={!data} className="mt-5 flex items-center gap-2 text-xs font-medium text-[#ff4d00] disabled:text-[#a29f98]">
                  Inspect decision logic <ChevronRight className={clsx('h-3.5 w-3.5 transition', showWhy && 'rotate-90')} />
                </button>
              </div>
            </div>
          </div>
        </div>

        <Card className="panel-boundary flex min-h-[430px] flex-col justify-between overflow-hidden p-0 xl:col-span-4">
          <div className="border-b border-black/[0.08] p-6">
            <span className="technical-label text-[#6d6b66]">02 / System boundary</span>
            <div className="mt-4 flex items-end justify-between">
              <div><p className="text-sm text-[#6d6b66]">P99 capacity margin</p><p className="mt-1 font-mono text-4xl tracking-tight text-[#141414]">{marginMw === null ? '—' : `${(marginMw / 1000).toFixed(2)}`} <span className="text-sm text-[#87847e]">GW</span></p></div>
              <Gauge className={clsx('h-10 w-10', marginMw !== null && marginMw < 0 ? 'text-[#b42318]' : 'text-[#2f6b4f]')} />
            </div>
          </div>
          <div className="grid flex-1 grid-cols-2">
            <MetricCell label="Current system load" value={gridContext ? `${(gridContext.current_load_mw / 1000).toFixed(1)} GW` : '—'} icon={<Radio />} />
            <MetricCell label="Available capacity" value={capacity !== null ? `${(capacity / 1000).toFixed(1)} GW` : '—'} icon={<Gauge />} />
            <MetricCell label="Expected / P50" value={data ? `${(data.q50_load_mw / 1000).toFixed(1)} GW` : '—'} icon={<Activity />} />
            <MetricCell label="Extreme / P99" value={data ? `${(data.q99_load_mw / 1000).toFixed(1)} GW` : '—'} icon={<Zap />} />
            <MetricCell label="Temperature" value={`${inputs.temperature.toFixed(1)}°C`} icon={<Thermometer />} />
            <MetricCell label="Wind signal" value={`${inputs.wind_speed.toFixed(1)} m/s`} icon={<Wind />} />
          </div>
          <div className="border-t border-black/[0.08] px-6 py-4">
            <div className={clsx('flex items-center gap-2 technical-label', contextError && !gridContext ? 'text-[#b42318]' : 'text-[#4f4d49]')}>
              <span className={clsx('h-1.5 w-1.5 rounded-full', contextError && !gridContext ? 'bg-[#b42318]' : officialLoad ? 'signal-dot bg-[#2f6b4f]' : 'bg-[#9a6200]')} />
              {presentationMode ? sourceLabel(provenance) : gridSourceLabel(gridContext, contextError)}
            </div>
          </div>
        </Card>
      </section>

      {showWhy && data && (
        <section className="reveal grid gap-px overflow-hidden border border-[#141414] bg-[#141414] shadow-[5px_5px_0_#ff4d00] md:grid-cols-3">
          <LogicStep index="A" title="Tail distance" body={`P99 sits ${Math.abs((marginMw ?? 0) / 1000).toFixed(2)} GW ${marginMw !== null && marginMw < 0 ? 'above' : 'below'} capacity.`} />
          <LogicStep index="B" title="Weather pressure" body={`${inputs.temperature.toFixed(1)}°C and ${inputs.wind_speed.toFixed(1)} m/s shape the next-hour load tail.`} />
          <LogicStep index="C" title="Run-to-run motion" body={riskDelta === null ? 'A prior comparable snapshot is not yet available.' : `Risk moved ${riskDelta > 0 ? 'up' : 'down'} ${Math.abs(riskDelta).toFixed(1)} points.`} />
        </section>
      )}

      <section className="reveal reveal-delay-2 grid gap-5 xl:grid-cols-12">
        <Card className="panel-data p-6 sm:p-7 xl:col-span-8">
          <div className="mb-8 flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
            <div><span className="technical-label text-[#6d6b66]">03 / Uncertainty geometry</span><h2 className="display-serif mt-2 text-2xl tracking-tight text-[#141414]">One forecast. Four confidence boundaries.</h2></div>
            <div className="flex items-center gap-2 rounded-full border border-[#175a73] px-3 py-1.5 text-[#175a73]"><CircleDotDashed className="h-3.5 w-3.5" /><span className="technical-label">Quantile engine</span></div>
          </div>
          <div className="min-h-[330px]">{data ? <QuantileChart prediction={data} /> : <EmptyForecast loading={loading} />}</div>
        </Card>

        <Card className="panel-system overflow-hidden p-0 xl:col-span-4">
          <div className="flex items-center justify-between border-b border-black/[0.08] px-6 py-5">
            <div><span className="technical-label text-[#6d6b66]">04 / Grid context</span><h2 className="display-serif mt-1 text-lg text-[#141414]">ERCOT interconnection</h2></div>
            <span className="technical-label rounded-full border border-[#2f6b4f] bg-[#2f6b4f]/10 px-2.5 py-1 text-[#2f6b4f]">System</span>
          </div>
          <GridMap selectedRegion={REGION} onSelect={() => undefined} className="min-h-[300px] border-0 bg-transparent" />
          <div className="border-t border-black/[0.08] px-6 py-4 text-xs leading-5 text-[#6d6b66]">Spatial context only. The active forecast is system-wide, not a fabricated weather-zone estimate.</div>
        </Card>
      </section>

      <section className="panel-scenario reveal reveal-delay-3 grid overflow-hidden border border-[#141414] lg:grid-cols-[0.7fr_1.3fr]">
        <div className="border-b border-black/[0.08] p-6 sm:p-8 lg:border-b-0 lg:border-r">
          <span className="technical-label text-[#6d6b66]">05 / Controlled intervention</span>
          <h2 className="display-serif mt-3 text-3xl leading-tight tracking-tight text-[#141414]">Stress the weather.<br />Keep the evidence.</h2>
          <p className="mt-4 max-w-sm text-sm leading-6 text-[#4f4e4a]">Adjust the physical drivers, rerun the same decision pipeline and compare against the {presentationMode ? 'simulated reference' : 'live snapshot'}.</p>
          <div className="mt-6 flex gap-2">
            <button onClick={resetScenario} className="technical-label flex items-center gap-2 border border-[#141414] px-4 py-2 text-[#141414] hover:bg-[#d9d8d4]"><RotateCcw className="h-3.5 w-3.5" /> Reset {presentationMode ? 'reference' : 'live'}</button>
            <button onClick={applyScenario} disabled={loading} className="technical-label flex items-center gap-2 border border-[#141414] bg-[#141414] px-4 py-2 text-[#e4e3e0] shadow-[3px_3px_0_#ff4d00] transition hover:bg-[#ff4d00] hover:text-[#141414] disabled:opacity-50">Run scenario <ArrowUpRight className="h-3.5 w-3.5" /></button>
          </div>
        </div>
        <div className="grid gap-px bg-black/[0.08] sm:grid-cols-3">
          <ScenarioControl icon={<Thermometer />} label="Temperature" value={`${draftInputs.temperature.toFixed(1)}°C`} live={liveSnapshot ? `${liveSnapshot.temperature.toFixed(1)}°C live` : 'sync pending'} min={-10} max={45} step={0.1} input={draftInputs.temperature} onChange={(temperature) => setDraftInputs({ ...draftInputs, temperature })} />
          <ScenarioControl icon={<Wind />} label="Wind speed" value={`${draftInputs.wind_speed.toFixed(1)} m/s`} live={liveSnapshot ? `${liveSnapshot.wind_speed.toFixed(1)} m/s live` : 'sync pending'} min={0} max={40} step={0.1} input={draftInputs.wind_speed} onChange={(wind_speed) => setDraftInputs({ ...draftInputs, wind_speed })} />
          <ScenarioControl icon={<Sun />} label="Solar input" value={`${draftInputs.solar_irradiance.toFixed(0)} W/m²`} live={liveSnapshot ? `${liveSnapshot.solar_irradiance.toFixed(0)} W/m² live` : 'sync pending'} min={0} max={1200} step={10} input={draftInputs.solar_irradiance} onChange={(solar_irradiance) => setDraftInputs({ ...draftInputs, solar_irradiance })} />
        </div>
      </section>

      <section className="grid gap-px overflow-hidden border border-[#141414] bg-[#141414] shadow-[5px_5px_0_#ff4d00] md:grid-cols-4">
        <EvidenceCell icon={<Database />} title="Load context" value={presentationMode ? 'Simulated peak-day load' : officialLoad ? 'Official ERCOT live' : gridContext ? 'Estimated fallback' : 'Unavailable'} verified={!presentationMode && officialLoad} />
        <EvidenceCell icon={<ShieldCheck />} title="Capacity basis" value={presentationMode ? 'Simulated adequacy margin' : officialCapacity ? gridContext?.capacity_basis ?? 'ERCOT adequacy' : gridContext?.capacity_basis ?? 'Unavailable'} verified={!presentationMode && officialCapacity} />
        <EvidenceCell icon={<Cpu />} title="Model artifact" value={presentationMode ? 'Presentation candidate' : backendReal ? data?.diagnostics.model_version ?? 'Trained' : 'Stub / demo'} verified={!presentationMode && backendReal} />
        <EvidenceCell icon={<Braces />} title="Decision contract" value="P50 → P99 + provenance" verified />
      </section>
    </div>
  );
}

function MetricCell({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
  return <div className="border-b border-r border-black/[0.07] p-5 last:border-b-0 [&_svg]:h-3.5 [&_svg]:w-3.5 [&_svg]:text-[#87847e]"><div className="flex items-center gap-2 text-[#87847e]">{icon}<span className="technical-label text-[9px]">{label}</span></div><p className="mt-3 font-mono text-lg text-[#141414]">{value}</p></div>;
}

function LogicStep({ index, title, body }: { index: string; title: string; body: string }) {
  return <div className="bg-[#deddd9] p-5"><div className="flex items-center gap-3"><span className="font-mono text-xs text-[#ff4d00]">{index}</span><span className="technical-label text-[#6d6b66]">{title}</span></div><p className="mt-3 text-sm leading-6 text-[#454545]">{body}</p></div>;
}

function EmptyForecast({ loading }: { loading: boolean }) {
  return <div className="grid h-[330px] place-items-center rounded-xl border border-dashed border-black/[0.1] bg-black/[0.015] text-center"><div><Layers3 className="mx-auto h-8 w-8 text-[#a29f98]" /><p className="mt-4 text-sm text-[#4f4e4a]">{loading ? 'Initializing probability boundaries…' : 'Forecast boundaries unavailable'}</p><p className="mt-1 text-xs text-[#87847e]">The interface will not invent a distribution.</p></div></div>;
}

function ScenarioControl({ icon, label, value, live, min, max, step, input, onChange }: { icon: React.ReactNode; label: string; value: string; live: string; min: number; max: number; step: number; input: number; onChange: (value: number) => void }) {
  return <div className="bg-[#e4e3e0] p-6 sm:p-7"><div className="flex items-center justify-between text-[#6d6b66]"><span className="flex items-center gap-2 technical-label [&_svg]:h-3.5 [&_svg]:w-3.5">{icon}{label}</span><span className="font-mono text-[10px] text-[#87847e]">{live}</span></div><p className="mt-8 font-mono text-2xl text-[#141414]">{value}</p><input aria-label={label} type="range" min={min} max={max} step={step} value={input} onChange={(event) => onChange(Number(event.target.value))} className="mt-6 h-1 w-full cursor-pointer appearance-none rounded bg-black/10 accent-[#ff4d00]" /></div>;
}

function EvidenceCell({ icon, title, value, verified }: { icon: React.ReactNode; title: string; value: string; verified: boolean }) {
  return <div className={clsx('p-5', verified ? 'evidence-verified' : 'evidence-fallback')}><div className="flex items-center justify-between"><span className="text-[#4f4d49] [&_svg]:h-4 [&_svg]:w-4">{icon}</span>{verified ? <Check className="h-3.5 w-3.5 text-[#2f6b4f]" /> : <AlertTriangle className="h-3.5 w-3.5 text-[#9a6200]" />}</div><p className="technical-label mt-5 text-[#4f4d49]">{title}</p><p className="mt-1 text-xs text-[#141414]">{value}</p></div>;
}
