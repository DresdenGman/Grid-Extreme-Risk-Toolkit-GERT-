'use client';

import { useState } from 'react';
import { sameMeterScenario, sameMeterSnapshot } from '@/lib/same-meter';

const format = (value: number) => new Intl.NumberFormat('en-US').format(value);

export default function SameMeterChallenge() {
  const [demand, setDemand] = useState(65000);
  const [notice, setNotice] = useState('');
  const scenario = sameMeterScenario(demand);

  function download() {
    let url: string | undefined;
    try {
      const snapshot = sameMeterSnapshot(demand, new Date().toISOString());
      url = URL.createObjectURL(new Blob([JSON.stringify(snapshot, null, 2)], { type: 'application/json' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = 'gert-same-meter-model.json';
      document.body.appendChild(link);
      try { link.click(); } finally { link.remove(); }
      setNotice('Download requested. The model snapshot is not a certificate or proof of independent use.');
    } catch {
      setNotice('Download unavailable. You can copy the assumptions and calculations from the tables below.');
    } finally {
      if (url) { const fileUrl = url; setTimeout(() => URL.revokeObjectURL(fileUrl), 1000); }
    }
  }

  return <section aria-labelledby="same-meter-heading" className="space-y-6">
    <div className="border border-[#141414] bg-[#dfe8ea] p-5 sm:p-8">
      <span className="technical-label text-[#175a73]">01 / What both meters show</span>
      <h2 id="same-meter-heading" className="display-serif mt-3 text-3xl sm:text-4xl">The same fall. A different story.</h2>
      <div className="mt-5 flex flex-wrap items-baseline gap-x-5 gap-y-2 font-mono text-3xl sm:text-5xl" aria-label="Delivered electricity: 60 gigawatts in hour one, 45 gigawatts in hour two">
        <span>60 GW</span><span aria-hidden="true">→</span><span>45 GW</span>
      </div>
      <p className="mt-4 max-w-2xl text-sm leading-6">Each reading is constant over one hour in this invented example. Before looking below: does the fall tell you how much electricity people wanted but did not receive?</p>
    </div>

    <div className="grid gap-5 lg:grid-cols-2">
      <div className="border border-black/25 bg-[#e0e7df] p-5 sm:p-6">
        <span className="technical-label text-[#2f6b4f]">World A / Less wanted</span>
        <h3 className="display-serif mt-3 text-3xl">Demand falls to 45 GW.</h3>
        <p className="mt-3 text-sm leading-6">The assumed delivery ceiling stays at 90 GW. All demand in both hours is served.</p>
        <p className="mt-5 text-sm">Model unserved energy, two hours</p>
        <p className="mt-1 font-mono text-3xl">0 MWh</p>
      </div>
      <div className="border border-black/25 bg-[#eee0d4] p-5 sm:p-6">
        <span className="technical-label text-[#a83400]">World B / Delivery constrained</span>
        <h3 className="display-serif mt-3 text-3xl">The ceiling falls to 45 GW.</h3>
        <p className="mt-3 text-sm leading-6">Change the assumed second-hour demand. The meter cannot show electricity that is not delivered.</p>
        <label htmlFor="same-meter-demand" className="mt-5 block text-sm font-semibold">World B: second-hour demand — {demand / 1000} GW</label>
        <input id="same-meter-demand" type="range" min={45000} max={90000} step={5000} value={demand} onChange={(event) => setDemand(Number(event.target.value))} aria-valuetext={`${demand / 1000} gigawatts`} className="my-3 w-full accent-[#a83400]" />
        <div className="flex justify-between font-mono text-xs"><span>45 GW</span><span>90 GW</span></div>
        <p className="mt-4 border border-[#a83400] bg-white/50 px-3 py-2 text-sm font-semibold" role="status" aria-live="polite">
          Applied input: {demand / 1000} GW. The model outputs below have been recalculated.
        </p>
        <div className="mt-5 flex flex-wrap gap-x-8 gap-y-3" aria-live="polite" aria-atomic="true">
          <div><p className="text-sm">Hour-two meter</p><p className="mt-1 font-mono text-2xl">45 GW</p></div>
          <div><p className="text-sm">Model unserved energy, two hours</p><p className="mt-1 font-mono text-2xl">{format(scenario.b.totalUnservedMwh)} MWh</p></div>
        </div>
      </div>
    </div>

    <details className="border-l-4 border-[#175a73] bg-[#f7f6f2] p-5">
      <summary className="cursor-pointer font-semibold">Reveal the interpretation after recording your own</summary>
      <p className="mt-3 font-semibold">{scenario.differentUnservedEnergy ? 'Same two readings. Different unserved energy.' : 'At 45 GW, both worlds serve all demand. Move above 45 GW to construct the counterexample.'}</p>
      <p className="mt-2 text-sm leading-6">{scenario.differentUnservedEnergy ? `World A leaves 0 MWh unserved; World B leaves ${format(scenario.b.totalUnservedMwh)} MWh unserved under its assumptions. The readings alone do not tell you which world you are in.` : 'The different delivery ceilings alone do not imply unserved energy: demand must exceed the ceiling in this model.'}</p>
    </details>

    <section className="border-t border-black/20 pt-6" aria-labelledby="arithmetic-heading">
      <span className="technical-label">02 / Inspect every assumption</span>
      <h2 id="arithmetic-heading" className="display-serif mt-3 text-3xl">A counterexample you can check.</h2>
      <p className="mt-3 text-sm leading-6">In this simplified model, delivered power = min(demand, delivery ceiling). Unserved energy = (demand − delivered power) × 1 hour. 1 GW = 1,000 MW. All table inputs are invented assumptions.</p>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[580px] text-left text-sm">
          <caption className="mb-3 text-left text-xs text-[#514e48]">Two one-hour intervals; arithmetic in MW and MWh. No historical loss estimate.</caption>
          <thead className="bg-[#deddd9]"><tr>{['World / hour', 'Demand (MW)', 'Ceiling (MW)', 'Delivered (MW)', 'Unserved (MWh)'].map((label) => <th key={label} scope="col" className="p-3 font-semibold">{label}</th>)}</tr></thead>
          <tbody>{(['a', 'b'] as const).flatMap((key) => scenario[key].rows.map((row) => <tr key={`${key}-${row.hour}`} className="border-b border-black/15"><th scope="row" className="p-3 font-normal">{key.toUpperCase()} / {row.hour}</th><td className="p-3 font-mono">{format(row.assumedDemandMw)}</td><td className="p-3 font-mono">{format(row.assumedDeliveryCeilingMw)}</td><td className="p-3 font-mono">{format(row.deliveredMw)}</td><td className="p-3 font-mono">{format(row.unservedMwh)}</td></tr>))}</tbody>
        </table>
      </div>
      <button type="button" onClick={download} className="mt-5 border border-[#141414] bg-[#141414] px-5 py-3 text-sm font-semibold text-white">Download this model snapshot</button>
      <p className="mt-3 text-xs leading-5 text-[#514e48]">This activity does not send your slider setting to GERT or count you as a participant. The JSON stays on your device unless you choose to share it. It records model parameters, not identity, learning gains, or verified participation.</p>
      <p role="status" className="mt-2 text-sm leading-6">{notice}</p>
    </section>
  </section>;
}
