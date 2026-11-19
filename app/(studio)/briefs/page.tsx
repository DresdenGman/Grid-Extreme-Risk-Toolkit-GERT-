import type { Metadata } from 'next';
import Link from 'next/link';
import { PRODUCT_NAME } from '@/lib/citations';

export const metadata: Metadata = {
  title: `Grid Notes | ${PRODUCT_NAME}`,
  description: 'Short teaching notes on recorded ERCOT load and a same-meter counterexample.',
  alternates: { canonical: '/briefs' },
};

const notes = [
  {
    href: '/briefs/winter-load',
    kicker: 'Grid notes 01',
    title: 'Why can electricity use fall during a blackout?',
    text: 'A source-linked reading of 72 ERCOT native-load hours from February 14–16, 2021. Recorded load is not unmet demand.',
  },
  {
    href: '/briefs/same-meter',
    kicker: 'Five-minute counterexample',
    title: 'Same meter. Two worlds.',
    text: 'An invented teaching model: identical electricity readings can hide different unmet demand. It is not a historical measurement.',
  },
];

export default function BriefsIndex() {
  return (
    <div className="mx-auto max-w-5xl space-y-8 pb-14">
      <header className="border-b border-black/20 pb-7">
        <span className="technical-label text-[#b73700]">Grid notes</span>
        <h1 className="display-serif mt-4 text-[clamp(2.6rem,6vw,4.5rem)] leading-[0.95] tracking-[-0.04em]">Two short readings.</h1>
        <p className="mt-4 max-w-2xl text-sm leading-6 text-[#514e48]">These notes sit beside the Historical Lab. They do not add a forecast, and they do not count a reader as a participant.</p>
      </header>
      <ul className="space-y-4">
        {notes.map((note) => (
          <li key={note.href} className="border border-[#141414] bg-[#f7f6f2] p-6 shadow-[4px_4px_0_#141414]">
            <span className="technical-label text-[#6d6b66]">{note.kicker}</span>
            <h2 className="display-serif mt-3 text-3xl tracking-tight">
              <Link href={note.href} className="underline decoration-transparent underline-offset-4 hover:decoration-[#141414]">{note.title}</Link>
            </h2>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-[#514e48]">{note.text}</p>
            <Link href={note.href} className="mt-4 inline-block text-sm font-semibold underline">Open this note</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
