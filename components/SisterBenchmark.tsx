import { ArrowUpRight } from 'lucide-react';
import { doiUrl, PJM_BENCHMARK } from '@/lib/citations';

export function SisterBenchmark() {
  return (
    <section className="border border-[#141414] bg-[#f7f6f2] p-6 shadow-[7px_7px_0_#141414] sm:p-8">
      <span className="technical-label text-[#175a73]">Sister benchmark</span>
      <h2 className="display-serif mt-3 text-3xl tracking-tight text-[#141414]">{PJM_BENCHMARK.name}</h2>
      <p className="mt-4 max-w-3xl text-sm leading-6 text-[#4f4e4a]">
        Day-ahead quantile gradient boosting, 90% intervals: {PJM_BENCHMARK.coldCoverage} coverage of {PJM_BENCHMARK.coldWindow}, against {PJM_BENCHMARK.fullPeriodCoverage} over {PJM_BENCHMARK.comparisonWindow}. {PJM_BENCHMARK.repair}.
      </p>
      <p className="mt-3 max-w-3xl text-xs leading-5 text-[#6d6b66]">
        Those two coverage figures and the 0-of-18 repair result are the benchmark README&apos;s headline findings J1 and J2. The archive is Zenodo {PJM_BENCHMARK.version}, published {PJM_BENCHMARK.published}. The 12.5% figure is the January 2014 polar-vortex window.
      </p>
      <div className="mt-5 flex flex-wrap gap-4 text-sm font-semibold">
        <a className="inline-flex items-center gap-1 underline" href={doiUrl(PJM_BENCHMARK.doi)}>
          DOI {PJM_BENCHMARK.doi} <ArrowUpRight className="h-3.5 w-3.5" />
        </a>
        <a className="inline-flex items-center gap-1 underline" href={PJM_BENCHMARK.repoUrl}>
          Repository <ArrowUpRight className="h-3.5 w-3.5" />
        </a>
      </div>
    </section>
  );
}
