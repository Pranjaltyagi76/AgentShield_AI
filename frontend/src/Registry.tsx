import { useState, type FormEvent } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { API_BASE, ApiError } from './lib/api'

const key = 'agentshield.guest'
type Profile = { id: string; name: string; description: string; is_shared: boolean }
type Version = {
  version_number: number
  demo_profile: string
  system_prompt: string
  prompt_hash: string
  tool_config_json: string[]
}
type Scenario = {
  id: string
  name: string
  description: string
  category: string
  severity: string
  version: number
}

async function api<T>(path: string, method = 'GET', data?: unknown, auth = false): Promise<T> {
  const token = auth ? sessionStorage.getItem(key) : null
  const r = await fetch(API_BASE + path, {
    method,
    credentials: 'omit',
    signal: AbortSignal.timeout(10000),
    headers: {
      ...(token ? { Authorization: 'Bearer ' + token } : {}),
      ...(data ? { 'Content-Type': 'application/json' } : {}),
    },
    body: data ? JSON.stringify(data) : undefined,
  })
  if (r.status === 401 && token && sessionStorage.getItem(key) === token)
    sessionStorage.removeItem(key)
  if (!r.ok)
    throw new ApiError(
      (
        {
          401: 'Your guest session has ended.',
          403: 'Shared profiles are read-only.',
          404: 'Record unavailable.',
          409: 'Workspace limit reached.',
          422: 'Check the form values and prompt length.',
          429: 'Too many workspaces requested. Try again in ten minutes.',
          503: 'Workspace storage is unavailable. Try again later.',
        } as Record<number, string>
      )[r.status] ?? 'Request failed.',
      r.status,
    )
  return r.status === 204 ? (undefined as T) : r.json()
}
function problem(e: unknown) {
  return e instanceof Error ? e.message : 'Unable to connect.'
}

