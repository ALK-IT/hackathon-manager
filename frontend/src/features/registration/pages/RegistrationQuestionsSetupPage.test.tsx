import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
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
})
