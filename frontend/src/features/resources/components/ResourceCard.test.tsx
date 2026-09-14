import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import type { MyResource } from '../types'
import { ResourceCard } from './ResourceCard'

const resource: MyResource = {
  public_id: 'resource-item-id',
  name: 'OpenAI API key',
  type: 'api_key',
  target: 'team',
  metadata: { provider: 'OpenAI', sandbox: true },
  is_revoked: false,
  hackathon: { public_id: 'hackathon-id', name: 'HackYeah' },
}

function renderCard(item: MyResource = resource) {
  return render(
    <MemoryRouter>
      <ResourceCard resource={item} />
    </MemoryRouter>,
  )
}

describe('ResourceCard', () => {
  it('shows resource metadata and masked value', () => {
    renderCard()

    expect(screen.getByRole('heading', { name: 'OpenAI API key' })).toBeInTheDocument()
    expect(screen.getByText('Hackathon: HackYeah')).toBeInTheDocument()
    expect(screen.getByText('Drużynowy')).toBeInTheDocument()
    expect(screen.getByText('OpenAI')).toBeInTheDocument()
    expect(screen.getByLabelText('Wartość zasobu')).toHaveTextContent('••••••••••••••••')
    expect(screen.getByRole('button', { name: 'Kopiuj' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Pokaż' })).toBeInTheDocument()
  })

  it('does not allow revealing or copying a revoked resource', () => {
    renderCard({ ...resource, is_revoked: true })

    expect(screen.getByRole('alert')).toHaveTextContent('Zasób został cofnięty')
    expect(screen.queryByRole('button', { name: 'Kopiuj' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Pokaż' })).not.toBeInTheDocument()
  })
})
