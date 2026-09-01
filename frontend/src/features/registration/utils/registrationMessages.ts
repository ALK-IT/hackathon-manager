import { ApiError } from '../../../lib/api/client'

export function isRegistrationNotFoundError(error: unknown): boolean {
  return error instanceof ApiError && error.errorCode === 'REGISTRATION_NOT_FOUND'
}

export function getQuestionsErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.errorCode === 'HACKATHON_NOT_FOUND') {
    return 'Ten hackathon nie istnieje lub został usunięty.'
  }

  return 'Nie udało się pobrać formularza zgłoszeniowego. Spróbuj ponownie.'
}

export function getRegistrationErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return 'Nie udało się wysłać zgłoszenia. Spróbuj ponownie.'
  }

  const messages: Record<string, string> = {
    REGISTRATION_ALREADY_EXISTS: 'Masz już zgłoszenie do tego hackathonu.',
    REGISTRATION_CLOSED: 'Rejestracja na ten hackathon jest już zamknięta.',
    MISSING_REQUIRED_ANSWERS: 'Odpowiedz na wszystkie wymagane pytania.',
    INVALID_REGISTRATION_QUESTION: 'Formularz uległ zmianie. Odśwież stronę i spróbuj ponownie.',
    TEAM_NOT_FOUND: 'Nie znaleziono drużyny z podanym kodem.',
    TEAM_FULL: 'Ta drużyna ma już maksymalną liczbę członków.',
    TEAM_NAME_ALREADY_EXISTS: 'Drużyna o tej nazwie już istnieje w tym hackathonie.',
    VALIDATION_ERROR: 'Sprawdź poprawność danych formularza.',
  }

  return error.errorCode ? (messages[error.errorCode] ?? error.message) : error.message
}

export function getManagedRegistrationsErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) return 'Nie udało się pobrać zgłoszeń.'
  if (error.status === 403) return 'Nie masz uprawnień do przeglądania tych zgłoszeń.'
  if (error.status === 404 || error.errorCode === 'HACKATHON_NOT_FOUND') {
    return 'Ten hackathon nie istnieje lub został usunięty.'
  }
  return error.message
}

export function getManagedRegistrationStatusErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) return 'Nie udało się zmienić statusu zgłoszenia.'

  const messages: Record<string, string> = {
    REGISTRATION_STATUS_CHANGE_LOCKED:
      'Nie można zmieniać statusów zgłoszeń po zakończeniu hackathonu.',
    REGISTRATION_CLOSED: 'Nie można zmienić statusu, ponieważ rejestracja jest zamknięta.',
    REGISTRATION_NOT_FOUND: 'To zgłoszenie nie istnieje lub zostało usunięte.',
    REGISTRATION_PERMISSION_DENIED: 'Nie masz uprawnień do zmiany statusu tego zgłoszenia.',
    TEAM_FULL: 'Nie można zaakceptować zgłoszenia, ponieważ drużyna jest już pełna.',
    VALIDATION_ERROR: 'Nie można ustawić wybranego statusu zgłoszenia.',
  }

  if (error.status === 403) return messages.REGISTRATION_PERMISSION_DENIED
  if (error.status === 404) return messages.REGISTRATION_NOT_FOUND
  return error.errorCode ? (messages[error.errorCode] ?? error.message) : error.message
}

export function isRegistrationStatusChangeLockedError(error: unknown): boolean {
  return error instanceof ApiError && error.errorCode === 'REGISTRATION_STATUS_CHANGE_LOCKED'
}
