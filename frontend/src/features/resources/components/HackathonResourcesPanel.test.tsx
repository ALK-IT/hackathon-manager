import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getMyResources } from '../api/resourcesApi'
import type { MyResource } from '../types'
import { HackathonResourcesPanel } from './HackathonResourcesPanel'

vi.mock('../api/resourcesApi', () => ({
  getMyResources: vi.fn(),
  revealResourceValue: vi.fn(),
}))

const resources: MyResource[] = [
  {
    public_id: 'current-resource-id',
    name: 'Klucz bieżącego hackathonu',
    type: 'api_key',
    target: 'individual',
    metadata: {},
    is_revoked: false,
    hackathon: { public_id: 'hackathon-id', name: 'Hackathon AI' },
  },
  {
    public_id: 'other-resource-id',
    name: 'Klucz innego hackathonu',
    type: 'api_key',
    target: 'team',
    metadata: {},
    is_revoked: false,
    hackathon: { public_id: 'other-hackathon-id', name: 'Inny hackathon' },
  },
]

describe('HackathonResourcesPanel', () => {
  beforeEach(() => vi.mocked(getMyResources).mockReset())

  it('shows only resources assigned for the selected hackathon', async () => {
    vi.mocked(getMyResources).mockResolvedValue(resources)

    render(<HackathonResourcesPanel hackathonPublicId="hackathon-id" />)

    expect(
      await screen.findByRole('heading', { name: 'Klucz bieżącego hackathonu' }),
    ).toBeInTheDocument()
    expect(
      screen.queryByRole('heading', { name: 'Klucz innego hackathonu' }),
    ).not.toBeInTheDocument()
    expect(screen.getByLabelText('Wartość zasobu')).toHaveTextContent(
      '••••••••••••••••',
    )
    expect(screen.getByRole('button', { name: 'Pokaż' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Kopiuj' })).toBeInTheDocument()
  })

  it('shows an empty state for a hackathon without assigned resources', async () => {
    vi.mocked(getMyResources).mockResolvedValue([resources[1]])

    render(<HackathonResourcesPanel hackathonPublicId="hackathon-id" />)

    expect(
      await screen.findByText(
        'Nie masz jeszcze zasobów przypisanych do tego hackathonu.',
      ),
    ).toBeInTheDocument()
  })
})
