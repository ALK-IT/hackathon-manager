export interface ResourceInventory {
  public_id: string
  name: string
  type: string
  distribution_mode: string
  target: 'individual' | 'team'
  metadata: Record<string, unknown>
  item_count: number
  available_item_count: number
}

export interface ResourceResponse {
  public_id: string
  name: string
  type: string
  distribution_mode: string
  target: 'individual' | 'team'
  metadata: Record<string, unknown>
  item_count: number
}

export interface ParticipantResourceAssignment {
  public_id: string
  registration_public_id: string
  assigned_at: string
  revoked_at: string | null
}

export interface ParticipantResourceAssignmentsResult {
  assignments: ParticipantResourceAssignment[]
  already_assigned_registration_public_ids: string[]
}
