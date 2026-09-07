import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../../../lib/api/client'
import { getManagedRegistrations, updateManagedRegistration } from '../managementApi'
import { ManageRegistrationsPage } from './ManageRegistrationsPage'

vi.mock('../managementApi', () => ({
  getManagedRegistrations: vi.fn(),
  updateManagedRegistration: vi.fn(),
}))

const registration = {
  public_id: 'registration-id',
  status: 'pending' as const,
  user: { public_id: 'user-id', name: 'Jan Kowalski', email: 'jan@example.com' },
  team: null,
  answers: [
    {
      content: 'Chcę się nauczyć.',
      question: { public_id: 'question-id', content: 'Dlaczego?', is_required: true },
    },
  ],
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/hackathons/hackathon-id/registrations']}>
      <Routes>
        <Route
          path="/hackathons/:hackathonPublicId/registrations"
          element={<ManageRegistrationsPage />}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ManageRegistrationsPage', () => {
  beforeEach(() => {
    vi.mocked(getManagedRegistrations).mockReset()
    vi.mocked(updateManagedRegistration).mockReset()
  })

  it('shows answers after selecting a registration', async () => {
    vi.mocked(getManagedRegistrations).mockResolvedValue([registration])
    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Obejrzyj zgłoszenie' }))

    expect(screen.getByRole('heading', { name: 'Jan Kowalski' })).toBeInTheDocument()
    expect(screen.getByText('Dlaczego?')).toBeInTheDocument()
    expect(screen.getByText('Chcę się nauczyć.')).toBeInTheDocument()
  })

  it('accepts the selected registration on the same page', async () => {
    vi.mocked(getManagedRegistrations).mockResolvedValue([registration])
    vi.mocked(updateManagedRegistration).mockResolvedValue({
      public_id: registration.public_id,
      status: 'accepted',
      team: null,
    })
    renderPage()
    fireEvent.click(await screen.findByRole('button', { name: 'Obejrzyj zgłoszenie' }))
    fireEvent.click(screen.getByRole('button', { name: 'Akceptuj' }))

    expect(await screen.findByText('Status: zaakceptowane')).toBeInTheDocument()
    expect(updateManagedRegistration).toHaveBeenCalledWith('registration-id', 'accepted')
  })

  it('loads registrations page by page', async () => {
    const firstPage = Array.from({ length: 51 }, (_, index) => ({
      ...registration,
      public_id: `registration-${index + 1}`,
      user: { ...registration.user, name: `Uczestnik ${index + 1}` },
    }))
    const secondPage = [
      {
        ...registration,
        public_id: 'registration-51',
        user: { ...registration.user, name: 'Uczestnik 51' },
      },
    ]
    vi.mocked(getManagedRegistrations)
      .mockResolvedValueOnce(firstPage)
      .mockResolvedValueOnce(secondPage)
    renderPage()

    expect(await screen.findByText(/Uczestnik 1 —/)).toBeInTheDocument()
    expect(screen.queryByText(/Uczestnik 51 —/)).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Następna strona' }))

    expect(await screen.findByText(/Uczestnik 51 —/)).toBeInTheDocument()
    expect(screen.getByText('Strona 2')).toBeInTheDocument()
    expect(getManagedRegistrations).toHaveBeenLastCalledWith(
      'hackathon-id',
      expect.objectContaining({ limit: 51, offset: 50 }),
    )
    expect(screen.getByRole('button', { name: 'Następna strona' })).toBeDisabled()
  })

  it('aborts loading after unmounting the page', () => {
    let signal: AbortSignal | undefined
    vi.mocked(getManagedRegistrations).mockImplementation((_hackathonId, options) => {
      signal = options.signal
      return new Promise(() => undefined)
    })
    const view = renderPage()

    view.unmount()

    expect(signal?.aborted).toBe(true)
  })

  it('shows a locked-status message, refetches data and disables actions', async () => {
    vi.mocked(getManagedRegistrations).mockResolvedValue([registration])
    vi.mocked(updateManagedRegistration).mockImplementationOnce(async () => {
      throw new ApiError(409, {
        error_code: 'REGISTRATION_STATUS_CHANGE_LOCKED',
      })
    })
    renderPage()
    fireEvent.click(await screen.findByRole('button', { name: 'Obejrzyj zgłoszenie' }))
    fireEvent.click(screen.getByRole('button', { name: 'Akceptuj' }))

    expect(
      await screen.findByText(
        'Nie można zmieniać statusów zgłoszeń po zakończeniu hackathonu.',
      ),
    ).toBeInTheDocument()
    await waitFor(() => expect(getManagedRegistrations).toHaveBeenCalledTimes(2))
    fireEvent.click(await screen.findByRole('button', { name: 'Obejrzyj zgłoszenie' }))
    expect(screen.getByRole('button', { name: 'Akceptuj' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Odrzuć' })).toBeDisabled()
  })
})
