import { ArrowUpRight, CheckCircle2, CircleDashed, MessageSquareText, ShieldCheck } from 'lucide-react';
import { REPO_URL } from '@/lib/historical';

const DISCUSSION_URL = `${REPO_URL}/discussions/3`;

const evidence = [
  { value: '4', label: 'organizer-forwarded reports', note: 'Stored privately with source and method limits.' },
  { value: '2', label: 'hands-on core completions', note: 'Self-reported: one desktop and one iPhone.' },
  { value: '1', label: 'script-assisted walkthrough', note: 'Tracked separately from hands-on use.' },
  { value: '2', label: 'feedback-linked changes', note: 'Included in this release and covered by automated checks.' },
  { value: '0', label: 'independent retests', note: 'A retest is counted only after someone tries the changed interaction.' },
];

const findings = [
  {
    id: 'GERT-UX-001',
    title: 'The fixed meter can make the slider look unresponsive.',
    evidence: 'Reported in two hands-on trials and one script-assisted walkthrough.',
    status: 'Change included in this release; independent retest pending.',
  },
  {
    id: 'GERT-UX-002',
    title: 'The automatic interpretation could reveal the conclusion too early.',
    evidence: 'Reported in one script-assisted walkthrough and confirmed in source inspection.',
    status: 'Change included in this release; independent retest pending.',
  },
];

export const metadata = {
  title: 'Community evidence | GERT',
  description: 'A public, evidence-bounded record of GERT trials, critiques, changes and retests.',
};

export default function CommunityPage() {
  return <div className="max-w-5xl space-y-8 pb-14">
    <header className="border-b border-black/20 pb-8">
      <span className="technical-label text-[#a83400]">Community evidence / Updated September 25, 2026</span>
      <h1 className="display-serif mt-4 text-[clamp(3rem,7vw,6rem)] leading-[0.95] tracking-[-0.05em]">Try it.<br />Leave a trace.</h1>
      <p className="mt-6 max-w-3xl text-base leading-7 text-[#514e48]">This ledger separates invitations, hands-on trials, scripted checks, product changes and retests. It is a record of what happened—not a wall of endorsements.</p>
      <div className="mt-6 flex flex-wrap gap-3">
        <a href={DISCUSSION_URL} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 bg-[#141414] px-5 py-3 text-sm font-semibold text-white">Add one public field note <ArrowUpRight size={16} /></a>
        <a href={`${REPO_URL}/issues/new?template=historical_review.yml`} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 border border-[#141414] px-5 py-3 text-sm font-semibold">Submit a structured review <ArrowUpRight size={16} /></a>
      </div>
      <p className="mt-4 max-w-3xl text-xs leading-5 text-[#6d6b66]">GitHub posts are public and require an account. Do not include names, contact details, class records, credentials, private data, or another person&apos;s words without permission.</p>
    </header>

    <section aria-labelledby="evidence-heading">
      <div className="flex items-end justify-between gap-4"><div><span className="technical-label text-[#175a73]">01 / Current evidence</span><h2 id="evidence-heading" className="display-serif mt-3 text-4xl">What is actually recorded.</h2></div><span className="hidden text-xs text-[#6d6b66] sm:block">Private source records · public aggregate</span></div>
      <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {evidence.map((item) => <article key={item.label} className="border border-[#141414] bg-[#f7f6f2] p-5 shadow-[4px_4px_0_#141414]"><p className="font-mono text-4xl">{item.value}</p><h3 className="mt-3 text-sm font-semibold">{item.label}</h3><p className="mt-2 text-xs leading-5 text-[#6d6b66]">{item.note}</p></article>)}
      </div>
      <p className="mt-5 text-sm leading-6">The organizer reports that 40 people are available to participate. Availability is not counted as an invitation, response or completed trial. These four reports do not establish adoption or learning effectiveness.</p>
    </section>

    <section className="border-t border-black/20 pt-8" aria-labelledby="findings-heading">
      <span className="technical-label text-[#a83400]">02 / Feedback to change</span>
      <h2 id="findings-heading" className="display-serif mt-3 text-4xl">Issues stay open until retested.</h2>
      <div className="mt-5 space-y-4">
        {findings.map((finding) => <article key={finding.id} className="grid gap-4 border border-black/25 bg-[#eee6cf] p-5 sm:grid-cols-[140px_1fr]"><div><span className="font-mono text-sm font-semibold">{finding.id}</span><div className="mt-3 inline-flex items-center gap-2 text-xs text-[#8a4b00]"><CircleDashed size={14} /> Pending retest</div></div><div><h3 className="text-lg font-semibold">{finding.title}</h3><p className="mt-2 text-sm leading-6">{finding.evidence}</p><p className="mt-2 text-xs leading-5 text-[#6d6b66]">{finding.status}</p></div></article>)}
      </div>
    </section>

    <section className="grid gap-5 border-t border-black/20 pt-8 md:grid-cols-2">
      <article className="border border-[#175a73] bg-[#dfe8ea] p-6"><MessageSquareText size={24} /><h2 className="display-serif mt-4 text-3xl">What makes a useful note?</h2><p className="mt-3 text-sm leading-6">Name the page you tried, what you expected, what happened, and whether you operated it by hand or used a script. One precise criticism is more useful than a general compliment.</p></article>
      <article className="border border-[#2f6b4f] bg-[#e0e7df] p-6"><ShieldCheck size={24} /><h2 className="display-serif mt-4 text-3xl">What becomes public?</h2><p className="mt-3 text-sm leading-6">Only comments people publish themselves, or quotations they explicitly permit GERT to publish. Private replies remain private; this page may report de-identified totals and issue summaries.</p></article>
    </section>

    <section className="border-t border-black/20 pt-7 text-sm leading-6"><div className="flex items-center gap-2 font-semibold"><CheckCircle2 size={17} /> Counting rule</div><p className="mt-2 max-w-3xl">A public comment is feedback, not automatically a completed trial. A fix is counted only after the code changes and passes checks. A retest is counted only after someone tries the changed interaction and reports the result.</p></section>
  </div>;
}
