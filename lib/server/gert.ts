import modelEvidence from '@/evidence/ercot_v1_4_validation.json';

const TOKEN_URL =
  'https://ercotb2c.b2clogin.com/ercotb2c.onmicrosoft.com/' +
  'B2C_1_PUBAPI-ROPC-FLOW/oauth2/v2.0/token';
const ERCOT_CLIENT_ID = 'fec253ea-0d06-4272-a5e6-b478baeecd70';
const LOAD_URL =
  'https://api.ercot.com/api/public-reports/np6-346-cd/act_sys_load_by_fzn';
const ADEQUACY_URL =
  'https://api.ercot.com/api/public-reports/np3-763-cd/st_sys_adequacy';
const CONFIGURED_CAPACITY_MW = 65_000;

const WEATHER_POINTS = [
  {
    zone: 'NORTH',
    latitude: 32.7767,
    longitude: -96.797,
    nwsHourly: 'https://api.weather.gov/gridpoints/FWD/89,104/forecast/hourly',
  },
  {
    zone: 'SOUTH',
    latitude: 29.4241,
    longitude: -98.4936,
    nwsHourly: 'https://api.weather.gov/gridpoints/EWX/126,54/forecast/hourly',
  },
  {
    zone: 'WEST',
    latitude: 31.9973,
    longitude: -102.0779,
    nwsHourly: 'https://api.weather.gov/gridpoints/MAF/123,133/forecast/hourly',
  },
  {
    zone: 'HOUSTON',
    latitude: 29.7604,
    longitude: -95.3698,
    nwsHourly: 'https://api.weather.gov/gridpoints/HGX/63,95/forecast/hourly',
  },
] as const;

const WEATHER_WEIGHTS: Record<(typeof WEATHER_POINTS)[number]['zone'], number> = {
  NORTH: 0.3448663984031006,
  SOUTH: 0.26127382930701115,
  WEST: 0.1319804768720815,
  HOUSTON: 0.2618792954178068,
};

type JsonRecord = Record<string, unknown>;
type CacheEntry<T> = { expiresAt: number; value: T };

let tokenCache: CacheEntry<string> | null = null;
let contextCache: CacheEntry<GridContext> | null = null;
let weatherCache: CacheEntry<WeatherSnapshot> | null = null;

const rateWindows = new Map<string, { count: number; resetAt: number }>();

type GridContext = {
  loadMw: number;
  capacityMw: number;
  dataSource: 'official_live' | 'estimated_fallback';
  capacitySource: 'official_adequacy' | 'configured_reference';
  capacityBasis: string;
};

type WeatherSnapshot = {
  temperature: number;
  wind_speed: number;
  solar_irradiance: number;
  timestamp: string;
  data_source: 'external_forecast' | 'estimated_fallback';
  provider?: 'Open-Meteo' | 'NOAA/NWS';
  solar_source?: 'external_forecast' | 'clear_sky_estimate';
};

function json(data: unknown, status = 200, extraHeaders?: HeadersInit) {
  const headers = new Headers(extraHeaders);
  headers.set('cache-control', 'no-store');
  headers.set('x-content-type-options', 'nosniff');
  headers.set('referrer-policy', 'no-referrer');
  return Response.json(data, {
    status,
    headers,
  });
}

function publicError(detail: string, status: number, requestId: string) {
  return json({ detail, request_id: requestId }, status);
}

function getRequestId(request: Request) {
  const candidate = request.headers.get('x-request-id');
  return candidate && /^[A-Za-z0-9._:-]{1,100}$/.test(candidate)
    ? candidate
    : crypto.randomUUID();
}

function allowRequest(request: Request, bucket: string, limit: number) {
  const now = Date.now();
  const ip =
    request.headers.get('cf-connecting-ip') ??
    request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ??
    'unknown';
  const key = `${bucket}:${ip}`;
  const current = rateWindows.get(key);
  if (!current || current.resetAt <= now) {
    rateWindows.set(key, { count: 1, resetAt: now + 60_000 });
    return true;
  }
  if (current.count >= limit) return false;
  current.count += 1;
  return true;
}

function credentials() {
  const username =
    process.env.ERCOT_API_USERNAME?.trim() ??
    '';
  const password = process.env.ERCOT_API_PASSWORD ?? '';
  const subscriptionKey =
    process.env.ERCOT_API_SUBSCRIPTION_KEY?.trim() ??
    '';
  return {
    username,
    password,
    subscriptionKey,
    configured: Boolean(username && password && subscriptionKey),
  };
}

