import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { Runs } from './Runs'
import type { Health } from './lib/api'
import { guestKey } from './lib/workspace'
import { rates, pollDelay, maxPolls, type Run } from './lib/runs'

const health: Health = {
  service: 'agentshield-api',
  version: 'test',
  status: 'ok',
  phase: 5,
  run_mode: 'local',
}
function mount(path = '/runs', mode: Health = health) {
  const page = <Runs health={mode} healthError={false} refresh={() => {}} />
  return render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/runs" element={page} />
          <Route path="/runs/:runId" element={page} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}
const run = {
  id: 'r1',
  version_id: 'v2',
  status: 'completed',
  reason: null,
  queued_at: '2026-11-19T00:00:00Z',
  config: {
    profile: 'hardened',
    suite_id: null,
    behavior_version: '2',
    scenarios: [{ id: 'AS-006', version: 2 }],
  },
}
const json = (data: unknown, status = 200, headers?: Record<string, string>) =>
  new Response(JSON.stringify(data), { status, headers })
function respond(path: string) {
  if (path === '/agents') return json([{ id: 'a', name: 'Hardened demo', is_shared: true }])
  if (path === '/agents/a')
    return json({
      versions: [
        {
          id: 'v2',
          version_number: 2,
          demo_profile: 'hardened',
          tool_config_json: ['send_message_simulated'],
        },
      ],
    })
  if (path === '/scenario-suites')
    return json([{ id: 'core-v2', members: [{ scenario_id: 'AS-006', version: 2 }] }])
  if (path === '/scenarios') return json([{ id: 'AS-006', name: 'Destination check' }])
  if (path.startsWith('/runs?')) return json([])
  if (path === '/runs/r1') return json(run)
  if (path.endsWith('/results'))
    return json([
      { scenario_id: 'AS-006', version: 2, status: 'completed', outcome: 'pass', steps: 2 },
    ])
  if (path.endsWith('/metrics'))
    return json({
      oracle_version: '1',
      blocked_attempts: 1,
      invalid_requests: 0,
      confirmation_required: 0,
      inconclusive: 0,
      ...Object.fromEntries(
        Object.keys(rates).map((k) => [
          k,
          { numerator: 0, denominator: 0, percent: null, excluded: 1 },
        ]),
      ),
    })
  if (path.endsWith('/findings'))
    return json([
      {
        scenario_id: 'AS-006',
        summary: 'Observed fixture finding.',
        severity: 'high',
        remediation: 'Inspect the policy.',
        sequence: 2,
        evidence_id: 'event2',
      },
    ])
  if (path.includes('/traces?'))
    return json([
      {
        id: 'event2',
        sequence: 2,
        scenario_id: 'AS-006',
        kind: 'policy_decision',
        payload: {
          decision: 'blocked',
          reason: 'destination_not_allowed',
          hidden_reasoning: 'private test text',
        },
      },
    ])
  throw Error('Unexpected test path ' + path)
}
beforeEach(() => sessionStorage.setItem(guestKey, 'fixture-credential'))
afterEach(() => {
  sessionStorage.clear()
  vi.unstubAllGlobals()
})
it('stops polling on errors, terminal statuses and the update ceiling', () => {
  const pending = { ...run, status: 'queued' } as Run
  expect(pollDelay(pending, false, maxPolls - 1)).toBe(2500)
  expect(pollDelay(pending, false, maxPolls)).toBe(false)
  expect(pollDelay(pending, true, 1)).toBe(false)
  expect(pollDelay({ ...pending, status: 'cancelled' }, false, 1)).toBe(false)
})
it('keeps the launcher unavailable on a disabled API', () => {
  const fetcher = vi.fn()
  vi.stubGlobal('fetch', fetcher)
  mount('/runs', { ...health, run_mode: 'disabled' })
  expect(screen.getByText(/Scripted execution is disabled/)).toBeVisible()
  expect(fetcher).not.toHaveBeenCalled()
})
it('retries a selected launch with its original idempotency key and exact approval', async () => {
  const posts: { body: string; key: string }[] = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, init: RequestInit) => {
      const path = url.replace('/api/v1', '')
      if (path === '/runs' && init.method === 'POST') {
        const h = new Headers(init.headers)
        expect(h.get('Authorization')).toBe('Bearer fixture-credential')
        posts.push({ body: String(init.body), key: h.get('Idempotency-Key')! })
        return posts.length === 1 ? json({}, 503, { 'Retry-After': '2' }) : json(run, 202)
      }
      return respond(path)
    }),
  )
  mount()
  await userEvent.selectOptions(screen.getByLabelText('Scenarios'), 'selected')
  expect(screen.getByRole('button', { name: 'Launch run' })).toBeDisabled()
  await userEvent.click(await screen.findByRole('checkbox', { name: /AS-006 · Destination check/ }))
  await userEvent.click(screen.getByRole('checkbox', { name: /Approve AS-006/ }))
  await userEvent.click(screen.getByRole('button', { name: 'Launch run' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Retry after 2 seconds')
  await userEvent.click(screen.getByRole('button', { name: 'Launch run' }))
  expect(await screen.findByRole('heading', { name: 'Run details' })).toBeVisible()
  expect(posts[0]).toEqual(posts[1])
  expect(posts[0].key).toBeTruthy()
  expect(JSON.parse(posts[0].body)).toMatchObject({
    agent_version_id: 'v2',
    scenarios: ['AS-006'],
    confirmation: { step: 1, scenario: 'AS-006' },
  })
  await userEvent.click(await screen.findByRole('link', { name: /View evidence/ }))
  await waitFor(() =>
    expect(document.querySelector('details.trace-target')).toHaveAttribute('open'),
  )
  expect(screen.getByText('destination_not_allowed')).toBeVisible()
  expect(screen.queryByText('private test text')).toBeNull()
  await userEvent.click(screen.getByText('All metrics and exclusions'))
  expect(screen.getAllByText('N/A')[0]).toBeVisible()
})
it('clears expired workspace data and presents a new guest action', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => json({}, 401)),
  )
  mount('/runs/r1')
  expect(await screen.findByText(/Your guest session has ended/)).toBeVisible()
  expect(sessionStorage.getItem(guestKey)).toBeNull()
  expect(screen.getByRole('button', { name: 'Start guest workspace' })).toBeVisible()
})
it('shows retained evidence on interruption and stops offering cancellation', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) =>
      url === '/api/v1/runs/r1'
        ? json({ ...run, status: 'failed', reason: 'interrupted' })
        : respond(url.replace('/api/v1', '')),
    ),
  )
  mount('/runs/r1')
  expect(await screen.findByText(/Execution was interrupted/)).toBeVisible()
  expect(screen.queryByRole('button', { name: 'Cancel run' })).toBeNull()
  expect(await screen.findByText('Policy decision')).toBeVisible()
})
