import { readFileSync } from 'fs';
import path from 'path';
import type { Citation } from './types';

function read(relativePath: string) {
  return readFileSync(path.join(process.cwd(), relativePath), 'utf8');
}

function field(source: string, key: string) {
  const match = source.match(new RegExp(`(?:^|\\n)\\s*(?:-\\s*)?${key}:\\s*"?([^"\\n]+)"?`));
  if (!match) throw new Error(`CITATION.cff is missing ${key}`);
  return match[1].trim();
}

export function loadCitation(): Citation {
  const cff = read('CITATION.cff');
  const changelog = read('CHANGELOG.md');
  const readme = read('README.md');
  const conceptDoi = field(cff, 'doi');
  const versionMatch = changelog.match(/version DOI\s+(10\.5281\/zenodo\.\d+)/);
  if (!versionMatch) throw new Error('CHANGELOG.md does not name a Zenodo version DOI');
  const conceptMention = changelog.match(/concept DOI\s+(10\.5281\/zenodo\.\d+)/);
  if (conceptMention && conceptMention[1] !== conceptDoi) {
    throw new Error('CHANGELOG concept DOI does not match CITATION.cff');
  }
  const dataset = readme.match(
    /\[!\[Dataset DOI\]\(https:\/\/zenodo\.org\/badge\/DOI\/(10\.5281\/zenodo\.\d+)\.svg\)\]/,
  );
  if (!dataset) throw new Error('README.md does not name a dataset DOI');
  const released = field(cff, 'date-released');
  const year = released.slice(0, 4);
  if (!/^\d{4}$/.test(year)) throw new Error('CITATION.cff date-released has no year');
  const given = field(cff, 'given-names');
  return {
    author: `${field(cff, 'family-names')}, ${given.charAt(0)}.`,
    year,
    title: field(cff, 'title'),
    version: field(cff, 'version'),
    softwareDoi: versionMatch[1],
    conceptDoi,
    datasetDoi: dataset[1],
    repository: field(cff, 'repository-code').replace(/\/$/, ''),
  };
}
