import { ApiError } from '../../../lib/api/client'

export function getQuestionsErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.errorCode === 'HACKATHON_NOT_FOUND') {
    return 'Ten hackathon nie istnieje lub został usunięty.'
  }

  return 'Nie udało się pobrać formularza zgłoszeniowego. Spróbuj ponownie.'
}

export function getCreateQuestionsErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return 'Nie udało się utworzyć pytań. Spróbuj ponownie.'
  }

  const messages: Record<string, string> = {
    HACKATHON_NOT_FOUND: 'Ten hackathon nie istnieje lub został usunięty.',
    REGISTRATION_PERMISSION_DENIED: 'Nie masz uprawnień do zarządzania pytaniami.',
    VALIDATION_ERROR: 'Sprawdź poprawność pytań.',
  }

  return error.errorCode ? (messages[error.errorCode] ?? error.message) : error.message
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
