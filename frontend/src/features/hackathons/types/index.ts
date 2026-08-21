export interface Hackathon {
  public_id: string
  name: string
  start_date: string
  end_date: string
  registration_open: boolean
  capacity: number | null
  max_team_size: number
  access_level: 'owner' | 'co_organizer' | 'viewer'
}

export interface UserSummary {
  public_id: string
  name: string
}

export interface HackathonDetails extends Hackathon {
  description: string
  registration_opens_at: string
  registration_deadline: string
  organizer: UserSummary
  co_organizers: UserSummary[]
  created_at: string
  updated_at: string
}

export interface HackathonFilters {
  upcoming?: boolean
  registrationOpen?: boolean
}

export interface CreateHackathonPayload {
  name: string
  description: string
  start_date: string
  end_date: string
  registration_opens_at: string
  registration_deadline?: string
  capacity?: number
  max_team_size: number
}

export interface AddCoOrganizerPayload {
  user_public_id: string
}
