import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { Button } from './components/ui/button'
import { api, problem } from './lib/workspace'
import { active, rates, useRunRead, type Rate, type Run } from './lib/runs'

type Side = { version: number; outcome: string; reason: string | null }
const categories = [
  'improved',
  'regressed',
  'unchanged',
  'inconclusive',
  'incompatible',
  'unmatched',
] as const
type Category = (typeof categories)[number]
type Source = {
  id: string
  profile: string | null
  behavior_version: string | null
  prompt_hash: string | null
  coverage: Rate
  agent_version_id: string
  status: string
}
type Comparison = {
  id: string
  baseline: Source
  candidate: Source
  settings_issues: string[]
  changes: string[]
  counts: Record<Category, number>
  paired_evaluable: number
  paired_compatible: number
  action_counts: Record<string, { baseline: number; candidate: number; delta: number }>
  metrics: Record<keyof typeof rates, { baseline: Rate; candidate: Rate; delta_pp: number | null }>
  scenarios: {
    scenario_id: string
    baseline: Side | null
    candidate: Side | null
    classification: Category
    issues: string[]
  }[]
}
const readable = (key: string) => key.replaceAll('_', ' ')
const count = (v: Rate) => v.numerator + '/' + v.denominator
const pct = (v: Rate) => (v.percent === null ? 'N/A' : v.percent + '%')

export function Compare({ id }: { id?: string }) {
  const [scope] = useState(() => crypto.randomUUID())
  return (
    <section className="run-page">
      <header className="run-heading">
        <h1>Benchmark comparison</h1>
        {id ? (
          <Link to="/compare">Choose another pair</Link>
        ) : (
          <p>Choose two finished runs from your guest workspace.</p>
        )}
      </header>
      {id ? <SavedComparison scope={scope} id={id} /> : <Selection scope={scope} />}
    </section>
  )
}

function Picker({
  label,
  scope,
  value,
  onChange,
}: {
  label: string
  scope: string
  value: string
  onChange: (id: string) => void
}) {
  const [offset, page] = useState(0)
  const query = useRunRead<Run[]>(scope, '/runs?limit=11&offset=' + offset)
  const options = query.data?.slice(0, 10) ?? []
  return (
    <div>
      <label>
        {label}
        <select value={value} onChange={(e) => onChange(e.target.value)}>
          <option value="">Select a run</option>
          {options.map((r) => (
            <option key={r.id} value={r.id} disabled={active(r)}>
              {r.config.profile} · {r.config.scenarios.length} scenarios · {r.status} ·{' '}
              {new Date(r.queued_at).toLocaleString()} · {r.id.slice(0, 8)}
            </option>
          ))}
        </select>
      </label>
      {query.error ? (
        <p role="alert">
          {problem(query.error)}{' '}
          <button type="button" className="run-inline" onClick={() => query.refetch()}>
            Retry {label.toLowerCase()} list
          </button>
        </p>
      ) : query.isPending ? (
        <p>Loading runs…</p>
      ) : !options.length ? (
        <p>
          No runs on this page. <Link to="/runs">Open benchmark runs</Link>
        </p>
      ) : null}
      {(offset > 0 || (query.data?.length ?? 0) > 10) && (
        <div>
          <button
            type="button"
            className="run-inline"
            disabled={offset === 0}
            onClick={() => {
              page(offset - 10)
              onChange('')
            }}
          >
            Newer runs
          </button>
          <button
            type="button"
            className="run-inline"
            disabled={(query.data?.length ?? 0) <= 10}
            onClick={() => {
              page(offset + 10)
              onChange('')
            }}
          >
            Older runs
          </button>
        </div>
      )}
    </div>
  )
}

function Selection({ scope }: { scope: string }) {
  const [baseline, setBaseline] = useState(''),
    [candidate, setCandidate] = useState('')
  const navigate = useNavigate()
  const create = useMutation({
    retry: false,
    mutationFn: () =>
      api<Comparison>(
        '/benchmarks/compare',
        'POST',
        { baseline_run_id: baseline, candidate_run_id: candidate },
        true,
      ),
  })
  return (
    <form
      className="surface run-panel"
      onSubmit={(e) => {
        e.preventDefault()
        if (baseline && candidate && baseline !== candidate && !create.isPending)
          create.mutate(undefined, { onSuccess: (c) => navigate('/compare/' + c.id) })
      }}
    >
      <h2>Comparison runs</h2>
      <fieldset disabled={create.isPending} className="run-fields compare-fields">
        <Picker label="Baseline" scope={scope} value={baseline} onChange={setBaseline} />
        <Picker label="Candidate" scope={scope} value={candidate} onChange={setCandidate} />
      </fieldset>
      {baseline && baseline === candidate && <p role="status">Choose two different runs.</p>}
      {create.error && <p role="alert">{problem(create.error)}</p>}
      <Button disabled={!baseline || !candidate || baseline === candidate || create.isPending}>
        {create.isPending ? 'Comparing…' : 'Compare runs'}
      </Button>
    </form>
  )
}

