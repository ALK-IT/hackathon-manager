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

export function getSaveQuestionsErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return 'Nie udało się zapisać pytań. Spróbuj ponownie.'
  }

  if (error.errorCode === 'REGISTRATION_QUESTIONS_LOCKED') {
    return 'Nie można zmieniać pytań po otwarciu rejestracji.'
  }
  if (error.errorCode === 'REGISTRATION_PERMISSION_DENIED' || error.status === 403) {
    return 'Nie masz uprawnień do zmiany pytań rejestracyjnych.'
  }
  if (error.errorCode === 'HACKATHON_NOT_FOUND' || error.status === 404) {
    return 'Ten hackathon nie istnieje lub został usunięty.'
  }
  if (error.errorCode === 'VALIDATION_ERROR') {
    return 'Formularz może zawierać od 1 do 50 poprawnie uzupełnionych pytań.'
  }

  return error.message
}

export function getRegistrationErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return 'Nie udało się wysłać zgłoszenia. Spróbuj ponownie.'
  }

  const messages: Record<string, string> = {
    ALREADY_REGISTERED: 'Masz już zgłoszenie do tego hackathonu.',
    REGISTRATION_CLOSED: 'Rejestracja na ten hackathon jest już zamknięta.',
    MISSING_REQUIRED_ANSWERS: 'Odpowiedz na wszystkie wymagane pytania.',
    INVALID_REGISTRATION_QUESTION: 'Formularz uległ zmianie. Odśwież stronę i spróbuj ponownie.',
    TEAM_NOT_FOUND: 'Nie znaleziono drużyny z podanym kodem.',
    TEAM_FULL: 'Ta drużyna ma już maksymalną liczbę członków.',
    TEAM_NAME_TAKEN: 'Drużyna o tej nazwie już istnieje w tym hackathonie.',
    VALIDATION_ERROR: 'Sprawdź poprawność danych formularza.',
  }

  return error.errorCode ? (messages[error.errorCode] ?? error.message) : error.message
}
