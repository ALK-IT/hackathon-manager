export interface HackathonFormErrors {
  name?: string
  description?: string
  startDate?: string
  endDate?: string
  registrationOpensAt?: string
  registrationDeadline?: string
  capacity?: string
  maxTeamSize?: string
}

export interface HackathonFormValues {
  name: string
  description: string
  startDate: string
  endDate: string
  registrationOpensAt: string
  registrationDeadline: string
  capacity: string
  maxTeamSize: string
}

function parseDate(value: string): Date | null {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

function parsePositiveInteger(value: string): number | null {
  const number = Number(value)
  return Number.isInteger(number) && number >= 1 ? number : null
}

interface ValidateHackathonOptions {
  registrationDeadlineRequired?: boolean
}

export function validateHackathon(
  values: HackathonFormValues,
  options: ValidateHackathonOptions = {},
): HackathonFormErrors {
  const errors: HackathonFormErrors = {}
  const startDate = parseDate(values.startDate)
  const endDate = parseDate(values.endDate)
  const registrationOpensAt = parseDate(values.registrationOpensAt)
  const registrationDeadline = values.registrationDeadline
    ? parseDate(values.registrationDeadline)
    : startDate && new Date(startDate.getTime() - 48 * 60 * 60 * 1000)

  if (!values.name.trim()) errors.name = 'Podaj nazwę hackathonu.'
  if (values.name.trim().length > 200) errors.name = 'Nazwa może mieć maksymalnie 200 znaków.'
  if (values.description.trim().length > 5000) {
    errors.description = 'Opis może mieć maksymalnie 5000 znaków.'
  }
  if (!startDate) errors.startDate = 'Podaj datę rozpoczęcia hackathonu.'
  if (!endDate) errors.endDate = 'Podaj datę zakończenia hackathonu.'
  if (startDate && endDate && endDate <= startDate) {
    errors.endDate = 'Zakończenie musi być późniejsze niż rozpoczęcie.'
  }
  if (!registrationOpensAt) {
    errors.registrationOpensAt = 'Podaj datę otwarcia zapisów.'
  }
  if (options.registrationDeadlineRequired && !values.registrationDeadline) {
    errors.registrationDeadline = 'Podaj datę zamknięcia zapisów.'
  } else if (values.registrationDeadline && !registrationDeadline) {
    errors.registrationDeadline = 'Podaj poprawną datę zamknięcia zapisów.'
  }
  if (startDate && registrationDeadline && registrationDeadline >= startDate) {
    errors.registrationDeadline = 'Zapisy muszą zamknąć się przed rozpoczęciem hackathonu.'
  }
  if (
    registrationOpensAt &&
    registrationDeadline &&
    registrationOpensAt >= registrationDeadline
  ) {
    errors.registrationOpensAt = 'Zapisy muszą otworzyć się przed ich zamknięciem.'
  }

  const capacity = values.capacity ? parsePositiveInteger(values.capacity) : undefined
  const maxTeamSize = parsePositiveInteger(values.maxTeamSize)
  if (values.capacity && capacity === null) {
    errors.capacity = 'Limit uczestników musi być dodatnią liczbą całkowitą.'
  }
  if (maxTeamSize === null) {
    errors.maxTeamSize = 'Wielkość drużyny musi być dodatnią liczbą całkowitą.'
  }
  if (capacity && maxTeamSize && maxTeamSize > capacity) {
    errors.maxTeamSize = 'Wielkość drużyny nie może przekraczać limitu uczestników.'
  }

  return errors
}

export type CreateHackathonErrors = HackathonFormErrors
export type CreateHackathonValues = HackathonFormValues
export const validateCreateHackathon = validateHackathon
