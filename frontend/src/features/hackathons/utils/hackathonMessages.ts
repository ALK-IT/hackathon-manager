import { ApiError } from '../../../lib/api/client'

export function getCreateHackathonErrorMessage(error: unknown, language: 'pl' | 'en' = 'pl'): string {
  if (language === 'en') return mapHackathonError(error, 'create')
  if (error instanceof ApiError) {
    if (error.status === 403) return 'Nie masz uprawnień do tworzenia hackathonów.'
    if (error.errorCode === 'VALIDATION_ERROR') return 'Sprawdź poprawność danych hackathonu.'
    return 'Nie udało się utworzyć hackathonu. Spróbuj ponownie.'
  }

  return 'Nie udało się utworzyć hackathonu. Spróbuj ponownie.'
}

export function getHackathonDetailsErrorMessage(error: unknown, language: 'pl' | 'en' = 'pl'): string {
  if (language === 'en') return mapHackathonError(error, 'details')
  if (error instanceof ApiError) {
    if (error.status === 403) return 'Nie masz uprawnień do wyświetlenia tego hackathonu.'
    if (error.status === 404) return 'Nie znaleziono tego hackathonu.'
    return 'Nie udało się pobrać szczegółów hackathonu. Spróbuj ponownie.'
  }

  return 'Nie udało się pobrać szczegółów hackathonu. Spróbuj ponownie.'
}

export function getUpdateHackathonErrorMessage(error: unknown, language: 'pl' | 'en' = 'pl'): string {
  if (language === 'en') return mapHackathonError(error, 'update')
  if (error instanceof ApiError) {
    if (error.status === 403) return 'Nie masz uprawnień do edycji tego hackathonu.'
    if (error.status === 404) return 'Ten hackathon nie istnieje lub został usunięty.'
    if (error.errorCode === 'VALIDATION_ERROR') {
      return 'Sprawdź poprawność danych hackathonu.'
    }
    return 'Nie udało się zapisać ustawień hackathonu. Spróbuj ponownie.'
  }

  return 'Nie udało się zapisać ustawień hackathonu. Spróbuj ponownie.'
}

export function getDeleteHackathonErrorMessage(error: unknown, language: 'pl' | 'en' = 'pl'): string {
  if (language === 'en') {
    if (error instanceof ApiError) {
      if (error.status === 404) return 'The hackathon does not exist or you cannot delete it.'
      if (error.errorCode === 'INVALID_CONFIRM_NAME') {
        return 'The entered name does not match the hackathon name.'
      }
      return error.message
    }
    return 'Could not delete the hackathon. Try again.'
  }
  if (error instanceof ApiError) {
    if (error.status === 404) {
      return 'Hackathon nie istnieje albo nie masz uprawnień do jego usunięcia.'
    }
    if (error.errorCode === 'INVALID_CONFIRM_NAME') {
      return 'Wpisana nazwa nie jest zgodna z nazwą hackathonu.'
    }
    return error.message
  }

  return 'Nie udało się usunąć hackathonu. Spróbuj ponownie.'
}

