import { useQuery } from '@tanstack/react-query'
import { getHealth, getReadiness } from './api'
export function useSystemStatus() {
  const health = useQuery({ queryKey: ['health'], queryFn: ({ signal }) => getHealth(signal) })
  const readiness = useQuery({
    queryKey: ['readiness'],
    queryFn: ({ signal }) => getReadiness(signal),
    refetchIntervalInBackground: false,
    refetchInterval: (q) =>
      !q.state.error && q.state.data?.status === 'not_ready' && q.state.dataUpdateCount < 3
        ? 3000
        : false,
  })
  return {
    health,
    readiness,
    checking: health.isFetching || readiness.isFetching,
    refresh: () => {
      void health.refetch()
      void readiness.refetch()
    },
  }
}
