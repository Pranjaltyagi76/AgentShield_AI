import { z } from 'zod'
export const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/+$/, '')
const healthSchema = z.object({
  status: z.literal('ok'),
  service: z.string(),
  version: z.string(),
  phase: z.literal(0),
})
const readinessSchema = z.object({
  status: z.enum(['ready', 'not_ready']),
  database: z.enum(['connected', 'unavailable', 'not_configured']),
  service: z.string(),
  phase: z.literal(0),
})
export type Health = z.infer<typeof healthSchema>
export type Readiness = z.infer<typeof readinessSchema>
export class ApiError extends Error {
  readonly status?: number
  constructor(message: string, status?: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}
async function getJson(
  path: string,
  signal?: AbortSignal,
  allowUnavailable = false,
): Promise<unknown> {
  const timeout = AbortSignal.timeout(8_000)
  const requestSignal = signal ? AbortSignal.any([signal, timeout]) : timeout
  let response: Response
  try {
    response = await fetch(API_BASE + path, {
      signal: requestSignal,
      headers: { Accept: 'application/json' },
      credentials: 'omit',
    })
  } catch (error) {
    if (signal?.aborted) throw error
    throw new ApiError('Cannot reach the API. It may be starting; check the address and try again.')
  }
  if (!response.ok && !(allowUnavailable && response.status === 503)) {
    throw new ApiError('The API returned an unexpected response.', response.status)
  }
  try {
    return await response.json()
  } catch {
    throw new ApiError('The API did not return JSON. Check VITE_API_BASE_URL.', response.status)
  }
}
export async function getHealth(signal?: AbortSignal): Promise<Health> {
  const parsed = healthSchema.safeParse(await getJson('/health', signal))
  if (!parsed.success) throw new ApiError('The health response did not match the API contract.')
  return parsed.data
}
export async function getReadiness(signal?: AbortSignal): Promise<Readiness> {
  const parsed = readinessSchema.safeParse(await getJson('/ready', signal, true))
  if (!parsed.success) throw new ApiError('The readiness response did not match the API contract.')
  return parsed.data
}
