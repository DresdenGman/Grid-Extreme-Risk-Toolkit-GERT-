import type { Metadata } from 'next';
import Link from 'next/link';
import SameMeterChallenge from '@/components/SameMeterChallenge';
import { REPO_URL } from '@/lib/historical';

export const metadata: Metadata = {
  title: 'Same meter, two worlds | GERT',
  description: 'A five-minute interactive counterexample: identical electricity readings can hide different unmet demand. Inspect the assumptions and download the arithmetic.',
  alternates: { canonical: '/briefs/same-meter' },
};

export default function SameMeterPage() {
  return <article className="mx-auto max-w-5xl space-y-8 pb-14">
    <header className="border-b border-black/20 pb-7">
      <span className="technical-label text-[#a83400]">Grid notes / A five-minute counterexample</span>
      <h1 className="display-serif mt-5 text-[clamp(2.8rem,6vw,5.5rem)] leading-[0.98] tracking-[-0.045em]">Same meter.<br />Two worlds.</h1>
      <p className="mt-5 max-w-2xl text-base leading-7 text-[#514e48]">Can the same falling electricity readings mean two different things? Build a counterexample, then see why a real blackout curve needs careful interpretation.</p>
      <p className="mt-4 text-xs leading-5">No account required · Calculator optional · Invented teaching model, not historical data</p>
    </header>
    <SameMeterChallenge />
    <section className="border border-[#141414] bg-[#eee6cf] p-5 sm:p-8">
      <span className="technical-label">03 / Take the idea to real data</span>
      <h2 className="display-serif mt-3 text-3xl">The mathematical idea: non-identifiability.</h2>
      <p className="mt-4 text-sm leading-6">Different hidden inputs can produce the same observation. The mapping from demand and delivery ceiling to a meter reading is many-to-one, so the reading alone cannot recover both inputs. This example establishes that logical limitation; it does not establish which mechanism caused any real-world change.</p>
      <p className="mt-3 text-sm leading-6">Real grids also involve transmission, generation availability, reserves, behavior, and changing conditions. The toy model leaves those out. Its chosen demand values are not estimates of demand during the Texas storm.</p>
      <Link href="/briefs/winter-load" className="mt-5 inline-block bg-[#141414] px-5 py-3 text-sm font-semibold text-white">Inspect the actual winter-load curve →</Link>
    </section>
    <section aria-labelledby="host-heading" className="border-t border-black/20 pt-7">
      <h2 id="host-heading" className="display-serif text-3xl">Host it with one shared screen.</h2>
      <ol className="mt-4 list-decimal space-y-3 pl-5 text-sm leading-6">
        <li><strong>Minute 1:</strong> Show only the two readings. Ask what they do and do not establish.</li>
        <li><strong>Minutes 2–3:</strong> Change World B to 70 GW. Have someone compute its two-hour unserved energy. Ask why the meter still reads 45 GW in hour two.</li>
        <li><strong>Minutes 4–5:</strong> Try 45 GW. Ask why there is now no unserved energy in either world, then name one extra observation needed to distinguish the two worlds.</li>
      </ol>
      <details className="mt-5 border border-black/20 bg-[#f7f6f2] p-4"><summary className="cursor-pointer text-sm font-semibold">Facilitator answer and honest evidence record</summary><div className="mt-4 space-y-3 text-sm leading-6"><p>At 70 GW, World B has (70,000 − 45,000) MW × 1 hour = 25,000 MWh unserved in hour two, and zero in hour one. World A has zero in both hours. At 45 GW there is no unserved energy in either world.</p><p>A demand estimate independent of the delivered-load reading, together with information about supply and interruptions, could help distinguish explanations; those inputs bring their own uncertainty.</p><p>After a real activity, record the date, number present, number who attempted the calculation, and one concrete misconception or critique. Keep host confirmation privately. Attendance and attempted calculations overlap; do not add them as different users. This is a teaching aid, not a learning-effectiveness study or certificate.</p></div></details>
      <a href={`${REPO_URL}/blob/main/docs/WORKSHOP.md`} className="mt-5 inline-block text-sm font-semibold underline">Extend it with the existing 20-minute historical-data workshop</a>
    </section>
    <section className="border-t border-black/20 pt-7 text-sm leading-6">
      <h2 className="display-serif text-3xl">Found a confusing sentence or a broken assumption?</h2>
      <p className="mt-3">A specific counterexample or correction is more useful than a rating. Note your chosen demand, what you expected, and what happened. Downloading a model does not send feedback.</p>
      <div className="mt-4 flex flex-wrap gap-4"><Link href="/review" className="font-semibold underline">Choose how to inspect and share a review →</Link><a href={`${REPO_URL}/discussions/3`} target="_blank" rel="noreferrer" className="font-semibold underline">Leave one public field note →</a></div>
      <p className="mt-4 text-xs text-[#514e48]">The review page links to public GitHub issues, which require a GitHub account. Do not post student names, private class records, or personal contact information. Original GERT material uses the repository MIT license. No institutional endorsement is implied.</p>
    </section>
  </article>;
}
