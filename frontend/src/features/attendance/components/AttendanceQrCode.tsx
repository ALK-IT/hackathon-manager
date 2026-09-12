import { useEffect, useState } from 'react'
import { Alert } from '../../../components/ui'

interface AttendanceQrCodeProps {
  dataUrl: string
  expiresAt: string
  onExpire?: () => void
}

function getRemainingSeconds(expiresAt: number, now: number): number {
  return Math.max(0, Math.ceil((expiresAt - now) / 1000))
}

function formatRemainingTime(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

export function AttendanceQrCode({
  dataUrl,
  expiresAt,
  onExpire,
}: AttendanceQrCodeProps) {
  const [now, setNow] = useState(() => Date.now())
  const expirationTimestamp = new Date(expiresAt).getTime()
  const remainingSeconds = Number.isNaN(expirationTimestamp)
    ? 0
    : getRemainingSeconds(expirationTimestamp, now)

  useEffect(() => {
    if (Number.isNaN(expirationTimestamp)) return

    const intervalId = window.setInterval(() => {
      const currentTime = Date.now()
      setNow(currentTime)

      if (currentTime >= expirationTimestamp) {
        window.clearInterval(intervalId)
        onExpire?.()
      }
    }, 1000)

    return () => window.clearInterval(intervalId)
  }, [expirationTimestamp, onExpire])

  if (remainingSeconds === 0) {
    return (
      <div className="attendance-qr-result">
        <Alert variant="error">Kod QR wygasł. Wygeneruj nowy kod.</Alert>
      </div>
    )
  }

  return (
    <div className="attendance-qr-result">
      <img src={dataUrl} alt="Kod QR do potwierdzenia obecności" />
      <p>Ważny do: {new Date(expiresAt).toLocaleString('pl-PL')}</p>
      <p
        role="timer"
        aria-live="off"
        aria-label={`Kod QR wygaśnie za ${remainingSeconds} sekund`}
      >
        Kod QR wygaśnie za: {formatRemainingTime(remainingSeconds)}
      </p>
    </div>
  )
}
