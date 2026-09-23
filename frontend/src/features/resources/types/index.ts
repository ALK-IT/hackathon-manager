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
