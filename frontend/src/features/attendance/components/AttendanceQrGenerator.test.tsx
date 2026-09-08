import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
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
})
