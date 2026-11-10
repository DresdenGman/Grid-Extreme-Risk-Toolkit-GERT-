import Link from 'next/link';
import v14 from '@/evidence/ercot_v1_4_validation.json';
import v15 from '@/evidence/snapshots/pr-23/ercot_v1_5_validation.json';

export const metadata = {
  title: 'Methods — GERT',
  description: 'Gates, published Wilson intervals, data sources, and the exclusion rule for the GERT evidence files.',
};

export default function MethodsPage() {
  const calibration = v14.gates.filter((gate) => /calibration error/i.test(gate.gate));
  return (
    <article className="space-y-10">
      <header>
        <p className="journal-kicker">Methods</p>
        <h1 className="mt-3 text-[clamp(2.4rem,5vw,4.2rem)] leading-[1.02]">How a number gets onto this site.</h1>
        <p className="journal-lede">
          Gates, intervals, sources, and exclusions below are copied from the evidence files and the v1.5 preregistration. This page does not recompute a new interval or a new gate.
        </p>
      </header>

      <section>
        <h2 className="text-3xl">Gates and thresholds</h2>
        <p className="journal-note">
          v1.4 ({v14.candidate_id}) is {v14.validation_status.replaceAll('_', ' ')}. The calibration gates in its evidence file use one requirement: absolute coverage error ≤ 0.03. Q90, Q95, and Q99 failed. The candidate is not authorized for production inference.
        </p>
        <ul className="mt-4 space-y-2 text-sm">
          {calibration.map((gate) => (
            <li key={gate.gate} className="border-b border-[var(--hairline)] pb-2">
              <span className="font-medium">{gate.gate}.</span> {gate.requirement}. Observed {gate.observed}. {gate.passed ? 'Passed' : 'Failed'}.
            </li>
          ))}
        </ul>
        <p className="journal-note">
          v1.5 ({v15.candidate_id}) records {v15.validation_status.replaceAll('_', ' ')}. Its evidence file says every listed gate passed. It is not in production. PR #23 is unmerged. Commit of the evidence snapshot: 98d4fbf.
        </p>
      </section>

      <section>
        <h2 className="text-3xl">Wilson intervals, and what is not published</h2>
        <p className="journal-note">
          The v1.5 file stores a Wilson 95% interval on empirical coverage at each quantile, under the field coverage_wilson_95_ci. Fig. 1 plots those published endpoints after subtracting the nominal level. The file says the gate still uses the point estimate. v1.4’s file has no interval, so Fig. 1 shows v1.4 as a point.
        </p>
        <p className="journal-note">
          A Clopper-Pearson interval is the exact central binomial interval. It is not in either evidence file, so this site does not print Clopper-Pearson bounds.
        </p>
      </section>

      <section>
        <h2 className="text-3xl">Data sources</h2>
        <p className="journal-note">{v14.data_provenance}</p>
        <p className="journal-note">{v15.data_provenance}</p>
        <p className="journal-note">
          v1.5 limitations: {v15.limitations[0]} The preregistration commit 2fcf2c9b is dated 2026-11-05 03:11 PT, after the evaluation window closed on 2026-11-01, so that freeze is retrospective relative to the window. v1.5’s seasonal baseline is fit only on timestamps before 2025-01-01. The v1.4 evidence file does not record its baseline training window, so the v1.5 skill (0.93) and the v1.4 skills (0.76–0.84) are not the same comparison and are not directly comparable.
        </p>
      </section>

      <section>
        <h2 className="text-3xl">Exclusion, not imputation</h2>
        <p className="journal-note">
          The v1.5 preregistration says the pipeline rejects gaps rather than imputing them. The v1.5 evidence file says six load hours on 2026-11-03 were unmatched by ERA5 and excluded by the inner join. They lie outside the frozen windows. Missing hours are left out and named. They are not filled in.
        </p>
      </section>

      <section>
        <h2 className="text-3xl">Regenerate Fig. 1</h2>
        <p className="journal-note">
          One command reads the two evidence JSON files and prints the signed coverage errors and Wilson endpoints that Fig. 1 plots:
        </p>
        <pre className="mt-4 overflow-x-auto border border-[var(--hairline)] bg-[var(--paper-figure)] p-4 font-mono text-sm">node scripts/fig1.mjs</pre>
        <p className="journal-note">
          <Link href="/changelog" className="underline">Version and changelog</Link>
          {' · '}
          <Link href="/#evidence" className="underline">Fig. 1</Link>
        </p>
      </section>
    </article>
  );
}
