export type RegistrationStatus = 'pending' | 'accepted' | 'rejected'

export interface ProfileHackathon {
  registration_public_id: string
  hackathon_public_id: string
  name: string
  description: string
  start_date: string
  end_date: string
  status: RegistrationStatus
  team: { public_id: string; name: string } | null
  status_changed_at: string | null
}
