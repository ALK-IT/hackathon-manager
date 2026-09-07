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

interface GetManagedRegistrationsOptions {
  limit: number
  offset: number
  signal?: AbortSignal
}

export const getManagedRegistrations = (
  hackathonId: string,
  { limit, offset, signal }: GetManagedRegistrationsOptions,
) => {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  })
  return apiRequest<ManagedRegistration[]>(
    `/api/hackathons/${encodeURIComponent(hackathonId)}/registrations?${params}`,
    { signal },
  )
}

export const updateManagedRegistration = (
  registrationId: string,
  status: Exclude<ManagedStatus, 'pending'>,
) =>
  apiRequest<Pick<ManagedRegistration, 'public_id' | 'status' | 'team'>>(
    `/api/registrations/${encodeURIComponent(registrationId)}/status`,
    {
      method: 'PATCH',
      body: JSON.stringify({ status }),
      headers: { 'Content-Type': 'application/json' },
    },
  )
