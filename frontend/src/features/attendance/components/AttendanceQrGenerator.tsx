import { useCallback, useState } from 'react'
import { Alert, Button } from '../../../components/ui'
import { createCheckInSession } from '../api/attendanceApi'
import { getAttendanceErrorMessage } from '../utils/attendanceMessages'
import { AttendanceQrCode } from './AttendanceQrCode'

interface AttendanceQrGeneratorProps {
  hackathonPublicId: string
}

interface StoredQrCode {
  dataUrl: string
  expiresAt: string
}

interface QrCodeState {
  code: StoredQrCode | null
  isActive: boolean
}

function getStorageKey(hackathonPublicId: string): string {
  return `attendance-qr:${hackathonPublicId}`
}

function readStoredQrCode(hackathonPublicId: string): QrCodeState {
  const storageKey = getStorageKey(hackathonPublicId)

  try {
    const storedValue = sessionStorage.getItem(storageKey)
    if (!storedValue) return { code: null, isActive: false }

    const code = JSON.parse(storedValue) as Partial<StoredQrCode>
    const expirationTimestamp = new Date(code.expiresAt ?? '').getTime()
    if (
      typeof code.dataUrl !== 'string' ||
      typeof code.expiresAt !== 'string' ||
      Number.isNaN(expirationTimestamp) ||
      expirationTimestamp <= Date.now()
    ) {
      sessionStorage.removeItem(storageKey)
      return { code: null, isActive: false }
    }

    return { code: code as StoredQrCode, isActive: true }
  } catch {
    sessionStorage.removeItem(storageKey)
    return { code: null, isActive: false }
  }
}

export function AttendanceQrGenerator({
  hackathonPublicId,
}: AttendanceQrGeneratorProps) {
  const storageKey = getStorageKey(hackathonPublicId)
  const [qrCodeState, setQrCodeState] = useState<QrCodeState>(() =>
    readStoredQrCode(hackathonPublicId),
  )
  const [error, setError] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)

  const handleExpire = useCallback(() => {
    sessionStorage.removeItem(storageKey)
    setQrCodeState((currentState) => ({
      ...currentState,
      isActive: false,
    }))
  }, [storageKey])

  function handleRemove() {
    sessionStorage.removeItem(storageKey)
    setQrCodeState({ code: null, isActive: false })
  }

  async function handleGenerate() {
    setError(null)
    setQrCodeState({ code: null, isActive: false })
    sessionStorage.removeItem(storageKey)
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
      const code = { dataUrl, expiresAt: session.expires_at }
      sessionStorage.setItem(storageKey, JSON.stringify(code))
      setQrCodeState({ code, isActive: true })
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
          : qrCodeState.code
            ? 'Wygeneruj nowy kod QR'
            : 'Wygeneruj kod QR'}
      </Button>
      {qrCodeState.isActive && (
        <Button type="button" variant="ghost" onClick={handleRemove}>
          Usuń kod QR
        </Button>
      )}
      {qrCodeState.code && (
        <AttendanceQrCode
          key={qrCodeState.code.expiresAt}
          dataUrl={qrCodeState.code.dataUrl}
          expiresAt={qrCodeState.code.expiresAt}
          onExpire={handleExpire}
        />
      )}
    </section>
  )
}
