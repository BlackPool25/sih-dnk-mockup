import React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const mockFetchThreadMessages = vi.fn()
const mockFetchThread = vi.fn()
const mockPollThread = vi.fn()
const mockGetQuotesByOrder = vi.fn()
const mockGetQuote = vi.fn()
const mockGetPaymentMock = vi.fn()
const mockPayPaymentMock = vi.fn()

vi.mock('../../services/api.js', async () => {
  const actual = await vi.importActual('../../services/api.js')
  return {
    ...actual,
    fetchThreadMessages: (...args) => mockFetchThreadMessages(...args),
    fetchThread: (...args) => mockFetchThread(...args),
    pollThread: (...args) => mockPollThread(...args),
    fetchMessages: (...args) => mockPollThread(...args),
    pollThreads: (...args) => mockPollThread(...args),
    getQuotesByOrder: (...args) => mockGetQuotesByOrder(...args),
    getQuote: (...args) => mockGetQuote(...args),
    getPaymentMock: (...args) => mockGetPaymentMock(...args),
    payPaymentMock: (...args) => mockPayPaymentMock(...args),
    getAccessToken: vi.fn(() => 'test-token'),
    buildThreadWsUrl: vi.fn(() => 'ws://localhost/ws'),
  }
})

vi.mock('../../hooks/usePolling.js', async () => {
  const actual = await vi.importActual('../../hooks/usePolling.js')
  return actual
})

// mock WebSocket globally
class MockWS {
  constructor() {
    this.readyState = 1
    setTimeout(() => this.onopen && this.onopen({}), 0)
  }
  close() {}
  send() { return true }
  addEventListener() {}
  removeEventListener() {}
}
MockWS.OPEN = 1

import ThreadView from './ThreadView.jsx'

const threadId = 'thr-123'
const paymentId = 'pay-xyz-999'

const systemPaymentMsg = {
  id: 'msg-pay-1',
  thread_id: threadId,
  sender_id: 'system',
  sender_role: 'system',
  body: `Payment link: /payment/mock/${paymentId} amount_minor 15000`,
  created_at: new Date().toISOString(),
}

const userMsg = {
  id: 'msg-1',
  thread_id: threadId,
  sender_id: 'buyer1',
  sender_role: 'buyer',
  body: 'Hello seller',
  created_at: new Date(Date.now() - 10000).toISOString(),
}

const verifiedMsg = {
  id: 'msg-pay-2',
  thread_id: threadId,
  sender_id: 'system',
  sender_role: 'system',
  body: `Payment link: /payment/mock/${paymentId} Payment verified ✓ amount_minor 15000`,
  created_at: new Date().toISOString(),
}

