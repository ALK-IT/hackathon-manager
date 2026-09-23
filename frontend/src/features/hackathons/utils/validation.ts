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
  language?: 'pl' | 'en'
}

export function validateHackathon(
  values: HackathonFormValues,
  options: ValidateHackathonOptions = {},
): HackathonFormErrors {
  const errors: HackathonFormErrors = {}
  const en = options.language === 'en'
  const startDate = parseDate(values.startDate)
  const endDate = parseDate(values.endDate)
  const registrationOpensAt = parseDate(values.registrationOpensAt)
  const registrationDeadline = values.registrationDeadline
    ? parseDate(values.registrationDeadline)
    : startDate && new Date(startDate.getTime() - 48 * 60 * 60 * 1000)

  if (!values.name.trim()) errors.name = en ? 'Enter the hackathon name.' : 'Podaj nazwę hackathonu.'
  if (values.name.trim().length > 200) errors.name = en ? 'The name can be up to 200 characters.' : 'Nazwa może mieć maksymalnie 200 znaków.'
  if (values.description.trim().length > 5000) {
    errors.description = en ? 'The description can be up to 5,000 characters.' : 'Opis może mieć maksymalnie 5000 znaków.'
  }
  if (!startDate) errors.startDate = en ? 'Enter the hackathon start date.' : 'Podaj datę rozpoczęcia hackathonu.'
  if (!endDate) errors.endDate = en ? 'Enter the hackathon end date.' : 'Podaj datę zakończenia hackathonu.'
  if (startDate && endDate && endDate <= startDate) {
    errors.endDate = en ? 'The end must be later than the start.' : 'Zakończenie musi być późniejsze niż rozpoczęcie.'
  }
  if (!registrationOpensAt) {
    errors.registrationOpensAt = en ? 'Enter the registration opening date.' : 'Podaj datę otwarcia zapisów.'
  }
  if (options.registrationDeadlineRequired && !values.registrationDeadline) {
    errors.registrationDeadline = en ? 'Enter the registration deadline.' : 'Podaj datę zamknięcia zapisów.'
  } else if (values.registrationDeadline && !registrationDeadline) {
    errors.registrationDeadline = en ? 'Enter a valid registration deadline.' : 'Podaj poprawną datę zamknięcia zapisów.'
  }
  if (startDate && registrationDeadline && registrationDeadline >= startDate) {
    errors.registrationDeadline = en ? 'Registration must close before the hackathon starts.' : 'Zapisy muszą zamknąć się przed rozpoczęciem hackathonu.'
  }
  if (
    registrationOpensAt &&
    registrationDeadline &&
    registrationOpensAt >= registrationDeadline
  ) {
    errors.registrationOpensAt = en ? 'Registration must open before it closes.' : 'Zapisy muszą otworzyć się przed ich zamknięciem.'
  }

  const capacity = values.capacity ? parsePositiveInteger(values.capacity) : undefined
  const maxTeamSize = parsePositiveInteger(values.maxTeamSize)
  if (values.capacity && capacity === null) {
    errors.capacity = en ? 'The participant limit must be a positive integer.' : 'Limit uczestników musi być dodatnią liczbą całkowitą.'
  }
  if (maxTeamSize === null) {
    errors.maxTeamSize = en ? 'Team size must be a positive integer.' : 'Wielkość drużyny musi być dodatnią liczbą całkowitą.'
  }
  if (capacity && maxTeamSize && maxTeamSize > capacity) {
    errors.maxTeamSize = en ? 'Team size cannot exceed the participant limit.' : 'Wielkość drużyny nie może przekraczać limitu uczestników.'
  }

  return errors
}

export type CreateHackathonErrors = HackathonFormErrors
export type CreateHackathonValues = HackathonFormValues
export const validateCreateHackathon = validateHackathon
