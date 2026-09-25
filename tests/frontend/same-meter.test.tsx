import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import SameMeterChallenge from '../../components/SameMeterChallenge';
import { sameMeterScenario, sameMeterSnapshot } from '../../lib/same-meter';

describe('same-meter teaching counterexample', () => {
  it('preserves both meter readings across every slider position', () => {
    for (let demand = 45000; demand <= 90000; demand += 5000) {
      const result = sameMeterScenario(demand);
      expect(result.sameReadings).toBe(true);
      expect(result.a.rows.map((r) => r.deliveredMw)).toEqual([60000, 45000]);
      expect(result.b.rows.map((r) => r.deliveredMw)).toEqual([60000, 45000]);
      expect(result.a.totalUnservedMwh).toBe(0);
      expect(result.b.totalUnservedMwh).toBe(demand - 45000);
      expect(result.differentUnservedEnergy).toBe(demand > 45000);
    }
  });
  it.each([NaN, Infinity, -Infinity, 44999, 90001])('rejects invalid demand %s', (value) => {
    expect(() => sameMeterScenario(value)).toThrow(RangeError);
  });
  it('keeps the snapshot a local model record, not a participation claim', () => {
    const record = sameMeterSnapshot(70000, '2026-09-24T20:00:00Z');
    expect(record.b.totalUnservedMwh).toBe(25000);
    expect(record.evidence_status).toBe('local_model_snapshot_not_verified_participation');
    expect(record.limitations).toContain('not ERCOT observations');
    expect(record).not.toHaveProperty('name');
    expect(record).not.toHaveProperty('email');
    expect(record).not.toHaveProperty('participant_count');
    expect(() => sameMeterSnapshot(70000, 'bad date')).toThrow(RangeError);
  });
  it('updates assumptions without network writes and handles the equal-world boundary', () => {
    const request = vi.spyOn(globalThis, 'fetch');
    render(<SameMeterChallenge />);
    const slider = screen.getByRole('slider', { name: /World B: second-hour demand/ });
    fireEvent.change(slider, { target: { value: '70000' } });
    expect(slider).toHaveAttribute('aria-valuetext', '70 gigawatts');
    expect(screen.getByText(/Applied input: 70 GW/)).toBeInTheDocument();
    expect(screen.getByText('25,000 MWh')).toBeInTheDocument();
    fireEvent.change(slider, { target: { value: '45000' } });
    expect(screen.getByText(/Applied input: 45 GW/)).toBeInTheDocument();
    expect(screen.getByText(/At 45 GW, both worlds serve all demand/)).toBeInTheDocument();
    expect(request).not.toHaveBeenCalled();
    request.mockRestore();
  });
  it('keeps the interpretation behind an explicit reveal control', () => {
    render(<SameMeterChallenge />);
    const disclosure = screen.getByText('Reveal the interpretation after recording your own').closest('details');
    expect(disclosure).not.toBeNull();
    expect(disclosure).not.toHaveAttribute('open');
  });
  it('provides a copy-from-table fallback when download is unavailable', () => {
    const create = vi.fn(() => { throw new Error('downloads disabled'); });
    vi.stubGlobal('URL', { createObjectURL: create });
    render(<SameMeterChallenge />);
    fireEvent.click(screen.getByRole('button', { name: 'Download this model snapshot' }));
    expect(screen.getByText(/Download unavailable/)).toBeInTheDocument();
    expect(screen.getByRole('table')).toBeInTheDocument();
    vi.unstubAllGlobals();
  });
  it('requests one local download and revokes its temporary URL', () => {
    vi.useFakeTimers();
    const create = vi.fn(() => 'blob:local-model');
    const revoke = vi.fn();
    vi.stubGlobal('URL', { createObjectURL: create, revokeObjectURL: revoke });
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    render(<SameMeterChallenge />);
    fireEvent.click(screen.getByRole('button', { name: 'Download this model snapshot' }));
    expect(create).toHaveBeenCalledOnce();
    expect(click).toHaveBeenCalledOnce();
    expect(screen.getByText(/Download requested/)).toBeInTheDocument();
    vi.runAllTimers();
    expect(revoke).toHaveBeenCalledWith('blob:local-model');
    expect(document.querySelector('a[download]')).toBeNull();
    click.mockRestore();
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });
});
