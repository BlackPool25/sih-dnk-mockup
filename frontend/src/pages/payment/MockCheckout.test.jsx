import React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

vi.mock('../../services/api.js', async () => {
  const actual = await vi.importActual('../../services/api.js')
  return {
    ...actual,
    getPaymentMock: vi.fn(),
    payPaymentMock: vi.fn(),
    getAccessToken: vi.fn(() => 'test-token'),
  }
})

import { getPaymentMock, payPaymentMock } from '../../services/api.js'
import MockCheckout from './MockCheckout.jsx'

function renderWithRouter(id = 'pay-123') {
  return render(
    <MemoryRouter initialEntries={[`/payment/mock/${id}`]}>
      <Routes>
        <Route path="/payment/mock/:id" element={<MockCheckout />} />
      </Routes>
    </MemoryRouter>
  )
}

const initiatedPayload = {
  payment_id: 'pay-123',
  amount: 12300,
  amount_minor: 12300,
  status: 'initiated',
  dnk_fees: 2500,
  customs_excluded: true,
  order_id: 'order-999',
  quote_id: 'quote-abc',
}

const paidPayload = {
  ...initiatedPayload,
  status: 'paid_held',
}

describe('MockCheckout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('user', JSON.stringify({ id: 'u1', role: 'buyer', userType: 'buyer' }))
    localStorage.setItem('token', 'test-token')
    localStorage.setItem('access_token', 'test-token')
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  it('shows loading then amount, DNK fees line, customs excluded disclaimer, Pay button', async () => {
    getPaymentMock.mockResolvedValue(initiatedPayload)

    renderWithRouter('pay-123')

    expect(screen.getByText(/loading/i)).toBeInTheDocument()

    await waitFor(() => expect(getPaymentMock).toHaveBeenCalledWith('pay-123'))
    await waitFor(() => expect(screen.getAllByText(/₹123\.00/).length).toBeGreaterThan(0))
    expect(screen.getAllByText(/DNK fees/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/Customs not to seller/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Pay/i })).toBeInTheDocument()
    expect(screen.getAllByText(/initiated/i).length).toBeGreaterThan(0)
  })

  it('click Pay → calls POST /payment/mock/:id/pay → status paid_held after poll', async () => {
    getPaymentMock.mockResolvedValue(initiatedPayload)
    payPaymentMock.mockResolvedValue(paidPayload)

    renderWithRouter('pay-123')

    await waitFor(() => expect(screen.getByRole('button', { name: /Pay/i })).toBeInTheDocument())

    const payBtn = screen.getByRole('button', { name: /Pay/i })
    await act(async () => {
      fireEvent.click(payBtn)
    })

    await waitFor(() => expect(payPaymentMock).toHaveBeenCalledWith('pay-123'))
    await waitFor(() => expect(screen.getAllByText(/paid_held/i).length).toBeGreaterThan(0))
    await waitFor(() => expect(screen.getByRole('button', { name: /Paid/i })).toBeDisabled())
  })

  it('polls every 3000ms until paid_held, stops after', async () => {
    vi.useFakeTimers()
    getPaymentMock.mockResolvedValue(initiatedPayload)
    payPaymentMock.mockResolvedValue(paidPayload)
    renderWithRouter('pay-123')
    await act(async () => { await Promise.resolve(); await Promise.resolve() })
    expect(getPaymentMock).toHaveBeenCalled()
    getPaymentMock.mockClear()
    await act(async () => { vi.advanceTimersByTime(3000); await Promise.resolve(); await Promise.resolve() })
    expect(getPaymentMock).toHaveBeenCalled()
    getPaymentMock.mockClear()
    await act(async () => { vi.advanceTimersByTime(3000); await Promise.resolve(); await Promise.resolve() })
    expect(getPaymentMock).toHaveBeenCalled()
    const payBtn = screen.getByRole('button', { name: /Pay/i })
    await act(async () => { fireEvent.click(payBtn); await Promise.resolve(); await Promise.resolve() })
    getPaymentMock.mockClear()
    await act(async () => { vi.advanceTimersByTime(6000); await Promise.resolve(); await Promise.resolve() })
    expect(getPaymentMock).not.toHaveBeenCalled()
    vi.useRealTimers()
  })

  it('shows error state when fetch fails', async () => {
    getPaymentMock.mockRejectedValue(new Error('Not found'))

    renderWithRouter('bad-id')

    await waitFor(() => expect(screen.getByText(/failed to load payment/i)).toBeInTheDocument())
  })

  it('shows pay error and keeps Pay enabled', async () => {
    getPaymentMock.mockResolvedValue(initiatedPayload)
    payPaymentMock.mockRejectedValue(new Error('Payment failed'))

    renderWithRouter('pay-123')
    await waitFor(() => expect(screen.getByRole('button', { name: /Pay/i })).toBeInTheDocument())

    const btn = screen.getByRole('button', { name: /Pay/i })
    await act(async () => {
      fireEvent.click(btn)
    })

    await waitFor(() => expect(screen.getByText(/Payment failed/i)).toBeInTheDocument())
    expect(screen.getByRole('button', { name: /Pay/i })).not.toBeDisabled()
  })

  it('does not leak interval on unmount', async () => {
    getPaymentMock.mockResolvedValue(initiatedPayload)
    const { unmount } = renderWithRouter('pay-123')
    await waitFor(() => expect(screen.getAllByText(/₹123\.00/).length).toBeGreaterThan(0))
    const clearSpy = vi.spyOn(global, 'clearInterval')
    unmount()
    expect(clearSpy).toHaveBeenCalled()
    clearSpy.mockRestore()
  })

  it('no external navigation: does not render link to pay.mock', async () => {
    getPaymentMock.mockResolvedValue(initiatedPayload)
    renderWithRouter('pay-123')
    await waitFor(() => expect(screen.getAllByText(/₹123\.00/).length).toBeGreaterThan(0))
    expect(document.body.innerHTML).not.toContain('pay.mock')
    expect(document.body.innerHTML).not.toContain('https://pay.mock')
  })
})
