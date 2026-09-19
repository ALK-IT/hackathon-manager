import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getMyResources, revealResourceValue } from '../api/resourcesApi'
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
  beforeEach(() => {
    vi.mocked(getMyResources).mockReset()
    vi.mocked(revealResourceValue).mockReset()
  })

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
    expect(getMyResources).toHaveBeenCalledWith('hackathon-id', expect.any(AbortSignal))
  })

  it('passes the selected hackathon when revealing a resource', async () => {
    vi.mocked(getMyResources).mockResolvedValue([resources[0]])
    vi.mocked(revealResourceValue).mockResolvedValue('revealed-secret')
    render(<HackathonResourcesPanel hackathonPublicId="hackathon-id" />)

    fireEvent.click(await screen.findByRole('button', { name: 'Pokaż' }))

    expect(await screen.findByText('revealed-secret')).toBeInTheDocument()
    expect(revealResourceValue).toHaveBeenCalledWith('current-resource-id', 'hackathon-id')
  })

  it('fetches resources again with the new hackathon context', async () => {
    vi.mocked(getMyResources).mockResolvedValueOnce([resources[0]])
      .mockResolvedValueOnce([resources[1]])
    const { rerender } = render(<HackathonResourcesPanel hackathonPublicId="hackathon-id" />)
    await screen.findByRole('heading', { name: resources[0].name })

    rerender(<HackathonResourcesPanel hackathonPublicId="other-hackathon-id" />)

    expect(await screen.findByRole('heading', { name: resources[1].name })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: resources[0].name })).not.toBeInTheDocument()
    expect(getMyResources).toHaveBeenLastCalledWith('other-hackathon-id', expect.any(AbortSignal))
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
