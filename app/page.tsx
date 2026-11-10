import type { Metadata } from 'next';
import { Poster } from '@/components/home/Poster';
import { homeFonts, plexMono, plexSans, sourceSerif } from '@/components/home/fonts';
import { buildCopy } from '@/lib/homepage/copy';
import { loadCitation } from '@/lib/homepage/citation';
import { loadEvidence } from '@/lib/homepage/evidence';
import { buildFigure } from '@/lib/homepage/figure';

const evidence = loadEvidence();
const citation = loadCitation();
const copy = buildCopy(evidence, citation);
const figure = buildFigure(evidence);

export function generateMetadata(): Metadata {
  return {
    title: 'GERT — Grid Extreme Risk Toolkit',
    description: copy.description,
    openGraph: {
      title: 'GERT — Grid Extreme Risk Toolkit',
      description: copy.description,
    },
  };
}

export default function HomePage() {
  return (
    <Poster
      copy={copy}
      figure={figure}
      citation={citation}
      fonts={homeFonts}
      fontClassName={`${plexSans.variable} ${plexMono.variable} ${sourceSerif.variable}`}
    />
  );
}
