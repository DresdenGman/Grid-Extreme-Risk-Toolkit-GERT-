import type { Metadata } from 'next';
import Link from 'next/link';
import Image from 'next/image';
import BriefActions from '@/components/BriefActions';
import { WINTER_BRIEF } from '@/lib/briefs';
import { historicalCases, REPO_URL } from '@/lib/historical';

export const metadata: Metadata = {
  title: "Why can electricity use fall during a blackout? | GERT",
  description: 'A short source-linked exercise about observed load, unmet demand, and the February 2021 Texas winter storm. Free chart and interactive case.',
  alternates: { canonical: WINTER_BRIEF.url },
  openGraph: { type: 'article', title: WINTER_BRIEF.title, description: 'A 90-second introduction to what an electricity load curve cannot tell you.', url: WINTER_BRIEF.url, images: [{ url: '/briefs/winter-load.png', width: 1600, height: 1200, alt: WINTER_BRIEF.title }] },
  twitter: { card: 'summary_large_image', title: WINTER_BRIEF.title, description: 'Observed load is not the demand that would exist without interruptions.', images: ['/briefs/winter-load.png'] },
};

export default function WinterLoadBrief() {
  const winter = historicalCases.find((example) => example.id === 'winter-2021')!;
  return <article className="mx-auto max-w-5xl space-y-8 pb-14">
    <header className="border-b border-black/20 pb-7">
      <span className="technical-label text-[#b73700]">Grid notes 01 / About 90 seconds to read</span>
      <h1 className="display-serif mt-5 text-[clamp(2.7rem,5.8vw,5.4rem)] leading-[0.98] tracking-[-0.045em]">Why can electricity use fall during a blackout?</h1>
      <p className="mt-5 max-w-3xl text-base leading-7 text-[#514e48]">A lower reading can mean less electricity was delivered—not that people needed less. That distinction changes what you can conclude about a grid.</p>
      <p className="mt-4 text-xs text-[#6d6b66]">GERT · Dresden Goehner · September 13, 2026 · Historical educational example</p>
    </header>
    <figure>
      <Image src="/briefs/winter-load.png" width={1600} height={1200} priority unoptimized alt="72 hourly ERCOT native-load observations, February 14–16, 2021, on a zero-to-80-GW scale. A dashed reference marks the reported onset of rotating outages at 01:25 CST on February 15. The curve falls but does not measure unmet demand or reliability." className="h-auto w-full border border-black/15" />
      <figcaption className="mt-3 text-xs leading-5 text-[#514e48]">Recorded load only. The vertical reference is an externally reported event time, not a measurement of lost load. <a href="#sources" className="underline">Sources and all 72 values below.</a> <a href="/briefs/winter-load.png" target="_blank" rel="noopener noreferrer" className="inline-block py-2 underline">Open full-size graphic ↗</a></figcaption>
    </figure>
    <section className="grid gap-6 sm:grid-cols-2">
      <div><span className="technical-label text-[#b73700]">01 / Read the boundary</span><h2 className="display-serif mt-3 text-3xl">A measurement is not the whole system.</h2><p className="mt-4 text-sm leading-6">ERCOT reported that rotating outages began at 01:25 a.m. on February 15, 2021, after generating units became unavailable. When customers are disconnected, some intended electricity use cannot appear in the recorded load. <a href={WINTER_BRIEF.contextUrl} className="underline">Read the contemporaneous report.</a></p></div>
      <div className="border-l-4 border-[#b73700] bg-[#f7f6f2] p-5 text-sm leading-6"><h3 className="font-semibold">What this curve cannot establish</h3><ul className="mt-3 list-disc space-y-2 pl-5"><li>Demand in the absence of interruptions.</li><li>The amount of electricity not supplied.</li><li>Whether reliability improved, or an intervention worked.</li></ul><p className="mt-3">We do not attribute every change to outages. Weather, behavior, and other system conditions also matter.</p></div>
    </section>
    <BriefActions />
    <section className="border-t border-black/20 pt-7"><h2 className="display-serif text-3xl">Now change an assumption.</h2><p className="mt-3 text-sm leading-6">Open the winter case with an explicitly assumed 60,000 MW capacity and no load reduction. The arithmetic gap is a counterfactual exercise—not historical outage losses. Try other assumptions and export the calculation.</p><Link href={WINTER_BRIEF.labPath} className="mt-5 inline-block bg-[#171717] px-5 py-3 text-sm font-semibold text-white">Explore the winter case →</Link><Link href="/review" className="ml-0 mt-4 block text-sm underline sm:ml-5 sm:inline-block">Leave a substantive review</Link></section>
    <section id="sources" className="space-y-4 border-t border-black/20 pt-7 text-sm leading-6"><h2 className="display-serif text-3xl">Sources, exact values, and reuse</h2>
      <ol className="list-decimal space-y-3 pl-5"><li><a href={WINTER_BRIEF.archiveUrl} className="underline">ERCOT Native Load 2021 archive</a> — the source of the 72 hourly observations. Interval starts, America/Chicago (CST here); MW in the data, GW on the chart.</li><li><a href={WINTER_BRIEF.contextUrl} className="underline">ERCOT news release, February 15, 2021</a> — the source of the rotating-outage start time. The release is contemporaneous, not a complete retrospective loss estimate.</li><li><a href="/briefs/winter-load-figure-data.json" className="underline">Exact plotted data and metadata</a> · <a href={`${REPO_URL}/blob/main/scripts/build_winter_brief.mjs`} className="underline">Figure generator</a> · <a href={WINTER_BRIEF.termsUrl} className="underline">ERCOT data-use terms, section 5</a>.</li></ol>
      <p className="text-xs text-[#514e48]">GERT is independent of ERCOT. No affiliation or endorsement is implied. The original graphic and explanation follow the repository MIT license; underlying data remains attributed to its source. Read the complete notice in the forwarding pack.</p>
      <details className="border border-black/20 p-4"><summary className="cursor-pointer font-semibold">Inspect all 72 hourly source values</summary><div className="mt-4 overflow-x-auto"><table className="w-full text-left text-xs"><caption className="mb-3 text-left">Hourly interval starts (CST), February 14–16, 2021</caption><thead><tr><th scope="col" className="p-2">Interval start</th><th scope="col" className="p-2">Recorded load (MW)</th></tr></thead><tbody>{winter.hours.map((hour) => <tr key={hour.timestamp} className="border-t border-black/10"><td className="whitespace-nowrap p-2 font-mono">{hour.timestamp}</td><td className="p-2">{hour.load_mw.toFixed(3)}</td></tr>)}</tbody></table></div></details>
    </section>
  </article>;
}
