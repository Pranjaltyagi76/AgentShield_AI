import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import { Agents, Scenarios } from './Registry'

function mount(page: React.ReactNode) {
  return render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      {page}
    </QueryClientProvider>,
  )
}
afterEach(() => {
  sessionStorage.clear()
  vi.unstubAllGlobals()
})
it('clears expired credentials and lets the visitor return to shared profiles', async () => {
  sessionStorage.setItem('agentshield.guest', 'expired-test-token')
  vi.stubGlobal(
    'fetch',
    vi.fn(
      async (_url: string, init: RequestInit) =>
        new Response(
          JSON.stringify(
            init.headers && 'Authorization' in init.headers
              ? {}
              : [{ id: 'shared', name: 'Hardened demo', is_shared: true }],
          ),
          { status: init.headers && 'Authorization' in init.headers ? 401 : 200 },
        ),
    ),
  )
  mount(<Agents />)
  await userEvent.click(await screen.findByRole('button', { name: 'Clear expired workspace' }))
  expect(sessionStorage.getItem('agentshield.guest')).toBeNull()
  expect(await screen.findByRole('button', { name: 'Hardened demo' })).toBeVisible()
  expect(screen.getByRole('button', { name: 'Start guest workspace' })).toBeVisible()
})
it('filters definitions and retrieves the selected scenario without a credential', async () => {
  const records = [
    {
      id: 'AS-011',
      name: 'Routine request',
      category: 'Reliability',
      severity: 'low',
      version: 1,
      description: 'Synthetic task.',
    },
    {
      id: 'AS-003',
      name: 'Private marker',
      category: 'Disclosure',
      severity: 'high',
      version: 1,
      description: 'Private marker.',
    },
  ]
  const fetcher = vi.fn(
    async (url: string) =>
      new Response(JSON.stringify(url.endsWith('/AS-011') ? records[0] : records)),
  )
  vi.stubGlobal('fetch', fetcher)
  mount(<Scenarios />)
  await screen.findByRole('button', { name: /AS-003/ })
  await userEvent.selectOptions(screen.getByLabelText('Category'), 'Reliability')
  expect(screen.queryByRole('button', { name: /AS-003/ })).toBeNull()
  await userEvent.click(screen.getByRole('button', { name: /AS-011/ }))
  expect(await screen.findByText('Synthetic task.')).toBeVisible()
})