function marketDate(offsetDays = 0) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Chicago',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(new Date(Date.now() + offsetDays * 86_400_000));
  const value = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${value.year}-${value.month}-${value.day}`;
}

async function fetchWithTimeout(
  input: string | URL,
  init: RequestInit = {},
  timeoutMs = 10_000,
) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}

async function getErcotToken() {
  if (tokenCache && tokenCache.expiresAt > Date.now()) return tokenCache.value;
  const creds = credentials();
  if (!creds.configured) throw new Error('ERCOT credentials are not configured');

  const body = new URLSearchParams({
    username: creds.username,
    password: creds.password,
    grant_type: 'password',
    scope: `openid ${ERCOT_CLIENT_ID} offline_access`,
    client_id: ERCOT_CLIENT_ID,
    response_type: 'id_token',
  });
  const response = await fetchWithTimeout(
    TOKEN_URL,
    {
      method: 'POST',
      headers: { 'content-type': 'application/x-www-form-urlencoded' },
      body,
    },
    12_000,
  );
  if (!response.ok) throw new Error('ERCOT token request failed');
  const payload = (await response.json()) as JsonRecord;
  const token = typeof payload.id_token === 'string' ? payload.id_token : '';
  if (!token) throw new Error('ERCOT token was missing');
  const expiresIn = Number(payload.expires_in ?? 3600);
  tokenCache = {
    value: token,
    expiresAt: Date.now() + Math.max(60, expiresIn - 60) * 1000,
  };
  return token;
}

function records(payload: JsonRecord): JsonRecord[] {
  let data: unknown = payload.data ?? [];
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    const candidate = data as JsonRecord;
    data = candidate.rows ?? candidate.items ?? candidate.data ?? [candidate];
  }
  if (!Array.isArray(data)) return [];

  const fields = Array.isArray(payload.fields)
    ? payload.fields
        .map((field) =>
          field && typeof field === 'object' && 'name' in field
            ? String((field as JsonRecord).name)
            : '',
        )
        .filter(Boolean)
    : [];
  return data.flatMap((row) => {
    if (row && typeof row === 'object' && !Array.isArray(row)) {
      return [row as JsonRecord];
    }
    if (Array.isArray(row) && row.length === fields.length) {
      return [Object.fromEntries(fields.map((field, index) => [field, row[index]]))];
    }
    return [];
  });
}

function normalized(row: JsonRecord) {
  return Object.fromEntries(
    Object.entries(row).map(([key, value]) => [
      key.toLowerCase().replace(/[^a-z0-9]/g, ''),
      value,
    ]),
  );
}

function firstPositive(payload: JsonRecord, keys: string[]) {
  for (const raw of records(payload)) {
    const row = normalized(raw);
    for (const key of keys) {
      const value = Number(row[key]);
      if (Number.isFinite(value) && value > 0) return value;
    }
  }
  throw new Error('ERCOT response did not contain a positive value');
}

async function fetchErcotContext(): Promise<GridContext> {
  if (contextCache && contextCache.expiresAt > Date.now()) return contextCache.value;
  const creds = credentials();
  if (!creds.configured) throw new Error('ERCOT credentials are not configured');
  const token = await getErcotToken();
  const headers = {
    authorization: `Bearer ${token}`,
    'ocp-apim-subscription-key': creds.subscriptionKey,
  };

  const loadUrl = new URL(LOAD_URL);
  loadUrl.search = new URLSearchParams({
    // ERCOT can publish the newest complete market day with a short lag.
    // Query a bounded lookback so weekends and publication delays do not
    // incorrectly force the product into estimated fallback mode.
    operatingDayFrom: marketDate(-9),
    operatingDayTo: marketDate(),
    page: '1',
    size: '500',
    sort: 'operatingDay',
    dir: 'DESC',
  }).toString();
  const loadResponse = await fetchWithTimeout(loadUrl, { headers }, 12_000);
  if (!loadResponse.ok) throw new Error('ERCOT load request failed');
  const loadMw = firstPositive((await loadResponse.json()) as JsonRecord, [
    'total',
    'totalload',
  ]);

  let capacityMw = CONFIGURED_CAPACITY_MW;
  let capacitySource: GridContext['capacitySource'] = 'configured_reference';
  let capacityBasis = 'configured ERCOT system reference';
  try {
    const adequacyUrl = new URL(ADEQUACY_URL);
    adequacyUrl.search = new URLSearchParams({
      deliveryDateFrom: marketDate(-1),
      deliveryDateTo: marketDate(),
      page: '1',
      size: '100',
      sort: 'postedDatetime',
      dir: 'DESC',
    }).toString();
    const adequacyResponse = await fetchWithTimeout(adequacyUrl, { headers }, 12_000);
    if (!adequacyResponse.ok) throw new Error('ERCOT adequacy request failed');
    capacityMw = firstPositive((await adequacyResponse.json()) as JsonRecord, [
      'availcapgen',
    ]);
    capacitySource = 'official_adequacy';
    capacityBasis = 'ERCOT available generation capacity (NP3-763-CD)';
  } catch {
    // Preserve the valid official load while clearly labelling capacity fallback.
  }

  const value: GridContext = {
    loadMw,
    capacityMw,
    dataSource: 'official_live',
    capacitySource,
    capacityBasis,
  };
  contextCache = { value, expiresAt: Date.now() + 60_000 };
  return value;
}

function estimatedContext(): GridContext {
  const hour = Number(
    new Intl.DateTimeFormat('en-US', {
      timeZone: 'America/Chicago',
      hour: '2-digit',
      hour12: false,
    }).format(new Date()),
  );
  return {
    loadMw: 45_000 + 15_000 * Math.sin(((hour - 6) * Math.PI) / 12),
    capacityMw: CONFIGURED_CAPACITY_MW,
    dataSource: 'estimated_fallback',
    capacitySource: 'configured_reference',
    capacityBasis: 'configured ERCOT system reference',
  };
}

function clearSkyIrradiance(
  timestamp: Date,
  latitude: number,
  longitude: number,
) {
  const yearStart = Date.UTC(timestamp.getUTCFullYear(), 0, 0);
  const day = Math.floor((timestamp.getTime() - yearStart) / 86_400_000);
  const declination =
    (23.44 * Math.PI * Math.sin((2 * Math.PI * (284 + day)) / 365)) / 180;
  const latitudeRad = (latitude * Math.PI) / 180;
  const utcHour =
    timestamp.getUTCHours() +
    timestamp.getUTCMinutes() / 60 +
    longitude / 15;
  const hourAngle = ((15 * (utcHour - 12)) * Math.PI) / 180;
  const solarElevation =
    Math.sin(latitudeRad) * Math.sin(declination) +
    Math.cos(latitudeRad) * Math.cos(declination) * Math.cos(hourAngle);
  return 1_000 * Math.max(0, solarElevation);
}

async function fetchNwsWeather(target: Date): Promise<WeatherSnapshot> {
  const responses = await Promise.all(
    WEATHER_POINTS.map((point) =>
      fetchWithTimeout(
        point.nwsHourly,
        {
          headers: {
            accept: 'application/geo+json',
            'user-agent': 'GERT/1.2 (https://gertgrid.space)',
          },
        },
        8_000,
      ),
    ),
  );
  if (responses.some((response) => !response.ok)) {
    throw new Error('NOAA/NWS weather request failed');
  }
  const payloads = await Promise.all(
    responses.map((response) => response.json() as Promise<JsonRecord>),
  );
  let temperature = 0;
  let wind = 0;
  let solar = 0;
  payloads.forEach((payload, index) => {
    const properties = payload.properties as JsonRecord | undefined;
    const periods = Array.isArray(properties?.periods)
      ? (properties.periods as JsonRecord[])
      : [];
    const period =
      periods.find((candidate) => {
        const start =
          typeof candidate.startTime === 'string'
            ? Date.parse(candidate.startTime)
            : Number.NaN;
        return Number.isFinite(start) && start >= target.getTime();
      }) ?? periods[0];
    if (!period) throw new Error('NOAA/NWS forecast period was missing');
    const rawTemperature = Number(period.temperature);
    const temperatureC =
      period.temperatureUnit === 'F'
        ? ((rawTemperature - 32) * 5) / 9
        : rawTemperature;
    const windText =
      typeof period.windSpeed === 'string' ? period.windSpeed : '';
    const windValues = windText.match(/\d+(?:\.\d+)?/g);
    const windMph = windValues?.length
      ? windValues.map(Number).reduce((sum, value) => sum + value, 0) /
        windValues.length
      : Number.NaN;
    if (!Number.isFinite(temperatureC) || !Number.isFinite(windMph)) {
      throw new Error('NOAA/NWS forecast contained invalid values');
    }
    const point = WEATHER_POINTS[index];
    const weight = WEATHER_WEIGHTS[point.zone];
    temperature += temperatureC * weight;
    wind += windMph * 0.44704 * weight;
    solar +=
      clearSkyIrradiance(target, point.latitude, point.longitude) * weight;
  });
  return {
    temperature,
    wind_speed: wind,
    solar_irradiance: solar,
    timestamp: target.toISOString(),
    data_source: 'external_forecast',
    provider: 'NOAA/NWS',
    solar_source: 'clear_sky_estimate',
  };
}

async function fetchSystemWeather(): Promise<WeatherSnapshot> {
  if (weatherCache && weatherCache.expiresAt > Date.now()) return weatherCache.value;
  const target = new Date(Date.now() + 60 * 60 * 1000);
  target.setUTCMinutes(0, 0, 0);
  const targetKey = target.toISOString().slice(0, 13) + ':00';
  const url = new URL('https://api.open-meteo.com/v1/forecast');
  url.search = new URLSearchParams({
    latitude: WEATHER_POINTS.map((point) => point.latitude).join(','),
    longitude: WEATHER_POINTS.map((point) => point.longitude).join(','),
    hourly: 'temperature_2m,wind_speed_10m,shortwave_radiation',
    forecast_hours: '3',
    timezone: 'UTC',
    wind_speed_unit: 'ms',
  }).toString();
  const response = await fetchWithTimeout(url, {}, 8_000);
  if (!response.ok) {
    console.warn(`Open-Meteo unavailable (${response.status}); using NOAA/NWS.`);
    const value = await fetchNwsWeather(target);
    weatherCache = { value, expiresAt: Date.now() + 10 * 60_000 };
    return value;
  }
  const raw = await response.json();
  const locations = Array.isArray(raw) ? raw : [raw];
  if (locations.length !== WEATHER_POINTS.length) {
    throw new Error('Weather response was incomplete');
  }

  let temperature = 0;
  let wind = 0;
  let solar = 0;
  let observationTime = target.toISOString();
  locations.forEach((location: JsonRecord, index: number) => {
    const hourly = location.hourly as JsonRecord | undefined;
    const times = Array.isArray(hourly?.time)
      ? hourly.time.map(String)
      : [];
    const position = times.findIndex((value) => value >= targetKey);
    if (!hourly || position < 0) throw new Error('Target weather hour was missing');
    if (index === 0) observationTime = `${times[position]}:00Z`;
    const weight = WEATHER_WEIGHTS[WEATHER_POINTS[index].zone];
    temperature += Number((hourly.temperature_2m as unknown[])[position]) * weight;
    wind += Number((hourly.wind_speed_10m as unknown[])[position]) * weight;
    solar += Number((hourly.shortwave_radiation as unknown[])[position]) * weight;
  });
  if (![temperature, wind, solar].every(Number.isFinite)) {
    throw new Error('Weather response contained invalid values');
  }
  const value: WeatherSnapshot = {
    temperature,
    wind_speed: wind,
    solar_irradiance: solar,
    timestamp: new Date(observationTime).toISOString(),
    data_source: 'external_forecast',
    provider: 'Open-Meteo',
    solar_source: 'external_forecast',
  };
  weatherCache = { value, expiresAt: Date.now() + 10 * 60_000 };
  return value;
}

function eventPlayback(id: string) {
  if (id !== 'polar-vortex') return null;
  return {
    event_id: 'ercot-2021-educational-reconstruction',
    title: 'ERCOT Polar Vortex · Decision Replay',
    total_hours: 36,
    steps: Array.from({ length: 36 }, (_, hour) => {
      const pressure = Math.sin((hour / 35) * Math.PI);
      const actualLoad = 49_000 + pressure * 22_500 + hour * 95;
      const capacity = 78_500 - pressure * 7_600;
      return {
        hour,
        timestamp_label: `Feb ${14 + Math.floor(hour / 24)}, ${String(hour % 24).padStart(2, '0')}:00`,
        temperature: Number((8 - pressure * 23).toFixed(1)),
        actual_load_mw: Math.round(actualLoad),
        capacity_mw: Math.round(capacity),
        gert_p99_load_mw: Math.round(actualLoad + 2_300 + pressure * 2_500),
        risk_score: Number((22 + pressure * 76).toFixed(1)),
      };
    }),
    logs: [
      { hour: 4, message: 'Cold-weather watch initiated as the probabilistic tail widens.', source: 'GERT', severity: 'INFO' },
      { hour: 11, message: 'P99 demand enters the two-gigawatt capacity buffer.', source: 'RISK', severity: 'WARNING' },
      { hour: 17, message: 'Modeled tail crosses available capacity; reserve action indicated.', source: 'GERT', severity: 'CRITICAL' },
      { hour: 23, message: 'Sustained generation outages constrain the recovery window.', source: 'OPS', severity: 'CRITICAL' },
      { hour: 31, message: 'Capacity margin begins recovering as temperature pressure eases.', source: 'OPS', severity: 'INFO' },
    ],
    provenance: 'synthetic_reconstruction',
    methodology_note:
      'Deterministic educational reconstruction; not an official historical event record.',
  };
}

export async function handleGertRequest(
  request: Request,
  path: string[],
): Promise<Response> {
  const requestId = getRequestId(request);
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: { 'x-content-type-options': 'nosniff' },
    });
  }

  const route = `/${path.join('/')}`;
  const url = new URL(request.url);
  const rateLimit = route === '/load/current' ? 30 : route === '/weather/live' ? 20 : 60;
  if (!allowRequest(request, route, rateLimit)) {
    return publicError('Too many requests. Try again shortly.', 429, requestId);
  }

  if (request.method === 'GET' && route === '/health') {
    return json({
      status: 'ok',
      timestamp: new Date().toISOString(),
      backend: 'gert-vercel-native-v1',
      api_version: '1.2.0',
      release_sha: process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 12) ?? 'local',
      deployment_platform: 'vercel',
      env: 'production',
    });
  }

  if (request.method === 'GET' && route === '/status') {
    const officialData = credentials().configured;
    return json({
      status: 'degraded',
      environment: 'production',
      model_status: 'rejected_candidate',
      model_version: modelEvidence.candidate_id,
      api_version: '1.2.0',
      release_sha: process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 12) ?? 'local',
      deployment_platform: 'vercel',
      capabilities: {
        official_ercot_data: officialData,
        probabilistic_prediction: false,
        scenario_analysis: false,
        validated_backtest: false,
        presentation_mode: true,
      },
    });
  }

  if (request.method === 'GET' && route === '/model/evidence') {
    return json(modelEvidence);
  }

  if (request.method === 'GET' && route === '/weather/live') {
    if (url.searchParams.get('region') !== 'ERCOT_SYSTEM') {
      return publicError('Only ERCOT_SYSTEM is supported.', 422, requestId);
    }
    try {
      return json(await fetchSystemWeather());
    } catch (error) {
      console.warn(
        'GERT weather upstream fallback:',
        error instanceof Error ? error.message : 'unknown upstream error',
      );
      return json({
        temperature: 25,
        wind_speed: 10,
        solar_irradiance: 600,
        timestamp: new Date().toISOString(),
        data_source: 'estimated_fallback',
      });
    }
  }

  if (request.method === 'GET' && route === '/load/current') {
    if (url.searchParams.get('region') !== 'ERCOT_SYSTEM') {
      return publicError('Only ERCOT_SYSTEM is supported.', 422, requestId);
    }
    let context: GridContext;
    try {
      context = await fetchErcotContext();
    } catch {
      context = estimatedContext();
    }
    return json({
      region: 'ERCOT_SYSTEM',
      current_load_mw: context.loadMw,
      capacity_mw: context.capacityMw,
      utilization_percent: (context.loadMw / context.capacityMw) * 100,
      timestamp: new Date().toISOString(),
      data_source: context.dataSource,
      capacity_source: context.capacitySource,
      capacity_basis: context.capacityBasis,
    });
  }

  if (request.method === 'GET' && route.startsWith('/events/playback/')) {
    const event = eventPlayback(path.at(-1) ?? '');
    return event
      ? json(event)
      : publicError('Event reconstruction was not found.', 404, requestId);
  }

  if (
    (request.method === 'POST' && ['/predict', '/scenario'].includes(route)) ||
    (request.method === 'GET' && route === '/backtest')
  ) {
    const messages: Record<string, string> = {
      '/predict': 'Validated probabilistic model is not yet available in production.',
      '/scenario': 'Scenario analysis requires a validated production model.',
      '/backtest': 'Validated model backtest is not yet available in production.',
    };
    return publicError(messages[route], 503, requestId);
  }

  return publicError('Not found.', 404, requestId);
}
