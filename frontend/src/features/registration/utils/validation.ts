import type { RegistrationQuestion, TeamMode } from '../types'

export interface RegistrationFormErrors {
  answers: Record<string, string>
  teamName?: string
  joinCode?: string
}

interface RegistrationFormValues {
  questions: RegistrationQuestion[]
  answers: Record<string, string>
  teamMode: TeamMode
  teamName: string
  joinCode: string
  language?: 'pl' | 'en'
}

export function validateRegistrationForm({
  questions,
  answers,
  teamMode,
  teamName,
  joinCode,
  language = 'pl',
}: RegistrationFormValues): RegistrationFormErrors {
  const errors: RegistrationFormErrors = { answers: {} }

  for (const question of questions) {
    const answer = answers[question.public_id]?.trim() ?? ''
    if (question.is_required && !answer) {
      errors.answers[question.public_id] = language === 'en' ? 'An answer is required.' : 'Odpowiedź jest wymagana.'
    } else if (answer.length > 5000) {
      errors.answers[question.public_id] = language === 'en' ? 'The answer can be up to 5,000 characters.' : 'Odpowiedź może mieć maksymalnie 5000 znaków.'
    }
  }

  if (teamMode === 'create') {
    const normalizedName = teamName.trim()
    if (!normalizedName) {
      errors.teamName = language === 'en' ? 'Enter a team name.' : 'Podaj nazwę drużyny.'
    } else if (normalizedName.length > 200) {
      errors.teamName = language === 'en' ? 'The team name can be up to 200 characters.' : 'Nazwa drużyny może mieć maksymalnie 200 znaków.'
    }
  }

  if (teamMode === 'join' && joinCode.trim().length !== 8) {
    errors.joinCode = language === 'en' ? 'The team code must be 8 characters.' : 'Kod drużyny musi mieć 8 znaków.'
  }

  return errors
}

export function hasRegistrationFormErrors(errors: RegistrationFormErrors): boolean {
  return (
    Object.keys(errors.answers).length > 0 ||
    Boolean(errors.teamName) ||
    Boolean(errors.joinCode)
  )
}
