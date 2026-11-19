import { formatNominal, formatPlain, formatSigned, formatSignedAbsolute } from './format';
import type { EvidenceModel, QuantilePoint } from './types';

const WIDTH = 1312;
const HEIGHT = 920;
const Y_ZERO = 482;
const Y_LIMIT = 142;
const PLOT_LEFT = 108;
const PLOT_RIGHT = 1288;
const CENTERS = [248, 548, 848, 1148];
const SERIES_OFFSET = 33.6;

export interface TickMark {
  y: number;
  textY: number;
  label: string;
  tone: 'muted' | 'ink';
}

export interface DesktopColumn {
  label: string;
  nominal: string;
  x: number;
  v14: {
    square: { x: number; y: number; size: number };
    centerY: number;
    stub: { x: number; y1: number; y2: number } | null;
    signed: string;
    emp: string;
    labelX: number;
    labelY: number;
    signedSize: number;
  };
  v15: {
    x: number;
    y: number;
    y1: number;
    y2: number;
    signed: string;
    emp: string;
    ci: string;
    labelX: number;
    labelY: number;
    note: { x: number; y: number; text: string } | null;
  } | null;
}

export interface LegendItem {
  kind: 'square' | 'interval';
  x: number;
  label: string;
  labelX: number;
}

export interface FigureView {
  width: number;
  height: number;
  yZero: number;
  plotLeft: number;
  plotRight: number;
  band: { x: number; y: number; width: number; height: number };
  ticks: TickMark[];
  dividers: number[];
  columns: DesktopColumn[];
  legend: LegendItem[];
  axisNote: string;
  mobile: MobileFigure;
}

export interface MobileRow {
  label: string;
  nominal: string;
  v14Pct: number;
  v14Signed: string;
  v14Emp: string;
  v14Past: boolean;
  v15: {
    pct: number;
    ciLeft: number;
    ciWidth: number;
    signed: string;
    emp: string;
    ci: string;
    past: boolean;
  } | null;
}

export interface MobileFigure {
  bandLeft: number;
  bandWidth: number;
  zeroPct: number;
  v14Version: string;
  v15Version: string | null;
  ticks: { pct: number; label: string }[];
  rows: MobileRow[];
}

function yFor(signed: number, limit: number) {
  return Y_ZERO - (signed / limit) * (Y_ZERO - Y_LIMIT);
}

function chooseLimit(values: number[], tolerance: number) {
  const need = Math.max(0.05, tolerance, ...values.map((value) => Math.abs(value)));
  if (need <= 0.05) return 0.05;
  return Number((Math.ceil((need + 1e-9) / 0.01) * 0.01).toFixed(2));
}

function tickTextY(y: number, signed: number) {
  if (signed > 0) return y - 5;
  if (signed < 0) return y + 12;
  return y - 6;
}

function plotPct(signed: number, limit: number) {
  const inset = 6;
  const inner = ((Math.max(-limit, Math.min(limit, signed)) + limit) / (2 * limit)) * 100;
  return inset + inner * ((100 - 2 * inset) / 100);
}

function signedLabel(point: QuantilePoint) {
  return formatSignedAbsolute(point.empirical, point.nominal, point.absoluteError);
}

function v15LabelY(centerY: number, ciTop: number, ciBottom: number) {
  const spanBelow = 26;
  const crossesZero = (baseline: number) => baseline - 11 < Y_ZERO && baseline + spanBelow > Y_ZERO;
  let baseline = centerY - 8;
  if (crossesZero(baseline)) {
    baseline = ciTop - 16.8;
    if (crossesZero(baseline) || baseline < 120) baseline = ciBottom + 22;
  }
  return baseline;
}

function legend(v14: string, v15: string | null): LegendItem[] {
  const right = PLOT_RIGHT;
  const char = 6.35;
  if (!v15) {
    const labelX = right - v14.length * char;
    return [{ kind: 'square', x: labelX - 16, label: v14, labelX }];
  }
  const v15LabelX = right - v15.length * char;
  const v15MarkX = v15LabelX - 14;
  const v14LabelX = v15MarkX - 36 - v14.length * char;
  return [
    { kind: 'square', x: v14LabelX - 16, label: v14, labelX: v14LabelX },
    { kind: 'interval', x: v15MarkX, label: v15, labelX: v15LabelX },
  ];
}

function mobileFigure(model: EvidenceModel, limit: number): MobileFigure {
  const { tolerance, v14, v15 } = model;
  return {
    bandLeft: plotPct(-tolerance, limit),
    bandWidth: plotPct(tolerance, limit) - plotPct(-tolerance, limit),
    zeroPct: plotPct(0, limit),
    v14Version: v14.version,
    v15Version: v15?.version ?? null,
    ticks: [-limit, -tolerance, 0, tolerance, limit].map((signed) => ({
      pct: plotPct(signed, limit),
      label: formatSigned(signed),
    })),
    rows: v14.points.map((point) => {
      const other = v15?.points.find((candidate) => candidate.quantile === point.quantile) ?? null;
      const ciLeft = other?.signedWilson ? plotPct(other.signedWilson[0], limit) : 0;
      const ciRight = other?.signedWilson ? plotPct(other.signedWilson[1], limit) : 0;
      return {
        label: point.label,
        nominal: formatNominal(point.nominal),
        v14Pct: plotPct(point.signedError, limit),
        v14Signed: signedLabel(point),
        v14Emp: formatPlain(point.empirical),
        v14Past: point.pastGate,
        v15: other
          ? {
              pct: plotPct(other.signedError, limit),
              ciLeft: Math.min(ciLeft, ciRight),
              ciWidth: Math.abs(ciRight - ciLeft),
              signed: signedLabel(other),
              emp: formatPlain(other.empirical),
              ci: other.wilson ? `${formatPlain(other.wilson[0])}, ${formatPlain(other.wilson[1])}` : '',
              past: other.intervalPastGate,
            }
          : null,
      };
    }),
  };
}

