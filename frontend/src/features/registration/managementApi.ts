import { apiRequest } from '../../lib/api/client'

export type ManagedStatus = 'pending' | 'accepted' | 'rejected'

export interface ManagedRegistration {
  public_id: string
  status: ManagedStatus
  user: { public_id: string; name: string; email: string }
  team: { public_id: string; name: string; join_code: string } | null
  answers: Array<{
    content: string
    question: { public_id: string; content: string; is_required: boolean }
  }>
}

export const getManagedRegistrations = (hackathonId: string) =>
  apiRequest<ManagedRegistration[]>(`/api/hackathons/${hackathonId}/registrations`)

export const updateManagedRegistration = (
  registrationId: string,
  status: Exclude<ManagedStatus, 'pending'>,
) =>
  apiRequest<Pick<ManagedRegistration, 'public_id' | 'status' | 'team'>>(
    `/api/registrations/${registrationId}/status`,
    {
      method: 'PATCH',
      body: JSON.stringify({ status }),
      headers: { 'Content-Type': 'application/json' },
    },
  )
