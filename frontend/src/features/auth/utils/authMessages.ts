import { ApiError } from '../../../lib/api/client'

export function getLoginErrorMessage(error: unknown, language: 'pl' | 'en' = 'pl'): string {
  if (language === 'en') {
    if (error instanceof ApiError && error.status === 403) return 'Verify your account using the link sent by email first.'
    if (error instanceof ApiError && (error.status === 401 || error.errorCode === 'INVALID_CREDENTIALS')) return 'Invalid email or password.'
    if (error instanceof ApiError && error.errorCode === 'VALIDATION_ERROR') return 'Check your sign-in details.'
    return 'Could not sign in. Try again.'
  }
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

export function getRegisterErrorMessage(error: unknown, language: 'pl' | 'en' = 'pl'): string {
  if (language === 'en') {
    if (error instanceof ApiError && error.status === 503) return 'The account was created, but the email could not be sent. Try resending the activation link later.'
    if (error instanceof ApiError && (error.status === 409 || error.errorCode === 'EMAIL_ALREADY_REGISTERED')) return 'An account with this email already exists.'
    if (error instanceof ApiError && error.errorCode === 'VALIDATION_ERROR') return 'Check your registration details.'
    return 'Could not create the account. Try again.'
  }
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
