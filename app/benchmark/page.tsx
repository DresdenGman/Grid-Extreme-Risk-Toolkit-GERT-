'use client';

import { useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';
import {
  evaluateCalibrationTolerance,
  PREDECLARED_CALIBRATION_TOLERANCE,
} from '@/lib/calibration';
import { BacktestResponse, ModelEvidence, ProductStatus } from '@/lib/types';
import { Card, SkeletonCard } from '@/components/ui';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Area,
} from 'recharts';
import {
  ArrowUpRight,
  CheckCircle2,
  Database,
  Gauge,
  LockKeyhole,
  ShieldAlert,
  SlidersHorizontal,
  XCircle,
} from 'lucide-react';

const percent = (value: number, digits = 1) => `${(value * 100).toFixed(digits)}%`;

export default function BenchmarkPage() {
  const [evidence, setEvidence] = useState<ModelEvidence | null>(null);
  const [status, setStatus] = useState<ProductStatus | null>(null);
  const [backtest, setBacktest] = useState<BacktestResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tolerancePp, setTolerancePp] = useState(3);
  const [selectedQuantile, setSelectedQuantile] = useState<ModelEvidence['quantile_metrics'][number]['quantile']>('q99');

  useEffect(() => {
    let active = true;

    async function loadEvidence() {
      const [statusResult, evidenceResult] = await Promise.allSettled([
        api.status(),
        api.modelEvidence(),
      ]);
      if (!active) return;

      const productStatus = statusResult.status === 'fulfilled' ? statusResult.value.data : null;
      setStatus(productStatus);

      if (evidenceResult.status === 'rejected') {
        setError('The versioned validation record is temporarily unavailable.');
        setLoading(false);
        return;
      }

      setEvidence(evidenceResult.value.data);
      if (productStatus?.capabilities.validated_backtest) {
        try {
          const response = await api.backtest();
          if (active) setBacktest(response.data);
        } catch {
          // The versioned evidence remains useful if the optional production
          // backtest artifact is temporarily unavailable.
        }
      }
      if (active) setLoading(false);
    }

    void loadEvidence();
    return () => { active = false; };
  }, []);

  const passedCalibrationGates = useMemo(
    () => evidence?.quantile_metrics.filter((metric) => metric.absolute_coverage_error <= 0.03).length ?? 0,
    [evidence],
  );

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="h-6 w-64 animate-pulse rounded bg-[#d0cfca]" />
        <div className="grid gap-6 md:grid-cols-3">
          <SkeletonCard /><SkeletonCard /><SkeletonCard />
        </div>
        <SkeletonCard className="h-80" />
      </div>
    );
  }

  if (!evidence) {
    return (
      <div className="border border-[#b42318] bg-[#f7e6e2] p-8 text-[#721c15]">
        <p className="technical-label">Evidence service unavailable</p>
        <p className="mt-3 text-sm">{error}</p>
      </div>
    );
  }

  const productionValidated = status?.model_status === 'validated_production';
  const minSkill = Math.min(...evidence.quantile_metrics.map((metric) => metric.pinball_skill_vs_baseline));
  const selectedMetric = evidence.quantile_metrics.find((metric) => metric.quantile === selectedQuantile)
    ?? evidence.quantile_metrics[0];
  const hypotheticalDecision = evaluateCalibrationTolerance(evidence.quantile_metrics, tolerancePp / 100);
  const originalDecision = evaluateCalibrationTolerance(
    evidence.quantile_metrics,
    PREDECLARED_CALIBRATION_TOLERANCE,
  );

  return (
    <div className="space-y-8 pb-12">
      <header className="grid gap-8 border-b border-black/[0.09] pb-8 lg:grid-cols-[1.25fr_0.75fr] lg:items-end">
        <div>
          <span className="technical-label text-[#ff4d00]">Evidence layer / Model governance</span>
          <h1 className="display-serif mt-4 text-[clamp(2.8rem,6vw,6rem)] leading-[0.91] tracking-[-0.06em] text-[#141414]">
            Evidence before<br />authority.
          </h1>
        </div>
        <p className="max-w-lg text-sm leading-6 text-[#4f4e4a]">
          GERT publishes the result that matters—including failed gates. A candidate earns production authority only after predictive skill, calibration, monotonicity and data-integrity checks all pass.
        </p>
      </header>

      <section className={`grid gap-5 border p-6 shadow-[7px_7px_0_#141414] sm:p-8 lg:grid-cols-[1fr_auto] lg:items-center ${productionValidated ? 'border-[#2f6b4f] bg-[#dce9e1]' : 'border-[#141414] bg-[#f3c64d]'}`}>
        <div>
          <div className="flex items-center gap-2">
            {productionValidated ? <CheckCircle2 className="h-5 w-5" /> : <LockKeyhole className="h-5 w-5" />}
            <span className="technical-label">{productionValidated ? 'Production validated' : 'Research candidate · Production gated'}</span>
          </div>
          <h2 className="display-serif mt-4 text-3xl tracking-[-0.035em]">{evidence.candidate_id}</h2>
          <p className="mt-3 max-w-4xl text-sm leading-6">{evidence.summary}</p>
        </div>
        <div className="border border-black/20 bg-white/35 px-5 py-4 text-right">
          <span className="technical-label text-black/50">Promotion result</span>
          <p className="mt-1 font-mono text-lg font-semibold uppercase">{evidence.validation_status.replaceAll('_', ' ')}</p>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Frozen holdout" value={`${evidence.observations} h`} note="Aug 21–24, 2026" icon={Database} />
        <MetricCard label="Median error" value={`${Math.round(evidence.q50_mae_mw)} MW`} note="Q50 mean absolute error" icon={Gauge} />
        <MetricCard label="Minimum skill" value={`+${percent(minSkill)}`} note="vs. month-hour baseline" icon={ArrowUpRight} />
        <MetricCard label="Calibration" value={`${passedCalibrationGates}/4`} note="quantiles within ±3 pp" icon={ShieldAlert} alert={!evidence.all_gates_passed} />
      </section>

      <section className="hairline-panel overflow-hidden rounded-[28px]">
        <div className="border-b border-black/10 p-6 sm:p-8">
          <span className="technical-label text-[#6d6b66]">Frozen-window quantile evidence</span>
          <h2 className="display-serif mt-3 text-3xl tracking-tight">Skill is strong. Calibration is not yet stable enough.</h2>
        </div>
        <div className="grid md:grid-cols-2 xl:grid-cols-4">
          {evidence.quantile_metrics.map((metric) => {
            const passed = metric.absolute_coverage_error <= 0.03;
            return (
              <div key={metric.quantile} className="border-b border-black/10 p-6 last:border-b-0 md:border-r xl:border-b-0">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xl font-semibold uppercase">{metric.quantile}</span>
                  {passed ? <CheckCircle2 className="h-4 w-4 text-[#2f6b4f]" /> : <XCircle className="h-4 w-4 text-[#b42318]" />}
                </div>
                <div className="mt-7 flex items-baseline gap-2">
                  <span className="display-serif text-4xl">{percent(metric.empirical_coverage)}</span>
                  <span className="text-xs text-[#6d6b66]">observed</span>
                </div>
                <dl className="mt-5 space-y-2 border-t border-black/10 pt-4 text-xs">
                  <div className="flex justify-between"><dt className="text-[#6d6b66]">Target</dt><dd className="font-mono">{percent(metric.target_coverage, 0)}</dd></div>
                  <div className="flex justify-between"><dt className="text-[#6d6b66]">Absolute error</dt><dd className={`font-mono ${passed ? 'text-[#2f6b4f]' : 'text-[#b42318]'}`}>{percent(metric.absolute_coverage_error, 2)}</dd></div>
                  <div className="flex justify-between"><dt className="text-[#6d6b66]">Pinball skill</dt><dd className="font-mono text-[#2f6b4f]">+{percent(metric.pinball_skill_vs_baseline)}</dd></div>
                </dl>
              </div>
            );
          })}
        </div>
      </section>

      <section id="evidence-rehearsal" className="scroll-mt-8 overflow-hidden border border-[#141414] bg-[#f7f6f2] shadow-[7px_7px_0_#f3c64d]">
        <div className="grid border-b border-black/10 lg:grid-cols-[0.85fr_1.15fr]">
          <div className="border-b border-black/10 p-6 sm:p-8 lg:border-b-0 lg:border-r">
            <div className="flex items-center gap-2 text-[#ff4d00]">
              <SlidersHorizontal className="h-4 w-4" />
              <span className="technical-label">Interactive evidence rehearsal</span>
            </div>
            <h2 className="display-serif mt-4 text-4xl tracking-[-0.04em]">Would you authorize this model?</h2>
            <p className="mt-4 text-sm leading-6 text-[#4f4e4a]">
              Stress-test the calibration tolerance against the frozen 96-hour record. This changes only the hypothetical rule below—not the predeclared ±3 percentage-point gate or the published rejection.
            </p>

            <label className="mt-8 block text-xs font-semibold uppercase tracking-[0.16em] text-[#6d6b66]" htmlFor="calibration-tolerance">
              Hypothetical tolerance
            </label>
            <div className="mt-3 flex items-center gap-4">
              <input
                id="calibration-tolerance"
                type="range"
                min="1"
                max="6"
                step="0.25"
                value={tolerancePp}
                onChange={(event) => setTolerancePp(Number(event.target.value))}
                className="h-2 flex-1 cursor-pointer appearance-none rounded-full bg-[#d0cfca] accent-[#ff4d00]"
              />
              <output htmlFor="calibration-tolerance" className="w-20 border border-black/15 bg-white px-3 py-2 text-right font-mono text-lg font-semibold">
                ±{tolerancePp.toFixed(2)} pp
              </output>
            </div>

            <button
              type="button"
              onClick={() => setTolerancePp(PREDECLARED_CALIBRATION_TOLERANCE * 100)}
              className="mt-4 text-xs font-semibold uppercase tracking-[0.14em] text-[#6d6b66] underline decoration-[#ff4d00] underline-offset-4 hover:text-[#141414]"
            >
              Restore predeclared 3 pp gate
            </button>
          </div>

          <div className="grid p-6 sm:p-8">
            <div className={`border p-6 ${hypotheticalDecision.allPassed ? 'border-[#2f6b4f] bg-[#dce9e1]' : 'border-[#b42318] bg-[#f7e6e2]'}`} role="status" aria-live="polite">
              <span className="technical-label text-black/55">Hypothetical result</span>
              <div className="mt-3 flex items-start gap-3">
                {hypotheticalDecision.allPassed
                  ? <CheckCircle2 className="mt-1 h-6 w-6 shrink-0 text-[#2f6b4f]" />
                  : <XCircle className="mt-1 h-6 w-6 shrink-0 text-[#b42318]" />}
                <div>
                  <p className="display-serif text-3xl tracking-tight">
                    {hypotheticalDecision.allPassed ? 'Calibration would pass.' : 'Calibration would still fail.'}
                  </p>
                  <p className="mt-2 text-sm leading-6 text-[#4f4e4a]">
                    {hypotheticalDecision.allPassed
                      ? 'All four observed coverage errors fall inside this hypothetical tolerance.'
                      : `${hypotheticalDecision.failedQuantiles.map((quantile) => quantile.toUpperCase()).join(', ')} remain outside this hypothetical tolerance.`}
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-6">
              <span className="technical-label text-[#6d6b66]">Inspect one quantile</span>
              <div className="mt-3 grid grid-cols-4 gap-2" role="group" aria-label="Quantile selection">
                {evidence.quantile_metrics.map((metric) => (
                  <button
                    key={metric.quantile}
                    type="button"
                    aria-pressed={selectedQuantile === metric.quantile}
                    onClick={() => setSelectedQuantile(metric.quantile)}
                    className={`border px-2 py-3 font-mono text-sm font-semibold uppercase transition ${selectedQuantile === metric.quantile ? 'border-[#141414] bg-[#141414] text-white' : 'border-black/15 bg-white hover:border-[#ff4d00]'}`}
                  >
                    {metric.quantile}
                  </button>
                ))}
              </div>

              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <RehearsalMetric label="Target coverage" value={percent(selectedMetric.target_coverage, 0)} />
                <RehearsalMetric label="Observed coverage" value={percent(selectedMetric.empirical_coverage, 2)} />
                <RehearsalMetric label="Absolute error" value={`${(selectedMetric.absolute_coverage_error * 100).toFixed(2)} pp`} />
              </div>
            </div>

            <div className="mt-6 border-t border-black/10 pt-5 text-xs leading-5 text-[#6d6b66]">
              Published decision: <strong className="text-[#141414]">{originalDecision.allPassed ? 'pass' : 'reject'}</strong> at the frozen ±3 pp rule. A looser after-the-fact threshold can explain sensitivity, but cannot retroactively authorize the candidate.
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-12">
        <div className="hairline-panel rounded-[28px] p-6 sm:p-8 lg:col-span-7">
          <span className="technical-label text-[#6d6b66]">Promotion gates</span>
          <div className="mt-6 divide-y divide-black/10">
            {evidence.gates.map((gate) => (
              <div key={gate.gate} className="grid gap-2 py-4 first:pt-0 sm:grid-cols-[1fr_auto_auto] sm:items-center sm:gap-6">
                <div className="flex items-center gap-2 text-sm font-medium">
                  {gate.passed ? <CheckCircle2 className="h-4 w-4 text-[#2f6b4f]" /> : <XCircle className="h-4 w-4 text-[#b42318]" />}
                  {gate.gate}
                </div>
                <span className="font-mono text-xs text-[#4f4e4a]">observed {gate.observed.toFixed(6)}</span>
                <span className="text-xs text-[#6d6b66]">{gate.requirement}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="border border-[#141414] bg-[#141414] p-6 text-[#f1f0ec] shadow-[7px_7px_0_#ff4d00] sm:p-8 lg:col-span-5">
          <span className="technical-label text-[#ff7a42]">Evidence provenance</span>
          <p className="mt-5 text-sm leading-6 text-[#d0cfca]">{evidence.data_provenance}</p>
          <div className="mt-7 border-t border-white/15 pt-5">
            <span className="technical-label text-white/45">Known limitations</span>
            <ul className="mt-4 space-y-3">
              {evidence.limitations.map((limitation) => (
                <li key={limitation} className="flex gap-3 text-xs leading-5 text-[#d0cfca]"><span className="text-[#ff4d00]">—</span>{limitation}</li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {backtest ? (
        <Card>
          <span className="technical-label text-[#2f6b4f]">Validated production artifact</span>
          <h2 className="display-serif mt-3 text-2xl">Observed holdout trace</h2>
          <div className="mt-6 h-[340px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={backtest.time_series}>
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
      ) : (
        <section className="flex flex-col gap-5 border border-dashed border-[#87847e] bg-white/25 p-6 sm:flex-row sm:items-center sm:justify-between sm:p-8">
          <div>
            <span className="technical-label text-[#6d6b66]">Production backtest</span>
            <h2 className="display-serif mt-2 text-2xl">Locked until every promotion gate passes.</h2>
          </div>
          <LockKeyhole className="h-9 w-9 text-[#87847e]" />
        </section>
      )}
    </div>
  );
}

function RehearsalMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-black/10 bg-white p-4">
      <p className="technical-label text-[#6d6b66]">{label}</p>
      <p className="mt-2 font-mono text-xl font-semibold text-[#141414]">{value}</p>
    </div>
  );
}

function MetricCard({
  label,
  value,
  note,
  icon: Icon,
  alert = false,
}: {
  label: string;
  value: string;
  note: string;
  icon: typeof Database;
  alert?: boolean;
}) {
  return (
    <Card className={alert ? 'border-[#b42318] bg-[#f7e6e2]' : ''}>
      <div className="flex items-center justify-between">
        <span className="technical-label text-[#6d6b66]">{label}</span>
        <Icon className={`h-4 w-4 ${alert ? 'text-[#b42318]' : 'text-[#ff4d00]'}`} />
      </div>
      <p className="display-serif mt-6 text-4xl tracking-tight">{value}</p>
      <p className="mt-2 text-xs text-[#6d6b66]">{note}</p>
    </Card>
  );
}
