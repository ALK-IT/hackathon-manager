import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../../../lib/api/client'
import { createRegistrationQuestions } from '../api/registrationApi'
import { RegistrationQuestionsSetupPage } from './RegistrationQuestionsSetupPage'

vi.mock('../api/registrationApi', () => ({ createRegistrationQuestions: vi.fn() }))

function renderPage() {
  render(
    <MemoryRouter initialEntries={['/hackathons/hackathon-id/questions/setup']}>
      <Routes>
        <Route
          path="/hackathons/:hackathonPublicId/questions/setup"
          element={<RegistrationQuestionsSetupPage />}
        />
        <Route path="/hackathons/:hackathonPublicId" element={<p>Szczegóły</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('RegistrationQuestionsSetupPage', () => {
  beforeEach(() => vi.mocked(createRegistrationQuestions).mockReset())

  it('validates empty questions', async () => {
    renderPage()

    fireEvent.click(screen.getByRole('button', { name: 'Zapisz pytania' }))

    expect(await screen.findByText('Uzupełnij treść każdego pytania.')).toBeInTheDocument()
    expect(createRegistrationQuestions).not.toHaveBeenCalled()
  })

  it('adds and saves questions', async () => {
    vi.mocked(createRegistrationQuestions).mockResolvedValue([])
    renderPage()

    fireEvent.change(screen.getByLabelText('Pytanie 1'), {
      target: { value: 'Dlaczego chcesz wziąć udział?' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Dodaj pytanie' }))
    fireEvent.change(screen.getByLabelText('Pytanie 2'), {
      target: { value: 'Jakie masz doświadczenie?' },
    })
    fireEvent.click(screen.getAllByLabelText('Wymagane')[1])
    fireEvent.click(screen.getByRole('button', { name: 'Zapisz pytania' }))

    expect(await screen.findByText('Szczegóły')).toBeInTheDocument()
    expect(createRegistrationQuestions).toHaveBeenCalledWith('hackathon-id', [
      { content: 'Dlaczego chcesz wziąć udział?', is_required: true },
      { content: 'Jakie masz doświadczenie?', is_required: false },
    ])
  })

  it('uses contextual labels for removing questions', () => {
    renderPage()

    fireEvent.click(screen.getByRole('button', { name: 'Dodaj pytanie' }))

    expect(screen.getByRole('button', { name: 'Usuń pytanie 1' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Usuń pytanie 2' })).toBeInTheDocument()
  })

  it('prevents adding more than 50 questions', () => {
    renderPage()

    const addButton = screen.getByRole('button', { name: 'Dodaj pytanie' })
    for (let index = 1; index < 50; index += 1) fireEvent.click(addButton)

    expect(addButton).toBeDisabled()
    expect(screen.getByRole('status')).toHaveTextContent('Możesz dodać maksymalnie 50 pytań.')
  })

  it('shows a specific error when registration questions are locked', async () => {
    vi.mocked(createRegistrationQuestions).mockImplementationOnce(async () => {
      throw new ApiError(409, { error_code: 'REGISTRATION_QUESTIONS_LOCKED' })
    })
    renderPage()

    fireEvent.change(screen.getByLabelText('Pytanie 1'), {
      target: { value: 'Jakie masz doświadczenie?' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Zapisz pytania' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Nie można zmieniać pytań po otwarciu rejestracji.',
    )
  })
})
