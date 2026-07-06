import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import type { Alert } from '../../lib/mockData'
import { toAlert } from './adapter'
import { dismissAlert, fetchAlerts, fetchRules, type FetchAlertsParams } from './api'
import type { AlertRuleDto } from './types'

const ALERTS_KEY = 'alerts'

export function useAlerts(params: FetchAlertsParams = {}) {
  return useQuery<Alert[]>({
    queryKey: [ALERTS_KEY, params],
    queryFn: async () => {
      const dtos = await fetchAlerts(params)
      return dtos.map(toAlert)
    },
  })
}

export function useDismissAlert() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => dismissAlert(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [ALERTS_KEY] })
    },
  })
}

export function useAlertRules() {
  return useQuery<AlertRuleDto[]>({
    queryKey: [ALERTS_KEY, 'rules'],
    queryFn: fetchRules,
  })
}
