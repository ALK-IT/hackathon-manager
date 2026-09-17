import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { checkInCurrentUser } from '../api/attendanceApi'
import { AttendanceQrScanner } from './AttendanceQrScanner'

const scannerMocks = vi.hoisted(() => ({
  decodeFromVideoDevice: vi.fn(),
  stop: vi.fn(),
}))

vi.mock('@zxing/browser', () => ({
  BrowserQRCodeReader: class {
    decodeFromVideoDevice = scannerMocks.decodeFromVideoDevice
  },
}))
vi.mock('../api/attendanceApi', () => ({ checkInCurrentUser: vi.fn() }))

describe('AttendanceQrScanner', () => {
  beforeEach(() => {
    scannerMocks.decodeFromVideoDevice.mockReset()
    scannerMocks.stop.mockReset()
    vi.mocked(checkInCurrentUser).mockReset()
  })

  it('starts the camera after a click and sends the scanned token', async () => {
    scannerMocks.decodeFromVideoDevice.mockImplementation(
      async (_deviceId, _video, callback) => {
        callback(
          { getText: () => 'scanned-check-in-token' },
          undefined,
          { stop: scannerMocks.stop },
        )
        return { stop: scannerMocks.stop }
      },
    )
    vi.mocked(checkInCurrentUser).mockResolvedValue({
      public_id: 'check-in-id',
      checked_in_at: '2099-09-08T12:00:00Z',
    })
    render(<AttendanceQrScanner hackathonPublicId="hackathon-id" />)

    expect(scannerMocks.decodeFromVideoDevice).not.toHaveBeenCalled()
    fireEvent.click(screen.getByRole('button', { name: 'Skanuj kod QR' }))

    await waitFor(() =>
      expect(checkInCurrentUser).toHaveBeenCalledWith(
        'hackathon-id',
        'scanned-check-in-token',
      ),
    )
    expect(scannerMocks.stop).toHaveBeenCalled()
    expect(
      await screen.findByText('Obecność została potwierdzona.'),
    ).toBeInTheDocument()
  })
})
