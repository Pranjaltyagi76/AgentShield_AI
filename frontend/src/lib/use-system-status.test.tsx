import { act, renderHook } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { afterEach, expect, it, vi } from 'vitest'
import { useSystemStatus } from './use-system-status'

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})
it.each([false, true])(
  'bounds readiness checks when the API fails after a not-ready response: %s',
  async (fail) => {
    vi.useFakeTimers()
    let checks = 0
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        if (url.endsWith('/health'))
          return Response.json({ status: 'ok', service: 'api', version: 'test', phase: 8 })
        checks++
        if (fail && checks > 1) throw Error('offline')
        return Response.json(
          { status: 'not_ready', database: 'unavailable', service: 'api', phase: 8 },
          { status: 503 },
        )
      }),
    )
    const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })
    const mounted = renderHook(() => useSystemStatus(), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={client}>{children}</QueryClientProvider>
      ),
    })
    for (let i = 0; i < 5; i++) {
      await act(async () => {
        await vi.advanceTimersByTimeAsync(3000)
      })
    }
    expect(checks).toBe(fail ? 2 : 3)
    mounted.unmount()
    client.clear()
  },
)
