import { ApiError } from '../../../lib/api/client'

const messages: Record<string, string> = {
  RESOURCE_NOT_FOUND: 'Nie znaleziono wybranej puli zasobów.',
  RESOURCE_RECIPIENT_NOT_FOUND:
    'Nie znaleziono zaakceptowanego zgłoszenia uczestnika.',
  RESOURCE_ITEMS_INSUFFICIENT:
    'W wybranej puli nie ma wystarczającej liczby wolnych zasobów.',
  RESOURCE_TARGET_MISMATCH:
    'W tym widoku można przydzielać wyłącznie zasoby indywidualne.',
  PERMISSION_DENIED: 'Nie masz uprawnień do zarządzania zasobami.',
}

export function getResourceErrorMessage(error: unknown, fallback: string) {
  if (!(error instanceof ApiError)) return fallback
  if (error.errorCode && messages[error.errorCode]) {
    return messages[error.errorCode]
  }
  return fallback
}
