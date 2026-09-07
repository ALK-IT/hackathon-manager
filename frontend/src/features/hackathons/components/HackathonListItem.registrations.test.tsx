import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import type { Hackathon } from '../types'
import { HackathonListItem } from './HackathonListItem'

const hackathon: Hackathon = {
  public_id: 'hackathon-id',
  name: 'Hackathon',
  start_date: '2026-09-01T10:00:00Z',
  end_date: '2026-09-02T10:00:00Z',
  registration_open: false,
  capacity: null,
  max_team_size: 4,
  access_level: 'viewer',
}

describe('HackathonListItem registrations link', () => {
  it.each(['owner', 'co_organizer'] as const)('opens registrations for %s', (accessLevel) => {
    function Location() {
      return <output>{useLocation().pathname}</output>
    }

    render(
      <MemoryRouter>
        <HackathonListItem hackathon={{ ...hackathon, access_level: accessLevel }} />
        <Location />
      </MemoryRouter>,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Zgłoszenia' }))
    expect(screen.getByText('/hackathons/hackathon-id/registrations')).toBeInTheDocument()
  })

  it('hides registrations from viewers', () => {
    render(
      <MemoryRouter>
        <HackathonListItem hackathon={hackathon} />
      </MemoryRouter>,
    )
    expect(screen.queryByRole('button', { name: 'Zgłoszenia' })).not.toBeInTheDocument()
  })

  it('shows registrations on the /hackathons page', () => {
    render(
      <MemoryRouter initialEntries={['/hackathons']}>
        <HackathonListItem hackathon={{ ...hackathon, access_level: 'owner' }} />
      </MemoryRouter>,
    )
    expect(screen.getByRole('button', { name: 'Zgłoszenia' })).toBeInTheDocument()
  })
})
