import { useEffect, useRef } from 'react'
import { Link, useLocation, useSearchParams } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, ListChecks, ListTree } from 'lucide-react'
import { api, problem } from './lib/workspace'
import { ReportDownloads } from './Reports'
import {
  active,
  rates,
  maxPolls,
  useRunRead,
  useRunStatus,
  type Run,
  type Result,
  type Metrics,
  type Finding,
  type TraceEvent,
  type Scenario,
} from './lib/runs'

export function RunDetail({ scope, id }: { scope: string; id: string }) {
  const status = useRunStatus(scope, id)
  const run = status.data
  const client = useQueryClient()
  const cancel = useMutation({
    retry: false,
    mutationFn: () =>
      api<Run>('/runs/' + encodeURIComponent(id) + '/cancel', 'POST', undefined, true),
    onSuccess: async (r) => {
      const key = ['runs-ui', scope, 'status', id]
      await client.cancelQueries({ queryKey: key })
      client.setQueryData(key, r)
    },
  })
  const paused =
    active(run) &&
    (client.getQueryState(['runs-ui', scope, 'status', id])?.dataUpdateCount ?? 0) >= maxPolls
  return (
    <section className="run-page">
      <Link className="run-back" to="/runs">
        <ArrowLeft size={15} />
        Benchmark runs
      </Link>
      <header className="run-heading">
        <h1>Run details</h1>
        <code>{id}</code>
      </header>
      {status.error && (
        <p role="alert">
          {problem(status.error)}{' '}
          <button className="run-inline" onClick={() => status.refetch()}>
            Retry status
          </button>
        </p>
      )}
      {!run ? (
        !status.error && <p>Loading run…</p>
      ) : (
        <>
          <section className="surface run-panel">
            <div className="run-row">
              <h2>
                {run.config.profile} · {run.config.suite_id ?? 'Selected scenarios'}
              </h2>
              <span className={'run-badge tone-' + run.status}>{run.status}</span>
            </div>
            <div className="run-meta">
              <span>Queued {new Date(run.queued_at).toLocaleString()}</span>
              <span>Scripted behavior v{run.config.behavior_version}</span>
              <span>{run.config.scenarios.length} scenarios</span>
            </div>
            <details>
              <summary>Run configuration and timing</summary>
              <dl className="run-snapshot">
                <dt>Agent version</dt>
                <dd>
                  <code>{run.version_id}</code>
                </dd>
                <dt>Started</dt>
                <dd>{run.started_at ? new Date(run.started_at).toLocaleString() : '—'}</dd>
                <dt>Finished</dt>
                <dd>{run.finished_at ? new Date(run.finished_at).toLocaleString() : '—'}</dd>
                {run.started_at && run.finished_at && (
                  <>
                    <dt>Execution time</dt>
                    <dd>
                      {((Date.parse(run.finished_at) - Date.parse(run.started_at)) / 1000).toFixed(
                        1,
                      )}{' '}
                      s
                    </dd>
                  </>
                )}
              </dl>
            </details>
            {run.reason && (
              <p role="status">
                {run.reason === 'interrupted'
                  ? 'Execution was interrupted. Partial evidence is retained.'
                  : 'Run reason · ' + run.reason.replaceAll('_', ' ')}
              </p>
            )}
            {active(run) && (
              <div className="run-row">
                <p role="status">
                  {status.error
                    ? 'Automatic updates stopped after the status request failed.'
                    : run.cancel_requested
                      ? 'Cancellation requested. Waiting for the worker to stop.'
                      : paused
                        ? 'Automatic updates paused. Refresh to check the current status.'
                        : 'Checking run status automatically.'}
                </p>
                <button
                  className="run-inline"
                  disabled={run.cancel_requested || cancel.isPending}
                  onClick={() => cancel.mutate()}
                >
                  Cancel run
                </button>
              </div>
            )}
            {cancel.error && <p role="alert">{problem(cancel.error)}</p>}
            {active(run) && (
              <button
                className="run-inline"
                onClick={() => client.invalidateQueries({ queryKey: ['runs-ui', scope] })}
              >
                Refresh status and evidence
              </button>
            )}
          </section>
          {!active(run) && (
            <section className="surface run-panel">
              <h2>Export report</h2>
              <ReportDownloads runId={run.id} />
            </section>
          )}
          <Evidence scope={scope} run={run} />
        </>
      )}
    </section>
  )
}

