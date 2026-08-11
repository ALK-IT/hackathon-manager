import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { Hackathon } from '../types'
import { HackathonListItem } from './HackathonListItem'

const hackathon: Hackathon = {
  public_id: '7b8b88c5-21cd-4b70-a4ad-240b32f365db',
  name: 'Test Hackathon',
  start_date: '2026-09-01T10:00:00Z',
  end_date: '2026-09-02T18:00:00Z',
  registration_open: true,
  capacity: 100,
  max_team_size: 4,
  access_level: 'viewer',
}

describe('HackathonListItem', () => {
  it('renders the hackathon details', () => {
    render(<HackathonListItem hackathon={hackathon} />)

    expect(screen.getByRole('listitem')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Test Hackathon' })).toBeInTheDocument()
    expect(screen.getByText('Rejestracja: otwarta')).toBeInTheDocument()
  })
})
