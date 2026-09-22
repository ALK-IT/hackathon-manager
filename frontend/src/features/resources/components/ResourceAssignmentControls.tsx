import { useCallback, useEffect, useState } from 'react'
import { Button } from '../../../components/ui'
import { assignResource, getManagedResources, getResourceAssignments, getResourceItems, revokeResourceAssignment } from '../api/resourcesApi'
import type { ManagedResource, ManagedResourceAssignment } from '../types'

export function ResourceAssignmentControls({ hackathonPublicId, registrationPublicId }: { hackathonPublicId: string; registrationPublicId: string }) {
  const [resources, setResources] = useState<ManagedResource[]>([])
  const [resourceId, setResourceId] = useState('')
  const [assignments, setAssignments] = useState<ManagedResourceAssignment[]>([])
  const [busy, setBusy] = useState(false)
  const reload = useCallback(async () => {
    try {
      const [allResources, allAssignments] = await Promise.all([getManagedResources(hackathonPublicId), getResourceAssignments(hackathonPublicId)])
      const individual = allResources.filter((resource) => resource.target === 'individual')
      setResources(individual); setResourceId((current) => current || individual[0]?.public_id || '')
      setAssignments(allAssignments.filter((item) => item.registration_public_id === registrationPublicId))
    } catch { setResources([]); setAssignments([]) }
  }, [hackathonPublicId, registrationPublicId])
  useEffect(() => { void reload() }, [reload])
  async function assign() {
    if (!resourceId) return
    setBusy(true)
    try {
      const items = await getResourceItems(hackathonPublicId, resourceId)
      const available = items.find((item) => !item.is_assigned && !item.is_revoked)
      if (!available) { window.alert('Brak wolnych wartości tego zasobu.'); return }
      await assignResource(hackathonPublicId, resourceId, available.public_id, registrationPublicId)
      await reload()
    } finally { setBusy(false) }
  }
  async function revoke(assignmentId: string) {
    if (!window.confirm('Czy na pewno chcesz cofnąć ten zasób?')) return
    setBusy(true); try { await revokeResourceAssignment(hackathonPublicId, assignmentId); await reload() } finally { setBusy(false) }
  }
  return <div className="attendance-resource-actions">
    <select aria-label="Wybierz zasób" value={resourceId} onChange={(event) => setResourceId(event.target.value)} disabled={busy || resources.length === 0}>
      {resources.length === 0 && <option value="">Brak zasobów</option>}
      {resources.map((resource) => <option key={resource.public_id} value={resource.public_id}>{resource.name}</option>)}
    </select>
    <Button type="button" variant="ghost" disabled={busy || !resourceId} onClick={() => void assign()}>Dodaj zasoby</Button>
    {assignments.map((assignment) => <Button key={assignment.public_id} type="button" variant="ghost" disabled={busy} onClick={() => void revoke(assignment.public_id)}>Cofnij: {assignment.resource_name}</Button>)}
    {assignments.length === 0 && <Button type="button" variant="ghost" disabled>Cofnij zasoby</Button>}
  </div>
}