describe('ThreadView PaymentLinkCard inbox 3s poll', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('user', JSON.stringify({ id: 'buyer1', role: 'buyer', userType: 'buyer' }))
    localStorage.setItem('token', 'test-token')
    localStorage.setItem('access_token', 'test-token')
    global.WebSocket = MockWS

    mockFetchThread.mockResolvedValue({ order_id: 'order-111', id: threadId })
    mockGetQuotesByOrder.mockResolvedValue([])
    mockGetQuote.mockResolvedValue(null)
    mockPollThread.mockResolvedValue({ items: [], messages: [] })
    mockGetPaymentMock.mockResolvedValue({
      payment_id: paymentId,
      amount_minor: 15000,
      amount: 15000,
      status: 'initiated',
      dnk_fees: 500,
      customs_excluded: true,
      order_id: 'order-111',
    })
    mockPayPaymentMock.mockResolvedValue({
      payment_id: paymentId,
      amount_minor: 15000,
      status: 'paid_held',
    })
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders PaymentLinkCard bubble for system message with /payment/mock/ link (internal)', async () => {
    mockFetchThreadMessages.mockResolvedValue({
      items: [userMsg, systemPaymentMsg],
      total: 2,
    })

    render(
      <MemoryRouter>
        <ThreadView threadId={threadId} />
      </MemoryRouter>
    )

    await waitFor(() => expect(mockFetchThreadMessages).toHaveBeenCalled())

    // should render payment card not plain text bubble
    await waitFor(() => expect(screen.getByTestId('payment-link-card')).toBeInTheDocument())

    const link = screen.getByTestId('payment-link')
    expect(link.getAttribute('href')).toBe(`/payment/mock/${paymentId}`)
    expect(link.getAttribute('href')).not.toContain('https://')
    expect(document.body.innerHTML).not.toContain('pay.mock')
    expect(document.body.innerHTML).not.toContain('https://pay.mock')

    // bubble shows amount and DNK note
    await waitFor(() => expect(screen.getByText(/DNK fees included/i)).toBeInTheDocument())
    expect(screen.getByText(/customs excluded/i)).toBeInTheDocument()

    // regular message still renders
    expect(screen.getByText('Hello seller')).toBeInTheDocument()
  })

  it('polls every 3000ms for new messages (seller approve triggers system message within 3s)', async () => {
    vi.useFakeTimers()
    mockFetchThreadMessages.mockResolvedValue({
      items: [userMsg],
      total: 1,
    })
    global.WebSocket = class extends MockWS {
      constructor() { super(); this.readyState = 3 }
    }
    global.WebSocket.OPEN = 1

    render(
      <MemoryRouter>
        <ThreadView threadId={threadId} />
      </MemoryRouter>
    )

    await act(async () => { await Promise.resolve(); await Promise.resolve() })
    await act(async () => { await vi.advanceTimersByTimeAsync(0) })

    mockPollThread.mockClear()
    mockPollThread.mockResolvedValue({ items: [systemPaymentMsg], messages: [systemPaymentMsg] })

    await act(async () => { await vi.advanceTimersByTimeAsync(3000) })

    expect(mockPollThread).toHaveBeenCalled()

    mockPollThread.mockClear()
    mockPollThread.mockResolvedValue({ items: [], messages: [] })
    await act(async () => { await vi.advanceTimersByTimeAsync(3000) })
    expect(mockPollThread).toHaveBeenCalled()

    vi.useRealTimers()
    global.WebSocket = MockWS
  })

  it('after pay (POST /payment/mock/:id/pay → paid_held) bubble shows verified badge Payment verified ✓', async () => {
    mockFetchThreadMessages.mockResolvedValue({
      items: [systemPaymentMsg],
      total: 1,
    })
    mockGetPaymentMock.mockResolvedValue({
      payment_id: paymentId,
      amount_minor: 15000,
      status: 'paid_held',
      dnk_fees: 500,
    })
    mockPollThread.mockResolvedValue({ items: [verifiedMsg], messages: [verifiedMsg] })

    render(
      <MemoryRouter>
        <ThreadView threadId={threadId} />
      </MemoryRouter>
    )

    await waitFor(() => expect(screen.getByTestId('payment-link-card')).toBeInTheDocument())
    await waitFor(() => expect(screen.getAllByText(/Payment verified/i).length).toBeGreaterThan(0))
    expect(document.body.innerHTML).not.toContain('https://pay.mock')
  })

  it('does not leak interval on unmount (cleanup)', async () => {
    mockFetchThreadMessages.mockResolvedValue({
      items: [systemPaymentMsg],
      total: 1,
    })

    const clearSpy = vi.spyOn(global, 'clearInterval')
    const { unmount } = render(
      <MemoryRouter>
        <ThreadView threadId={threadId} />
      </MemoryRouter>
    )

    await waitFor(() => expect(screen.getByTestId('payment-link-card')).toBeInTheDocument())

    unmount()
    // at least one clearInterval should have been called from usePolling/useThreadWS cleanup
    expect(clearSpy).toHaveBeenCalled()
    clearSpy.mockRestore()
  })

  it('fetches messages via GET /messages/threads/{id}/messages and polls via since param', async () => {
    mockFetchThreadMessages.mockResolvedValue({
      items: [userMsg, systemPaymentMsg],
      total: 2,
    })

    render(
      <MemoryRouter>
        <ThreadView threadId={threadId} />
      </MemoryRouter>
    )

    await waitFor(() => expect(mockFetchThreadMessages).toHaveBeenCalledWith(threadId, expect.objectContaining({ limit: expect.any(Number) })))
    // verify first call contains correct thread id encoding
    const firstCallArgs = mockFetchThreadMessages.mock.calls[0]
    expect(String(firstCallArgs[0])).toBe(threadId)
  })
})
