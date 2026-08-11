import { Activity, ArrowDown, Braces, Database, FlaskConical, ShieldCheck, Target } from 'lucide-react';

const layers = [
  { n: '01', icon: Database, title: 'Observe', text: 'Official load, adequacy and weather context enter with explicit provenance.' },
  { n: '02', icon: Braces, title: 'Forecast', text: 'Quantile models estimate a distribution from P50 through the extreme P99 tail.' },
  { n: '03', icon: FlaskConical, title: 'Stress', text: 'Scenario controls perturb physical drivers through the same inference contract.' },
  { n: '04', icon: ShieldCheck, title: 'Prove', text: 'Calibration gates, artifact identity and source status remain visible to the operator.' },
];

export default function About() {
  return (
    <div className="space-y-6 pb-12">
      <header className="reveal grid gap-8 border-b border-black/[0.09] pb-8 lg:grid-cols-[1.25fr_0.75fr] lg:items-end">
        <div>
          <span className="technical-label text-[#ff4d00]">Method / Product thesis</span>
          <h1 className="display-serif mt-4 max-w-4xl text-[clamp(2.6rem,6vw,6rem)] leading-[0.92] tracking-[-0.06em] text-[#141414]">The average is not where grids break.</h1>
        </div>
        <p className="max-w-lg text-base leading-7 text-[#4f4e4a]">GERT is built around the operational question conventional load dashboards obscure: how close is an unlikely—but plausible—demand tail to the system boundary?</p>
      </header>

      <section className="grid overflow-hidden border border-[#141414] bg-[#141414] shadow-[7px_7px_0_#ff4d00] md:grid-cols-4">
        {layers.map(({ n, icon: Icon, title, text }, index) => (
          <div key={title} className="relative bg-[#deddd9] p-6 sm:p-7">
            <div className="flex items-center justify-between"><span className="technical-label text-[#87847e]">{n}</span><Icon className="h-4 w-4 text-[#ff4d00]" /></div>
            <h2 className="display-serif mt-10 text-xl text-[#141414]">{title}</h2>
            <p className="mt-3 text-sm leading-6 text-[#4f4e4a]">{text}</p>
            {index < layers.length - 1 && <ArrowDown className="mt-6 h-4 w-4 text-[#a29f98] md:hidden" />}
          </div>
        ))}
      </section>

      <section className="grid gap-5 lg:grid-cols-12">
        <div className="hairline-panel rounded-[28px] p-6 sm:p-8 lg:col-span-7">
          <span className="technical-label text-[#6d6b66]">What makes GERT distinct</span>
          <div className="mt-7 divide-y divide-black/15">
            <Difference conventional="A single expected-load line" gert="A visible P50–P99 uncertainty geometry" />
            <Difference conventional="Weather conditions as the endpoint" gert="Weather translated into capacity-tail pressure" />
            <Difference conventional="A black-box risk badge" gert="Risk logic, source provenance and artifact identity" />
            <Difference conventional="A read-only monitoring dashboard" gert="Monitor → stress → replay → validate workflow" />
          </div>
        </div>

        <div className="relative overflow-hidden border border-[#141414] bg-[#ff4d00] p-6 text-[#07100a] shadow-[7px_7px_0_#141414] sm:p-8 lg:col-span-5">
          <Activity className="absolute -bottom-16 -right-14 h-64 w-64 opacity-[0.08]" />
          <span className="technical-label text-[#22320d]/60">Core decision contract</span>
          <p className="display-serif relative mt-8 text-[clamp(2rem,4vw,4rem)] leading-[0.95] tracking-[-0.055em]">Tail demand<br />minus capacity<br />equals exposure.</p>
          <div className="relative mt-12 grid grid-cols-2 gap-5 border-t border-black/15 pt-5">
            <div><span className="technical-label text-black/45">Forecast</span><p className="mt-1 font-mono text-sm">P50 / P90 / P95 / P99</p></div>
            <div><span className="technical-label text-black/45">Target</span><p className="mt-1 font-mono text-sm">One hour ahead</p></div>
          </div>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-2">
        <div className="hairline-panel rounded-[28px] p-6 sm:p-8">
          <div className="flex items-center gap-3"><Target className="h-5 w-5 text-[#141414]" /><span className="technical-label text-[#6d6b66]">Quality before promotion</span></div>
          <h2 className="display-serif mt-5 text-2xl tracking-tight text-[#141414]">A model is not “real” because it finished training.</h2>
          <p className="mt-3 text-sm leading-6 text-[#4f4e4a]">Production promotion requires held-out calibration and data-quality gates. A failed candidate remains a candidate; the interface exposes fallback and stub states instead of silently upgrading their authority.</p>
        </div>
        <div className="border border-[#141414] bg-[#deddd9] p-6 shadow-[7px_7px_0_#141414] sm:p-8">
          <span className="technical-label text-[#ff4d00]">Use boundary</span>
          <h2 className="display-serif mt-5 text-2xl tracking-tight text-[#141414]">Decision support, not autonomous control.</h2>
          <p className="mt-3 text-sm leading-6 text-[#4f4e4a]">GERT is a research and demonstration system. Any stub, fallback or uncalibrated output is labeled and must not be used for real grid operations. Operational deployment requires validated live integrations, governance and human authorization.</p>
        </div>
      </section>
    </div>
  );
}

function Difference({ conventional, gert }: { conventional: string; gert: string }) {
  return <div className="grid gap-2 py-5 first:pt-0 last:pb-0 sm:grid-cols-[0.8fr_1.2fr] sm:gap-6"><p className="text-sm text-[#87847e] line-through decoration-[#87847e]">{conventional}</p><p className="flex gap-2 text-sm text-[#141414]"><span className="text-[#ff4d00]">→</span>{gert}</p></div>;
}
