import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const originalEnv = { ...process.env };

describe('live ERCOT load', () => {
  beforeEach(() => {
    vi.resetModules();
    process.env = { ...originalEnv };
    delete process.env.ERCOT_API_USERNAME;
    delete process.env.ERCOT_API_PASSWORD;
    delete process.env.ERCOT_API_SUBSCRIPTION_KEY;
  });

  afterEach(() => {
    process.env = { ...originalEnv };
  });

  it('returns 503 and no load number when official load is unavailable', async () => {
    const { handleGertRequest } = await import('@/lib/server/gert');
    const response = await handleGertRequest(
      new Request('http://localhost/api/gert/load/current?region=ERCOT_SYSTEM'),
      ['load', 'current'],
    );

    expect(response.status).toBe(503);
    const body = await response.json();
    expect(body.error).toBe('live_load_unavailable');
    expect(String(body.detail).toLowerCase()).toContain('unavailable');
    expect(body.current_load_mw).toBeUndefined();
  });
});
