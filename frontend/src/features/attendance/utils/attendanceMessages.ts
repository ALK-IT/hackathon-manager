import { ApiError } from '../../../lib/api/client'

const messages: Record<string, string> = {
  CHECK_IN_NOT_ALLOWED:
    'Obecność mogą potwierdzić wyłącznie uczestnicy z zaakceptowanym zgłoszeniem.',
  INVALID_CHECK_IN_TOKEN: 'Kod QR jest nieprawidłowy lub wygasł.',
  HACKATHON_NOT_IN_PROGRESS:
    'Obecność można potwierdzić tylko podczas trwania hackathonu.',
  PERMISSION_DENIED: 'Nie masz uprawnień do zarządzania obecnością.',
  HACKATHON_NOT_FOUND: 'Nie znaleziono hackathonu.',
}

export function getAttendanceErrorMessage(
  error: unknown,
  fallback: string,
): string {
  if (!(error instanceof ApiError)) return fallback
  if (error.errorCode && messages[error.errorCode]) {
    return messages[error.errorCode]
  }
  return fallback
}

export function getCameraErrorMessage(error: unknown): string {
  if (error instanceof DOMException) {
    if (error.name === 'NotAllowedError') {
      return 'Brak dostępu do kamery. Zezwól przeglądarce na jej użycie.'
    }
    if (error.name === 'NotFoundError') {
      return 'Nie znaleziono kamery na tym urządzeniu.'
    }
  }
  return 'Nie udało się uruchomić kamery.'
}
