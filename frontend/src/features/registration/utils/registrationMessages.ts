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

export function getParticipantAreaErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return 'Nie udało się pobrać strefy uczestnika. Spróbuj ponownie.'
  }

  const messages: Record<string, string> = {
    REGISTRATION_NOT_FOUND: 'Nie masz zgłoszenia do tego hackathonu.',
    REGISTRATION_NOT_ACCEPTED: 'Strefa uczestnika będzie dostępna po zaakceptowaniu zgłoszenia.',
  }

  return error.errorCode ? (messages[error.errorCode] ?? error.message) : error.message
}

export function getTaskSubmissionErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return 'Nie udało się zapisać rozwiązania. Spróbuj ponownie.'
  }

  const messages: Record<string, string> = {
    REGISTRATION_NOT_ACCEPTED: 'Tylko zaakceptowany uczestnik może wysłać rozwiązanie.',
    TEAM_REQUIRED_FOR_SUBMISSION: 'Musisz należeć do drużyny, aby wysłać rozwiązanie.',
    TASKS_NOT_RELEASED: 'Zadania nie zostały jeszcze opublikowane.',
    TASK_SUBMISSION_CLOSED: 'Termin wysyłania rozwiązań już minął.',
    TASK_NOT_FOUND: 'To zadanie nie istnieje.',
    VALIDATION_ERROR: 'Podaj poprawny link do repozytorium na GitHubie.',
  }

  return error.errorCode ? (messages[error.errorCode] ?? error.message) : error.message
}