export function buildFigure(model: EvidenceModel): FigureView {
  const samples = model.v14.points.flatMap((point) => {
    const other = model.v15?.points.find((candidate) => candidate.quantile === point.quantile);
    return [point.signedError, ...(other?.signedWilson ?? []), other?.signedError ?? 0];
  });
  const limit = chooseLimit(samples, model.tolerance);
  const y = (signed: number) => yFor(signed, limit);
  const bandTop = y(model.tolerance);
  const bandBottom = y(-model.tolerance);
  const columns: DesktopColumn[] = model.v14.points.map((point, index) => {
    const center = CENTERS[index];
    const other = model.v15?.points.find((candidate) => candidate.quantile === point.quantile) ?? null;
    const v14Center = center - SERIES_OFFSET;
    const v14Y = y(point.signedError);
    const square = { x: v14Center - 6.5, y: v14Y - 6.5, size: 13 };
    const stub = point.pastGate
      ? {
          x: v14Center,
          y1: y(point.signedError < 0 ? -model.tolerance : model.tolerance),
          y2: v14Y,
        }
      : null;
    let v15: DesktopColumn['v15'] = null;
    if (other) {
      const x = center + SERIES_OFFSET;
      const pointY = y(other.signedError);
      const top = other.signedWilson ? y(other.signedWilson[1]) : pointY;
      const bottom = other.signedWilson ? y(other.signedWilson[0]) : pointY;
      const exceedsHigh = other.signedWilson ? other.signedWilson[1] > model.tolerance + 1e-6 : false;
      const exceedsLow = other.signedWilson ? other.signedWilson[0] < -model.tolerance - 1e-6 : false;
      v15 = {
        x,
        y: pointY,
        y1: Math.min(top, bottom),
        y2: Math.max(top, bottom),
        signed: signedLabel(other),
        emp: formatPlain(other.empirical),
        ci: other.wilson ? `${formatPlain(other.wilson[0])}, ${formatPlain(other.wilson[1])}` : '',
        labelX: x + 14,
        labelY: other.signedWilson
          ? v15LabelY(pointY, Math.min(top, bottom), Math.max(top, bottom))
          : pointY - 8,
        note: exceedsHigh
          ? { x: x + 12, y: Math.min(top, bottom) - 14, text: 'interval past the gate' }
          : exceedsLow
            ? { x: x + 12, y: Math.max(top, bottom) + 16, text: 'interval past the gate' }
            : null,
      };
    }
    return {
      label: point.label,
      nominal: `nominal ${formatNominal(point.nominal)}`,
      x: center,
      v14: {
        square,
        centerY: v14Y,
        stub,
        signed: signedLabel(point),
        emp: formatPlain(point.empirical),
        labelX: square.x - 7.5,
        labelY: v14Y - 10,
        signedSize: point.pastGate ? 12 : 11,
      },
      v15,
    };
  });

  const v14Legend = `${model.v14.version} point, n = ${model.v14.observations}`;
  const v15Legend = model.v15
    ? `${model.v15.version}, n = ${model.v15.observations}${model.v15.wilsonComplete ? ', Wilson 95%' : ''}`
    : null;

  return {
    width: WIDTH,
    height: HEIGHT,
    yZero: Y_ZERO,
    plotLeft: PLOT_LEFT,
    plotRight: PLOT_RIGHT,
    band: {
      x: PLOT_LEFT,
      y: bandTop,
      width: PLOT_RIGHT - PLOT_LEFT,
      height: bandBottom - bandTop,
    },
    ticks: [limit, model.tolerance, 0, -model.tolerance, -limit].map((signed) => {
      const tickY = y(signed);
      return {
        y: tickY,
        textY: tickTextY(tickY, signed),
        label: signed === 0 ? '0' : `${formatSigned(signed)}${Math.abs(signed) === model.tolerance ? '  gate' : ''}`,
        tone: Math.abs(signed) === limit ? 'muted' : 'ink',
      };
    }),
    dividers: CENTERS.slice(0, -1).map((center, index) => (center + CENTERS[index + 1]) / 2),
    columns,
    legend: legend(v14Legend, v15Legend),
    axisNote: `Shaded band: preregistered gate, absolute coverage error ≤ ${model.gateLabel}. Negative values are undercoverage.`,
    mobile: mobileFigure(model, limit),
  };
}
