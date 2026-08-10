import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { Hackathon } from '../types'
import { HackathonListItem } from './HackathonListItem'

const hackathon: Hackathon = {
  public_id: 'hackathon-1',
  name: 'Test Hackathon',
  start_date: '2026-09-01T10:00:00Z',
  end_date: '2026-09-02T10:00:00Z',
  registration_open: true,
  capacity: 100,
  max_team_size: 4,
  access_level: 'owner',
}

describe('HackathonListItem', () => {
  it('renders the hackathon name, dates and registration status', () => {
    render(<HackathonListItem hackathon={hackathon} />)

    expect(screen.getByRole('listitem')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Test Hackathon' })).toBeInTheDocument()
    expect(screen.getByText('1.09.2026 – 2.09.2026')).toBeInTheDocument()
    expect(screen.getByText('Rejestracja: otwarta')).toBeInTheDocument()
  })
})
