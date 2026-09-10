import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getParticipantArea } from '../api/registrationApi'
import { ParticipantAreaPage } from './ParticipantAreaPage'

vi.mock('../api/registrationApi', () => ({
  getParticipantArea: vi.fn(),
  saveTaskSubmission: vi.fn(),
}))

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/hackathons/hackathon-id/participant-area']}>
      <Routes>
        <Route
          path="/hackathons/:hackathonPublicId/participant-area"
          element={<ParticipantAreaPage />}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ParticipantAreaPage', () => {
  beforeEach(() => vi.mocked(getParticipantArea).mockReset())

  it('displays the team and its accepted members', async () => {
    vi.mocked(getParticipantArea).mockResolvedValue({
      public_id: 'hackathon-id',
      name: 'Hackathon AI',
      description: 'Zbuduj użyteczne rozwiązanie.',
      start_date: '2026-09-03T08:00:00Z',
      end_date: '2099-09-05T18:00:00Z',
      tasks: [],
      team: {
        public_id: 'team-id',
        name: 'Byte Buccaneers',
        members: [
          { public_id: 'user-1', name: 'Jan Kowalski' },
          { public_id: 'user-2', name: 'Anna Nowak' },
        ],
      },
    })

    renderPage()

    expect(await screen.findByRole('heading', { name: 'Hackathon AI' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Drużyna: Byte Buccaneers' })).toBeInTheDocument()
    expect(screen.getByText('Jan Kowalski')).toBeInTheDocument()
    expect(screen.getByText('Anna Nowak')).toBeInTheDocument()
  })

  it('displays an accepted participant without a team', async () => {
    vi.mocked(getParticipantArea).mockResolvedValue({
      public_id: 'hackathon-id',
      name: 'Hackathon AI',
      description: 'Zbuduj użyteczne rozwiązanie.',
      start_date: '2026-09-03T08:00:00Z',
      end_date: '2099-09-05T18:00:00Z',
      tasks: [],
      team: null,
    })

    renderPage()

    expect(await screen.findByText('Nie należysz do żadnej drużyny.')).toBeInTheDocument()
  })
})