function SavedComparison({ scope, id }: { scope: string; id: string }) {
  const query = useRunRead<Comparison>(scope, '/benchmarks/' + encodeURIComponent(id))
  const [filter, setFilter] = useState<Category | 'all'>('all')
  if (query.error)
    return (
      <p role="alert">
        {problem(query.error)}{' '}
        <button className="run-inline" onClick={() => query.refetch()}>
          Retry comparison
        </button>
      </p>
    )
  if (!query.data) return <p>Loading comparison…</p>
  const c = query.data
  return (
    <>
      <section className="surface run-panel">
        <h2>Source runs</h2>
        <div className="compare-sources">
          {(['baseline', 'candidate'] as const).map((k) => (
            <div key={k}>
              <strong>
                {k === 'baseline' ? 'Baseline' : 'Candidate'} · {c[k].profile ?? 'Unknown profile'}
              </strong>
              <p>
                Behavior v{c[k].behavior_version ?? 'unknown'} · {c[k].status}
              </p>
              <details>
                <summary>Version details</summary>
                <p>
                  Agent version · <code>{c[k].agent_version_id}</code>
                </p>
                <p>
                  Prompt hash · <code>{c[k].prompt_hash ?? 'Unavailable'}</code>
                </p>
              </details>
              <p>Full-run coverage {count(c[k].coverage)}</p>
              <Link to={'/runs/' + c[k].id}>Open run {c[k].id.slice(0, 8)}</Link>
            </div>
          ))}
        </div>
        {c.changes.length > 0 && <p>Recorded changes · {c.changes.map(readable).join(', ')}</p>}
        <p>
          Scripted decisions use the profile and behavior version. A prompt edit alone does not
          change the script.
        </p>
        {c.settings_issues.length > 0 && (
          <p role="status">
            Settings prevent a like-for-like comparison ·{' '}
            {c.settings_issues.map(readable).join(', ')}
          </p>
        )}
      </section>
      <section className="surface run-panel">
        <h2>Scenario changes</h2>
        <div className="compare-counts">
          {categories.map((k) => (
            <span key={k}>
              <strong>{c.counts[k]}</strong> {k}
            </span>
          ))}
        </div>
        <label>
          Show scenarios{' '}
          <select value={filter} onChange={(e) => setFilter(e.target.value as Category | 'all')}>
            <option value="all">All classifications</option>
            {categories.map((k) => (
              <option key={k}>{k}</option>
            ))}
          </select>
        </label>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Scenario</th>
                <th>Baseline</th>
                <th>Candidate</th>
                <th>Change</th>
              </tr>
            </thead>
            <tbody>
              {c.scenarios
                .filter((s) => filter === 'all' || s.classification === filter)
                .map((s) => (
                  <tr key={s.scenario_id}>
                    <th>{s.scenario_id}</th>
                    {(['baseline', 'candidate'] as const).map((k) => (
                      <td key={k}>
                        {s[k] ? (
                          <>
                            <Link to={'/runs/' + c[k].id + '?scenario=' + s.scenario_id}>
                              v{s[k].version} · {s[k].outcome}
                            </Link>
                            {s[k].reason && <small> · {readable(s[k].reason)}</small>}
                          </>
                        ) : (
                          'Absent'
                        )}
                      </td>
                    ))}
                    <td>
                      <strong>{s.classification}</strong>
                      {s.issues.length > 0 && <small> · {s.issues.map(readable).join(', ')}</small>}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
        {filter !== 'all' && !c.counts[filter] && <p>No {filter} scenarios.</p>}
      </section>
      <section className="surface run-panel">
        <h2>Metric changes</h2>
        <p>
          {c.paired_evaluable} jointly evaluable of {c.paired_compatible} compatible pairs. Coverage
          includes compatible pairs with incomplete evidence.
        </p>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Metric</th>
                <th>Baseline</th>
                <th>Candidate</th>
                <th>Change (pp)</th>
              </tr>
            </thead>
            <tbody>
              {(Object.keys(rates) as (keyof typeof rates)[]).map((k) => {
                const metric = c.metrics[k]
                return (
                  <tr key={k}>
                    <th>{rates[k]}</th>
                    {(['baseline', 'candidate'] as const).map((side) => (
                      <td key={side}>
                        <span>
                          {count(metric[side])} · {pct(metric[side])}
                        </span>
                        {metric[side].percent !== null && (
                          <meter
                            aria-label={side + ' ' + rates[k]}
                            min={0}
                            max={100}
                            value={metric[side].percent}
                          />
                        )}
                      </td>
                    ))}
                    <td>
                      {metric.delta_pp === null
                        ? 'N/A'
                        : (metric.delta_pp > 0 ? '+' : '') + metric.delta_pp}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        <details>
          <summary>Paired action counts</summary>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Count</th>
                  <th>Baseline</th>
                  <th>Candidate</th>
                  <th>Change</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(c.action_counts).map(([key, value]) => (
                  <tr key={key}>
                    <th>{readable(key)}</th>
                    <td>{value.baseline}</td>
                    <td>{value.candidate}</td>
                    <td>{value.delta}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      </section>
    </>
  )
}
