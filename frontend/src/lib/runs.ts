import { useQuery } from '@tanstack/react-query'
import { api } from './workspace'

export type Profile = { id: string; name: string; is_shared: boolean }
export type Version = {
  id: string
  version_number: number
  demo_profile: string
  tool_config_json: string[]
}
export type Scenario = { id: string; name: string }
export type Run = {
  id: string
  status: 'queued' | 'running' | 'completed' | 'cancelled' | 'failed'
  reason: string | null
  queued_at: string
  started_at: string | null
  finished_at: string | null
  cancel_requested: boolean
  version_id: string
  config: {
    profile: string
    suite_id?: string | null
    behavior_version: string
    scenarios: { id: string; version: number }[]
  }
}
export type Result = {
  scenario_id: string
  version: number
  status: string
  outcome: string | null
  reason: string | null
  evaluation_reason: string | null
  steps: number
}
export type Rate = {
  numerator: number
  denominator: number
  percent: number | null
  excluded: number
}
export const rates = {
  coverage: 'Evaluation coverage',
  pass_rate: 'Scenarios passed',
  attack_success: 'Adversarial objectives achieved',
  attempted_violation: 'Attempted violations',
  unauthorized_execution: 'Unauthorized execution',
  secret_exposure: 'Secret exposure',
  safe_containment: 'Safe containment',
  benign_completion: 'Benign completion',
  allowlist_compliance: 'Allowlist compliance',
  tool_accuracy: 'Tool accuracy',
} as const
export type Metrics = Record<keyof typeof rates, Rate> & {
  oracle_version: string | null
  blocked_attempts: number
  invalid_requests: number
  confirmation_required: number
  inconclusive: number
}
export type Finding = {
  scenario_id: string
  severity: string
  summary: string
  remediation: string
  sequence: number
  evidence_id: string
}
export type TraceEvent = {
  id: string
  scenario_id: string
  sequence: number
  kind: string
  created_at?: string
  payload: Record<string, unknown>
}

export function active(run?: Run) {
  return run?.status === 'queued' || run?.status === 'running'
}
export const maxPolls = 100
export function pollDelay(run: Run | undefined, failed: boolean, updates: number) {
  return active(run) && !failed && updates < maxPolls ? 2500 : false
}
export function useRunRead<T>(scope: string, path: string, enabled = true, revision = '') {
  return useQuery({
    queryKey: ['runs-ui', scope, path, revision],
    queryFn: ({ signal }) => api<T>(path, 'GET', undefined, true, { signal }),
    enabled,
    retry: false,
    gcTime: 0,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  })
}
export function useRunStatus(scope: string, id: string) {
  return useQuery({
    queryKey: ['runs-ui', scope, 'status', id],
    queryFn: ({ signal }) =>
      api<Run>('/runs/' + encodeURIComponent(id), 'GET', undefined, true, { signal }),
    retry: false,
    gcTime: 0,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchIntervalInBackground: false,
    refetchInterval: (q) => pollDelay(q.state.data, !!q.state.error, q.state.dataUpdateCount),
  })
}
