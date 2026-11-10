import {
  ArrowUpRight,
  BadgeCheck,
  BookOpenCheck,
  Code2,
  GitFork,
  MessageSquareText,
  Scale,
} from 'lucide-react';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Open Research — GERT',
  description: 'Inspect GERT source, model evidence, limitations, reproduction pathways and public contribution channels.',
  alternates: { canonical: '/research' },
};

const repositoryUrl = 'https://github.com/DresdenGman/Grid-Extreme-Risk-Toolkit-GERT-';

const pathways = [
  {
    icon: BookOpenCheck,
    title: 'Audit the evidence',
    text: 'Review the frozen evaluation window, quantile coverage, pinball skill and the gates that kept the latest candidate out of production.',
    label: 'Open evidence',
    href: '/benchmark',
  },
  {
    icon: GitFork,
    title: 'Reproduce the work',
    text: 'Inspect the public architecture, tests, model contract and data-provenance boundaries. Clone the repository and rerun the documented checks.',
    label: 'View repository',
    href: repositoryUrl,
  },
  {
    icon: MessageSquareText,
    title: 'Challenge an assumption',
    text: 'Report a reproducibility problem, propose a calibration test or identify an operational edge case through a public issue.',
    label: 'Open an issue',
    href: `${repositoryUrl}/issues/new/choose`,
  },
];

export default function ResearchPage() {
  return (
    <div className="space-y-7 pb-12">
      <header className="reveal grid gap-8 border-b border-black/[0.09] pb-8 lg:grid-cols-[1.2fr_0.8fr] lg:items-end">
        <div>
          <span className="technical-label text-[#ff4d00]">Open project / Public verification</span>
          <h1 className="display-serif mt-4 max-w-4xl text-[clamp(2.8rem,6vw,6rem)] leading-[0.91] tracking-[-0.06em] text-[#141414]">
            Don&apos;t trust the badge.<br />Inspect the boundary.
          </h1>
        </div>
        <div className="max-w-lg">
          <p className="text-sm leading-6 text-[#4f4e4a]">
            GERT is designed as public, falsifiable research software. Its strongest claim is not that every candidate works—it is that evidence, limitations and promotion decisions stay inspectable.
          </p>
          <a
            href={repositoryUrl}
            target="_blank"
            rel="noreferrer"
            className="technical-label mt-5 inline-flex items-center gap-2 border border-[#141414] bg-[#141414] px-4 py-3 text-[#e4e3e0] shadow-[4px_4px_0_#ff4d00] transition hover:bg-[#ff4d00] hover:text-[#141414]"
          >
            <Code2 className="h-4 w-4" /> Inspect source <ArrowUpRight className="h-3.5 w-3.5" />
          </a>
        </div>
      </header>

      <section className="grid gap-5 lg:grid-cols-3">
        {pathways.map(({ icon: Icon, title, text, label, href }) => {
          const external = href.startsWith('http');
          return (
            <article key={title} className="hairline-panel flex min-h-72 flex-col rounded-[28px] p-6 sm:p-8">
              <Icon className="h-5 w-5 text-[#ff4d00]" />
              <h2 className="display-serif mt-8 text-2xl tracking-tight text-[#141414]">{title}</h2>
              <p className="mt-3 flex-1 text-sm leading-6 text-[#4f4e4a]">{text}</p>
              <a
                href={href}
                {...(external ? { target: '_blank', rel: 'noreferrer' } : {})}
                className="technical-label mt-8 inline-flex items-center gap-2 text-[#ff4d00] transition hover:text-[#141414]"
              >
                {label} <ArrowUpRight className="h-3.5 w-3.5" />
              </a>
            </article>
          );
        })}
      </section>

      <section className="grid gap-5 lg:grid-cols-12">
        <div className="border border-[#141414] bg-[#141414] p-6 text-[#f1f0ec] shadow-[7px_7px_0_#ff4d00] sm:p-8 lg:col-span-7">
          <div className="flex items-center gap-3">
            <BadgeCheck className="h-5 w-5 text-[#ff4d00]" />
            <span className="technical-label text-[#ff7a42]">Current authority state</span>
          </div>
          <h2 className="display-serif mt-6 text-3xl tracking-tight">The latest model candidate is not production-authorized.</h2>
          <p className="mt-4 max-w-3xl text-sm leading-6 text-[#d0cfca]">
            It showed positive pinball skill but missed predeclared calibration tolerances. Live operating context remains useful; probabilistic prediction stays gated until a frozen candidate passes every promotion requirement.
          </p>
        </div>

        <div className="border border-[#141414] bg-[#f3c64d] p-6 shadow-[7px_7px_0_#141414] sm:p-8 lg:col-span-5">
          <div className="flex items-center gap-3">
            <Scale className="h-5 w-5" />
            <span className="technical-label">Contribution standard</span>
          </div>
          <p className="display-serif mt-7 text-[clamp(2rem,4vw,3.5rem)] leading-[0.96] tracking-[-0.045em]">
            Useful criticism beats passive attention.
          </p>
          <p className="mt-5 text-sm leading-6 text-black/70">
            Reproducibility reports, calibration alternatives, operational edge cases and documented failures are the highest-value contributions to this project.
          </p>
        </div>
      </section>
    </div>
  );
}
