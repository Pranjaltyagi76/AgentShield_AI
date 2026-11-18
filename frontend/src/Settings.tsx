import { useState, useSyncExternalStore } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api, guestState, subscribeGuest, startGuest, problem } from './lib/workspace'
import { defaultDemoProfile, saveDemoProfile, type DemoProfile } from './lib/preferences'
import { useRunRead } from './lib/runs'
import './runs.css'

type DemoStatus = {
  execution_enabled: boolean
  requires_api_key: false
  inference: { provider: string; enabled: false; reason: string }
  limits: Record<string, number>
}
const labels: Record<string, string> = {
  scenarios_per_run: 'Scenarios per run',
  active_runs_global: 'Active runs globally',
  queued_runs_global: 'Queued runs globally',
  steps_per_scenario: 'Steps per scenario',
  calls_per_scenario: 'Tool calls per scenario',
  trace_bytes_per_run: 'Trace bytes per run',
  scripted_bytes_per_run: 'Scripted byte budget per run',
  guest_retention_days: 'Guest retention in days',
  custom_scenarios_per_guest: 'Custom scenarios per guest',
  versions_per_custom_scenario: 'Versions per custom scenario',
  database_admission_bytes: 'Database admission ceiling in bytes',
}

export function Settings() {
  const [profile, setProfile] = useState(defaultDemoProfile)
  const [saved, setSaved] = useState(false)
  const status = useQuery({
    queryKey: ['demo-status'],
    queryFn: ({ signal }) => api<DemoStatus>('/demo/status', 'GET', undefined, false, { signal }),
    retry: false,
  })
  const session = useSyncExternalStore(subscribeGuest, guestState)
  const issue = useMutation({ mutationFn: startGuest, retry: false })
  return (
    <section className="run-page">
      <header className="run-heading">
        <h1>Settings</h1>
        <p>
          Choose your demo default and review provider availability, retention and enforced limits.
        </p>
      </header>
      <form
        className="surface run-panel"
        onSubmit={(event) => {
          event.preventDefault()
          saveDemoProfile(profile)
          setSaved(true)
        }}
      >
        <h2>Demo preferences</h2>
        <label>
          Default demo profile
          <select
            className="preference-select"
            value={profile}
            onChange={(event) => {
              setProfile(event.target.value as DemoProfile)
              setSaved(false)
            }}
          >
            <option value="hardened">Hardened</option>
            <option value="vulnerable">Vulnerable</option>
          </select>
        </label>
        <p>
          This non-secret preference is saved for this browser tab and selects the shared default in
          the run launcher. Individual runs can use another immutable profile version.
        </p>
        <button className="run-inline" type="submit">
          Save demo preference
        </button>
        {saved && <p role="status">Default demo profile saved for this tab.</p>}
        <Link to="/runs">Open benchmark runs</Link>
      </form>
      <section className="surface run-panel">
        <h2>Provider configuration</h2>
        <p>
          Active provider: scripted demo. No model API key is required or accepted from visitors.
        </p>
        {status.isPending && <p>Loading provider availability…</p>}
        {status.error && (
          <p role="alert">
            {problem(status.error)}{' '}
            <button className="run-inline" onClick={() => status.refetch()}>
              Retry provider status
            </button>
          </p>
        )}
        {status.data && !status.error && (
          <>
            <p>
              Scripted execution:{' '}
              {status.data.execution_enabled
                ? 'enabled by the operator'
                : 'disabled by the operator'}
              . <Link to="/system">Check API and database readiness</Link>.
            </p>
            <p>
              Gemini: disabled · {status.data.inference.reason.replaceAll('_', ' ')}. A live
              provider adapter is not implemented. Provider credentials and execution switches are
              operator-managed.
            </p>
            <h3>Enforced server limits</h3>
            <dl className="run-snapshot">
              {Object.entries(status.data.limits).map(([key, value]) => (
                <div key={key}>
                  <dt>{labels[key] ?? key.replaceAll('_', ' ')}</dt>
                  <dd>{value.toLocaleString()}</dd>
                </div>
              ))}
            </dl>
            <p>
              Scripted limits count UTF-8 bytes, not provider tokens. Anonymous rate and queue
              limits also apply. Limits cannot be bypassed through browser preferences.
            </p>
          </>
        )}
      </section>
      <section className="surface run-panel">
        <h2>Temporary workspace</h2>
        {session === 'active' ? (
          <WorkspaceExpiry />
        ) : (
          <>
            <p>
              {session === 'expired'
                ? 'Your previous guest session has ended.'
                : 'No guest workspace is active in this tab.'}
            </p>
            <button
              className="run-inline"
              disabled={issue.isPending}
              onClick={() => issue.mutate()}
            >
              {issue.isPending ? 'Starting…' : 'Start guest workspace'}
            </button>
            {issue.error && <p role="alert">{problem(issue.error)}</p>}
          </>
        )}
        <p>
          Guest data expires seven days after issuance. Losing the tab credential loses access.
          Physical cleanup runs while the backend is active; free hosting may sleep.
        </p>
        <Link to="/agents">Manage profiles and workspace</Link>
        <Link to="/sample">Explore the historical sample</Link>
      </section>
    </section>
  )
}

function WorkspaceExpiry() {
  const [scope] = useState(() => crypto.randomUUID())
  const session = useRunRead<{ expires_at: string }>(scope, '/guest-session')
  return (
    <>
      {session.data && (
        <p>Workspace expires {new Date(session.data.expires_at).toLocaleString()}.</p>
      )}
      {session.isPending && <p>Checking workspace expiry…</p>}
      {session.error && (
        <p role="alert">
          {problem(session.error)}{' '}
          <button className="run-inline" onClick={() => session.refetch()}>
            Retry workspace status
          </button>
        </p>
      )}
    </>
  )
}