export function Scenarios() {
  const [q, setQ] = useState(''),
    [category, setCategory] = useState(''),
    [id, select] = useState('')
  const list = useQuery({ queryKey: ['catalog'], queryFn: () => api<Scenario[]>('/scenarios') })
  const detail = useQuery({
    queryKey: ['scenario', id],
    enabled: !!id,
    queryFn: () => api<Scenario>('/scenarios/' + encodeURIComponent(id)),
  })
  const items = list.data ?? [],
    visible = items.filter(
      (x) =>
        (!category || x.category === category) &&
        (x.id + ' ' + x.name).toLowerCase().includes(q.toLowerCase()),
    )
  return (
    <section className="registry">
      <div className="eyebrow">CURATED CATALOG</div>
      <h1>Scenarios</h1>
      <p>Browse the twelve definitions in Core v1. The scripted API supports selected fixtures.</p>
      <label>
        Search by name or ID
        <input value={q} onChange={(e) => setQ(e.target.value)} />
      </label>
      <label>
        Category
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">All categories</option>
          {[...new Set(items.map((x) => x.category))].map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
      </label>
      {list.isPending ? (
        'Loading scenarios…'
      ) : list.error ? (
        <p role="alert">
          {problem(list.error)} <button onClick={() => list.refetch()}>Retry</button>
        </p>
      ) : visible.length === 0 ? (
        'No matching scenarios.'
      ) : (
        <ul>
          {visible.map((x) => (
            <li key={x.id}>
              <button onClick={() => select(x.id)}>
                {x.id} · {x.name}
              </button>{' '}
              {x.category}
            </li>
          ))}
        </ul>
      )}
      {id && (
        <article className="surface">
          {detail.error ? (
            problem(detail.error)
          ) : detail.data ? (
            <>
              <h2>{detail.data.name}</h2>
              <p>{detail.data.description}</p>
              <small>
                Version {detail.data.version} · {detail.data.severity} severity
              </small>
            </>
          ) : (
            'Loading definition…'
          )}
        </article>
      )}
    </section>
  )
}

export function Agents() {
  const client = useQueryClient(),
    [active, setActive] = useState(() => !!sessionStorage.getItem(key)),
    [id, select] = useState(''),
    [busy, setBusy] = useState(false),
    [error, setError] = useState('')
  const [epoch, setEpoch] = useState(0)
  const list = useQuery({
    queryKey: ['registry', epoch, active],
    queryFn: () => api<Profile[]>('/agents', 'GET', undefined, true),
    retry: false,
    gcTime: 0,
    refetchOnMount: 'always',
  })
  const detail = useQuery({
    queryKey: ['profile', epoch, id],
    enabled: !!id,
    queryFn: () => api<Profile & { versions: Version[] }>('/agents/' + id, 'GET', undefined, true),
    retry: false,
    gcTime: 0,
  })
  const session = useQuery({
    queryKey: ['session', epoch],
    enabled: active,
    queryFn: () => api<{ expires_at: string }>('/guest-session', 'GET', undefined, true),
    retry: false,
    gcTime: 0,
  })
  const fault = list.error || detail.error || session.error
  const expired = fault instanceof ApiError && fault.status === 401
  function reset() {
    sessionStorage.removeItem(key)
    client.removeQueries({
      predicate: (q) => ['registry', 'profile', 'session'].includes(String(q.queryKey[0])),
    })
    setActive(false)
    select('')
    setEpoch((x) => x + 1)
    setError('')
  }
  async function act(work: () => Promise<void>) {
    setBusy(true)
    setError('')
    try {
      await work()
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) reset()
      setError(problem(e))
    } finally {
      setBusy(false)
    }
  }
  function submit(e: FormEvent<HTMLFormElement>, mode: 'new' | 'edit' | 'version') {
    e.preventDefault()
    const form = e.currentTarget,
      f = new FormData(form)
    const meta = { name: f.get('name'), description: f.get('description') }
    const cfg = {
      demo_profile: f.get('profile'),
      system_prompt: f.get('prompt'),
      allowed_tools: f.getAll('tool'),
    }
    void act(async () => {
      if (mode === 'new') {
        const a = await api<Profile>('/agents', 'POST', { ...meta, configuration: cfg }, true)
        select(a.id)
        form.reset()
      } else if (mode === 'edit') await api('/agents/' + id, 'PATCH', meta, true)
      else await api('/agents/' + id + '/versions', 'POST', cfg, true)
      await client.invalidateQueries({ queryKey: ['registry'] })
      await client.invalidateQueries({ queryKey: ['profile'] })
    })
  }
  const config = (v?: Version) => (
    <>
      <label>
        Scripted behavior
        <select name="profile" defaultValue={v?.demo_profile ?? 'hardened'}>
          <option>hardened</option>
          <option>vulnerable</option>
        </select>
      </label>
      <label>
        System prompt
        <textarea
          name="prompt"
          required
          maxLength={16384}
          defaultValue={v?.system_prompt ?? 'Use synthetic workspace records only.'}
        />
      </label>
      <fieldset>
        <legend>Allowed mock tools</legend>
        {[
          'search_docs',
          'get_customer_record',
          'send_message_simulated',
          'export_file_simulated',
        ].map((t) => (
          <label key={t}>
            <input
              type="checkbox"
              name="tool"
              value={t}
              defaultChecked={v?.tool_config_json.includes(t)}
            />
            {t}
          </label>
        ))}
      </fieldset>
    </>
  )
  const meta = (a?: Profile) => (
    <>
      <label>
        Name
        <input name="name" required maxLength={80} defaultValue={a?.name} />
      </label>
      <label>
        Description
        <input name="description" maxLength={512} defaultValue={a?.description} />
      </label>
    </>
  )
  const a = detail.data
  return (
    <section className="registry">
      <div className="eyebrow">GUEST WORKSPACE</div>
      <h1>Agents</h1>
      <p>Browse shared examples or open a seven-day workspace to save private profiles.</p>
      {(error || fault) && <p role="alert">{error || problem(fault)}</p>}
      {expired ? (
        <button onClick={reset}>Clear expired workspace</button>
      ) : active ? (
        <>
          <p>{session.data && 'Expires ' + new Date(session.data.expires_at).toLocaleString()}</p>
          <button
            disabled={busy}
            onClick={() =>
              act(async () => {
                await api('/guest-session', 'DELETE', undefined, true)
                reset()
              })
            }
          >
            End workspace and delete profiles
          </button>
        </>
      ) : (
        <button
          disabled={busy}
          onClick={() =>
            act(async () => {
              const s = await api<{ credential: string }>('/guest-sessions', 'POST')
              sessionStorage.setItem(key, s.credential)
              select('')
              setActive(true)
              setEpoch((x) => x + 1)
            })
          }
        >
          Start guest workspace
        </button>
      )}
      {!expired && (
        <>
          <h2>Profiles</h2>
          {list.isPending ? (
            'Loading profiles…'
          ) : (
            <ul>
              {list.data?.map((x) => (
                <li key={x.id}>
                  <button onClick={() => select(x.id)}>{x.name}</button>{' '}
                  {x.is_shared ? 'Shared · read-only' : 'Private'}
                </li>
              ))}
            </ul>
          )}
          {active && (
            <details>
              <summary>Create private profile</summary>
              <form onSubmit={(e) => submit(e, 'new')}>
                {meta()}
                {config()}
                <button disabled={busy}>Create profile</button>
              </form>
            </details>
          )}
          {id && a && !detail.error && (
            <article className="surface" key={id}>
              <h2>{a.name}</h2>
              <p>{a.description}</p>
              {!a.is_shared && (
                <details>
                  <summary>Edit profile</summary>
                  <form onSubmit={(e) => submit(e, 'edit')}>
                    {meta(a)}
                    <button disabled={busy}>Save metadata</button>
                  </form>
                </details>
              )}
              <h3>Version history</h3>
              {a.versions.map((v) => (
                <details key={v.version_number}>
                  <summary>
                    Version {v.version_number} · {v.demo_profile}
                  </summary>
                  <p>{v.system_prompt}</p>
                  <small>Prompt SHA-256: {v.prompt_hash}</small>
                </details>
              ))}
              {active && (
                <details>
                  <summary>{a.is_shared ? 'Copy into my workspace' : 'Add version'}</summary>
                  <form onSubmit={(e) => submit(e, a.is_shared ? 'new' : 'version')}>
                    {a.is_shared && meta({ ...a, name: a.name + ' copy' })}
                    {config(a.versions[0])}
                    <button disabled={busy}>
                      {a.is_shared ? 'Create private copy' : 'Save new version'}
                    </button>
                  </form>
                </details>
              )}
            </article>
          )}
        </>
      )}
    </section>
  )
}
