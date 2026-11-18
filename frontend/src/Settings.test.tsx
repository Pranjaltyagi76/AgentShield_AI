import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, expect, it, vi } from 'vitest'
import { Settings } from './Settings'
import { Runs } from './Runs'
import { guestKey } from './lib/workspace'
import { defaultDemoProfile } from './lib/preferences'

afterEach(() => {
  sessionStorage.clear()
  vi.unstubAllGlobals()
})
it('saves a tab default used by the launcher while leaving the provider demo-only', async () => {
  sessionStorage.setItem(guestKey, 'test-owner')
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => {
      const path = url.replace('/api/v1', '')
      if (path === '/demo/status')
        return Response.json({
          execution_enabled: true,
          requires_api_key: false,
          inference: {
            provider: 'gemini',
            enabled: false,
            reason: 'free_account_access_unverified',
          },
          limits: { scenarios_per_run: 12, custom_scenarios_per_guest: 8 },
        })
      if (path === '/guest-session') return Response.json({ expires_at: '2026-11-25T00:00:00Z' })
      if (path === '/agents')
        return Response.json([
          { id: 'hard', name: 'Hardened demo', is_shared: true },
          { id: 'weak', name: 'Vulnerable demo', is_shared: true },
        ])
      if (path.startsWith('/agents/'))
        return Response.json({
          versions: [
            { id: 'v1', version_number: 1, demo_profile: 'vulnerable', tool_config_json: [] },
          ],
        })
      if (path === '/scenario-suites') return Response.json([{ id: 'core-v2', members: [] }])
      return Response.json([])
    }),
  )
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })}
    >
      <MemoryRouter initialEntries={['/settings']}>
        <Routes>
          <Route path="/settings" element={<Settings />} />
          <Route
            path="/runs"
            element={
              <Runs
                health={{
                  status: 'ok',
                  service: 'test',
                  version: 'test',
                  phase: 8,
                  run_mode: 'public',
                }}
                healthError={false}
                refresh={() => {}}
              />
            }
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
  expect(await screen.findByText(/Gemini: disabled/)).toBeVisible()
  expect(screen.getByText('Custom scenarios per guest')).toBeVisible()
  expect(screen.queryByLabelText(/API key/)).toBeNull()
  await userEvent.selectOptions(screen.getByLabelText('Default demo profile'), 'vulnerable')
  await userEvent.click(screen.getByRole('button', { name: 'Save demo preference' }))
  expect(defaultDemoProfile()).toBe('vulnerable')
  await userEvent.click(screen.getByRole('link', { name: 'Open benchmark runs' }))
  expect(
    await screen.findByRole('option', { name: 'Vulnerable demo · Shared' }),
  ).toBeInTheDocument()
  expect(screen.getByLabelText('Agent profile')).toHaveValue('weak')
})

it('keeps local preferences usable during a provider-status outage', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => {
      throw Error('offline')
    }),
  )
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <MemoryRouter>
        <Settings />
      </MemoryRouter>
    </QueryClientProvider>,
  )
  expect(await screen.findByRole('button', { name: 'Retry provider status' })).toBeVisible()
  await userEvent.selectOptions(screen.getByLabelText('Default demo profile'), 'vulnerable')
  await userEvent.click(screen.getByRole('button', { name: 'Save demo preference' }))
  expect(screen.getByText('Default demo profile saved for this tab.')).toBeVisible()
})
