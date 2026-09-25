import { render, screen } from '@testing-library/react'
import { expect, it } from 'vitest'
import { evaluation, submission } from '../testFixtures'
import { ParticipantResults } from './ParticipantResults'

it('distinguishes a zero score, pending evaluation, and missing submission', () => {
  const task = { public_id: 'task', title: 'Zadanie', description: 'Opis',
    criteria: submission.task.criteria, visible_from: '', created_at: '', updated_at: '' }
  render(<ParticipantResults tasks={[
    { ...task, public_id: '1', submission: { ...submission, evaluation } },
    { ...task, public_id: '2', submission },
    { ...task, public_id: '3', submission: null },
  ]} />)
  expect(screen.getByText('Ocena: 0 / 200')).toBeInTheDocument()
  expect(screen.getByText('Feedback: Do poprawy')).toBeInTheDocument()
  expect(screen.getByText('Oczekuje na ocenę.')).toBeInTheDocument()
  expect(screen.getByText('Nie przesłano rozwiązania.')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Zapisz ocenę' })).not.toBeInTheDocument()
  expect(screen.getAllByRole('link')[0]).toHaveAttribute('rel', 'noreferrer')
})
