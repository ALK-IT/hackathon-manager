import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
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
    render(
      <MemoryRouter>
        <HackathonListItem hackathon={hackathon} />
      </MemoryRouter>,
    )

    expect(screen.getByRole('listitem')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Test Hackathon' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Test Hackathon' })).toHaveAttribute(
      'href',
      `/hackathons/${hackathon.public_id}`,
    )
    expect(screen.getByText('Rejestracja: otwarta')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Zarejestruj się' })).toBeInTheDocument()
  })

  it('navigates to the registration page', () => {
    function Location() {
      return <output>{useLocation().pathname}</output>
    }

    render(
      <MemoryRouter>
        <HackathonListItem hackathon={hackathon} />
        <Location />
      </MemoryRouter>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Zarejestruj się' }))

    expect(screen.getByText(`/hackathons/${hackathon.public_id}/register`)).toBeInTheDocument()
  })

  it('does not render the button when registration is closed', () => {
    render(
      <MemoryRouter>
        <HackathonListItem hackathon={{ ...hackathon, registration_open: false }} />
      </MemoryRouter>,
    )

    expect(screen.getByText('Rejestracja: zamknięta')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Zarejestruj się' })).not.toBeInTheDocument()
  })

  it.each(['owner', 'co_organizer'] as const)(
    'shows registrations only for the explicit %s access level',
    (accessLevel) => {
      render(
        <MemoryRouter>
          <HackathonListItem hackathon={{ ...hackathon, access_level: accessLevel }} />
        </MemoryRouter>,
      )

      expect(screen.getByRole('button', { name: 'Zgłoszenia' })).toBeInTheDocument()
    },
  )

  it('hides registrations from viewers', () => {
    render(
      <MemoryRouter>
        <HackathonListItem hackathon={hackathon} />
      </MemoryRouter>,
    )

    expect(screen.queryByRole('button', { name: 'Zgłoszenia' })).not.toBeInTheDocument()
  })
})
