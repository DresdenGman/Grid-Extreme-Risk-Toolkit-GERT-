const MONTHS = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
] as const;

/** Spell a finite number the way the evidence JSON spells these decimals. */
export function formatPlain(n: number): string {
  if (!Number.isFinite(n)) {
    throw new Error('Cannot format a non-finite number');
  }
  const negative = n < 0;
  let text = Math.abs(n).toFixed(6);
  text = text.replace(/(\.\d*?[1-9])0+$/, '$1').replace(/\.0+$/, '');
  return negative ? `-${text}` : text;
}

export function formatSigned(n: number): string {
  if (n < 0) return `−${formatPlain(Math.abs(n))}`;
  if (n > 0) return `+${formatPlain(n)}`;
  return formatPlain(0);
}

/** Signed error, using the published absolute error so float subtraction cannot change the digits. */
export function formatSignedAbsolute(empirical: number, target: number, absolute: number): string {
  const delta = empirical - target;
  if (Math.abs(Math.abs(delta) - absolute) > 1e-4) {
    throw new Error(
      `absolute_coverage_error ${absolute} disagrees with empirical ${empirical} minus target ${target}`,
    );
  }
  if (Math.abs(delta) <= 1e-9) return formatPlain(0);
  return delta < 0 ? `−${formatPlain(absolute)}` : `+${formatPlain(absolute)}`;
}

export function formatNominal(n: number): string {
  const plain = formatPlain(n);
  const [whole, frac = ''] = plain.split('.');
  if (frac.length >= 2) return plain;
  return `${whole}.${frac.padEnd(2, '0')}`;
}

function utcParts(iso: string) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    throw new Error(`Evidence date is not valid: ${iso}`);
  }
  return {
    day: date.getUTCDate(),
    month: date.getUTCMonth(),
    year: date.getUTCFullYear(),
  };
}

export function formatUtcDate(iso: string): string {
  const parts = utcParts(iso);
  return `${parts.day} ${MONTHS[parts.month]} ${parts.year}`;
}

export function formatWindow(start: string, end: string): string {
  const a = utcParts(start);
  const b = utcParts(end);
  if (a.year === b.year && a.month === b.month) {
    return `${a.day}–${b.day} ${MONTHS[a.month]} ${a.year}`;
  }
  if (a.year === b.year) {
    return `${a.day} ${MONTHS[a.month]}–${b.day} ${MONTHS[b.month]} ${a.year}`;
  }
  return `${a.day} ${MONTHS[a.month]} ${a.year}–${b.day} ${MONTHS[b.month]} ${b.year}`;
}

export function joinAnd(items: string[]): string {
  if (items.length === 0) return '';
  if (items.length === 1) return items[0];
  if (items.length === 2) return `${items[0]} and ${items[1]}`;
  return `${items.slice(0, -1).join(', ')}, and ${items[items.length - 1]}`;
}
