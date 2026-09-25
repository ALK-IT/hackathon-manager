import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
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
  my_registration_status: null,
}

describe('HackathonListItem', () => {
  afterEach(() => vi.restoreAllMocks())

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
    expect(screen.getByLabelText('Odliczanie czasu hackathonu')).toBeInTheDocument()
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
    'shows management actions and navigates there for %s',
    (accessLevel) => {
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
      expect(
        screen.getByText(`/hackathons/${hackathon.public_id}/registrations`),
      ).toBeInTheDocument()

      fireEvent.click(screen.getByRole('button', { name: 'Ustawienia' }))
      expect(screen.getByText(`/hackathons/${hackathon.public_id}/settings`)).toBeInTheDocument()
    },
  )

  it('hides management actions from viewers', () => {
    render(
      <MemoryRouter>
        <HackathonListItem hackathon={hackathon} />
      </MemoryRouter>,
    )

    expect(screen.queryByRole('button', { name: 'Zgłoszenia' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Ustawienia' })).not.toBeInTheDocument()
  })

  it('shows an accepted status and navigates to the participant area', () => {
    function Location() {
      return <output>{useLocation().pathname}</output>
    }

    render(
      <MemoryRouter>
        <HackathonListItem
          hackathon={{
            ...hackathon,
            registration_open: false,
            my_registration_status: 'accepted',
            end_date: new Date(Date.now() + 3600000).toISOString(),
          }}
        />
        <Location />
      </MemoryRouter>,
    )

    expect(screen.getByText('Status zgłoszenia: zaakceptowane')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Przejdź do hackathonu' }))

    expect(
      screen.getByText(`/hackathons/${hackathon.public_id}/participant-area`),
    ).toBeInTheDocument()
  })

  it('shows a pending status without an entry button', () => {
    render(
      <MemoryRouter>
        <HackathonListItem
          hackathon={{ ...hackathon, my_registration_status: 'pending' }}
        />
      </MemoryRouter>,
    )

    expect(screen.getByText('Status zgłoszenia: oczekujące')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Zarejestruj się' })).not.toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: 'Przejdź do hackathonu' }),
    ).not.toBeInTheDocument()
  })

  it('links an accepted participant to results after the end', () => {
    function Location() {
      const location = useLocation()
      return <output>{location.pathname}{location.search}</output>
    }
    render(<MemoryRouter>
      <HackathonListItem hackathon={{ ...hackathon, end_date: new Date(Date.now() - 1000).toISOString(), my_registration_status: 'accepted' }} />
      <Location />
    </MemoryRouter>)
    fireEvent.click(screen.getByRole('button', { name: 'Zobacz wyniki' }))
    expect(screen.getByText(`/hackathons/${hackathon.public_id}/participant-area?view=results`)).toBeInTheDocument()
  })

  it.each([
    ['owner', false],
    ['co_organizer', false],
    ['viewer', true],
  ] as const)('links a finished hackathon manager to managed results (%s)', (access_level, isAdmin) => {
    function Location() {
      const location = useLocation()
      return <output>{location.pathname}{location.search}</output>
    }
    render(<MemoryRouter>
      <HackathonListItem hackathon={{
        ...hackathon,
        access_level,
        end_date: new Date(Date.now() - 1000).toISOString(),
      }} isAdmin={isAdmin} />
      <Location />
    </MemoryRouter>)

    fireEvent.click(screen.getByRole('button', { name: 'Zobacz wyniki' }))
    expect(screen.getByText(
      `/hackathons/${hackathon.public_id}/attendance?view=solutions`,
    )).toBeInTheDocument()
  })

  it('shows a rejected status without registration or participant area buttons', () => {
    render(
      <MemoryRouter>
        <HackathonListItem
          hackathon={{ ...hackathon, my_registration_status: 'rejected' }}
        />
      </MemoryRouter>,
    )

    expect(screen.getByText('Status zgłoszenia: odrzucone')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Zarejestruj się' })).not.toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: 'Przejdź do hackathonu' }),
    ).not.toBeInTheDocument()
  })

  it('requires two confirmations before the owner deletes a hackathon', async () => {
    const onDelete = vi.fn().mockResolvedValue(undefined)
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true)
    const prompt = vi.spyOn(window, 'prompt').mockReturnValue(hackathon.name)

    render(
      <MemoryRouter>
        <HackathonListItem
          hackathon={{ ...hackathon, access_level: 'owner' }}
          onDelete={onDelete}
        />
      </MemoryRouter>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Usuń hackathon' }))

    expect(confirm).toHaveBeenCalledWith('Czy na pewno chcesz usunąć ten hackathon?')
    expect(prompt).toHaveBeenCalledWith(
      `Aby potwierdzić usunięcie, wpisz nazwę hackathonu: ${hackathon.name}`,
    )
    await waitFor(() => expect(onDelete).toHaveBeenCalledWith(
      expect.objectContaining({ public_id: hackathon.public_id }),
    ))
  })

  it('does not delete when the second confirmation has a different name', () => {
    const onDelete = vi.fn()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.spyOn(window, 'prompt').mockReturnValue('Inny hackathon')

    render(
      <MemoryRouter>
        <HackathonListItem
          hackathon={{ ...hackathon, access_level: 'owner' }}
          onDelete={onDelete}
        />
      </MemoryRouter>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Usuń hackathon' }))

    expect(onDelete).not.toHaveBeenCalled()
    expect(screen.getByRole('alert')).toHaveTextContent(
      'Wpisana nazwa nie jest zgodna z nazwą hackathonu.',
    )
  })

  it('does not show delete action to a co-organizer', () => {
    render(
      <MemoryRouter>
        <HackathonListItem
          hackathon={{ ...hackathon, access_level: 'co_organizer' }}
          onDelete={vi.fn()}
        />
      </MemoryRouter>,
    )

    expect(
      screen.queryByRole('button', { name: 'Usuń hackathon' }),
    ).not.toBeInTheDocument()
  })

  it('allows withdrawing before the hackathon ends after confirmation', async () => {
    const onWithdraw = vi.fn().mockResolvedValue(undefined)
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true)

    render(
      <MemoryRouter>
        <HackathonListItem
          hackathon={{
            ...hackathon,
            end_date: '2099-09-02T18:00:00Z',
            my_registration_status: 'accepted',
          }}
          onWithdraw={onWithdraw}
        />
      </MemoryRouter>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Wycofaj zgłoszenie' }))

    expect(confirm).toHaveBeenCalledWith('Czy na pewno chcesz się wycofać?')
    await waitFor(() => expect(onWithdraw).toHaveBeenCalledOnce())
  })

  it('does not allow withdrawing after the hackathon ends', () => {
    render(
      <MemoryRouter>
        <HackathonListItem
          hackathon={{
            ...hackathon,
            end_date: '2000-09-02T18:00:00Z',
            my_registration_status: 'pending',
          }}
          onWithdraw={vi.fn()}
        />
      </MemoryRouter>,
    )

    expect(
      screen.queryByRole('button', { name: 'Wycofaj zgłoszenie' }),
    ).not.toBeInTheDocument()
  })
})
