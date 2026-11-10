export const UNAVAILABLE = 'UNAVAILABLE';

export interface LiveView {
  asOfLabel: string;
  weather: string;
  weatherDetail: string | null;
  weatherLive: boolean;
  load: string;
  loadDetail: string | null;
  loadLive: boolean;
  capacity: string;
  capacityDetail: string | null;
  capacityLive: boolean;
  foot: string;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function finite(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function timestamp(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) return null;
  return new Date(parsed).toISOString();
}

function formatAsOf(iso: string): string {
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: 'America/Chicago',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).format(new Date(iso));
}

function formatMw(mw: number): string {
  return `${Math.round(mw).toLocaleString('en-US')} MW`;
}

interface AcceptedWeather {
  temperature: number;
  wind: number;
  solar: number | null;
  provider: string;
  timestamp: string;
}

interface AcceptedQuantity {
  text: string;
  detail: string;
  timestamp: string;
}

function acceptWeather(payload: unknown): AcceptedWeather | null {
  if (!isRecord(payload)) return null;
  if (payload.data_source !== 'external_forecast') return null;
  if (typeof payload.provider !== 'string' || payload.provider.trim() === '') return null;
  const temperature = finite(payload.temperature);
  const wind = finite(payload.wind_speed);
  const when = timestamp(payload.timestamp);
  if (temperature === null || wind === null || wind < 0 || when === null) return null;

  let solar: number | null = null;
  if (payload.solar_source === 'external_forecast') {
    const value = finite(payload.solar_irradiance);
    if (value !== null && value >= 0) solar = value;
  }

  return {
    temperature,
    wind,
    solar,
    provider: payload.provider.trim(),
    timestamp: when,
  };
}

function acceptLoad(payload: unknown): AcceptedQuantity | null {
  if (!isRecord(payload) || payload.data_source !== 'official_live') return null;
  const mw = finite(payload.current_load_mw);
  const when = timestamp(payload.timestamp);
  if (mw === null || mw < 0 || when === null) return null;
  return { text: formatMw(mw), detail: 'Official ERCOT', timestamp: when };
}

function acceptCapacity(payload: unknown): AcceptedQuantity | null {
  if (!isRecord(payload) || payload.capacity_source !== 'official_adequacy') return null;
  const mw = finite(payload.capacity_mw);
  const basis = typeof payload.capacity_basis === 'string' ? payload.capacity_basis.trim() : '';
  const when = timestamp(payload.timestamp);
  if (mw === null || mw <= 0 || basis === '' || when === null) return null;
  return { text: formatMw(mw), detail: basis, timestamp: when };
}

export function footLine(flags: { weather: boolean; load: boolean; capacity: boolean }): string {
  if (!flags.weather && !flags.load && !flags.capacity) {
    return 'Weather · load · capacity \u00A0 UNAVAILABLE';
  }
  const bit = (name: string, on: boolean, word: string) => `${name} ${on ? word : UNAVAILABLE}`;
  return [
    bit('Weather', flags.weather, 'forecast'),
    bit('load', flags.load, 'official'),
    bit('capacity', flags.capacity, 'official'),
  ].join(' · ');
}

/**
 * Turn weather and load payloads into homepage fields.
 * Estimated, simulated, and clear-sky values stay UNAVAILABLE.
 * Nothing here invents a forecast when the payload is missing or unlabeled.
 */
export function interpretLive(weatherPayload: unknown, loadPayload: unknown): LiveView {
  const weather = acceptWeather(weatherPayload);
  const load = acceptLoad(loadPayload);
  const capacity = acceptCapacity(loadPayload);
  const times = [weather?.timestamp, load?.timestamp, capacity?.timestamp].filter(
    (value): value is string => Boolean(value),
  );
  const latest = times.sort().at(-1) ?? null;

  const weatherText = weather
    ? [
        `${weather.temperature.toFixed(1)}°C`,
        `${weather.wind.toFixed(1)} m/s`,
        weather.solar === null ? 'solar UNAVAILABLE' : `${Math.round(weather.solar)} W/m²`,
      ].join(' · ')
    : UNAVAILABLE;

  return {
    asOfLabel: latest ? formatAsOf(latest) : UNAVAILABLE,
    weather: weatherText,
    weatherDetail: weather?.provider ?? null,
    weatherLive: weather !== null,
    load: load?.text ?? UNAVAILABLE,
    loadDetail: load?.detail ?? null,
    loadLive: load !== null,
    capacity: capacity?.text ?? UNAVAILABLE,
    capacityDetail: capacity?.detail ?? null,
    capacityLive: capacity !== null,
    foot: footLine({
      weather: weather !== null,
      load: load !== null,
      capacity: capacity !== null,
    }),
  };
}
