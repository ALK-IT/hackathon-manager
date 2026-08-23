import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
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
  render(
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
})
