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
}

export function validateRegistrationForm({
  questions,
  answers,
  teamMode,
  teamName,
  joinCode,
}: RegistrationFormValues): RegistrationFormErrors {
  const errors: RegistrationFormErrors = { answers: {} }

  for (const question of questions) {
    const answer = answers[question.public_id]?.trim() ?? ''
    if (question.is_required && !answer) {
      errors.answers[question.public_id] = 'Odpowiedź jest wymagana.'
    } else if (answer.length > 5000) {
      errors.answers[question.public_id] = 'Odpowiedź może mieć maksymalnie 5000 znaków.'
    }
  }

  if (teamMode === 'create') {
    const normalizedName = teamName.trim()
    if (!normalizedName) {
      errors.teamName = 'Podaj nazwę drużyny.'
    } else if (normalizedName.length > 200) {
      errors.teamName = 'Nazwa drużyny może mieć maksymalnie 200 znaków.'
    }
  }

  if (teamMode === 'join' && joinCode.trim().length !== 8) {
    errors.joinCode = 'Kod drużyny musi mieć 8 znaków.'
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
