import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, expect, it, vi } from 'vitest'
import App from './App'
afterEach(() => vi.unstubAllGlobals())
function renderApp(path = '/') {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string) => {
      const body = input.endsWith('/health')
        ? { status: 'ok', service: 'agentshield-api', version: '0.1.0', phase: 0 }
        : { status: 'not_ready', database: 'not_configured', service: 'agentshield-api', phase: 0 }
      return new Response(JSON.stringify(body), { status: input.endsWith('/health') ? 200 : 503 })
    }),
  )
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}
it('shows honest foundation status and actual connection results', async () => {
  renderApp()
  expect(screen.getByRole('heading', { name: /Test the boundaries/ })).toBeInTheDocument()
  expect(screen.getByText('No execution endpoints')).toBeInTheDocument()
  expect(await screen.findByText('Connected')).toBeInTheDocument()
  expect(await screen.findByText('Not configured')).toBeInTheDocument()
})
it('navigates to system setup and renders typed response evidence', async () => {
  renderApp()
  await userEvent.click(screen.getByRole('link', { name: /Review system setup/ }))
  expect(await screen.findByRole('heading', { name: 'API response inspector' })).toBeInTheDocument()
  expect(await screen.findByText(/"database": "not_configured"/)).toBeInTheDocument()
})
it('shows the planned roadmap without marking future phases complete', () => {
  renderApp('/roadmap')
  expect(screen.getByRole('heading', { name: /A deliberate path/ })).toBeInTheDocument()
  expect(screen.getByText('Phase 0 in progress')).toBeInTheDocument()
  expect(screen.getAllByText('Planned')).toHaveLength(10)
})
it('handles an unknown deep link with a working return link', () => {
  renderApp('/missing')
  expect(screen.getByRole('heading', { name: 'This page is not here.' })).toBeInTheDocument()
  expect(screen.getByRole('link', { name: /Back to overview/ })).toHaveAttribute('href', '/')
})

it('does not display stale health as connected after a failed refresh', async () => {
  renderApp()
  expect(await screen.findByText('Connected')).toBeInTheDocument()
  vi.mocked(fetch).mockRejectedValue(new TypeError('offline'))
  await userEvent.click(screen.getByRole('button', { name: 'Check connection' }))
  expect(await screen.findByText('Unreachable')).toBeInTheDocument()
  expect(screen.queryByText('Connected')).not.toBeInTheDocument()
})
