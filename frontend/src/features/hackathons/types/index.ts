export type HackathonAccessLevel = 'owner' | 'co_organizer'

export interface Hackathon {
  public_id: string
  name: string
  start_date: string
  end_date: string
  registration_open: boolean
  capacity: number | null
  max_team_size: number
  access_level: HackathonAccessLevel
}
