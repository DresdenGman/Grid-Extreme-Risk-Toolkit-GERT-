import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Patch process.env before importing the module
const originalEnv = { ...process.env }

function setEnv(key: string, value: string | undefined) {
  if (value === undefined) {
    delete (process.env as Record<string, string | undefined>)[key]
  } else {
    process.env[key] = value
  }
}

describe('API Client (lib/api.ts)', () => {
  let api: any
  let fetchSpy: ReturnType<typeof vi.fn>

  beforeEach(async () => {
    // Reset env
    process.env = { ...originalEnv }
    vi.resetModules()
    // Mock global fetch
    fetchSpy = vi.fn()
    global.fetch = fetchSpy
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  async function loadApi() {
    const mod = await import('../../lib/api')
    api = mod.api
  }

  // --- Demo mode ---
  describe('demo mode', () => {
    it('returns mock data without calling fetch', async () => {
      setEnv('NEXT_PUBLIC_DATA_MODE', 'demo')
      await loadApi()

      fetchSpy.mockResolvedValue(new Response('{}', { status: 200 }))
      const result = await api.predict({ region: 'ERCOT_NORTH', date: '2026-01-01', weather_features: { temperature: 20, wind_speed: 10, solar_irradiance: 500 } })

      expect(result.source).toBe('simulated_demo')
      expect(result.data.risk_level).toBe('EXTREME')
      expect(fetchSpy).not.toHaveBeenCalled()
    })
  })

  // --- Live mode success ---
  describe('live mode success', () => {
    it('returns live_api source on 200', async () => {
      setEnv('NEXT_PUBLIC_DATA_MODE', 'live')
      setEnv('NEXT_PUBLIC_API_URL', 'http://test.local')
      await loadApi()

      fetchSpy.mockResolvedValue(new Response(JSON.stringify({
        timestamp: '2026-01-01T00:00:00Z',
        q50_load_mw: 40000, q90_load_mw: 42000, q95_load_mw: 43000, q99_load_mw: 44000,
        risk_level: 'LOW', risk_score: 10, diagnostics: { input_region: 'ERCOT_NORTH', model_version: 'test', backend_type: 'stub', capacity_used: 65000 }
      }), { status: 200 }))

      const result = await api.predict({ region: 'ERCOT_NORTH', date: '2026-01-01', weather_features: { temperature: 20, wind_speed: 10, solar_irradiance: 500 } })

      expect(result.source).toBe('live_api')
      expect(result.data.risk_level).toBe('LOW')
    })
  })

  // --- Network failure ---
  describe('network failure', () => {
    it('throws ApiClientError(network) on fetch failure', async () => {
      setEnv('NEXT_PUBLIC_DATA_MODE', 'live')
      setEnv('NEXT_PUBLIC_API_URL', 'http://test.local')
      await loadApi()

      fetchSpy.mockRejectedValue(new Error('Failed to fetch'))

      await expect(api.predict({ region: 'ERCOT_NORTH', date: '2026-01-01', weather_features: { temperature: 20, wind_speed: 10, solar_irradiance: 500 } }))
        .rejects.toThrow(/Cannot reach/)
    })
  })

  // --- Timeout ---
  describe('timeout', () => {
    it('throws ApiClientError(timeout) on abort', async () => {
      setEnv('NEXT_PUBLIC_DATA_MODE', 'live')
      setEnv('NEXT_PUBLIC_API_URL', 'http://test.local')
      await loadApi()

      const abortError = new Error('The operation was aborted')
      abortError.name = 'AbortError'
      fetchSpy.mockRejectedValue(abortError)

      await expect(api.predict({ region: 'ERCOT_NORTH', date: '2026-01-01', weather_features: { temperature: 20, wind_speed: 10, solar_irradiance: 500 } }))
        .rejects.toThrow(/timed out/)
    })
  })

  // --- Rate limit ---
  describe('rate limit', () => {
    it('throws ApiClientError(rate_limit) on 429', async () => {
      setEnv('NEXT_PUBLIC_DATA_MODE', 'live')
      setEnv('NEXT_PUBLIC_API_URL', 'http://test.local')
      await loadApi()

      fetchSpy.mockResolvedValue(new Response('', { status: 429 }))

      await expect(api.predict({ region: 'ERCOT_NORTH', date: '2026-01-01', weather_features: { temperature: 20, wind_speed: 10, solar_irradiance: 500 } }))
        .rejects.toHaveProperty('kind', 'rate_limit')
    })
  })

  // --- HTTP error ---
  describe('HTTP error', () => {
    it('throws ApiClientError(http) on 500', async () => {
      setEnv('NEXT_PUBLIC_DATA_MODE', 'live')
      setEnv('NEXT_PUBLIC_API_URL', 'http://test.local')
      await loadApi()

      fetchSpy.mockResolvedValue(new Response('', { status: 500 }))

      await expect(api.predict({ region: 'ERCOT_NORTH', date: '2026-01-01', weather_features: { temperature: 20, wind_speed: 10, solar_irradiance: 500 } }))
        .rejects.toHaveProperty('kind', 'http')
    })
  })

  // --- Invalid JSON ---
  describe('invalid response', () => {
    it('throws on bad JSON', async () => {
      setEnv('NEXT_PUBLIC_DATA_MODE', 'live')
      setEnv('NEXT_PUBLIC_API_URL', 'http://test.local')
      await loadApi()

      // Return invalid JSON that fetch.json() fails on
      const badResponse = {
        ok: true,
        json: vi.fn().mockRejectedValue(new Error('Invalid JSON')),
        status: 200,
      }
      fetchSpy.mockResolvedValue(badResponse)

      const { ApiClientError } = await import('../../lib/types')
      await expect(api.health()).rejects.toBeInstanceOf(ApiClientError)
    })
  })

  // --- No mock substitution in live mode ---
  describe('no silent mock in live mode', () => {
    it('never returns mock data on failure', async () => {
      setEnv('NEXT_PUBLIC_DATA_MODE', 'live')
      setEnv('NEXT_PUBLIC_API_URL', 'http://test.local')
      await loadApi()

      fetchSpy.mockRejectedValue(new Error('Failed to fetch'))

      const result = api.predict({ region: 'ERCOT_NORTH', date: '2026-01-01', weather_features: { temperature: 20, wind_speed: 10, solar_irradiance: 500 } })
      await expect(result).rejects.toThrow()
      // Verify no mock data returned
      try { await result } catch (e: any) {
        expect(e).not.toHaveProperty('source', 'simulated_demo')
      }
    })
  })

  // --- Default mode is live ---
  describe('default mode', () => {
    it('defaults to live when NEXT_PUBLIC_DATA_MODE is unset', async () => {
      setEnv('NEXT_PUBLIC_DATA_MODE', undefined)
      setEnv('NEXT_PUBLIC_API_URL', 'http://test.local')
      await loadApi()

      fetchSpy.mockRejectedValue(new Error('Failed to fetch'))
      await expect(api.predict({ region: 'ERCOT_NORTH', date: '2026-01-01', weather_features: { temperature: 20, wind_speed: 10, solar_irradiance: 500 } }))
        .rejects.toThrow()
    })
  })
})
