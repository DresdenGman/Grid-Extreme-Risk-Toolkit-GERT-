import { readFileSync } from 'fs';
import path from 'path';
import { loadCitation } from '@/lib/homepage/citation';

export const metadata = {
  title: 'Version — GERT',
  description: 'Software version, changelog, and the citation DOIs already recorded for GERT.',
};

export default function ChangelogPage() {
  const citation = loadCitation();
  const changelog = readFileSync(path.join(process.cwd(), 'CHANGELOG.md'), 'utf8');
  return (
    <article>
      <header>
        <p className="journal-kicker">Version {citation.version}</p>
        <h1 className="mt-3 text-[clamp(2.4rem,5vw,4.2rem)] leading-[1.02]">{citation.title}</h1>
        <p className="journal-lede">
          {citation.author} ({citation.year}). The changelog below is the file in the repository. The DOIs are the ones already recorded there.
        </p>
      </header>
      <p className="journal-note font-mono text-xs leading-6">
        Software DOI {citation.softwareDoi}
        <br />
        Concept DOI {citation.conceptDoi}
        <br />
        Dataset DOI {citation.datasetDoi}
      </p>
      <pre className="mt-8 whitespace-pre-wrap border-t border-[var(--ink)] pt-6 font-serif text-sm leading-6">{changelog}</pre>
    </article>
  );
}
