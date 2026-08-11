import { Card } from '../../../components/ui'
import type { Hackathon } from '../types'

interface HackathonListItemProps {
  hackathon: Hackathon
}

export function HackathonListItem({ hackathon }: HackathonListItemProps) {
  return (
    <li>
      <Card>
        <h3>
          #{hackathon.id} — {hackathon.name}
        </h3>
      </Card>
    </li>
  )
}
