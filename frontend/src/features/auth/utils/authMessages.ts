import { ApiError } from '../../../lib/api/client'

export function getLoginErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 403) {
      return 'Najpierw potwierdź konto przez link wysłany e-mailem.'
    }
    if (error.status === 401 || error.errorCode === 'INVALID_CREDENTIALS') {
      return 'Nieprawidłowy e-mail lub hasło.'
    }
    if (error.errorCode === 'VALIDATION_ERROR') {
      return 'Sprawdź poprawność danych logowania.'
    }
  }

  return 'Nie udało się zalogować. Spróbuj ponownie.'
}

export function getRegisterErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 503) {
      return 'Konto utworzono, ale nie udało się wysłać e-maila. Spróbuj wysłać link aktywacyjny później.'
    }
    if (error.status === 409 || error.errorCode === 'EMAIL_ALREADY_REGISTERED') {
      return 'Konto z tym adresem e-mail już istnieje.'
    }
    if (error.errorCode === 'VALIDATION_ERROR') {
      return 'Sprawdź poprawność danych rejestracji.'
    }
  }

  return 'Nie udało się utworzyć konta. Spróbuj ponownie.'
}
