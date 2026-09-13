'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ArrowUpRight, Download, Link2, RotateCcw } from 'lucide-react';
import { ResponsiveContainer, ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine } from 'recharts';
import { analyzeHistory, analysisReport, historicalCases, historicalSource, reportCsv } from '@/lib/historical';

const number = (n: number) => n.toLocaleString('en-US', { maximumFractionDigits: 0 });
function download(filename: string, content: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement('a');
  link.href = url; link.download = filename; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function HistoryPage() {
  const [caseId, setCaseId] = useState(historicalCases[0].id);
  const [capacity, setCapacity] = useState(historicalCases[0].default_capacity_mw);
  const [reduction, setReduction] = useState(5);
  const [notice, setNotice] = useState('');
  const [initialized, setInitialized] = useState(false);
  useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    const selected = historicalCases.find((item) => item.id === query.get('case')) ?? historicalCases[0];
    const cap = Number(query.get('capacity'));
    const cut = query.has('reduction') ? Number(query.get('reduction')) : 5;
    setCaseId(selected.id);
    setCapacity(Number.isFinite(cap) && cap >= 10000 && cap <= 120000 ? cap : selected.default_capacity_mw);
    setReduction(Number.isFinite(cut) && cut >= 0 && cut <= 20 ? cut : 5);
    setInitialized(true);
  }, []);
  useEffect(() => {
    if (!initialized) return;
    const url = new URL(window.location.href);
    url.searchParams.set('case', caseId);
    url.searchParams.set('capacity', String(capacity));
    url.searchParams.set('reduction', String(reduction));
    window.history.replaceState(null, '', url);
  }, [caseId, capacity, reduction, initialized]);
  const selected = historicalCases.find((item) => item.id === caseId)!;
  const result = useMemo(() => analyzeHistory(selected, capacity, reduction), [selected, capacity, reduction]);
  const report = useMemo(() => analysisReport(selected, capacity, reduction), [selected, capacity, reduction]);

  return <div className="space-y-8 pb-16">
    <header className="grid gap-6 border-b border-black/15 pb-8 xl:grid-cols-[1.2fr_0.8fr] xl:items-end">
      <div><span className="technical-label text-[#b73700]">Historical lab / 216 observed hours</span>
        <h1 className="display-serif mt-4 text-[clamp(2.8rem,6vw,5.8rem)] leading-[0.94] tracking-[-0.055em]">A real load curve.<br />Your planning decision.</h1></div>
      <p className="max-w-lg text-sm leading-6 text-[#4f4e4a]">Explore published ERCOT load, choose a hypothetical capacity, and compare a load-reduction assumption. Every result can be downloaded and independently reproduced. No account required.</p>
    </header>
    <Link href="/briefs/winter-load" className="block border border-black/20 bg-[#ebe3cf] p-4 text-sm leading-6"><span className="font-semibold">New to grid data?</span> Why can electricity use fall during a blackout? Read the 90-second introduction →</Link>
    <div className="border-l-4 border-[#2f6b4f] bg-[#dce9e1] p-4 text-sm leading-6"><strong>Observed load · Hypothetical intervention.</strong> This lab works from a bundled historical archive. Capacity and load reductions are assumptions; the results are not live forecasts or measured outage savings.</div>
    <section aria-label="Choose a historical window" className="grid gap-3 md:grid-cols-3">
      {historicalCases.map((item) => <button key={item.id} onClick={() => { setCaseId(item.id); setCapacity(item.default_capacity_mw); setReduction(5); setNotice(''); }} aria-pressed={caseId === item.id} className={`border p-5 text-left transition ${caseId === item.id ? 'border-[#141414] bg-[#141414] text-white shadow-[4px_4px_0_#ff4d00]' : 'border-black/20 bg-[#f7f6f2] hover:border-[#141414]'}`}>
        <span className="technical-label opacity-70">72 hours / {item.start_date}</span><span className="mt-3 block text-lg font-semibold">{item.title}</span>
      </button>)}
    </section>
    <section className="grid gap-6 xl:grid-cols-[0.75fr_1.6fr]">
      <div className="border border-black/20 bg-[#f7f6f2] p-6">
        <span className="technical-label text-[#6d6b66]">01 / Set assumptions</span>
        <label htmlFor="capacity" className="mt-6 block text-sm font-semibold">Assumed available capacity</label>
        <output htmlFor="capacity" className="display-serif mt-2 block text-4xl">{number(capacity)} <span className="text-lg">MW</span></output>
        <input id="capacity" type="range" min="10000" max="120000" step="250" value={capacity} onChange={(e) => setCapacity(Number(e.target.value))} className="mt-5 w-full accent-[#d63f00]" />
        <label htmlFor="reduction" className="mt-7 block text-sm font-semibold">Uniform load reduction</label>
        <output htmlFor="reduction" className="display-serif mt-2 block text-4xl">{reduction.toFixed(1)}%</output>
        <input id="reduction" type="range" min="0" max="20" step="0.5" value={reduction} onChange={(e) => setReduction(Number(e.target.value))} className="mt-5 w-full accent-[#d63f00]" />
        <div className="mt-3 flex gap-2" role="group" aria-label="Load reduction presets">{[0, 5, 10].map((value) => <button key={value} onClick={() => setReduction(value)} aria-pressed={reduction === value} className={`flex-1 border border-black/25 py-2 text-sm ${reduction === value ? 'bg-[#f3c64d]' : 'bg-white'}`}>{value}%</button>)}</div>
        <button onClick={() => { setCapacity(selected.default_capacity_mw); setReduction(5); }} className="mt-6 flex items-center gap-2 text-sm underline underline-offset-4"><RotateCcw size={14} /> Reset assumptions</button>
        <p className="mt-6 border-t border-black/15 pt-5 text-xs leading-5 text-[#4f4e4a]">{selected.note}</p>
      </div>
      <div className="min-w-0 border border-black/20 bg-[#f7f6f2] p-4 sm:p-6">
        <span className="technical-label text-[#6d6b66]">02 / Compare the load curves</span>
        <h2 className="display-serif mt-3 text-3xl">Where does load cross the boundary?</h2>
        <p className="mt-2 text-xs text-[#6d6b66]">Hourly interval starts, America/Chicago · load in MW</p>
        <div className="mt-6 h-[330px]" role="img" aria-label={`Recorded peak ${number(result.recordedPeakMw)} MW. With ${reduction}% reduction, ${result.adjustedHoursAboveCapacity} hours exceed assumed capacity. Full data available below.`}>
          <ResponsiveContainer width="100%" height="100%"><ComposedChart data={result.rows} margin={{ top: 10, right: 15, bottom: 10, left: 0 }}>
            <CartesianGrid stroke="#d8d6d0" strokeDasharray="3 3" /><XAxis dataKey="timestamp" minTickGap={55} tickFormatter={(v: string) => `${v.slice(5, 10)} ${v.slice(11, 13)}h`} tick={{ fontSize: 10 }} />
            <YAxis domain={[0, (maximum: number) => Math.max(maximum, capacity) * 1.08]} tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} width={45} />
            <Tooltip labelFormatter={(label) => String(label).replace('T', ' ')} formatter={(value, name) => [`${number(Number(value))} MW`, name]} /><Legend wrapperStyle={{ fontSize: 12 }} />
            <Line dataKey="recordedLoadMw" name="Recorded load" stroke="#141414" strokeWidth={2.5} dot={false} isAnimationActive={false} />
            <Line dataKey="adjustedLoadMw" name="With assumed reduction" stroke="#25684a" strokeWidth={2.5} strokeDasharray="6 3" dot={false} isAnimationActive={false} />
            <ReferenceLine y={capacity} stroke="#b73700" strokeWidth={2} strokeDasharray="3 3" label={{ value: 'Assumed capacity', position: 'insideTopRight', fill: '#b73700', fontSize: 11 }} />
          </ComposedChart></ResponsiveContainer>
        </div>
      </div>
    </section>
    <section className="grid gap-4 md:grid-cols-3" aria-label="Analysis results" aria-live="polite">
      <Metric label="Hours above assumed capacity" value={`${result.originalHoursAboveCapacity} → ${result.adjustedHoursAboveCapacity}`} note="Before → after assumed reduction, out of 72 hours" />
      <Metric label="Counterfactual gap energy" value={`${number(result.adjustedGapMwh)} MWh`} note={`Before reduction: ${number(result.originalGapMwh)} MWh. Not expected unserved energy.`} />
      <Metric label="Reduction needed to clear the peak" value={`${result.minimumUniformReductionPercent.toFixed(2)}%`} note="Algebraic minimum at this assumed capacity; feasibility is not evaluated." />
    </section>
    <section className="border border-[#141414] bg-[#f3c64d] p-6 sm:p-8">
      <span className="technical-label">03 / Keep a reproducible record</span>
      <h2 className="display-serif mt-3 text-3xl">Take the calculation with you.</h2>
      <p className="mt-3 max-w-3xl text-sm leading-6">The report includes all 72 observations, assumptions, formulas, source links, and the source archive checksum. Downloads stay on your device. Share the report or a link to let someone reproduce your analysis.</p>
      <div className="mt-5 flex flex-wrap gap-3">
        <button onClick={() => { download(`gert-${caseId}-report.json`, JSON.stringify(report, null, 2), 'application/json'); setNotice('JSON report downloaded.'); }} className="flex items-center gap-2 bg-[#141414] px-5 py-3 text-sm text-white"><Download size={16} /> Download report (JSON)</button>
        <button onClick={() => { download(`gert-${caseId}-hourly.csv`, reportCsv(report), 'text/csv'); setNotice('Hourly CSV downloaded. Assumptions and limitations are in the JSON report.'); }} className="flex items-center gap-2 border border-[#141414] px-5 py-3 text-sm"><Download size={16} /> Hourly CSV</button>
        <button onClick={async () => { try { await navigator.clipboard.writeText(window.location.href); setNotice('Link copied with your case and assumptions.'); } catch { setNotice('Copy the URL from your address bar; your assumptions are included.'); } }} className="flex items-center gap-2 border border-[#141414] px-5 py-3 text-sm"><Link2 size={16} /> Copy this analysis</button>
      </div><p role="status" className="mt-3 min-h-5 text-xs">{notice}</p>
    </section>
    <section className="grid gap-8 border-t border-black/20 pt-8 lg:grid-cols-2">
      <div><span className="technical-label text-[#6d6b66]">04 / Challenge the result</span><h2 className="display-serif mt-3 text-3xl">What would change your decision?</h2><p className="mt-3 text-sm leading-6">Review a source value, reproduce the calculation, or identify a missing constraint. A useful critique becomes an inspectable issue and a documented product change.</p><Link href="/review" className="mt-5 inline-flex items-center gap-2 border-b border-[#b73700] pb-1 text-sm font-semibold">Open the 10-minute review guide <ArrowUpRight size={16} /></Link></div>
      <div className="text-xs leading-6 text-[#4f4e4a]"><h3 className="font-semibold text-[#141414]">Source and interpretation</h3><p>{historicalSource.load_definition}</p><a href={selected.source_url} className="underline underline-offset-4">Download the original ERCOT archive</a><p className="mt-2 break-all font-mono text-[10px]">Archive SHA-256: {selected.source_archive_sha256}</p><p className="mt-3">Gap energy = ∑ max(0, load − assumed capacity) × 1 hour. It has no probability model. Transmission, reserves, generation outages, behavioral response, and costs are not included.</p><a href="/data/historical-cases.json" className="mr-4 underline">Versioned dataset</a><a href="/data/historical-cases.sha256" className="underline">Dataset checksum</a></div>
    </section>
    <details className="border border-black/20 bg-[#f7f6f2] p-5"><summary className="cursor-pointer text-sm font-semibold">Inspect all 72 hourly calculations</summary><div className="mt-5 overflow-x-auto"><table className="w-full text-left text-xs"><caption className="mb-3 text-left">{selected.title}; interval starts in America/Chicago</caption><thead><tr>{['Interval start', 'Recorded MW', 'Adjusted MW', 'Capacity MW', 'Gap MW'].map((label) => <th className="border-b border-black/20 p-2" key={label}>{label}</th>)}</tr></thead><tbody>{result.rows.map((row) => <tr key={row.timestamp}><td className="whitespace-nowrap p-2 font-mono">{row.timestamp}</td><td className="p-2">{number(row.recordedLoadMw)}</td><td className="p-2">{number(row.adjustedLoadMw)}</td><td className="p-2">{number(capacity)}</td><td className="p-2">{number(row.adjustedGapMw)}</td></tr>)}</tbody></table></div></details>
  </div>;
}

function Metric({ label, value, note }: { label: string; value: string; note: string }) {
  return <div className="border border-black/20 bg-[#f7f6f2] p-6"><p className="technical-label text-[#6d6b66]">{label}</p><p className="display-serif mt-4 text-4xl">{value}</p><p className="mt-3 text-xs leading-5 text-[#4f4e4a]">{note}</p></div>;
}
