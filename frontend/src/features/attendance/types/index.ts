export interface CheckInSession {
  public_id: string
  token: string
  expires_at: string
  is_active: boolean
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
