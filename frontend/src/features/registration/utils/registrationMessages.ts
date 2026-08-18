import { ApiError } from '../../../lib/api/client'

export function getQuestionsErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.errorCode === 'HACKATHON_NOT_FOUND') {
    return 'Ten hackathon nie istnieje lub został usunięty.'
  }

  return 'Nie udało się pobrać formularza zgłoszeniowego. Spróbuj ponownie.'
}

export function areRegistrationQuestionsLocked(error: unknown): boolean {
  return (
    error instanceof ApiError &&
    error.errorCode === 'REGISTRATION_QUESTIONS_LOCKED'
  )
}

export function getQuestionManagementErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return 'Nie udało się zapisać zmian. Spróbuj ponownie.'
  }

  const messages: Record<string, string> = {
    HACKATHON_NOT_FOUND: 'Ten hackathon nie istnieje lub został usunięty.',
    QUESTION_NOT_FOUND: 'To pytanie już nie istnieje. Odśwież stronę.',
    REGISTRATION_PERMISSION_DENIED: 'Nie masz uprawnień do edycji tych pytań.',
    REGISTRATION_QUESTIONS_LOCKED:
      'Nie można już zmieniać pytań, ponieważ rejestracja została otwarta.',
    VALIDATION_ERROR: 'Sprawdź treść pytania i spróbuj ponownie.',
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
