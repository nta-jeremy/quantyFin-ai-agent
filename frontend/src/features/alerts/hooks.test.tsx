import type { ReactNode } from 'react'
import { describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'

import { server } from '../../test/setup'
import { useAlerts, useDismissAlert } from './hooks'
import type { TriggeredAlertDto } from './types'

function makeDto(overrides: Partial<TriggeredAlertDto> = {}): TriggeredAlertDto {
  return {
    id: 1,
    ruleId: 7,
    ticker: 'VCB',
    level: 'high',
    title: 'Giá VCB vượt ngưỡng',
    message: 'VCB tăng 5% trong phiên',
    isDismissed: false,
    triggeredAt: '2026-06-23T08:00:00.000Z',
    ...overrides,
  }
}

function createWrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>
  }
}

describe('useAlerts', () => {
  it('returns the mapped alert list when the request succeeds', async () => {
    server.use(
      http.get('*/api/v1/alerts', () =>
        HttpResponse.json({
          data: [makeDto({ id: 1, ticker: 'FPT', title: 'A', message: 'B' })],
          error: null,
          meta: null,
        }),
      ),
    )

    const { result } = renderHook(() => useAlerts({ isDismissed: false }), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual([
      { id: '1', sev: 'high', t: 'A', m: 'B', tickers: ['FPT'], when: expect.any(String) },
    ])
  })

  it('surfaces an error state when the backend returns an error envelope', async () => {
    server.use(
      http.get('*/api/v1/alerts', () =>
        HttpResponse.json({
          data: null,
          error: { code: 'SERVER_ERROR', message: 'boom' },
          meta: null,
        }),
      ),
    )

    const { result } = renderHook(() => useAlerts(), { wrapper: createWrapper() })

    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useDismissAlert', () => {
  it('posts to /{id}/dismiss and invalidates the alerts list so the item disappears', async () => {
    let store: TriggeredAlertDto[] = [makeDto({ id: 1 }), makeDto({ id: 2, ticker: 'FPT' })]
    let dismissUrl = ''

    server.use(
      http.get('*/api/v1/alerts', () =>
        HttpResponse.json({ data: store, error: null, meta: null }),
      ),
      http.post('*/api/v1/alerts/:id/dismiss', ({ params, request }) => {
        dismissUrl = request.url
        const id = Number(params.id)
        store = store.filter((a) => Number(a.id) !== id)
        return HttpResponse.json({ data: { id, isDismissed: true }, error: null, meta: null })
      }),
    )

    const wrapper = createWrapper()
    const alerts = renderHook(() => useAlerts({ isDismissed: false }), { wrapper })
    const dismiss = renderHook(() => useDismissAlert(), { wrapper })

    await waitFor(() => expect(alerts.result.current.data).toHaveLength(2))

    dismiss.result.current.mutate('1')

    await waitFor(() => expect(dismiss.result.current.isSuccess).toBe(true))
    expect(new URL(dismissUrl).pathname).toBe('/api/v1/alerts/1/dismiss')
    await waitFor(() => {
      expect(alerts.result.current.data?.map((a) => a.id)).toEqual(['2'])
    })
  })
})
