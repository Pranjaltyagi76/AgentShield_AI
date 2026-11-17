import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, expect, it, vi } from 'vitest'
import { ReportDownloads, Reports } from './Reports'
import { guestKey } from './lib/workspace'

afterEach(() => {
  sessionStorage.clear()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})
function mount(page: React.ReactNode) {
  return render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })}
    >
      <MemoryRouter>{page}</MemoryRouter>
    </QueryClientProvider>,
  )
}
it('creates an owned comparison export and downloads it with authorization only in headers', async () => {
  sessionStorage.setItem(guestKey, 'test-credential')
  const createObjectURL = vi.fn(() => 'blob:test-report')
  vi.stubGlobal(
    'URL',
    class extends URL {
      static createObjectURL = createObjectURL
      static revokeObjectURL = vi.fn()
    },
  )
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
  const fetcher = vi.fn(async (url: string, init: RequestInit) => {
    expect(url).not.toContain('test-credential')
    expect(new Headers(init.headers).get('Authorization')).toBe('Bearer test-credential')
    if (url.endsWith('/runs/run-id/reports')) {
      expect(JSON.parse(String(init.body))).toEqual({
        format: 'json',
        comparison_id: 'comparison-id',
      })
      return Response.json({ id: 'report-id', format: 'json' })
    }
    if (url.endsWith('/reports/report-id/download'))
      return new Response('{"redacted":true}', { headers: { 'Content-Type': 'application/json' } })
    throw Error('Unexpected request')
  })
  vi.stubGlobal('fetch', fetcher)
  mount(<ReportDownloads runId="run-id" comparisonId="comparison-id" />)
  await userEvent.click(screen.getByRole('button', { name: 'Download JSON report' }))
  expect(await screen.findByText('Report download prepared.')).toBeVisible()
  expect(createObjectURL).toHaveBeenCalledOnce()
})
it('shows an expired source failure without claiming a successful export', async () => {
  sessionStorage.setItem(guestKey, 'test-credential')
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => new Response('{}', { status: 404 })),
  )
  mount(<ReportDownloads runId="gone" />)
  await userEvent.click(screen.getByRole('button', { name: 'Download HTML report' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Report or source run unavailable')
  expect(screen.queryByText('Report download prepared.')).toBeNull()
})
it('keeps the saved sample accessible without a guest session', () => {
  mount(<Reports />)
  expect(screen.getByRole('link', { name: 'Open saved sample' })).toHaveAttribute('href', '/sample')
  expect(screen.getByText(/Start a guest workspace to create reports/)).toBeVisible()
})
