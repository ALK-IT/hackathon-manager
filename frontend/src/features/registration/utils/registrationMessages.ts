import { ApiError } from '../../../lib/api/client'

export function isRegistrationNotFoundError(error: unknown): boolean {
  return error instanceof ApiError && error.errorCode === 'REGISTRATION_NOT_FOUND'
}

export function getQuestionsErrorMessage(error: unknown, language: 'pl' | 'en' = 'pl'): string {
  if (language === 'en') return error instanceof ApiError && error.errorCode === 'HACKATHON_NOT_FOUND' ? 'This hackathon does not exist or has been removed.' : 'Could not load the application form. Try again.'
  if (error instanceof ApiError && error.errorCode === 'HACKATHON_NOT_FOUND') {
    return 'Ten hackathon nie istnieje lub został usunięty.'
  }

  return 'Nie udało się pobrać formularza zgłoszeniowego. Spróbuj ponownie.'
}

export function getSaveQuestionsErrorMessage(error: unknown, language: 'pl' | 'en' = 'pl'): string {
  if (language === 'en') {
    if (!(error instanceof ApiError)) return 'Could not save the questions. Try again.'
    const messages: Record<string, string> = { REGISTRATION_QUESTIONS_LOCKED: 'Questions cannot be changed after registration opens.', REGISTRATION_PERMISSION_DENIED: 'You do not have permission to change registration questions.', HACKATHON_NOT_FOUND: 'This hackathon does not exist or has been removed.', VALIDATION_ERROR: 'The form must contain between 1 and 50 valid questions.' }
    if (error.status === 403) return messages.REGISTRATION_PERMISSION_DENIED
    if (error.status === 404) return messages.HACKATHON_NOT_FOUND
    return error.errorCode ? (messages[error.errorCode] ?? 'Could not save the questions.') : 'Could not save the questions.'
  }
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

  return 'Nie udało się zapisać pytań. Spróbuj ponownie.'
}

export function getRegistrationErrorMessage(error: unknown, language: 'pl' | 'en' = 'pl'): string {
  if (language === 'en') {
    if (!(error instanceof ApiError)) return 'Could not submit the application. Try again.'
    const messages: Record<string, string> = { ALREADY_REGISTERED: 'You already applied to this hackathon.', REGISTRATION_CLOSED: 'Registration for this hackathon is closed.', MISSING_REQUIRED_ANSWERS: 'Answer all required questions.', INVALID_REGISTRATION_QUESTION: 'The form has changed. Refresh the page and try again.', TEAM_NOT_FOUND: 'No team was found for this code.', TEAM_FULL: 'This team has reached its member limit.', TEAM_NAME_TAKEN: 'A team with this name already exists in this hackathon.', VALIDATION_ERROR: 'Check the form data.' }
    return error.errorCode ? (messages[error.errorCode] ?? 'Could not submit the application.') : 'Could not submit the application.'
  }
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

  return error.errorCode ? (messages[error.errorCode] ?? 'Nie udało się wysłać zgłoszenia.') : 'Nie udało się wysłać zgłoszenia.'
}

export function getManagedRegistrationsErrorMessage(error: unknown, language: 'pl' | 'en' = 'pl'): string {
  if (language === 'en') {
    if (!(error instanceof ApiError)) return 'Could not load applications.'
    if (error.status === 403) return 'You do not have permission to view these applications.'
    if (error.status === 404 || error.errorCode === 'HACKATHON_NOT_FOUND') return 'This hackathon does not exist or has been removed.'
    return 'Could not load applications.'
  }
  if (!(error instanceof ApiError)) return 'Nie udało się pobrać zgłoszeń.'
  if (error.status === 403) return 'Nie masz uprawnień do przeglądania tych zgłoszeń.'
  if (error.status === 404 || error.errorCode === 'HACKATHON_NOT_FOUND') {
    return 'Ten hackathon nie istnieje lub został usunięty.'
  }
  return 'Nie udało się pobrać zgłoszeń.'
}

export function getManagedRegistrationStatusErrorMessage(error: unknown, language: 'pl' | 'en' = 'pl'): string {
  if (language === 'en') {
    if (!(error instanceof ApiError)) return 'Could not change the application status.'
    const messages: Record<string, string> = { REGISTRATION_STATUS_CHANGE_LOCKED: 'Application statuses cannot be changed after the hackathon ends.', REGISTRATION_CLOSED: 'The status cannot be changed because registration is closed.', REGISTRATION_NOT_FOUND: 'This application does not exist or has been removed.', REGISTRATION_PERMISSION_DENIED: 'You do not have permission to change this application status.', TEAM_FULL: 'The application cannot be accepted because the team is full.', VALIDATION_ERROR: 'The selected application status cannot be set.' }
    if (error.status === 403) return messages.REGISTRATION_PERMISSION_DENIED
    if (error.status === 404) return messages.REGISTRATION_NOT_FOUND
    return error.errorCode ? (messages[error.errorCode] ?? 'Could not change the application status.') : 'Could not change the application status.'
  }
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
  return error.errorCode ? (messages[error.errorCode] ?? 'Nie udało się zmienić statusu zgłoszenia.') : 'Nie udało się zmienić statusu zgłoszenia.'
}

export function isRegistrationStatusChangeLockedError(error: unknown): boolean {
  return error instanceof ApiError && error.errorCode === 'REGISTRATION_STATUS_CHANGE_LOCKED'
}

export function getParticipantAreaErrorMessage(error: unknown, language: 'pl' | 'en' = 'pl'): string {
  if (language === 'en') {
    if (!(error instanceof ApiError)) return 'Could not load the participant area. Try again.'
    const messages: Record<string, string> = { REGISTRATION_NOT_FOUND: 'You have not applied to this hackathon.', REGISTRATION_NOT_ACCEPTED: 'The participant area will be available after your application is accepted.' }
    return error.errorCode ? (messages[error.errorCode] ?? 'Could not load the participant area.') : 'Could not load the participant area.'
  }
  if (!(error instanceof ApiError)) {
    return 'Nie udało się pobrać strefy uczestnika. Spróbuj ponownie.'
  }

  const messages: Record<string, string> = {
    REGISTRATION_NOT_FOUND: 'Nie masz zgłoszenia do tego hackathonu.',
    REGISTRATION_NOT_ACCEPTED: 'Strefa uczestnika będzie dostępna po zaakceptowaniu zgłoszenia.',
  }

  return error.errorCode ? (messages[error.errorCode] ?? 'Nie udało się pobrać strefy uczestnika.') : 'Nie udało się pobrać strefy uczestnika.'
}

export function getTaskSubmissionErrorMessage(error: unknown, language: 'pl' | 'en' = 'pl'): string {
  if (language === 'en') {
    if (!(error instanceof ApiError)) return 'Could not save the solution. Try again.'
    const messages: Record<string, string> = { REGISTRATION_NOT_ACCEPTED: 'Only an accepted participant can submit a solution.', TEAM_REQUIRED_FOR_SUBMISSION: 'You must be on a team to submit a solution.', TASKS_NOT_RELEASED: 'Tasks have not been published yet.', TASK_SUBMISSION_CLOSED: 'The solution submission deadline has passed.', TASK_NOT_FOUND: 'This task does not exist.', VALIDATION_ERROR: 'Enter a valid GitHub repository link.' }
    return error.errorCode ? (messages[error.errorCode] ?? 'Could not save the solution.') : 'Could not save the solution.'
  }
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

  return error.errorCode ? (messages[error.errorCode] ?? 'Nie udało się zapisać rozwiązania.') : 'Nie udało się zapisać rozwiązania.'
}
