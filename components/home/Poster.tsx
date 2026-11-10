import Link from 'next/link';
import type { HomepageCopy, Span } from '@/lib/homepage/copy';
import type { FigureView } from '@/lib/homepage/figure';
import type { Citation } from '@/lib/homepage/types';
import { CoverageFigure } from './CoverageFigure';
import { AsOf, Facts, HeroFoot, OperationalProvider } from './Operational';
import { ToolIndex } from './ToolIndex';
import { ToolsMenu } from './ToolsMenu';
import styles from './home.module.css';

function Spans({ spans }: { spans: Span[] }) {
  return spans.map((span, index) =>
    span.kind === 'text' ? (
      <span key={index}>{span.text}</span>
    ) : (
      <sup key={index}>{span.note}</sup>
    ),
  );
}

function Footnotes({ copy }: { copy: HomepageCopy }) {
  return (
    <div className={styles.notes}>
      {copy.footnotes.map((note) => (
        <p key={note.n}>
          <sup>{note.n}</sup> {note.lead}
          {note.linked && note.href ? (
            <a href={note.href} target="_blank" rel="noreferrer">
              {note.linked}
            </a>
          ) : (
            note.linked
          )}
          {note.tail}
        </p>
      ))}
    </div>
  );
}

export function Poster({
  copy,
  figure,
  citation,
  fonts,
  fontClassName = '',
}: {
  copy: HomepageCopy;
  figure: FigureView;
  citation: Citation;
  fonts: { sans: string; serif: string; mono: string };
  fontClassName?: string;
}) {
  return (
    <OperationalProvider>
      <div className={`${styles.home} ${fontClassName}`.trim()}>
        <header className={styles.hero} id="decision">
          <div className={styles.heroTop}>
            <div className={styles.kicker}>Grid Extreme Risk Toolkit</div>
            <nav className={styles.nav} aria-label="Primary">
              <a href="#decision" aria-current="page">
                Decision
              </a>
              <a href="#evidence">Evidence</a>
              <Link href="/history">Data</Link>
              <ToolsMenu />
            </nav>
            <AsOf />
          </div>

          <h1 className={styles.wordmark}>GERT</h1>
          <p className={styles.subhead}>{copy.subhead}</p>
          <div className={styles.rule} />

          <div className={styles.heroLower}>
            <div>
              <div className={styles.gateBlock}>
                <div className={styles.gateLabel}>The gate</div>
                <div className={styles.gateNum}>{copy.gateValue}</div>
              </div>
              <p className={styles.gateNote}>{copy.gateNote}</p>
            </div>
            <div className={styles.statements}>
              {copy.verdicts.map((verdict) => (
                <div className={styles.row} key={verdict.label}>
                  <div className={styles.rowLabel}>{verdict.label}</div>
                  <p className={styles.verdict}>{verdict.value}</p>
                </div>
              ))}
              <p className={styles.aside}>{copy.aside}</p>
            </div>
          </div>

          <HeroFoot closer={copy.closer} />
        </header>

        <main className={styles.evidence} id="evidence">
          <h2 className={styles.evidenceTitle}>Observed coverage, and the {copy.gateValue} gate.</h2>
          <div className={styles.dek}>
            <p className={styles.dekCopy}>
              <Spans spans={copy.dek} />
            </p>
            <Facts />
          </div>

          <figure className={styles.figure}>
            <CoverageFigure figure={figure} title={copy.figureTitle} description={copy.figureDesc} fonts={fonts} />
            <figcaption className={styles.caption} id="fig1-caption">
              <span className={styles.tag}>Fig. 1</span>
              <Spans spans={copy.caption} />
            </figcaption>
          </figure>

          <section className={styles.ledger} aria-label="Model ledger">
            {copy.ledger.map((column) => (
              <article key={column.label}>
                <div className={styles.sectionLabel}>{column.label}</div>
                <h3 className={column.tone === 'rejected' ? styles.rejected : column.tone === 'provisional' ? styles.provisional : undefined}>{column.title}</h3>
                <p>{column.body}</p>
              </article>
            ))}
          </section>

          <footer className={styles.footer}>
            <Footnotes copy={copy} />
            <div className={styles.doi}>
              <p className={styles.doiTitle}>
                {citation.author} ({citation.year}). {citation.title} (Version {citation.version}).
              </p>
              <p>
                Software DOI{' '}
                <a href={`https://doi.org/${citation.softwareDoi}`}>{citation.softwareDoi}</a>
              </p>
              <p>
                Dataset DOI{' '}
                <a href={`https://doi.org/${citation.datasetDoi}`}>{citation.datasetDoi}</a>
              </p>
            </div>
            <p className={styles.end}>{copy.closer}</p>
          </footer>
          <ToolIndex />
        </main>
      </div>
    </OperationalProvider>
  );
}
