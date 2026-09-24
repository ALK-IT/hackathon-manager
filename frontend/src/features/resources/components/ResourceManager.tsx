import { useEffect, useState } from 'react'
import { Alert, Button } from '../../../components/ui'
import { deleteManagedResource, getManagedResources } from '../api/resourcesApi'
import type { ManagedResource } from '../types'
import { ResourceCreateForm } from './ResourceCreateForm'

export function ResourceManager({ hackathonPublicId }: { hackathonPublicId: string }) {
  const [resources, setResources] = useState<ManagedResource[]>([])
  const [version, setVersion] = useState(0)
  useEffect(() => {
    void getManagedResources(hackathonPublicId).then(setResources).catch(() => setResources([]))
  }, [hackathonPublicId, version])
  async function remove(resource: ManagedResource) {
    if (!window.confirm(`Czy na pewno usunąć zasób „${resource.name}” wraz z wartościami i przypisaniami?`)) return
    await deleteManagedResource(hackathonPublicId, resource.public_id)
    setVersion((value) => value + 1)
  }
  return <section>
    <ResourceCreateForm hackathonPublicId={hackathonPublicId} onCreated={() => setVersion((value) => value + 1)} />
    <h3>Utworzone zasoby</h3>
    {resources.length === 0 ? <Alert>Brak utworzonych zasobów.</Alert> : <ul>{resources.map((resource) => <li key={resource.public_id}>{resource.name} ({resource.item_count}) <Button type="button" variant="danger" onClick={() => void remove(resource)}>Usuń</Button></li>)}</ul>}
  </section>
}
