import { useEffect, useState } from 'react'
import { ApiError } from '../../lib/api/client'

export function useHasEnded(endDate: string) {
  const [now, setNow] = useState(Date.now)
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(timer)
  }, [])
  return now >= Date.parse(endDate)
}

export function evaluationError(error: unknown) {
  if (error instanceof ApiError) {
    const messages: Record<string, string> = {
      TASK_EVALUATION_NOT_OPEN: 'Ocenianie jest dostępne dopiero po zakończeniu hackathonu.',
      TASK_SUBMISSION_NOT_FOUND: 'Nie znaleziono rozwiązania. Odśwież listę.',
      TASK_NOT_FOUND: 'Nie znaleziono zadania.',
      HACKATHON_NOT_FOUND: 'Nie znaleziono hackathonu.',
      PERMISSION_DENIED: 'Nie masz uprawnień do przeglądania lub oceniania tych rozwiązań.',
      TASK_PERMISSION_DENIED: 'Nie masz uprawnień do przeglądania lub oceniania tych rozwiązań.',
    }
    if (error.errorCode && messages[error.errorCode]) return messages[error.errorCode]
    if (error.status === 401) return 'Zaloguj się ponownie.'
    if (error.status === 403) return 'Nie masz uprawnień do tych rozwiązań.'
    if (error.status === 422) return 'Sprawdź ocenę (0–10, maksymalnie dwa miejsca po przecinku) i feedback.'
  }
  return 'Nie udało się wykonać operacji. Spróbuj ponownie.'
}
