import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, afterEach } from 'vitest';
import { Poster } from '../../components/home/Poster';
import { buildCopy } from '../../lib/homepage/copy';
import { loadCitation } from '../../lib/homepage/citation';
import { loadEvidence } from '../../lib/homepage/evidence';
import { buildFigure } from '../../lib/homepage/figure';

const evidence = loadEvidence();
const copy = buildCopy(evidence, loadCitation());
const figure = buildFigure(evidence);
const fonts = { sans: 'IBM Plex Sans', serif: 'Source Serif 4', mono: 'IBM Plex Mono' };

function renderPoster() {
  return render(<Poster copy={copy} figure={figure} citation={loadCitation()} fonts={fonts} />);
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('homepage poster', () => {
  it('renders the decision ledger and does not prefill a forecast', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response(JSON.stringify({
        temperature: 32,
        wind_speed: 15,
        solar_irradiance: 800,
        data_source: 'estimated_fallback',
      }), { status: 200 })),
    );
    renderPoster();

    expect(screen.getByRole('heading', { level: 1, name: 'GERT' })).toBeInTheDocument();
    expect(screen.getByText('No validated production model.')).toBeInTheDocument();
    expect(screen.getByText('Rejected.')).toBeInTheDocument();
    expect(screen.getByText('Provisional.')).toBeInTheDocument();
    expect(screen.getByText('0.03')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Rejected' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Provisional' })).toBeInTheDocument();
    expect(screen.getByText(/Q90, Q95, and Q99 missed it/)).toBeInTheDocument();
    expect(screen.getByText('PR #23, unmerged. Realized ERA5, not in production.')).toBeInTheDocument();
    expect(screen.getAllByText('UNAVAILABLE')).toHaveLength(3);
    expect(screen.getByText(/As of UNAVAILABLE/)).toBeInTheDocument();
    expect(screen.queryByText(/32°/)).not.toBeInTheDocument();
    expect(screen.queryByText(/\b800\b/)).not.toBeInTheDocument();
    expect(screen.queryByText('LOW')).not.toBeInTheDocument();

    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
    });
    expect(screen.queryByText(/32°/)).not.toBeInTheDocument();
  });

  it('shows official context when the API labels it as such', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes('weather')) {
          return new Response(JSON.stringify({
            temperature: 11,
            wind_speed: 2,
            solar_irradiance: 40,
            timestamp: '2026-11-10T18:00:00Z',
            data_source: 'external_forecast',
            provider: 'Open-Meteo',
            solar_source: 'external_forecast',
          }), { status: 200 });
        }
        return new Response(JSON.stringify({
          current_load_mw: 50000,
          capacity_mw: 70000,
          timestamp: '2026-11-10T18:00:00Z',
          data_source: 'official_live',
          capacity_source: 'official_adequacy',
          capacity_basis: 'ERCOT available generation capacity (NP3-763-CD)',
        }), { status: 200 });
      }),
    );
    renderPoster();
    expect(await screen.findByText('11.0°C · 2.0 m/s · 40 W/m²')).toBeInTheDocument();
    expect(screen.getByText('50,000 MW')).toBeInTheDocument();
    expect(screen.getByText('70,000 MW')).toBeInTheDocument();
    expect(screen.getByText(/Weather forecast/)).toBeInTheDocument();
  });
});
