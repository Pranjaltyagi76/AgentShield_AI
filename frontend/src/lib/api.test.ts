import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, getHealth, getReadiness } from './api'
afterEach(() => vi.unstubAllGlobals())
describe('system API client', () => {
  it('accepts a healthy typed response', async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValue(
        new Response(
          JSON.stringify({ status: 'ok', service: 'agentshield-api', version: '0.1.0', phase: 0 }),
        ),
      )
    vi.stubGlobal('fetch', fetcher)
    expect((await getHealth()).status).toBe('ok')
    expect(fetcher.mock.calls[0][0]).toBe('/api/v1/health')
    expect(fetcher.mock.calls[0][1].credentials).toBe('omit')
  })
  it('treats 503 readiness as a known unavailable state', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            status: 'not_ready',
            database: 'unavailable',
            service: 'agentshield-api',
            phase: 0,
          }),
          { status: 503 },
        ),
      ),
    )
    expect((await getReadiness()).database).toBe('unavailable')
  })
  it('rejects malformed contracts instead of showing fake health', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: 'ok' }))),
    )
    await expect(getHealth()).rejects.toThrow('contract')
  })
  it('explains a wrong API address returning HTML', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('<html>frontend</html>')))
    await expect(getHealth()).rejects.toThrow('VITE_API_BASE_URL')
  })
  it('returns a safe message for network failure', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('private details')))
    await expect(getHealth()).rejects.toThrow('Cannot reach the API')
  })
  it('rejects unexpected HTTP errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 500 })))
    await expect(getHealth()).rejects.toBeInstanceOf(ApiError)
  })
})
