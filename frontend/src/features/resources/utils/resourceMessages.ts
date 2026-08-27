import { ApiError } from '../../../lib/api/client'

export function getResourcesErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.status === 401) {
    return 'Sesja wygasła. Zaloguj się ponownie.'
  }

  return 'Nie udało się pobrać zasobów. Spróbuj ponownie.'
}

export function getRevealErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.errorCode === 'RESOURCE_REVOKED') {
      return 'Zasób został cofnięty przez organizatora.'
    }
    if (error.errorCode === 'RESOURCE_NOT_ASSIGNED_TO_USER') {
      return 'Ten zasób nie jest już do Ciebie przypisany.'
    }
    if (error.status === 401) return 'Sesja wygasła. Zaloguj się ponownie.'
  }

  return 'Nie udało się pobrać wartości zasobu.'
}
