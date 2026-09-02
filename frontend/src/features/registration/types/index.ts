export interface RegistrationQuestion {
  public_id: string
  content: string
  is_required: boolean
}

export type RegistrationQuestionPayload = Pick<
  RegistrationQuestion,
  'content' | 'is_required'
>

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

export interface Participant {
  public_id: string
  name: string
}

export interface ParticipantTeam {
  public_id: string
  name: string
  members: Participant[]
}

export interface TaskSubmissionUser {
  public_id: string
  name: string
}

export interface TaskSubmissionTeam {
  public_id: string
  name: string
}

export interface TaskSubmission {
  public_id: string
  github_url: string
  team: TaskSubmissionTeam
  submitted_by: TaskSubmissionUser | null
  created_at: string
  updated_at: string
}

export interface ParticipantTask {
  public_id: string
  title: string
  description: string
  created_at: string
  updated_at: string
  submission: TaskSubmission | null
}

export interface ParticipantArea {
  public_id: string
  name: string
  description: string
  start_date: string
  end_date: string
  tasks_released_at: string
  team: ParticipantTeam | null
  tasks: ParticipantTask[]
}

export type TeamMode = 'none' | 'create' | 'join'
