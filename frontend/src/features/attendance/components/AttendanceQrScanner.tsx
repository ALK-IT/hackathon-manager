import type { IScannerControls } from '@zxing/browser'
import { useEffect, useRef, useState } from 'react'
import { Alert, Button } from '../../../components/ui'
import { checkInCurrentUser } from '../api/attendanceApi'
import {
  getAttendanceErrorMessage,
  getCameraErrorMessage,
} from '../utils/attendanceMessages'

interface AttendanceQrScannerProps {
  hackathonPublicId: string
}

export function AttendanceQrScanner({
  hackathonPublicId,
}: AttendanceQrScannerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const controlsRef = useRef<IScannerControls | null>(null)
  const isProcessingRef = useRef(false)
  const [isScanning, setIsScanning] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  function stopScanning() {
    controlsRef.current?.stop()
    controlsRef.current = null
    setIsScanning(false)
  }

  useEffect(() => {
    return () => {
      controlsRef.current?.stop()
      controlsRef.current = null
    }
  }, [])

  async function submitToken(token: string) {
    setIsSubmitting(true)
    setError(null)
    try {
      await checkInCurrentUser(hackathonPublicId, token)
      setSuccessMessage('Obecność została potwierdzona.')
    } catch (requestError) {
      setError(
        getAttendanceErrorMessage(
          requestError,
          'Nie udało się potwierdzić obecności.',
        ),
      )
    } finally {
      setIsSubmitting(false)
      isProcessingRef.current = false
    }
  }

  async function startScanning() {
    setError(null)
    setSuccessMessage(null)
    setIsScanning(true)
    isProcessingRef.current = false

    try {
      const { BrowserQRCodeReader } = await import('@zxing/browser')
      const reader = new BrowserQRCodeReader(undefined, {
        delayBetweenScanAttempts: 300,
      })
      const controls = await reader.decodeFromVideoDevice(
        undefined,
        videoRef.current ?? undefined,
        (result, _scanError, controls) => {
          if (!result || isProcessingRef.current) return
          isProcessingRef.current = true
          controls.stop()
          controlsRef.current = null
          setIsScanning(false)
          void submitToken(result.getText())
        },
      )
      if (isProcessingRef.current) {
        controls.stop()
      } else {
        controlsRef.current = controls
      }
    } catch (cameraError) {
      setIsScanning(false)
      setError(getCameraErrorMessage(cameraError))
    }
  }

  return (
    <section aria-labelledby="attendance-scanner-heading">
      <h2 id="attendance-scanner-heading">Potwierdzenie obecności</h2>
      <p>Zeskanuj kod QR wyświetlony przez organizatora.</p>
      {error && <Alert variant="error">{error}</Alert>}
      {successMessage && <Alert>{successMessage}</Alert>}
      <div className="attendance-scanner-actions">
        {!isScanning ? (
          <Button
            type="button"
            variant="ghost"
            disabled={isSubmitting}
            onClick={() => void startScanning()}
          >
            {isSubmitting ? 'Potwierdzanie…' : 'Skanuj kod QR'}
          </Button>
        ) : (
          <Button type="button" variant="ghost" onClick={stopScanning}>
            Zatrzymaj skanowanie
          </Button>
        )}
      </div>
      <video
        ref={videoRef}
        className={
          isScanning
            ? 'attendance-scanner-video'
            : 'attendance-scanner-video is-hidden'
        }
        aria-label="Podgląd kamery do skanowania kodu QR"
        muted
        playsInline
      />
    </section>
  )
}
