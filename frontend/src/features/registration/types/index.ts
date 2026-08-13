export interface RegistrationQuestion {
  public_id: string
  content: string
  is_required: boolean
}

export interface RegistrationQuestionCreate {
  content: string
  is_required: boolean
}

export interface RegistrationQuestionBulkPayload {
  questions: RegistrationQuestionCreate[]
}

export type TeamSelection =
  | { action: 'create'; name: string }
  | { action: 'join'; join_code: string }

export interface RegistrationPayload {
  answers: Array<{
    question_public_id: string
    content: string
  }>
  team: TeamSelection | null
}

export interface RegistrationTeam {
  public_id: string
  name: string
  join_code: string
}

export interface RegistrationResponse {
  public_id: string
  status: 'pending' | 'accepted' | 'rejected'
  team: RegistrationTeam | null
}

export type TeamMode = 'none' | 'create' | 'join'
