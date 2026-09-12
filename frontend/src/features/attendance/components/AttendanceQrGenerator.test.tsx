import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createCheckInSession } from '../api/attendanceApi'
import { AttendanceQrGenerator } from './AttendanceQrGenerator'

const qrCodeMocks = vi.hoisted(() => ({ toDataURL: vi.fn() }))

vi.mock('qrcode', () => ({ default: qrCodeMocks }))
vi.mock('../api/attendanceApi', () => ({
  createCheckInSession: vi.fn(),
}))

describe('AttendanceQrGenerator', () => {
  beforeEach(() => {
    vi.mocked(createCheckInSession).mockReset()
    qrCodeMocks.toDataURL.mockReset()
  })

  afterEach(() => vi.useRealTimers())

  it('creates a session and displays a QR code without exposing its token as text', async () => {
    vi.mocked(createCheckInSession).mockResolvedValue({
      public_id: 'session-id',
      token: 'secret-check-in-token',
      expires_at: '2099-09-08T12:15:00Z',
      is_active: true,
    })
    qrCodeMocks.toDataURL.mockResolvedValue('data:image/png;base64,qr-code')
    render(<AttendanceQrGenerator hackathonPublicId="hackathon-id" />)

    fireEvent.click(screen.getByRole('button', { name: 'Wygeneruj kod QR' }))

    expect(
      await screen.findByRole('img', {
        name: 'Kod QR do potwierdzenia obecności',
      }),
    ).toHaveAttribute('src', 'data:image/png;base64,qr-code')
    expect(createCheckInSession).toHaveBeenCalledWith('hackathon-id')
    expect(qrCodeMocks.toDataURL).toHaveBeenCalledWith(
      'secret-check-in-token',
      expect.objectContaining({ width: 280 }),
    )
    expect(screen.queryByText('secret-check-in-token')).not.toBeInTheDocument()
  })

  it('hides the QR code and reports when the session expires', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-09-11T12:00:00Z'))
    vi.mocked(createCheckInSession).mockResolvedValue({
      public_id: 'session-id',
      token: 'secret-check-in-token',
      expires_at: '2026-09-11T12:00:02Z',
      is_active: true,
    })
    qrCodeMocks.toDataURL.mockResolvedValue('data:image/png;base64,qr-code')
    render(<AttendanceQrGenerator hackathonPublicId="hackathon-id" />)

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Wygeneruj kod QR' }))
    })

    expect(
      screen.getByRole('img', {
        name: 'Kod QR do potwierdzenia obecności',
      }),
    ).toBeInTheDocument()
    expect(screen.getByRole('timer')).toHaveTextContent('Kod QR wygaśnie za: 0:02')

    act(() => vi.advanceTimersByTime(2000))

    expect(screen.queryByRole('img')).not.toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent(
      'Kod QR wygasł. Wygeneruj nowy kod.',
    )
  })
})
