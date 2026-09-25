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

export interface TaskSubmissionEvaluation {
  score: number
  feedback: string | null
  evaluated_by: TaskSubmissionUser | null
  evaluated_at: string
}

export interface TaskSubmission {
  public_id: string
  github_url: string
  evaluation: TaskSubmissionEvaluation | null
  team: TaskSubmissionTeam
  submitted_by: TaskSubmissionUser | null
  created_at: string
  updated_at: string
}

export interface ParticipantTask {
  public_id: string
  title: string
  description: string
  criteria: Array<{
    name: string
    description: string
    max_points: number
  }>
  visible_from: string
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
  team: ParticipantTeam | null
  tasks: ParticipantTask[]
  leaderboard_visible_to_participants?: boolean
}

export type TeamMode = 'none' | 'create' | 'join'