function Evidence({ scope, run }: { scope: string; run: Run }) {
  const [params, setParams] = useSearchParams()
  const names = useRunRead<Scenario[]>(scope, '/scenarios')
  const scenarios = run.config.scenarios
  const selected = scenarios.find((s) => s.id === params.get('scenario')) ?? scenarios[0]
  const base = '/runs/' + encodeURIComponent(run.id)
  const results = useRunRead<Result[]>(scope, base + '/results', true, run.status)
  const metrics = useRunRead<Metrics>(scope, base + '/metrics', true, run.status)
  const findings = useRunRead<Finding[]>(scope, base + '/findings', true, run.status)
  const trace = useRunRead<TraceEvent[]>(
    scope,
    base + '/traces?limit=100&scenario_id=' + encodeURIComponent(selected?.id ?? ''),
    !!selected,
    run.status,
  )
  const client = useQueryClient()
  const error = results.error || metrics.error || findings.error || trace.error
  return (
    <>
      {error && (
        <p role="alert">
          {problem(error)}{' '}
          <button
            className="run-inline"
            onClick={() => client.invalidateQueries({ queryKey: ['runs-ui', scope] })}
          >
            Retry evidence
          </button>
        </p>
      )}
      {metrics.data && <Summary metrics={metrics.data} />}
      <section className="surface run-panel">
        <h2>
          <ListChecks size={18} />
          Findings
        </h2>
        {!findings.data ? (
          <p>{findings.error ? 'Findings unavailable.' : 'Loading findings…'}</p>
        ) : findings.data.length === 0 ? (
          <p>{active(run) ? 'No findings recorded yet.' : 'No findings recorded for this run.'}</p>
        ) : (
          <ul className="finding-list">
            {findings.data.map((f) => (
              <li key={f.evidence_id + f.summary}>
                <small>
                  {f.scenario_id} · {f.severity} severity
                </small>
                <strong>{f.summary}</strong>
                <p>{f.remediation}</p>
                <Link
                  to={{
                    search: new URLSearchParams({
                      scenario: f.scenario_id,
                      event: f.evidence_id,
                    }).toString(),
                  }}
                >
                  View evidence · event {f.sequence}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
      <section className="surface run-panel">
        <h2>
          <ListTree size={18} />
          Scenario traces
        </h2>
        <div className="trace-layout">
          <div className="scenario-list" aria-label="Scenario results">
            {scenarios.map((s) => {
              const r = results.data?.find((x) => x.scenario_id === s.id)
              return (
                <button
                  type="button"
                  key={s.id}
                  aria-pressed={selected?.id === s.id}
                  onClick={() => setParams({ scenario: s.id })}
                >
                  <strong>{s.id}</strong>
                  <small>v{s.version}</small>
                  <span className={'run-badge tone-' + r?.outcome}>
                    {r?.outcome ?? r?.status ?? 'Loading'}
                  </span>
                </button>
              )
            })}
          </div>
          <div className="trace-column">
            <h3>{selected?.id} timeline</h3>
            <small>{names.data?.find((s) => s.id === selected?.id)?.name}</small>
            {results.data
              ?.filter((r) => r.scenario_id === selected?.id)
              .map((r) => (
                <p key={r.scenario_id}>
                  {r.status} · {r.steps} steps · {r.outcome ?? 'Unscored'}
                  {r.reason || r.evaluation_reason
                    ? ' · ' + (r.reason ?? r.evaluation_reason)?.replaceAll('_', ' ')
                    : ''}
                </p>
              ))}
            {trace.data ? (
              <Timeline events={trace.data} target={params.get('event')} />
            ) : (
              <p>{trace.error ? 'Trace unavailable.' : 'Loading trace…'}</p>
            )}
          </div>
        </div>
      </section>
    </>
  )
}

function Summary({ metrics: m }: { metrics: Metrics }) {
  if (!m.oracle_version)
    return <p className="surface run-panel">This run predates stored assessments.</p>
  return (
    <section className="surface run-panel">
      <h2>Evaluation summary</h2>
      <div className="metric-grid">
        {(['coverage', 'pass_rate', 'unauthorized_execution'] as const).map((k) => (
          <div key={k}>
            <small>{rates[k]}</small>
            <strong>{m[k].denominator ? m[k].numerator + ' / ' + m[k].denominator : 'N/A'}</strong>
          </div>
        ))}
      </div>
      <p>
        {m.blocked_attempts} blocked attempts · {m.confirmation_required} required confirmation ·{' '}
        {m.invalid_requests} invalid requests · {m.inconclusive} inconclusive scenarios
      </p>
      <details>
        <summary>All metrics and exclusions</summary>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Metric</th>
                <th>Count</th>
                <th>Rate</th>
                <th>Excluded</th>
              </tr>
            </thead>
            <tbody>
              {(Object.keys(rates) as (keyof typeof rates)[]).map((k) => (
                <tr key={k}>
                  <th>{rates[k]}</th>
                  <td>
                    {m[k].numerator}/{m[k].denominator}
                  </td>
                  <td>{m[k].percent === null ? 'N/A' : m[k].percent + '%'}</td>
                  <td>{m[k].excluded}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  )
}

const labels: Record<string, string> = {
  scenario_start: 'Scenario started',
  agent_input: 'Agent input',
  tool_requested: 'Tool requested',
  policy_decision: 'Policy decision',
  mock_tool_result: 'Mock tool executed',
  agent_output: 'Agent answer',
  scenario_end: 'Scenario ended',
}
const fields: Record<string, string[]> = {
  scenario_start: ['id', 'version'],
  agent_input: [
    'task',
    'workspace',
    'available_tools',
    'workspace_label',
    'message_label',
    'local_label',
    'document_source',
    'repeat',
    'delivery',
    'request',
  ],
  tool_requested: ['tool', 'arguments', 'omitted_fields', 'contains_private_marker'],
  policy_decision: ['decision', 'reason'],
  mock_tool_result: [
    'document',
    'record',
    'label',
    'destination',
    'receipt',
    'internal_note',
    'draft_caption',
    'display_caption',
  ],
  agent_output: ['answer'],
  scenario_end: ['status', 'reason'],
}
function displayField(name: string, value: unknown) {
  if (
    name === 'request' &&
    value &&
    typeof value === 'object' &&
    'tool' in value &&
    typeof value.tool === 'string' &&
    'arguments' in value
  )
    return value.tool + ' ' + displayField('arguments', value.arguments)
  if (name === 'arguments' && typeof value === 'object' && value !== null) {
    return JSON.stringify(
      Object.fromEntries(
        Object.entries(value).filter(
          ([key, fieldValue]) =>
            typeof fieldValue === 'string' &&
            ['query', 'record', 'destination', 'content'].includes(key),
        ),
      ),
      null,
      2,
    )
  }
  if (Array.isArray(value)) return value.filter((x) => typeof x === 'string').join(', ')
  return typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean'
    ? String(value)
    : '—'
}
function Timeline({ events, target }: { events: TraceEvent[]; target: string | null }) {
  const focused = useRef<HTMLDetailsElement>(null)
  const navigation = useLocation().key
  useEffect(() => {
    if (target && focused.current) {
      focused.current.open = true
      focused.current.focus()
      focused.current.scrollIntoView?.({ block: 'nearest' })
    }
  }, [target, events, navigation])
  if (!events.length) return <p>No trace events recorded for this scenario.</p>
  return (
    <>
      {target && !events.some((e) => e.id === target) && (
        <p role="status">The linked event is unavailable.</p>
      )}
      <ol className="trace-list">
        {events.map((e, index) => {
          const decision = e.kind === 'policy_decision' ? String(e.payload.decision ?? '') : ''
          return (
            <li key={e.id}>
              <details
                tabIndex={-1}
                ref={e.id === target ? focused : undefined}
                className={e.id === target ? 'trace-target' : ''}
              >
                <summary>
                  <span className="event-number">{String(e.sequence).padStart(2, '0')}</span>
                  <strong>{labels[e.kind] ?? 'Trace event'}</strong>
                  {decision && (
                    <span className={'run-badge tone-' + decision}>
                      {decision.replaceAll('_', ' ')}
                    </span>
                  )}
                  {e.kind === 'tool_requested' && (
                    <code>{String(e.payload.tool ?? 'unknown')}</code>
                  )}
                </summary>
                <dl>
                  {(fields[e.kind] ?? [])
                    .filter((k) => k in e.payload)
                    .map((k) => (
                      <div key={k}>
                        <dt>{k.replaceAll('_', ' ')}</dt>
                        <dd>
                          <code>{displayField(k, e.payload[k])}</code>
                        </dd>
                      </div>
                    ))}
                  {e.created_at && (
                    <div>
                      <dt>Recorded</dt>
                      <dd>
                        <time dateTime={e.created_at}>
                          {new Date(e.created_at).toLocaleTimeString()}
                        </time>
                      </dd>
                    </div>
                  )}
                </dl>
                {e.kind === 'tool_requested' && (
                  <CallDetail decision={events[index + 1]} result={events[index + 2]} />
                )}
              </details>
            </li>
          )
        })}
      </ol>
    </>
  )
}

function CallDetail({ decision, result }: { decision?: TraceEvent; result?: TraceEvent }) {
  const policy = decision?.kind === 'policy_decision' ? decision : undefined
  const executed = policy && result?.kind === 'mock_tool_result' ? result : undefined
  return (
    <div className="call-details">
      <strong>Tool call detail</strong>
      <p>
        {policy
          ? 'Policy · ' +
            String(policy.payload.decision).replaceAll('_', ' ') +
            ' (' +
            String(policy.payload.reason).replaceAll('_', ' ') +
            ')'
          : 'Awaiting a recorded policy decision.'}
      </p>
      {executed ? (
        <>
          <p>Executed · mock result at event {executed.sequence}</p>
          <dl>
            {fields.mock_tool_result
              .filter((k) => k in executed.payload)
              .map((k) => (
                <div key={k}>
                  <dt>{k.replaceAll('_', ' ')}</dt>
                  <dd>
                    <code>{displayField(k, executed.payload[k])}</code>
                  </dd>
                </div>
              ))}
          </dl>
        </>
      ) : (
        <p>No mock execution recorded for this request.</p>
      )}
    </div>
  )
}
