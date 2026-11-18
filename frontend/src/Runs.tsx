import './runs.css'
import { useState, useSyncExternalStore } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Play, History, ArrowRight } from 'lucide-react'
import { Button } from './components/ui/button'
import type { Health } from './lib/api'
import { api, guestState, subscribeGuest, startGuest, problem } from './lib/workspace'
import { useRunRead, type Profile, type Scenario, type Version, type Run } from './lib/runs'
import { Compare } from './Compare'
import { RunDetail } from './RunDetail'
import { type CustomChoice } from './CustomScenarios'
import { defaultDemoProfile, subscribePreferences } from './lib/preferences'

export function Runs({
  health,
  healthError,
  comparison = false,
  refresh,
}: {
  comparison?: boolean
  health?: Health
  healthError: boolean
  refresh: () => void
}) {
  const session = useSyncExternalStore(subscribeGuest, guestState)
  const { runId, comparisonId } = useParams()
  const title = comparison ? 'Benchmark comparison' : 'Benchmark runs'
  const navigate = useNavigate()
  const issue = useMutation({ mutationFn: startGuest, retry: false })
  if (
    comparison &&
    health &&
    !healthError &&
    health.run_mode &&
    health.run_mode !== 'disabled' &&
    health.phase < 6
  )
    return (
      <section className="run-page">
        <h1>{title}</h1>
        <p>Open this workspace with a Phase 6 API to compare runs.</p>
      </section>
    )
  if (!health || healthError || !health.run_mode || health.run_mode === 'disabled')
    return (
      <section className="run-page">
        <h1>{title}</h1>
        <div className="surface run-panel" role="status">
          {healthError
            ? 'Cannot reach the API.'
            : !health
              ? 'Checking execution availability…'
              : !health.run_mode && health.phase >= 3
                ? 'Use a Phase 5 API to open the run workspace.'
                : 'Scripted execution is disabled on this API.'}
          <button className="run-inline" onClick={refresh}>
            Check again
          </button>
        </div>
      </section>
    )
  if (session !== 'active')
    return (
      <section className="run-page">
        <h1>{title}</h1>
        <div className="surface run-panel">
          <h2>Guest workspace</h2>
          <p>
            {session === 'expired'
              ? 'Your guest session has ended. Start a new workspace to run another benchmark.'
              : 'Start a seven-day guest workspace to launch benchmarks and keep their results in this tab.'}
          </p>
          <Button
            disabled={issue.isPending}
            onClick={() =>
              issue.mutate(undefined, {
                onSuccess: () => navigate(comparison ? '/compare' : '/runs', { replace: true }),
              })
            }
          >
            {issue.isPending ? 'Starting…' : 'Start guest workspace'}
          </Button>
          {issue.error && <p role="alert">{problem(issue.error)}</p>}
        </div>
      </section>
    )
  if (comparison) return <Compare key={comparisonId ?? 'select'} id={comparisonId} />
  return <Workspace key={runId ?? 'history'} runId={runId} />
}

function Workspace({ runId }: { runId?: string }) {
  const [scope] = useState(() => crypto.randomUUID())
  if (runId) return <RunDetail scope={scope} id={runId} />
  return (
    <section className="run-page">
      <header className="run-heading">
        <h1>Benchmark runs</h1>
        <p>Launch a scripted evaluation and inspect its recorded evidence.</p>
      </header>
      <Launcher scope={scope} />
      <RunHistory scope={scope} />
      <Link to="/compare">Compare benchmark runs</Link>
    </section>
  )
}

