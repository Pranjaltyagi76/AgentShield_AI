import { API_BASE, ApiError } from './api'

export const guestKey = 'agentshield.guest'
let expired = false
export function guestState() {
  return sessionStorage.getItem(guestKey) ? 'active' : expired ? 'expired' : 'none'
}
export function changeGuest(token: string | null, ended = false) {
  if (token) sessionStorage.setItem(guestKey, token)
  else sessionStorage.removeItem(guestKey)
  sessionStorage.removeItem('agentshield.submission')
  expired = ended
  window.dispatchEvent(new Event('agentshield-session'))
}
export function subscribeGuest(listener: () => void) {
  window.addEventListener('agentshield-session', listener)
  return () => window.removeEventListener('agentshield-session', listener)
}
export function problem(error: unknown) {
  return error instanceof Error ? error.message : 'Unable to connect.'
}
export async function api<T>(
  path: string,
  method = 'GET',
  data?: unknown,
  auth = false,
  options: { signal?: AbortSignal; idempotencyKey?: string; blob?: boolean } = {},
): Promise<T> {
  const token = auth ? sessionStorage.getItem(guestKey) : null
  const timeout = AbortSignal.timeout(10_000)
  let response: Response
  try {
    response = await fetch(API_BASE + path, {
      method,
      credentials: 'omit',
      signal: options.signal ? AbortSignal.any([options.signal, timeout]) : timeout,
      headers: {
        ...(token ? { Authorization: 'Bearer ' + token } : {}),
        ...(data ? { 'Content-Type': 'application/json' } : {}),
        ...(options.idempotencyKey ? { 'Idempotency-Key': options.idempotencyKey } : {}),
      },
      body: data ? JSON.stringify(data) : undefined,
    })
  } catch (error) {
    if (options.signal?.aborted) throw error
    throw new ApiError('The API did not respond. Check the connection and retry.')
  }
  if (response.status === 401 && token && sessionStorage.getItem(guestKey) === token)
    changeGuest(null, true)
  if (!response.ok) {
    const runs = path.startsWith('/runs')
    const report = path.startsWith('/reports') || /^\/runs\/[^/]+\/reports/.test(path)
    const comparison = path.startsWith('/benchmarks')
    const custom = path.startsWith('/custom-scenarios')
    const retry = response.headers.get('Retry-After')
    const delay = retry && /^\d+$/.test(retry) ? ' Retry after ' + retry + ' seconds.' : ''
    const messages: Record<number, string> = {
      401: 'Your guest session has ended.',
      403: 'Access denied for this workspace.',
      404: report
        ? 'Report or source run unavailable in this workspace.'
        : runs
          ? 'Run unavailable in this workspace or execution is disabled.'
          : 'Record unavailable.',
      409: custom
        ? 'Custom scenario limit reached: eight scenarios per guest and four versions each.'
        : report
          ? 'Reports require a finished run and a supported renderer.'
          : comparison
            ? 'Both source runs must finish before comparison.'
            : runs
              ? 'Run request conflicts with an earlier submission.'
              : 'Workspace limit reached.',
      422: custom
        ? 'Check the registered checker, distinct lowercase labels, allowed mock tools and task byte limit.'
        : report
          ? 'Choose HTML or JSON and an accessible comparison.'
          : comparison
            ? 'Choose two distinct runs.'
            : runs
              ? 'Check the scenario and agent version selections.'
              : 'Check the form values and prompt length.',
      429: 'Request limit reached.' + delay,
      503: report
        ? 'Report storage or workspace capacity is unavailable.'
        : comparison
          ? 'Comparison storage or workspace capacity is unavailable.'
          : runs
            ? 'Run capacity or storage is unavailable.' + delay
            : 'Workspace storage is unavailable.',
    }
    throw new ApiError(messages[response.status] ?? 'Request failed.', response.status)
  }
  if (options.blob) return (await response.blob()) as T
  return response.status === 204 ? (undefined as T) : response.json()
}

export async function startGuest() {
  const session = await api<{ credential: string }>('/guest-sessions', 'POST')
  changeGuest(session.credential)
}
