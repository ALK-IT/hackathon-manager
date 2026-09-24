export type ResourceTarget = 'individual' | 'team'
export type ResourceType = 'api_key'
export type ResourceMetadataValue = string | number | boolean | null

export interface ResourceHackathon {
  public_id: string
  name: string
}

export interface MyResource {
  public_id: string
  name: string
  type: ResourceType
  target: ResourceTarget
  metadata: Record<string, ResourceMetadataValue>
  is_revoked: boolean
  hackathon: ResourceHackathon
}

export interface ResourceRevealResponse {
  value: string
}

export interface ManagedResource {
  public_id: string
  name: string
  type: ResourceType
  distribution_mode: 'manual'
  target: ResourceTarget
  metadata: Record<string, ResourceMetadataValue>
  item_count: number
}

export interface ResourceImportResponse {
  resource: ManagedResource
  imported_count: number
}

export interface ManagedResourceItem {
  public_id: string
  resource_public_id: string
  is_assigned: boolean
  is_revoked: boolean
}

export interface ManagedResourceAssignment {
  public_id: string
  resource_public_id: string
  resource_name: string
  resource_item_public_id: string
  registration_public_id: string | null
  team_public_id: string | null
  assigned_at: string
  revoked_at: string | null
}
