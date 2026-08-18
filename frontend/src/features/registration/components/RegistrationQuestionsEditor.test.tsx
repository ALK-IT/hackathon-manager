import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../../../lib/api/client'
import {
  createRegistrationQuestion,
  deleteRegistrationQuestion,
  getRegistrationQuestions,
} from '../api/registrationApi'
import { RegistrationQuestionsEditor } from './RegistrationQuestionsEditor'

vi.mock('../api/registrationApi', () => ({
  createRegistrationQuestion: vi.fn(),
  deleteRegistrationQuestion: vi.fn(),
  getRegistrationQuestions: vi.fn(),
}))

const existingQuestion = {
  public_id: 'existing-question-id',
  content: 'Jakie masz doświadczenie?',
  is_required: true,
}

describe('RegistrationQuestionsEditor', () => {
  beforeEach(() => {
    vi.mocked(getRegistrationQuestions).mockReset()
    vi.mocked(createRegistrationQuestion).mockReset()
    vi.mocked(deleteRegistrationQuestion).mockReset()
  })

  it('adds an optional question with the plus button', async () => {
    vi.mocked(getRegistrationQuestions).mockResolvedValue([])
    vi.mocked(createRegistrationQuestion).mockResolvedValue({
      public_id: 'new-question-id',
      content: 'Jaki projekt chcesz zbudować?',
      is_required: false,
    })

    render(<RegistrationQuestionsEditor hackathonPublicId="hackathon-id" />)

    await screen.findByText('Nie dodano jeszcze pytań. Ten krok możesz pominąć.')
    fireEvent.change(screen.getByLabelText('Treść pytania'), {
      target: { value: '  Jaki projekt chcesz zbudować?  ' },
    })
    fireEvent.click(screen.getByLabelText('Wymagane'))
    fireEvent.click(screen.getByRole('button', { name: '+ Dodaj pytanie' }))

    expect(await screen.findByText('Jaki projekt chcesz zbudować?')).toBeInTheDocument()
    expect(screen.getByText('Opcjonalne')).toBeInTheDocument()
    expect(createRegistrationQuestion).toHaveBeenCalledWith('hackathon-id', {
      content: 'Jaki projekt chcesz zbudować?',
      is_required: false,
    })
    expect(screen.getByLabelText('Treść pytania')).toHaveValue('')
    expect(screen.getByLabelText('Wymagane')).toBeChecked()
  })

  it('validates an empty question without calling the API', async () => {
    vi.mocked(getRegistrationQuestions).mockResolvedValue([])

    render(<RegistrationQuestionsEditor hackathonPublicId="hackathon-id" />)

    await screen.findByText('Nie dodano jeszcze pytań. Ten krok możesz pominąć.')
    fireEvent.click(screen.getByRole('button', { name: '+ Dodaj pytanie' }))

    expect(screen.getByText('Podaj treść pytania.')).toBeInTheDocument()
    expect(createRegistrationQuestion).not.toHaveBeenCalled()
  })

  it('deletes an existing question', async () => {
    vi.mocked(getRegistrationQuestions).mockResolvedValue([existingQuestion])
    vi.mocked(deleteRegistrationQuestion).mockResolvedValue(undefined)

    render(<RegistrationQuestionsEditor hackathonPublicId="hackathon-id" />)

    fireEvent.click(
      await screen.findByRole('button', {
        name: 'Usuń pytanie: Jakie masz doświadczenie?',
      }),
    )

    await waitFor(() =>
      expect(deleteRegistrationQuestion).toHaveBeenCalledWith(
        'hackathon-id',
        'existing-question-id',
      ),
    )
    expect(
      await screen.findByText('Nie dodano jeszcze pytań. Ten krok możesz pominąć.'),
    ).toBeInTheDocument()
  })

  it('locks controls when registration has already opened', async () => {
    vi.mocked(getRegistrationQuestions).mockResolvedValue([])
    vi.mocked(createRegistrationQuestion).mockRejectedValue(
      new ApiError(409, {
        error_code: 'REGISTRATION_QUESTIONS_LOCKED',
        detail: 'Registration questions are locked.',
      }),
    )

    render(<RegistrationQuestionsEditor hackathonPublicId="hackathon-id" />)

    await screen.findByText('Nie dodano jeszcze pytań. Ten krok możesz pominąć.')
    fireEvent.change(screen.getByLabelText('Treść pytania'), {
      target: { value: 'Za późne pytanie' },
    })
    fireEvent.click(screen.getByRole('button', { name: '+ Dodaj pytanie' }))

    expect(
      await screen.findByText(
        'Nie można już zmieniać pytań, ponieważ rejestracja została otwarta.',
      ),
    ).toBeInTheDocument()
    expect(screen.getByLabelText('Treść pytania')).toBeDisabled()
    expect(screen.getByRole('button', { name: '+ Dodaj pytanie' })).toBeDisabled()
  })
})
