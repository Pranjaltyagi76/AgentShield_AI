import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { rates, type Metrics, type Finding, type TraceEvent } from './lib/runs'
import './runs.css'

type SampleReport = {
  renderer_version: string
  created_at: string
  sample: { label: string; captured_at: string; method: string }
  run: {
    status: string
    configuration: { profile: string; suite_id: string; behavior_version: string }
  }
  metrics: Metrics
  scenarios: { scenario_id: string; version: number; outcome: string }[]
  findings: Finding[]
  evidence: TraceEvent[]
  comparison: {
    baseline: { profile: string }
    candidate: { profile: string }
    counts: Record<string, number>
  } | null
  limitations: string[]
}

export function Sample() {
  const query = useQuery({
    queryKey: ['saved-sample'],
    queryFn: async ({ signal }) => {
      const response = await fetch('/saved-sample.json', { signal, credentials: 'omit' })
      if (!response.ok) throw Error('Saved sample could not be loaded.')
      return response.json() as Promise<SampleReport>
    },
    retry: false,
    staleTime: Infinity,
  })
  const data = query.data
  return (
    <section className="run-page">
      <header className="run-heading">
        <h1>Saved sample - not a live run</h1>
        <Link to="/runs">Start a live scripted benchmark</Link>
      </header>
      <p>
        This historical workspace contains a captured scripted run. It is available independently of
        the API.
      </p>
      <div className="run-row">
        <a href="/saved-sample.html" download>
          Download sample HTML
        </a>
        <a href="/saved-sample.json" download>
          Download sample JSON
        </a>
      </div>
      {!data && !query.error && <p role="status">Loading saved sample…</p>}
      {query.error && (
        <p role="alert">
          {problemText(query.error)}{' '}
          <button className="run-inline" onClick={() => query.refetch()}>
            Retry sample
          </button>
        </p>
      )}
      {data && (
        <>
          <section className="surface run-panel">
            <h2>Captured workspace</h2>
            <p>
              {data.run.configuration.profile} · scripted behavior v
              {data.run.configuration.behavior_version} · {data.run.configuration.suite_id} ·{' '}
              {data.run.status}
            </p>
            <p>
              Captured {new Date(data.sample.captured_at).toLocaleString()} · renderer v
              {data.renderer_version}
            </p>
            <p>{data.sample.method}</p>
          </section>
          <section className="surface run-panel">
            <h2>Recorded metrics</h2>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Metric</th>
                    <th>Count</th>
                    <th>Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {(Object.keys(rates) as (keyof typeof rates)[]).map((key) => {
                    const rate = data.metrics[key]
                    return (
                      <tr key={key}>
                        <th>{rates[key]}</th>
                        <td>
                          {rate.numerator}/{rate.denominator}
                        </td>
                        <td>{rate.percent === null ? 'N/A' : rate.percent + '%'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </section>
          {data.comparison && (
            <section className="surface run-panel">
              <h2>Captured comparison</h2>
              <p>
                {data.comparison.baseline.profile} → {data.comparison.candidate.profile}
              </p>
              <ul>
                {Object.entries(data.comparison.counts).map(([label, value]) => (
                  <li key={label}>
                    {value} {label}
                  </li>
                ))}
              </ul>
            </section>
          )}
          <section className="surface run-panel">
            <h2>Scenario outcomes</h2>
            <ul>
              {data.scenarios.map((s) => (
                <li key={s.scenario_id}>
                  {s.scenario_id} v{s.version} · {s.outcome}
                </li>
              ))}
            </ul>
          </section>
          <section className="surface run-panel">
            <h2>Evidence-backed findings</h2>
            <ul className="finding-list">
              {data.findings.map((f) => (
                <li key={f.evidence_id + f.summary}>
                  <strong>
                    {f.scenario_id} · {f.severity} · {f.summary}
                  </strong>
                  <p>{f.remediation}</p>
                  <a href={'#event-' + f.evidence_id}>Recorded evidence</a>
                </li>
              ))}
            </ul>
          </section>
          <section className="surface run-panel">
            <h2>Recorded trace</h2>
            {data.evidence.map((e) => (
              <details key={e.id} id={'event-' + e.id}>
                <summary>
                  {e.scenario_id} · {e.sequence} · {e.kind.replaceAll('_', ' ')}
                </summary>
                <pre>{JSON.stringify(e.payload, null, 2)}</pre>
              </details>
            ))}
          </section>
          <section className="surface run-panel">
            <h2>Limitations</h2>
            <ul>
              {data.limitations.map((l) => (
                <li key={l}>{l}</li>
              ))}
            </ul>
          </section>
        </>
      )}
    </section>
  )
}

function problemText(error: unknown) {
  return error instanceof Error ? error.message : 'Saved sample unavailable.'
}
