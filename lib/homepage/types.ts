export const QUANTILE_ORDER = ['q50', 'q90', 'q95', 'q99'] as const;
export type QuantileId = (typeof QUANTILE_ORDER)[number];

export interface QuantilePoint {
  quantile: QuantileId;
  label: string;
  nominal: number;
  empirical: number;
  absoluteError: number;
  signedError: number;
  pastGate: boolean;
  wilson: [number, number] | null;
  signedWilson: [number, number] | null;
  intervalPastGate: boolean;
}

export type CandidateSource =
  | { kind: 'main'; path: string }
  | {
      kind: 'pr23-snapshot';
      path: string;
      upstreamPath: string;
      pr: number;
      branch: string;
      commit: string;
    };

export interface CandidateView {
  version: string;
  candidateId: string;
  status: string;
  summary: string;
  observations: number;
  crossings: number;
  publishedLabel: string;
  windowLabel: string;
  points: QuantilePoint[];
  failedLabels: string[];
  passedLabels: string[];
  allGatesPassed: boolean;
  mentionsEra5: boolean;
  realizedEra5: boolean;
  sameWeatherAsV14: boolean;
  optimisticRealizedWeather: boolean;
  gateUsesPointEstimate: boolean;
  wilsonComplete: boolean;
  source: CandidateSource;
}

export interface EvidenceModel {
  tolerance: number;
  gateLabel: string;
  v14: CandidateView;
  v15: CandidateView | null;
  productionValidated: boolean;
  windowsDiffer: boolean;
}

export type VerdictTone = 'rejected' | 'provisional' | 'plain';

export interface Verdict {
  title: string;
  tone: VerdictTone;
}

export interface Citation {
  author: string;
  year: string;
  title: string;
  version: string;
  softwareDoi: string;
  conceptDoi: string;
  datasetDoi: string;
  repository: string;
}