function Launcher({ scope }: { scope: string }) {
  const navigate = useNavigate()
  const preferred = useSyncExternalStore(subscribePreferences, defaultDemoProfile)
  const agents = useRunRead<Profile[]>(scope, '/agents')
  const suites = useRunRead<{ id: string; members: { scenario_id: string; version: number }[] }[]>(
    scope,
    '/scenario-suites',
  )
  const catalog = useRunRead<Scenario[]>(scope, '/scenarios')
  const authored = useRunRead<CustomChoice[]>(scope, '/custom-scenarios')
  const [revisions, setRevisions] = useState<Record<string, number>>({})
  const [agentId, setAgent] = useState(''),
    [versionId, setVersion] = useState('')
  const [selected, setSelected] = useState<string[]>([]),
    [custom, setCustom] = useState(false),
    [confirm, setConfirm] = useState(false)
  const agent =
    agentId ||
    agents.data?.find((a) => a.is_shared && a.name.toLowerCase().includes(preferred))?.id ||
    agents.data?.[0]?.id ||
    ''
  const detail = useRunRead<{ versions: Version[] }>(
    scope,
    '/agents/' + encodeURIComponent(agent),
    !!agent,
  )
  const version = detail.data?.versions.find((v) => v.id === versionId) ?? detail.data?.versions[0]
  const suite = suites.data?.find((s) => s.id === 'core-v2')
  const canConfirm =
    version?.tool_config_json.includes('send_message_simulated') &&
    (!custom || selected.includes('AS-006'))
  const launch = useMutation({
    retry: false,
    mutationFn: async (body: Record<string, unknown>) => {
      const payload = JSON.stringify(body)
      const saved = JSON.parse(sessionStorage.getItem('agentshield.submission') ?? 'null') as {
        payload: string
        key: string
      } | null
      const key = saved?.payload === payload ? saved.key : crypto.randomUUID()
      sessionStorage.setItem('agentshield.submission', JSON.stringify({ payload, key }))
      const run = await api<Run>('/runs', 'POST', body, true, { idempotencyKey: key })
      sessionStorage.removeItem('agentshield.submission')
      return run
    },
  })
  const error = agents.error || detail.error || suites.error || catalog.error
  const selectedCurated =
    suite?.members
      .filter((member) => selected.includes(member.scenario_id))
      .map((member) => member.scenario_id) ?? []
  const selectedCustom =
    authored.data
      ?.filter((item) => selected.includes(item.id))
      .map((item) => ({ id: item.id, version: revisions[item.id] ?? item.version })) ?? []
  const selectionCount = selectedCurated.length + selectedCustom.length
  return (
    <form
      className="surface run-panel"
      onSubmit={(e) => {
        e.preventDefault()
        if (
          !version ||
          !suite ||
          launch.isPending ||
          (custom && (!selectionCount || selectionCount > 12 || !!authored.error))
        )
          return
        const body = {
          agent_version_id: version.id,
          ...(custom
            ? {
                ...(selectedCurated.length ? { scenarios: selectedCurated } : {}),
                ...(selectedCustom.length ? { custom_scenarios: selectedCustom } : {}),
              }
            : { suite_id: suite.id }),
          ...(confirm && canConfirm
            ? {
                confirmation: {
                  scenario: 'AS-006',
                  step: 1,
                  tool: 'send_message_simulated',
                  arguments: { destination: 'mock-inbox', content: 'Workspace hours reviewed.' },
                },
              }
            : {}),
        }
        launch.mutate(body, { onSuccess: (run) => navigate('/runs/' + run.id) })
      }}
    >
      <h2>
        <Play size={18} />
        Run configuration
      </h2>
      <fieldset disabled={launch.isPending}>
        <div className="run-fields">
          <label>
            Agent profile
            <select
              value={agent}
              onChange={(e) => {
                setAgent(e.target.value)
                setVersion('')
                setConfirm(false)
              }}
            >
              {agents.data?.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                  {a.is_shared ? ' · Shared' : ''}
                </option>
              ))}
            </select>
          </label>
          <label>
            Immutable version
            <select
              value={version?.id ?? ''}
              onChange={(e) => {
                setVersion(e.target.value)
                setConfirm(false)
              }}
            >
              {detail.data?.versions.map((v) => (
                <option key={v.id} value={v.id}>
                  v{v.version_number} · {v.demo_profile}
                </option>
              ))}
            </select>
          </label>
          <label>
            Scenarios
            <select
              value={custom ? 'selected' : 'suite'}
              onChange={(e) => {
                setCustom(e.target.value === 'selected')
                setConfirm(false)
              }}
            >
              <option value="suite">Full suite · Core v2</option>
              <option value="selected">Choose curated or custom scenarios</option>
            </select>
          </label>
        </div>
        {custom && (
          <fieldset className="run-choices">
            <legend>Included scenarios</legend>
            {suite?.members.map((m) => (
              <label key={m.scenario_id}>
                <input
                  type="checkbox"
                  checked={selected.includes(m.scenario_id)}
                  onChange={(e) => {
                    setSelected(
                      e.target.checked
                        ? [...selected, m.scenario_id]
                        : selected.filter((s) => s !== m.scenario_id),
                    )
                    if (m.scenario_id === 'AS-006') setConfirm(false)
                  }}
                />
                {m.scenario_id} ·{' '}
                {catalog.data?.find((s) => s.id === m.scenario_id)?.name ?? 'v' + m.version}
              </label>
            ))}
            {authored.data?.map((item) => (
              <div key={item.id}>
                <label>
                  <input
                    type="checkbox"
                    checked={selected.includes(item.id)}
                    onChange={(event) =>
                      setSelected(
                        event.target.checked
                          ? [...selected, item.id]
                          : selected.filter((id) => id !== item.id),
                      )
                    }
                  />
                  {item.name} · custom
                </label>
                <select
                  aria-label={'Version for ' + item.name}
                  disabled={!selected.includes(item.id)}
                  value={revisions[item.id] ?? item.version}
                  onChange={(event) =>
                    setRevisions({ ...revisions, [item.id]: Number(event.target.value) })
                  }
                >
                  {Array.from({ length: item.version }, (_, index) => item.version - index).map(
                    (revision) => (
                      <option key={revision} value={revision}>
                        Immutable version {revision}
                      </option>
                    ),
                  )}
                </select>
              </div>
            ))}
            <p>
              Select up to twelve cases. <Link to="/scenarios">Author custom scenarios</Link>.
            </p>
            {selectionCount > 12 && <p role="alert">Choose no more than twelve scenarios.</p>}
            {authored.error && (
              <p role="alert">
                {problem(authored.error)}{' '}
                <button type="button" className="run-inline" onClick={() => authored.refetch()}>
                  Retry custom scenarios
                </button>
              </p>
            )}
          </fieldset>
        )}
        {canConfirm && (
          <label className="run-check">
            <input
              type="checkbox"
              checked={confirm}
              onChange={(e) => setConfirm(e.target.checked)}
            />
            Approve AS-006 step 1 to send “Workspace hours reviewed.” to mock-inbox
          </label>
        )}
      </fieldset>
      {error && (
        <p role="alert">
          {problem(error)}{' '}
          <button
            type="button"
            className="run-inline"
            onClick={() => {
              void agents.refetch()
              void suites.refetch()
              void catalog.refetch()
              if (agent) void detail.refetch()
            }}
          >
            Retry configuration
          </button>
        </p>
      )}
      {launch.error && <p role="alert">{problem(launch.error)}</p>}
      <Button
        type="submit"
        disabled={
          !version ||
          !suite ||
          !!error ||
          launch.isPending ||
          (custom && (!selectionCount || selectionCount > 12 || !!authored.error))
        }
      >
        <Play size={15} />
        {launch.isPending ? 'Submitting…' : 'Launch run'}
      </Button>
    </form>
  )
}

