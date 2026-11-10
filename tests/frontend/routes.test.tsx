import { readdirSync } from 'fs';
import path from 'path';
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import About from '../../app/(studio)/about/page';
import Benchmark from '../../app/(studio)/benchmark/page';
import Changelog from '../../app/(studio)/changelog/page';
import Community from '../../app/(studio)/community/page';
import Dashboard from '../../app/(studio)/dashboard/page';
import EventReplay from '../../app/(studio)/events/polar-vortex/page';
import History from '../../app/(studio)/history/page';
import Monitor from '../../app/(studio)/monitor/page';
import Research from '../../app/(studio)/research/page';
import Review from '../../app/(studio)/review/page';
import SameMeter from '../../app/(studio)/briefs/same-meter/page';
import Scenario from '../../app/(studio)/scenario/page';
import Winter from '../../app/(studio)/briefs/winter-load/page';

function studioRoutes(): string[] {
  const base = path.join(process.cwd(), 'app/(studio)');
  const routes: string[] = [];
  const walk = (dir: string) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.name === 'page.tsx') {
        routes.push(`/${path.relative(base, path.dirname(full)).split(path.sep).join('/')}`);
      }
    }
  };
  walk(base);
  return routes.sort();
}

const rendered: Array<[string, () => React.ReactNode]> = [
  ['/about', () => <About />],
  ['/benchmark', () => <Benchmark />],
  ['/briefs/same-meter', () => <SameMeter />],
  ['/briefs/winter-load', () => <Winter />],
  ['/changelog', () => <Changelog />],
  ['/community', () => <Community />],
  ['/events/polar-vortex', () => <EventReplay />],
  ['/history', () => <History />],
  ['/monitor', () => <Monitor />],
  ['/research', () => <Research />],
  ['/review', () => <Review />],
  ['/scenario', () => <Scenario />],
];

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ detail: 'gated' }), { status: 503 })));
  vi.stubGlobal('ResizeObserver', class {
    observe() {}
    unobserve() {}
    disconnect() {}
  });
});

describe('studio route smoke', () => {
  it('renders every studio page except the dashboard redirect', () => {
    expect(rendered.map(([route]) => route).sort()).toEqual(studioRoutes().filter((route) => route !== '/dashboard'));
  });

  it('dashboard redirects to the Historical Lab', () => {
    expect(() => Dashboard()).toThrow(/NEXT_REDIRECT/);
  });

  for (const [route, element] of rendered) {
    it(`renders ${route} with visible text`, async () => {
      const { container } = render(element());
      await waitFor(() => {
        expect((container.textContent ?? '').trim().length).toBeGreaterThan(40);
      });
    });
  }

  it('history and review say what they are', () => {
    render(<History />);
    expect(screen.getByText(/deterministic teaching exercise over three deliberately chosen 72-hour windows/)).toBeInTheDocument();
    expect(screen.getByText(/not a representative backtest/)).toBeInTheDocument();
    render(<Review />);
    expect(screen.getByText(/How to critique the evidence/)).toBeInTheDocument();
    expect(screen.getByText(/Criticism is recorded only if you submit it/)).toBeInTheDocument();
  });
});
