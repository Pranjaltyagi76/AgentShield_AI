import { useState, useSyncExternalStore } from 'react'
import { Link } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { api, guestState, subscribeGuest, startGuest, problem, guestKey } from './lib/workspace'
import { useRunRead } from './lib/runs'
import './runs.css'

type Report = {
  id: string
  run_id: string
  comparison_id: string | null
  format: 'html' | 'json'
  renderer_version: string
  created_at: string
}

async function download(report: Report) {
  const credential = sessionStorage.getItem(guestKey)
  const blob = await api<Blob>('/reports/' + report.id + '/download', 'GET', undefined, true, {
    blob: true,
  })
  if (sessionStorage.getItem(guestKey) !== credential) throw Error('Your guest session has ended.')
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = 'agentshield-' + report.id + '.' + report.format
  anchor.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export function ReportDownloads({ runId, comparisonId }: { runId: string; comparisonId?: string }) {
  const mutation = useMutation({
    retry: false,
    mutationFn: async (format: Report['format']) => {
      const credential = sessionStorage.getItem(guestKey)
      const report = await api<Report>(
        '/runs/' + runId + '/reports',
        'POST',
        { format, ...(comparisonId ? { comparison_id: comparisonId } : {}) },
        true,
      )
      if (sessionStorage.getItem(guestKey) !== credential)
        throw Error('Your guest session has ended.')
      await download(report)
    },
  })
  return (
    <div className="report-downloads">
      <div className="run-row">
        {(['html', 'json'] as const).map((format) => (
          <button
            key={format}
            className="run-inline"
            disabled={mutation.isPending}
            onClick={() => mutation.mutate(format)}
          >
            Download {format.toUpperCase()} report
          </button>
        ))}
        <Link to="/reports">Report history</Link>
      </div>
      {mutation.isPending && <p role="status">Preparing download…</p>}
      {mutation.isSuccess && <p role="status">Report download prepared.</p>}
      {mutation.error && <p role="alert">{problem(mutation.error)}</p>}
    </div>
  )
}

export function Reports() {
  const session = useSyncExternalStore(subscribeGuest, guestState)
  const start = useMutation({ mutationFn: startGuest, retry: false })
  return (
    <section className="run-page">
      <header className="run-heading">
        <h1>Reports</h1>
        <Link to="/sample">Open saved sample</Link>
      </header>
      <p>
        Downloads regenerate from retained records. Guest expiry or source deletion ends access.
      </p>
      {session === 'active' ? (
        <ReportHistory key={session} />
      ) : (
        <section className="surface run-panel">
          <p>
            {session === 'expired'
              ? 'Your guest session has ended.'
              : 'Start a guest workspace to create reports from your runs.'}
          </p>
          <button className="run-inline" disabled={start.isPending} onClick={() => start.mutate()}>
            {start.isPending ? 'Starting…' : 'Start guest workspace'}
          </button>
          {start.error && <p role="alert">{problem(start.error)}</p>}
        </section>
      )}
    </section>
  )
}

function ReportHistory() {
  const [scope] = useState(() => crypto.randomUUID())
  const [offset, setOffset] = useState(0)
  const query = useRunRead<Report[]>(scope, '/reports?limit=11&offset=' + offset)
  const save = useMutation({ mutationFn: download, retry: false })
  return (
    <section className="surface run-panel">
      <h2>Report history</h2>
      <button className="run-inline" onClick={() => query.refetch()} disabled={query.isFetching}>
        Refresh reports
      </button>
      {query.error && (
        <p role="alert">{problem(query.error)} Refresh to retry. The API may be waking.</p>
      )}
      {!query.data && !query.error && <p role="status">Loading reports…</p>}
      {query.data?.length === 0 && (
        <p>
          No reports yet. <Link to="/runs">Open a finished run</Link> to create one.
        </p>
      )}
      {query.data && (
        <ul className="finding-list">
          {query.data.slice(0, 10).map((report) => (
            <li key={report.id}>
              <strong>
                {report.format.toUpperCase()} · renderer v{report.renderer_version}
              </strong>
              <p>
                {new Date(report.created_at).toLocaleString()}
                {report.comparison_id ? ' · Includes comparison' : ''}
              </p>
              <div className="run-row">
                <Link to={'/runs/' + report.run_id}>Open source run</Link>
                <button
                  className="run-inline"
                  disabled={save.isPending}
                  onClick={() => save.mutate(report)}
                >
                  Download {report.format.toUpperCase()}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
      {save.error && <p role="alert">{problem(save.error)}</p>}
      <div className="run-row">
        <button
          className="run-inline"
          disabled={!offset || query.isFetching}
          onClick={() => setOffset(Math.max(0, offset - 10))}
        >
          Previous reports
        </button>
        <button
          className="run-inline"
          disabled={!query.data || query.data.length < 11 || query.isFetching}
          onClick={() => setOffset(offset + 10)}
        >
          More reports
        </button>
      </div>
    </section>
  )
}
