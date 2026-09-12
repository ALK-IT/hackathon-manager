import { useState } from 'react'
import { Alert, Button } from '../../../components/ui'
import { createCheckInSession } from '../api/attendanceApi'
import { getAttendanceErrorMessage } from '../utils/attendanceMessages'
import { AttendanceQrCode } from './AttendanceQrCode'

interface AttendanceQrGeneratorProps {
  hackathonPublicId: string
}

export function AttendanceQrGenerator({
  hackathonPublicId,
}: AttendanceQrGeneratorProps) {
  const [qrCodeUrl, setQrCodeUrl] = useState<string | null>(null)
  const [expiresAt, setExpiresAt] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)

  async function handleGenerate() {
    setError(null)
    setQrCodeUrl(null)
    setExpiresAt(null)
    setIsGenerating(true)

    try {
      const [session, { default: QRCode }] = await Promise.all([
        createCheckInSession(hackathonPublicId),
        import('qrcode'),
      ])
      const dataUrl = await QRCode.toDataURL(session.token, {
        errorCorrectionLevel: 'M',
        margin: 2,
        width: 280,
      })
      setQrCodeUrl(dataUrl)
      setExpiresAt(session.expires_at)
    } catch (requestError) {
      setError(
        getAttendanceErrorMessage(
          requestError,
          'Nie udało się wygenerować kodu QR.',
        ),
      )
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <section aria-labelledby="attendance-qr-heading">
      <h2 id="attendance-qr-heading">Potwierdzanie obecności</h2>
      <p>Kod jest ważny przez 15 minut. Nowy kod unieważnia poprzedni.</p>
      {error && <Alert variant="error">{error}</Alert>}
      <Button
        type="button"
        variant="ghost"
        disabled={isGenerating}
        onClick={() => void handleGenerate()}
      >
        {isGenerating
          ? 'Generowanie…'
          : qrCodeUrl
            ? 'Wygeneruj nowy kod QR'
            : 'Wygeneruj kod QR'}
      </Button>
      {qrCodeUrl && expiresAt && (
        <AttendanceQrCode
          key={expiresAt}
          dataUrl={qrCodeUrl}
          expiresAt={expiresAt}
        />
      )}
    </section>
  )
}
