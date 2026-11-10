import Link from 'next/link';
import { plexMono, plexSans, sourceSerif } from '@/components/home/fonts';
import { ToolsMenu } from '@/components/home/ToolsMenu';

export function JournalFrame({ children }: { children: React.ReactNode }) {
  return (
    <div className={`journal ${plexSans.variable} ${plexMono.variable} ${sourceSerif.variable}`}>
      <header className="journal-bar">
        <Link href="/" className="journal-mark">GERT</Link>
        <nav className="journal-nav" aria-label="Primary">
          <Link href="/#decision">Decision</Link>
          <Link href="/#evidence">Evidence</Link>
          <Link href="/history">Data</Link>
          <ToolsMenu tone="ink" indexHref="/#tools" />
        </nav>
      </header>
      <div className="journal-main">{children}</div>
    </div>
  );
}
