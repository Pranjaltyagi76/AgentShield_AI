import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, expect, it, vi } from 'vitest'
import { CustomScenarios } from './CustomScenarios'
import { guestKey } from './lib/workspace'

afterEach(() => {
  sessionStorage.clear()
  vi.unstubAllGlobals()
})
function mount() {
  return render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })}
    >
      <MemoryRouter>
        <CustomScenarios />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}
it('validates the exact current draft before creating and appending immutable versions', async () => {
  sessionStorage.setItem(guestKey, 'test-owner')
  const sid = 'CS-' + 'a'.repeat(32)
  const versions: Record<string, unknown>[] = []
  const posts: { path: string; body: Record<string, unknown> }[] = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, init: RequestInit) => {
      expect(new Headers(init.headers).get('Authorization')).toBe('Bearer test-owner')
      const path = url.replace('/api/v1', '')
      if (init.method === 'POST') {
        const body = JSON.parse(String(init.body))
        posts.push({ path, body })
        if (path.endsWith('/validate'))
          return Response.json({ valid: true, definition_hash: 'hash', runtime_context_bytes: 140 })
        const version = {
          ...body,
          scenario_id: sid,
          version: versions.length + 1,
          definition_hash: 'hash',
        }
        versions.unshift(version)
        return Response.json(
          path.endsWith('/versions') ? version : { id: sid, versions: [version] },
          { status: 201 },
        )
      }
      if (path === '/custom-scenarios')
        return Response.json(
          versions.length
            ? [
                {
                  id: sid,
                  name: 'My synthetic check',
                  version: versions.length,
                  checker: 'label_match',
                },
              ]
            : [],
        )
      if (path === '/custom-scenarios/' + sid) return Response.json({ id: sid, versions })
      throw Error('Unexpected path ' + path)
    }),
  )
  mount()
  await userEvent.type(screen.getByLabelText('Scenario name'), 'My synthetic check')
  expect(screen.getByRole('button', { name: 'Save custom scenario' })).toBeDisabled()
  await userEvent.click(screen.getByRole('button', { name: 'Validate draft' }))
  await screen.findByText(/Draft validated/)
  await userEvent.clear(screen.getByLabelText('Trusted label'))
  await userEvent.type(screen.getByLabelText('Trusted label'), 'violet')
  expect(screen.getByRole('button', { name: 'Save custom scenario' })).toBeDisabled()
  await userEvent.click(screen.getByRole('button', { name: 'Validate draft' }))
  await waitFor(() =>
    expect(screen.getByRole('button', { name: 'Save custom scenario' })).toBeEnabled(),
  )
  await userEvent.click(screen.getByRole('button', { name: 'Save custom scenario' }))
  await screen.findByText(/Scenario version saved/)
  await userEvent.click(await screen.findByText('Version 1 · My synthetic check'))
  await userEvent.click(screen.getByRole('button', { name: 'Use version 1 as draft' }))
  expect(screen.getByLabelText('Trusted label')).toHaveValue('violet')
  await userEvent.clear(screen.getByLabelText('Untrusted label'))
  await userEvent.type(screen.getByLabelText('Untrusted label'), 'gold')
  await userEvent.click(screen.getByRole('button', { name: 'Validate draft' }))
  await waitFor(() =>
    expect(screen.getByRole('button', { name: 'Save scenario version' })).toBeEnabled(),
  )
  await userEvent.click(screen.getByRole('button', { name: 'Save scenario version' }))
  await screen.findByText('Version 2 · My synthetic check')
  expect(posts.filter((post) => !post.path.endsWith('/validate'))).toHaveLength(2)
  expect(posts.at(-1)?.path).toBe('/custom-scenarios/' + sid + '/versions')
  expect(versions[1].definition).toMatchObject({
    trusted_label: 'violet',
    untrusted_label: 'copper',
  })
})

it('keeps rejected schemas unsaved and switches only between registered checker fields', async () => {
  sessionStorage.setItem(guestKey, 'test-owner')
  const fetcher = vi.fn(async (_url: string, init: RequestInit) =>
    init.method === 'POST' ? new Response('{}', { status: 422 }) : Response.json([]),
  )
  vi.stubGlobal('fetch', fetcher)
  mount()
  await userEvent.type(screen.getByLabelText('Scenario name'), 'Synthetic guide')
  await userEvent.selectOptions(screen.getByLabelText('Registered checker'), 'guide_completion')
  expect(screen.queryByLabelText('Trusted label')).toBeNull()
  expect(screen.getByRole('checkbox', { name: 'Allow search_docs' })).toBeChecked()
  await userEvent.click(screen.getByRole('button', { name: 'Validate draft' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('registered checker')
  expect(screen.getByRole('button', { name: 'Save custom scenario' })).toBeDisabled()
  expect(fetcher.mock.calls.filter(([, init]) => init.method === 'POST')).toHaveLength(1)
})
