import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  createRegistration,
  getRegistrationQuestions,
} from '../api/registrationApi'
import { RegistrationEntryPage } from './RegistrationEntryPage'

vi.mock('../api/registrationApi', () => ({
  createRegistration: vi.fn(),
  getRegistrationQuestions: vi.fn(),
}))

const question = {
  public_id: 'question-id',
  content: 'Dlaczego chcesz wziąć udział?',
  is_required: true,
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/hackathons/hackathon-id/register']}>
      <Routes>
        <Route
          path="/hackathons/:hackathonPublicId/register"
          element={<RegistrationEntryPage />}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe('RegistrationEntryPage', () => {
  beforeEach(() => {
    vi.mocked(getRegistrationQuestions).mockReset()
    vi.mocked(createRegistration).mockReset()
    vi.mocked(getRegistrationQuestions).mockResolvedValue([question])
  })

  it('loads questions and validates required answers', async () => {
    renderPage()

    expect(await screen.findByLabelText('Dlaczego chcesz wziąć udział?')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Wyślij zgłoszenie' }))

    expect(screen.getByText('Odpowiedź jest wymagana.')).toBeInTheDocument()
    expect(createRegistration).not.toHaveBeenCalled()
  })

  it('submits answers without a team', async () => {
    vi.mocked(createRegistration).mockResolvedValue({
      public_id: 'registration-id',
      status: 'pending',
      team: null,
    })
    renderPage()

    fireEvent.change(await screen.findByLabelText('Dlaczego chcesz wziąć udział?'), {
      target: { value: 'Chcę stworzyć ciekawy projekt.' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Wyślij zgłoszenie' }))

    expect(await screen.findByText('Zgłoszenie zostało wysłane. Status: oczekujące.')).toBeInTheDocument()
    expect(createRegistration).toHaveBeenCalledWith('hackathon-id', {
      answers: [
        {
          question_public_id: 'question-id',
          content: 'Chcę stworzyć ciekawy projekt.',
        },
      ],
      team: null,
    })
  })

  it('creates a team and displays its join code', async () => {
    vi.mocked(createRegistration).mockResolvedValue({
      public_id: 'registration-id',
      status: 'pending',
      team: {
        public_id: 'team-id',
        name: 'Byte Buccaneers',
        join_code: 'ABCD1234',
      },
    })
    renderPage()

    fireEvent.change(await screen.findByLabelText('Dlaczego chcesz wziąć udział?'), {
      target: { value: 'Odpowiedź' },
    })
    fireEvent.click(screen.getByLabelText('Utwórz drużynę'))
    fireEvent.change(screen.getByLabelText('Nazwa drużyny'), {
      target: { value: 'Byte Buccaneers' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Wyślij zgłoszenie' }))

    await waitFor(() =>
      expect(createRegistration).toHaveBeenCalledWith(
        'hackathon-id',
        expect.objectContaining({
          team: { action: 'create', name: 'Byte Buccaneers' },
        }),
      ),
    )
    expect(await screen.findByText('ABCD1234')).toBeInTheDocument()
  })
})
