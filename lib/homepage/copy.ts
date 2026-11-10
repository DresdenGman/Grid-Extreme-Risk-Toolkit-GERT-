import { formatPlain, joinAnd } from './format';
import type { CandidateView, Citation, EvidenceModel, Verdict } from './types';

export type Span = { kind: 'text'; text: string } | { kind: 'note'; note: number };

export interface Footnote {
  n: number;
  lead: string;
  linked: string | null;
  href: string | null;
  tail: string;
}

export interface LedgerColumn {
  label: string;
  title: string;
  tone: Verdict['tone'] | 'plain';
  body: string;
}

export interface HomepageCopy {
  description: string;
  subhead: string;
  gateValue: string;
  gateNote: string;
  verdicts: { label: string; value: string }[];
  aside: string;
  dek: Span[];
  caption: Span[];
  figureTitle: string;
  figureDesc: string;
  ledger: LedgerColumn[];
  footnotes: Footnote[];
  closer: string;
}

export function verdictFor(status: string): Verdict {
  if (status === 'rejected_candidate') return { title: 'Rejected', tone: 'rejected' };
  if (status === 'provisional_candidate') return { title: 'Provisional', tone: 'provisional' };
  return { title: status, tone: 'plain' };
}

function fileHref(citation: Citation, ref: string, commit: string) {
  return `${citation.repository}/blob/${commit}/${ref}`;
}

function footnoteFor(candidate: CandidateView, citation: Citation, n: number): Footnote {
  if (candidate.source.kind === 'main') {
    return {
      n,
      lead: '',
      linked: candidate.source.path,
      href: fileHref(citation, candidate.source.path, 'main'),
      tail: `, candidate ${candidate.candidateId}, published ${candidate.publishedLabel}. Validation status: ${candidate.status}.${
        candidate.source.path.endsWith('ercot_v1_4_validation.json') ? ' Commit 4cb93a8e.' : ''
      }`,
    };
  }
  const short = candidate.source.commit.slice(0, 7);
  return {
    n,
    lead: 'Snapshot of ',
    linked: candidate.source.upstreamPath,
    href: fileHref(citation, candidate.source.upstreamPath, candidate.source.commit),
      tail: ` at commit ${short} on unmerged PR #${candidate.source.pr} (${candidate.source.branch}), candidate ${candidate.candidateId}, published ${candidate.publishedLabel}. Validation status: ${candidate.status}. Preregistration commit 2fcf2c9b is dated 2026-11-05 03:11 PT, after the evaluation window closed on 2026-11-01, so that freeze is retrospective relative to the window. Training timestamps recorded in the file are before 2025-01-01.`,
  };
}

function v14Ledger(model: EvidenceModel) {
  const { v14, gateLabel } = model;
  const failed = v14.points.filter((point) => point.pastGate);
  const passed = v14.points.filter((point) => !point.pastGate);
  const listed = failed.length ? failed : v14.points;
  let body = `Coverage error ${listed.map((point) => point.label).join(' / ')}: ${listed
    .map((point) => formatPlain(point.absoluteError))
    .join(' / ')}, against a gate of ≤ ${gateLabel}.`;
  if (failed.length && passed.length) {
    body += ` ${passed.map((point) => point.label).join(' / ')} held at ${passed
      .map((point) => formatPlain(point.absoluteError))
      .join(' / ')}.`;
  }
  body += ` Empirical coverage ${v14.points.map((point) => formatPlain(point.empirical)).join(' / ')}. Crossings ${formatPlain(v14.crossings)}.`;
  return body;
}

function v15Ledger(candidate: CandidateView) {
  let body = `Coverage error ${candidate.points
    .map((point) => formatPlain(point.absoluteError))
    .join(' / ')} on ${candidate.observations} hours.`;
  if (candidate.source.kind === 'pr23-snapshot') body += ` PR #${candidate.source.pr} unmerged.`;
  if (candidate.realizedEra5) body += ' Realized ERA5 weather.';
  if (candidate.status !== 'validated_production') body += ' Not in production.';
  return body;
}

function v15Dek(candidate: CandidateView | null) {
  if (!candidate) {
    return 'v1.5 evidence is not on main and no snapshot is available, so no v1.5 result is shown.';
  }
  const pr =
    candidate.source.kind === 'pr23-snapshot'
      ? `PR #${candidate.source.pr} is unmerged and not in production`
      : 'it is recorded on main and not in production';
  if (candidate.allGatesPassed && candidate.status === 'provisional_candidate') {
    return `${candidate.version} passed the gates recorded in its evidence JSON and remains provisional: ${pr}.`;
  }
  if (candidate.status === 'provisional_candidate') {
    return `${candidate.version} remains provisional and is not in production.`;
  }
  if (candidate.status === 'validated_production') {
    return `${candidate.version} is recorded as validated_production.`;
  }
  return `${candidate.version} validation status is ${candidate.status}.`;
}

function eraSentence(model: EvidenceModel) {
  const v15 = model.v15;
  if (!v15?.realizedEra5 || !v15.sameWeatherAsV14 || !model.v14.mentionsEra5) return '';
  if (v15.optimisticRealizedWeather) {
    return ' Both evaluations used realized ERA5 weather — an upper bound, not a production weather forecast.';
  }
  return ' Both evaluations used realized ERA5 weather, not a production weather forecast.';
}

