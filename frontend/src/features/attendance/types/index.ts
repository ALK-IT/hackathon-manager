export interface CheckInSession {
  public_id: string
  token: string
  expires_at: string
  is_active: boolean
}

export interface AttendancePage<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

export interface AttendancePageOptions {
  limit?: number
  offset?: number
  signal?: AbortSignal
}

export interface CheckIn {
  public_id: string
  checked_in_at: string
}

export interface CheckInListItem {
  check_in: CheckIn
  participant: {
    public_id: string
    name: string
    email: string
    created_at: string
  }
  registration_public_id: string
}

export interface AttendanceParticipant {
  participant: {
    public_id: string
    name: string
    email: string
    created_at: string
  }
  registration_public_id: string
  team: {
    public_id: string
    name: string
  } | null
  is_present: boolean
  checked_in_at: string | null
}

export interface AttendanceTeam {
  public_id: string
  name: string
  participants: Array<{
    public_id: string
    name: string
  }>
}
