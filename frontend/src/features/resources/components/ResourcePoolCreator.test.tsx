import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createIndividualResourcePool } from '../api/resourceManagementApi'
import { ResourcePoolCreator } from './ResourcePoolCreator'

vi.mock('../api/resourceManagementApi', () => ({
  createIndividualResourcePool: vi.fn(),
}))

describe('ResourcePoolCreator', () => {
  beforeEach(() => vi.mocked(createIndividualResourcePool).mockReset())

  it('creates a named pool with one key per line', async () => {
    vi.mocked(createIndividualResourcePool).mockResolvedValue({
      public_id: 'resource-id',
      name: 'Klucze API',
      type: 'api_key',
      distribution_mode: 'manual',
      target: 'individual',
      metadata: {},
      item_count: 2,
    })
    const onCreated = vi.fn()
    render(
      <ResourcePoolCreator
        hackathonPublicId="hackathon-id"
        onCreated={onCreated}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Utwórz zasób' }))
    fireEvent.change(screen.getByLabelText('Nazwa zasobu'), {
      target: { value: ' Klucze API ' },
    })
    fireEvent.change(screen.getByLabelText('Klucze — jeden w wierszu'), {
      target: { value: ' first-secret \n\nsecond-secret' },
    })
    fireEvent.click(
      screen.getByRole('button', { name: 'Utwórz i dodaj klucze' }),
    )

    await waitFor(() =>
      expect(createIndividualResourcePool).toHaveBeenCalledWith(
        'hackathon-id',
        'Klucze API',
        ['first-secret', 'second-secret'],
      ),
    )
    expect(onCreated).toHaveBeenCalledWith('resource-id')
  })

  it('does not send an empty resource pool', async () => {
    render(
      <ResourcePoolCreator
        hackathonPublicId="hackathon-id"
        onCreated={vi.fn()}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Utwórz zasób' }))
    fireEvent.change(screen.getByLabelText('Nazwa zasobu'), {
      target: { value: 'Klucze API' },
    })
    fireEvent.click(
      screen.getByRole('button', { name: 'Utwórz i dodaj klucze' }),
    )

    expect(
      await screen.findByText('Dodaj przynajmniej jeden klucz.'),
    ).toBeInTheDocument()
    expect(createIndividualResourcePool).not.toHaveBeenCalled()
  })
})