export function getAddCoOrganizerErrorMessage(error: unknown, language: 'pl' | 'en' = 'pl'): string {
  if (language === 'en') {
    if (error instanceof ApiError) {
      const messages: Record<string, string> = { CO_ORGANIZER_USER_NOT_FOUND: 'User not found.', CO_ORGANIZER_ALREADY_ASSIGNED: 'This user is already a co-organizer.', ORGANIZER_CANNOT_BE_CO_ORGANIZER: 'The owner cannot also be a co-organizer.', VALIDATION_ERROR: 'Select a valid user.' }
      if (error.errorCode && messages[error.errorCode]) return messages[error.errorCode]
      if (error.status === 401) return 'Sign in again and retry.'
      if (error.status === 404) return 'The hackathon does not exist or you cannot modify it.'
    }
    return 'Could not add the co-organizer. Try again.'
  }
  if (error instanceof ApiError) {
    if (error.errorCode === 'CO_ORGANIZER_USER_NOT_FOUND') {
      return 'Nie znaleziono użytkownika o podanym public_id.'
    }
    if (error.errorCode === 'CO_ORGANIZER_ALREADY_ASSIGNED') {
      return 'Ten użytkownik jest już współorganizatorem.'
    }
    if (error.errorCode === 'ORGANIZER_CANNOT_BE_CO_ORGANIZER') {
      return 'Właściciel hackathonu nie może być jednocześnie współorganizatorem.'
    }
    if (error.status === 401) return 'Zaloguj się ponownie i spróbuj jeszcze raz.'
    if (error.status === 404) {
      return 'Hackathon nie istnieje albo nie masz uprawnień do jego zmiany.'
    }
    if (error.errorCode === 'VALIDATION_ERROR') return 'Podaj poprawne public_id użytkownika.'
    return 'Nie udało się dodać współorganizatora. Spróbuj ponownie.'
  }

  return 'Nie udało się dodać współorganizatora. Spróbuj ponownie.'
}

export function getHackathonTasksErrorMessage(error: unknown, language: 'pl' | 'en' = 'pl'): string {
  if (language === 'en') {
    if (error instanceof ApiError && error.status === 401) return 'Sign in again and retry.'
    if (error instanceof ApiError && error.status === 403) return 'You do not have permission to manage tasks.'
    if (error instanceof ApiError && error.status === 404) return 'This hackathon was not found.'
    return 'Could not load tasks. Try again.'
  }
  if (error instanceof ApiError) {
    if (error.status === 401) return 'Zaloguj się ponownie i spróbuj jeszcze raz.'
    if (error.status === 403) return 'Nie masz uprawnień do zarządzania zadaniami.'
    if (error.status === 404) return 'Nie znaleziono tego hackathonu.'
    return 'Nie udało się pobrać zadań. Spróbuj ponownie.'
  }

  return 'Nie udało się pobrać zadań. Spróbuj ponownie.'
}

export function getCreateHackathonTaskErrorMessage(error: unknown, language: 'pl' | 'en' = 'pl'): string {
  if (language === 'en') {
    if (error instanceof ApiError && error.errorCode === 'INVALID_TASK_VISIBILITY_DATE') return 'The publication date must be before the hackathon ends.'
    if (error instanceof ApiError && error.errorCode === 'VALIDATION_ERROR') return 'Check the task details.'
    if (error instanceof ApiError && error.status === 403) return 'You do not have permission to add tasks.'
    return 'Could not add the task. Try again.'
  }
  if (error instanceof ApiError) {
    if (error.errorCode === 'INVALID_TASK_VISIBILITY_DATE') {
      return 'Termin publikacji musi przypadać przed zakończeniem hackathonu.'
    }
    if (error.errorCode === 'VALIDATION_ERROR') return 'Sprawdź dane zadania.'
    if (error.status === 403) return 'Nie masz uprawnień do dodawania zadań.'
    return 'Nie udało się dodać zadania. Spróbuj ponownie.'
  }

  return 'Nie udało się dodać zadania. Spróbuj ponownie.'
}

function mapHackathonError(error: unknown, operation: 'create' | 'details' | 'update'): string {
  if (error instanceof ApiError) {
    if (error.status === 403) return operation === 'details' ? 'You do not have permission to view this hackathon.' : operation === 'update' ? 'You do not have permission to edit this hackathon.' : 'You do not have permission to create hackathons.'
    if (error.status === 404) return 'This hackathon does not exist or has been removed.'
    if (error.errorCode === 'VALIDATION_ERROR') return 'Check the hackathon details.'
  }
  return operation === 'create' ? 'Could not create the hackathon. Try again.' : operation === 'update' ? 'Could not save the hackathon settings. Try again.' : 'Could not load the hackathon details. Try again.'
}