function RunHistory({ scope }: { scope: string }) {
  const [offset, setOffset] = useState(0)
  const history = useRunRead<Run[]>(scope, '/runs?limit=11&offset=' + offset)
  return (
    <section className="surface run-panel">
      <div className="run-row">
        <h2>
          <History size={18} />
          Run history
        </h2>
        <button className="run-inline" onClick={() => history.refetch()}>
          Refresh history
        </button>
      </div>
      {history.error ? (
        <p role="alert">{problem(history.error)}</p>
      ) : history.isPending ? (
        <p>Loading history…</p>
      ) : !history.data?.length ? (
        <p>No runs on this page.</p>
      ) : (
        <ul className="run-list">
          {history.data.slice(0, 10).map((r) => (
            <li key={r.id}>
              <Link to={'/runs/' + r.id}>
                <strong>
                  {r.config.profile} · {r.config.scenarios.length} scenarios
                </strong>
                <small>
                  {new Date(r.queued_at).toLocaleString()} · {r.id.slice(0, 8)}
                </small>
                <span className="run-badge">{r.status}</span>
                <ArrowRight size={16} />
              </Link>
            </li>
          ))}
        </ul>
      )}
      {(offset > 0 || (history.data?.length ?? 0) > 10) && (
        <div className="run-row">
          <button className="run-inline" disabled={!offset} onClick={() => setOffset(offset - 10)}>
            Previous page
          </button>
          <button
            className="run-inline"
            disabled={(history.data?.length ?? 0) <= 10}
            onClick={() => setOffset(offset + 10)}
          >
            Next page
          </button>
        </div>
      )}
    </section>
  )
}
