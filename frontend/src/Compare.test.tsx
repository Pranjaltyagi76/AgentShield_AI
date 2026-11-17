import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, expect, it, vi } from 'vitest'
import { Runs } from './Runs'
import { rates } from './lib/runs'
import { guestKey } from './lib/workspace'

function mount(path: string) {
  sessionStorage.setItem(guestKey, 'test-guest')
  const page = (
    <Runs
      comparison
      health={{
        status: 'ok',
        service: 'agentshield',
        version: 'test',
        phase: 6,
        run_mode: 'local',
      }}
      healthError={false}
      refresh={() => {}}
    />
  )
  return render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/compare/:comparisonId?" element={page} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}
const fraction = { numerator: 1, denominator: 2, percent: 50, excluded: 0 }
const source = {
  profile: 'vulnerable',
  coverage: fraction,
  behavior_version: '2',
  status: 'completed',
}
const snapshot = {
  id: 'saved',
  baseline: { ...source, id: 'first' },
  candidate: { ...source, id: 'second', profile: 'hardened' },
  counts: {
    improved: 1,
    regressed: 0,
    unchanged: 0,
    inconclusive: 1,
    incompatible: 0,
    unmatched: 0,
  },
  paired_evaluable: 1,
  paired_compatible: 2,
  action_counts: {},
  changes: ['profile'],
  settings_issues: [],
  metrics: Object.fromEntries(
    Object.keys(rates).map((k) => [k, { baseline: fraction, candidate: fraction, delta_pp: null }]),
  ),
  scenarios: [
    {
      scenario_id: 'AS-001',
      baseline: { version: 2, outcome: 'fail' },
      candidate: { version: 2, outcome: 'pass' },
      classification: 'improved',
      issues: [],
    },
    {
      scenario_id: 'AS-002',
      baseline: { version: 2, outcome: 'pass' },
      candidate: { version: 2, outcome: 'inconclusive', reason: 'interrupted' },
      classification: 'inconclusive',
      issues: [],
    },
  ],
}
afterEach(() => {
  sessionStorage.clear()
  vi.unstubAllGlobals()
})
it('selects distinct finished runs and loads the persisted comparison with scoped evidence links', async () => {
  let submitted
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, init: RequestInit) => {
      expect(new Headers(init.headers).get('Authorization')).toBe('Bearer test-guest')
      if (url.includes('/runs?'))
        return Response.json(
          ['first', 'second', 'active'].map((id) => ({
            id,
            status: id === 'active' ? 'running' : 'completed',
            queued_at: '2026-11-17T00:00:00Z',
            config: { profile: 'demo', scenarios: [] },
          })),
        )
      if (url.endsWith('/benchmarks/compare')) {
        submitted = JSON.parse(String(init.body))
        return Response.json(snapshot)
      }
      if (url.endsWith('/benchmarks/saved')) return Response.json(snapshot)
      throw Error('Unexpected request')
    }),
  )
  mount('/compare')
  const baseline = await screen.findByLabelText('Baseline')
  await screen.findAllByRole('option', { name: /first/ })
  expect(within(baseline).getByRole('option', { name: /active/ })).toBeDisabled()
  await userEvent.selectOptions(baseline, 'first')
  await userEvent.selectOptions(screen.getByLabelText('Candidate'), 'first')
  expect(screen.getByRole('button', { name: 'Compare runs' })).toBeDisabled()
  await userEvent.selectOptions(screen.getByLabelText('Candidate'), 'second')
  await userEvent.click(screen.getByRole('button', { name: 'Compare runs' }))
  expect(await screen.findByRole('heading', { name: 'Metric changes' })).toBeVisible()
  expect(submitted).toEqual({ baseline_run_id: 'first', candidate_run_id: 'second' })
  expect(screen.getByRole('link', { name: 'v2 · fail' })).toHaveAttribute(
    'href',
    '/runs/first?scenario=AS-001',
  )
  expect(screen.getAllByText('N/A').length).toBeGreaterThan(0)
  await userEvent.selectOptions(screen.getByLabelText('Show scenarios'), 'inconclusive')
  expect(screen.queryByText('AS-001')).toBeNull()
  expect(screen.getByText(/interrupted/)).toBeVisible()
})
it('handles an inaccessible comparison without rendering its data', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => new Response('{}', { status: 404 })),
  )
  mount('/compare/foreign')
  expect(await screen.findByRole('alert')).toHaveTextContent('Record unavailable')
  expect(screen.queryByText('Source runs')).toBeNull()
})
