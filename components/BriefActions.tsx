'use client';

import { useState } from 'react';
import { BRIEF_QUESTIONS, WINTER_BRIEF, exerciseReceipt } from '@/lib/briefs';

function downloadReceipt(record: ReturnType<typeof exerciseReceipt>) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' }));
  const link = document.createElement('a');
  link.href = url; link.download = 'gert-winter-load-self-check.json'; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function BriefActions() {
  const [answers, setAnswers] = useState([-1, -1]);
  const [receipt, setReceipt] = useState<ReturnType<typeof exerciseReceipt> | null>(null);
  const [notice, setNotice] = useState('');
  async function copy(content: string, label: string) {
    try { await navigator.clipboard.writeText(content); setNotice(`${label} copied.`); }
    catch { setNotice('Clipboard unavailable. Select the text in the forwarding box below.'); }
  }
  return <>
    <section id="self-check" className="border border-black/20 bg-[#f7f6f2] p-5 sm:p-8">
      <span className="technical-label text-[#b73700]">02 / Check your interpretation</span>
      <h2 className="display-serif mt-3 text-3xl">Two questions. No sign-up.</h2>
      <p className="mt-3 text-sm leading-6 text-[#514e48]">Choose your answers, then reveal the explanation. Your first answers stay in the downloadable record. Nothing is sent to GERT.</p>
      <form onSubmit={(event) => { event.preventDefault(); setReceipt(exerciseReceipt(answers, new Date().toISOString())); }}>
        {BRIEF_QUESTIONS.map((question, i) => <fieldset key={question.id} disabled={receipt !== null} className="mt-7 space-y-3">
          <legend className="mb-3 text-sm font-semibold leading-6">{i + 1}. {question.prompt}</legend>
          {question.options.map((option, j) => <label key={option} className={`flex cursor-pointer items-start gap-3 border p-3 text-sm leading-6 ${answers[i] === j ? 'border-[#171717] bg-[#ebe3cf]' : 'border-black/15 bg-white'}`}>
            <input type="radio" name={question.id} value={j} checked={answers[i] === j} onChange={() => setAnswers((current) => current.map((answer, index) => index === i ? j : answer))} className="mt-1.5 shrink-0 accent-[#b73700]" />{option}
          </label>)}
          {receipt && <p className="border-l-2 border-[#171717] pl-4 text-sm leading-6">{receipt.responses[i].correct ? 'Correct. ' : 'Explanation: '}{question.explanation}</p>}
        </fieldset>)}
        {!receipt && <button disabled={answers.some((answer) => answer < 0)} className="mt-6 bg-[#171717] px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40">Check my answers</button>}
      </form>
      {receipt && <div className="mt-6 border-t border-black/20 pt-5" aria-live="polite">
        <p className="font-semibold">{receipt.correct_answers} of {receipt.total_questions} initial answers correct.</p>
        <button onClick={() => downloadReceipt(receipt)} className="mt-4 border border-[#171717] px-5 py-3 text-sm font-semibold">Download my exercise record</button>
        <p className="mt-3 text-xs leading-5 text-[#514e48]">Optional, self-reported record—not a certificate or independent verification. Share it only if you choose; it contains no name or email.</p>
      </div>}
    </section>
    <section id="share" className="border border-[#171717] bg-[#ebe3cf] p-5 sm:p-8">
      <span className="technical-label">03 / Pass the question on</span>
      <h2 className="display-serif mt-3 text-3xl">One link. One ready-to-use graphic.</h2>
      <p className="mt-3 text-sm leading-6">For a class, a club message, or a reading list. Preserve the source credit and limitations when sharing.</p>
      <div className="mt-5 flex flex-wrap gap-3">
        <button onClick={() => copy(WINTER_BRIEF.url, 'Exercise link')} className="border border-[#171717] bg-white px-4 py-3 text-sm font-semibold">Copy exercise link</button>
        <button onClick={() => copy(WINTER_BRIEF.blurb, 'Forwarding text')} className="border border-[#171717] bg-white px-4 py-3 text-sm font-semibold">Copy forwarding text</button>
        <a href="/briefs/winter-load.png" download className="bg-[#171717] px-4 py-3 text-sm font-semibold text-white">Download PNG</a>
        <a href="/briefs/winter-load.svg" download className="border border-[#171717] px-4 py-3 text-sm font-semibold">Download SVG</a>
      </div>
      <p role="status" className="mt-3 min-h-5 text-xs">{notice}</p>
      <details className="mt-2"><summary className="cursor-pointer text-sm font-semibold">Forwarding text and reuse notes</summary>
        <textarea readOnly aria-label="Forwarding text" value={WINTER_BRIEF.blurb} rows={9} className="mt-4 w-full resize-y border border-black/25 bg-white p-4 text-sm leading-6" />
        <p className="mt-3 text-xs leading-5">Original GERT material follows the repository MIT license; public raw data follows ERCOT&apos;s terms. Do not imply ERCOT or another organization endorses GERT. <a className="underline" href="/briefs/winter-load-pack.txt">Download the complete forwarding pack and license notice.</a></p>
      </details>
    </section>
  </>;
}