function aside(candidate: CandidateView | null) {
  if (!candidate) return 'Evidence is not on main. No v1.5 numbers are shown.';
  const parts: string[] = [];
  if (candidate.source.kind === 'pr23-snapshot') parts.push(`PR #${candidate.source.pr}, unmerged.`);
  else parts.push('Recorded on main.');
  if (candidate.realizedEra5 && candidate.status !== 'validated_production') {
    parts.push('Realized ERA5, not in production.');
  } else if (candidate.realizedEra5) {
    parts.push('Realized ERA5 weather.');
  } else if (candidate.status !== 'validated_production') {
    parts.push('Not in production.');
  }
  return parts.join(' ');
}

export function buildCopy(model: EvidenceModel, citation: Citation): HomepageCopy {
  const v14Verdict = verdictFor(model.v14.status);
  const v15Verdict = model.v15 ? verdictFor(model.v15.status) : { title: 'Pending', tone: 'plain' as const };
  const auth = /not authorized for production inference/i.test(model.v14.summary) || model.v14.status === 'rejected_candidate'
    ? 'The candidate is not authorized for production inference.'
    : '';
  const missed = model.v14.failedLabels.length
    ? `${joinAnd(model.v14.failedLabels)} missed it.`
    : 'No reported quantile missed it.';
  const quantileList = joinAnd(model.v14.points.map((point) => point.label));
  const outside = model.v15?.points.filter((point) => point.intervalPastGate).map((point) => point.label) ?? [];
  const v15Caption = model.v15
    ? `${model.v15.version} (n = ${model.v15.observations}; ${model.v15.windowLabel}) ${
        model.v15.wilsonComplete
          ? `shows the published Wilson 95% interval${
              model.v15.gateUsesPointEstimate ? '; the gate still uses the point estimate' : ''
            }${outside.length ? `, and at ${joinAnd(outside)} that interval extends outside the band` : ''}`
          : 'has no complete Wilson interval in its evidence JSON'
      }.`
    : 'v1.5 is not shown.';
  const skill = model.windowsDiffer
    ? ' v1.5’s seasonal baseline is fit only on timestamps before 2025-01-01. The v1.4 evidence file does not record its baseline training window, so the v1.5 skill (0.93) and the v1.4 skills (0.76–0.84) are not the same comparison and are not directly comparable.'
    : '';
  const caption: Span[] = [
    {
      kind: 'text',
      text: `Signed coverage error (empirical coverage minus the nominal level) at ${quantileList}. The shaded band is the preregistered gate of absolute error ≤ ${model.gateLabel}; the heavy line is perfect calibration. ${model.v14.version} (n = ${model.v14.observations}; ${model.v14.windowLabel}) is a point estimate — a Wilson interval was not published in the v1.4 evidence JSON.`,
    },
    { kind: 'note', note: 1 },
    { kind: 'text', text: ` ${v15Caption}` },
    { kind: 'note', note: 2 },
    { kind: 'text', text: skill },
  ];
  const figureDesc = caption.map((span) => (span.kind === 'text' ? span.text : '')).join('');

  return {
    description: model.productionValidated
      ? 'A validated production model is on record.'
      : `No validated production model. ${model.v14.version} is ${v14Verdict.title.toLowerCase()}. ${
          model.v15
            ? `${model.v15.version} is ${v15Verdict.title.toLowerCase()} and not in production.`
            : 'v1.5 evidence is not shown.'
        }`,
    subhead: model.productionValidated ? 'A validated production model is on record.' : 'No validated production model.',
    gateValue: model.gateLabel,
    gateNote: [missed, auth].filter(Boolean).join(' '),
    verdicts: [
      { label: 'Production', value: model.productionValidated ? 'Validated.' : 'None.' },
      { label: model.v14.version, value: `${v14Verdict.title}.` },
      { label: model.v15?.version ?? 'v1.5', value: model.v15 ? `${v15Verdict.title}.` : 'Pending.' },
    ],
    aside: aside(model.v15),
    dek: [
      {
        kind: 'text',
        text: `The plate below is the evidence, not a forecast. ${model.v14.version} was ${v14Verdict.title.toLowerCase()} after ${joinAnd(model.v14.failedLabels)} missed a preregistered calibration gate of absolute error ≤ ${model.gateLabel}.`,
      },
      { kind: 'note', note: 1 },
      { kind: 'text', text: ` ${v15Dek(model.v15)}` },
      { kind: 'note', note: 2 },
      { kind: 'text', text: eraSentence(model) },
    ],
    caption,
    figureTitle: `Signed coverage error at four quantiles, with the ±${model.gateLabel} gate`,
    figureDesc,
    ledger: [
      {
        label: 'Production',
        title: model.productionValidated ? 'Validated' : 'None',
        tone: 'plain',
        body: model.productionValidated
          ? 'A validated model is on record.'
          : 'No validated model is in production. Prediction endpoints stay gated.',
      },
      {
        label: model.v14.version,
        title: v14Verdict.title,
        tone: v14Verdict.tone,
        body: v14Ledger(model),
      },
      {
        label: model.v15?.version ?? 'v1.5',
        title: model.v15 ? v15Verdict.title : 'Pending',
        tone: model.v15 ? v15Verdict.tone : 'plain',
        body: model.v15
          ? v15Ledger(model.v15)
          : 'No v1.5 evidence file is on main, and the PR #23 snapshot is not available. No v1.5 numbers are shown.',
      },
    ],
    footnotes: [footnoteFor(model.v14, citation, 1), model.v15 ? footnoteFor(model.v15, citation, 2) : {
      n: 2,
      lead: 'v1.5 evidence is not on main, and no snapshot is committed.',
      linked: null,
      href: null,
      tail: '',
    }],
    closer: 'This page does not invent a forecast.',
  };
}

export function spanText(spans: Span[]) {
  return spans.map((span) => (span.kind === 'text' ? span.text : `[${span.note}]`)).join('');
}
