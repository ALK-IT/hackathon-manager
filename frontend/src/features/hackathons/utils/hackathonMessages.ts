import { ApiError } from '../../../lib/api/client'

export function getCreateHackathonErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 403) return 'Nie masz uprawnień do tworzenia hackathonów.'
    if (error.errorCode === 'VALIDATION_ERROR') return 'Sprawdź poprawność danych hackathonu.'
    return error.message
  }

  return 'Nie udało się utworzyć hackathonu. Spróbuj ponownie.'
}

export function getHackathonSettingsErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.errorCode === 'HACKATHON_NOT_FOUND') {
      return 'Nie znaleziono hackathonu albo nie masz uprawnień do jego edycji.'
    }
    if (error.errorCode === 'VALIDATION_ERROR') {
      return 'Sprawdź poprawność ustawień hackathonu.'
    }
    return error.message
  }

  return 'Nie udało się zapisać ustawień hackathonu. Spróbuj ponownie.'
}
