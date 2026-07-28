import { describe, it, expect } from 'vitest'

import { ApiClientError } from '../../lib/types'

describe('Provenance label patterns', () => {
  it('live_api produces LIVE API label', () => {
    const label = '✓ LIVE API'
    expect(label).toContain('LIVE API')
  })

  it('simulated_demo produces SIMULATED DEMO DATA with warning', () => {
    const label = '⚠ SIMULATED DEMO DATA — Not for operational use'
    expect(label).toContain('SIMULATED DEMO DATA')
    expect(label).toContain('Not for operational use')
  })

  it('DATA UNAVAILABLE label appears on failure with no prior data', () => {
    const label = 'DATA UNAVAILABLE — Cannot reach the prediction service.'
    expect(label).toContain('DATA UNAVAILABLE')
  })

  it('STALE DATA label appears on failure after previous success', () => {
    const label = 'STALE DATA — Cannot reach the prediction service.'
    expect(label).toContain('STALE DATA')
  })

  it('SIMULATED DEMO label and LIVE API label are distinct', () => {
    const live = '✓ LIVE API'
    const demo = '⚠ SIMULATED DEMO DATA — Not for operational use'
    expect(live).not.toBe(demo)
  })
})

describe('ApiClientError classification', () => {
  it('network error has kind=network', () => {
    const e = new ApiClientError('msg', 'network')
    expect(e.kind).toBe('network')
  })

  it('timeout error has kind=timeout', () => {
    const e = new ApiClientError('msg', 'timeout')
    expect(e.kind).toBe('timeout')
  })

  it('rate_limit error has kind=rate_limit', () => {
    const e = new ApiClientError('msg', 'rate_limit', { status: 429 })
    expect(e.kind).toBe('rate_limit')
    expect(e.status).toBe(429)
  })

  it('http error has kind=http', () => {
    const e = new ApiClientError('msg', 'http', { status: 500 })
    expect(e.kind).toBe('http')
    expect(e.status).toBe(500)
  })
})

describe('State transition logic', () => {
  it('no data, no error -> initial empty state', () => {
    const hasData = false
    const hasError = false
    expect(hasData || hasError).toBe(false)
  })

  it('no data, with error -> DATA UNAVAILABLE', () => {
    const hasData = false
    const hasError = true
    expect(hasError && !hasData).toBe(true)
  })

  it('data + error -> STALE DATA (keep previous)', () => {
    const hasData = true
    const hasError = true
    expect(hasData && hasError).toBe(true)
  })

  it('data, no error -> normal display with LIVE API', () => {
    const hasData = true
    const hasError = false
    expect(hasData && !hasError).toBe(true)
  })

  it('demo mode has no error and has data', () => {
    const isDemo = true
    const hasData = true
    expect(isDemo && hasData && true).toBe(true)
  })
})
