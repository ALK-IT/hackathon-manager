import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { getRegistrationQuestions } from '../api/registrationApi'
import { RegistrationQuestionsSetupPage } from './RegistrationQuestionsSetupPage'

vi.mock('../api/registrationApi', () => ({
  createRegistrationQuestion: vi.fn(),
  deleteRegistrationQuestion: vi.fn(),
  getRegistrationQuestions: vi.fn(),
}))

describe('RegistrationQuestionsSetupPage', () => {
  it('allows finishing the setup without questions', async () => {
    vi.mocked(getRegistrationQuestions).mockResolvedValue([])

    render(
      <MemoryRouter initialEntries={['/hackathons/hackathon-id/questions/setup']}>
        <Routes>
          <Route
            path="/hackathons/:hackathonPublicId/questions/setup"
            element={<RegistrationQuestionsSetupPage />}
          />
          <Route path="/hackathons" element={<p>Lista hackathonów</p>} />
        </Routes>
      </MemoryRouter>,
    )

    expect(
      await screen.findByText('Nie dodano jeszcze pytań. Ten krok możesz pominąć.'),
    ).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Zakończ konfigurację' }))

    expect(await screen.findByText('Lista hackathonów')).toBeInTheDocument()
  })
})
