import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createRegistrationQuestions } from '../api/registrationApi'
import { RegistrationQuestionsCreatePage } from './RegistrationQuestionsCreatePage'

vi.mock('../api/registrationApi', () => ({
  createRegistrationQuestions: vi.fn(),
}))

function renderPage() {
  render(
    <MemoryRouter initialEntries={['/hackathons/hackathon-id/questions/create']}>
      <Routes>
        <Route
          path="/hackathons/:hackathonPublicId/questions/create"
          element={<RegistrationQuestionsCreatePage />}
        />
        <Route path="/hackathons" element={<p>Lista hackathonów</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('RegistrationQuestionsCreatePage', () => {
  beforeEach(() => vi.mocked(createRegistrationQuestions).mockReset())

  it('validates an empty question', async () => {
    renderPage()

    fireEvent.click(screen.getByRole('button', { name: 'Zapisz pytania' }))

    expect(await screen.findByText('Podaj treść pytania.')).toBeInTheDocument()
    expect(createRegistrationQuestions).not.toHaveBeenCalled()
  })

  it('adds questions and sends them in one request', async () => {
    vi.mocked(createRegistrationQuestions).mockResolvedValue([])
    renderPage()

    fireEvent.change(screen.getByLabelText('Treść pytania'), {
      target: { value: 'Dlaczego chcesz wziąć udział?' },
    })
    fireEvent.click(screen.getByRole('button', { name: '+ Dodaj pytanie' }))
    fireEvent.change(screen.getAllByLabelText('Treść pytania')[1], {
      target: { value: 'Jakie masz doświadczenie?' },
    })
    fireEvent.click(screen.getAllByLabelText('Pytanie wymagane')[1])
    fireEvent.click(screen.getByRole('button', { name: 'Zapisz pytania' }))

    expect(await screen.findByText('Lista hackathonów')).toBeInTheDocument()
    expect(createRegistrationQuestions).toHaveBeenCalledWith('hackathon-id', {
      questions: [
        { content: 'Dlaczego chcesz wziąć udział?', is_required: true },
        { content: 'Jakie masz doświadczenie?', is_required: false },
      ],
    })
  })

  it('allows skipping questions', async () => {
    renderPage()

    fireEvent.click(screen.getByRole('button', { name: 'Pomiń' }))

    expect(await screen.findByText('Lista hackathonów')).toBeInTheDocument()
    expect(createRegistrationQuestions).not.toHaveBeenCalled()
  })
})
