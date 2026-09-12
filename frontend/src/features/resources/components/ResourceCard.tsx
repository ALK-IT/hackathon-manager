import { Alert, Card } from '../../../components/ui'
import { revealResourceValue } from '../api/resourcesApi'
import type { MyResource, ResourceMetadataValue } from '../types'
import { ResourceSecret } from './ResourceSecret'

interface ResourceCardProps {
  resource: MyResource
}

const targetLabels = {
  individual: 'Indywidualny',
  team: 'Drużynowy',
} as const

function formatMetadataValue(value: ResourceMetadataValue): string {
  if (value === null) return '—'
  if (typeof value === 'boolean') return value ? 'Tak' : 'Nie'
  return String(value)
}

export function ResourceCard({ resource }: ResourceCardProps) {
  const metadata = Object.entries(resource.metadata)

  return (
    <li>
      <Card className="resource-card">
        <div className="resource-card-header">
          <div>
            <h2>{resource.name}</h2>
            <p>Hackathon: {resource.hackathon.name}</p>
          </div>
          <span className="resource-target-badge">{targetLabels[resource.target]}</span>
        </div>

        <p>Typ: Klucz API</p>
        <p>Status: {resource.is_revoked ? 'cofnięty' : 'aktywny'}</p>

        {metadata.length > 0 && (
          <dl className="resource-metadata">
            {metadata.map(([key, value]) => (
              <div key={key}>
                <dt>{key}</dt>
                <dd>{formatMetadataValue(value)}</dd>
              </div>
            ))}
          </dl>
        )}

        {resource.is_revoked ? (
          <Alert variant="error">Zasób został cofnięty przez organizatora.</Alert>
        ) : (
          <ResourceSecret onReveal={() => revealResourceValue(resource.public_id)} />
        )}
      </Card>
    </li>
  )
}
