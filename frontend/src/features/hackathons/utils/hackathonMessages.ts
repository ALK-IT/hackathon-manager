import { ApiError } from '../../../lib/api/client'

export function getCreateHackathonErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 403) return 'Nie masz uprawnień do tworzenia hackathonów.'
    if (error.errorCode === 'VALIDATION_ERROR') return 'Sprawdź poprawność danych hackathonu.'
    return error.message
  }

  return 'Nie udało się utworzyć hackathonu. Spróbuj ponownie.'
}

export function getHackathonDetailsErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 403) return 'Nie masz uprawnień do wyświetlenia tego hackathonu.'
    if (error.status === 404) return 'Nie znaleziono tego hackathonu.'
    return error.message
  }

  return 'Nie udało się pobrać szczegółów hackathonu. Spróbuj ponownie.'
}

export function getUpdateHackathonErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 403) return 'Nie masz uprawnień do edycji tego hackathonu.'
    if (error.status === 404) return 'Ten hackathon nie istnieje lub został usunięty.'
    if (error.errorCode === 'VALIDATION_ERROR') {
      return 'Sprawdź poprawność danych hackathonu.'
    }
    return error.message
  }

  return 'Nie udało się zapisać ustawień hackathonu. Spróbuj ponownie.'
}

export function getAddCoOrganizerErrorMessage(error: unknown): string {
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
    return error.message
  }

  return 'Nie udało się dodać współorganizatora. Spróbuj ponownie.'
}

export function getHackathonTasksErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) return 'Zaloguj się ponownie i spróbuj jeszcze raz.'
    if (error.status === 403) return 'Nie masz uprawnień do zarządzania zadaniami.'
    if (error.status === 404) return 'Nie znaleziono tego hackathonu.'
    return error.message
  }

  return 'Nie udało się pobrać zadań. Spróbuj ponownie.'
}

export function getCreateHackathonTaskErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.errorCode === 'INVALID_TASK_VISIBILITY_DATE') {
      return 'Termin publikacji musi przypadać przed zakończeniem hackathonu.'
    }
    if (error.errorCode === 'VALIDATION_ERROR') return 'Sprawdź dane zadania.'
    if (error.status === 403) return 'Nie masz uprawnień do dodawania zadań.'
    return error.message
  }

  return 'Nie udało się dodać zadania. Spróbuj ponownie.'
}
