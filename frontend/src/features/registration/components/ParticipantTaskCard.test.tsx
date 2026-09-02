import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { saveTaskSubmission } from '../api/registrationApi'
import type { ParticipantTask } from '../types'
import { ParticipantTaskCard } from './ParticipantTaskCard'

vi.mock('../api/registrationApi', () => ({
  saveTaskSubmission: vi.fn(),
}))

const task: ParticipantTask = {
  public_id: 'task-id',
  title: 'Publiczne API',
  description: 'Zbuduj API dla aplikacji.',
  created_at: '2026-09-03T08:00:00Z',
  updated_at: '2026-09-03T08:00:00Z',
  submission: null,
}

describe('ParticipantTaskCard', () => {
  beforeEach(() => vi.mocked(saveTaskSubmission).mockReset())

  it('saves and displays a GitHub solution', async () => {
    vi.mocked(saveTaskSubmission).mockResolvedValue({
      public_id: 'submission-id',
      github_url: 'https://github.com/example/repo',
      team: { public_id: 'team-id', name: 'Byte Buccaneers' },
      submitted_by: { public_id: 'user-id', name: 'Jan Kowalski' },
      created_at: '2026-09-03T09:00:00Z',
      updated_at: '2026-09-03T09:00:00Z',
    })

    render(
      <ParticipantTaskCard
        hackathonPublicId="hackathon-id"
        task={task}
        canSubmit
        submissionsClosed={false}
      />,
    )

    fireEvent.change(screen.getByLabelText('Link do rozwiązania na GitHubie'), {
      target: { value: 'https://github.com/example/repo' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Wyślij link' }))

    await waitFor(() => {
      expect(saveTaskSubmission).toHaveBeenCalledWith(
        'hackathon-id',
        'task-id',
        'https://github.com/example/repo',
      )
    })
    expect(await screen.findByRole('link', { name: 'https://github.com/example/repo' }))
      .toBeInTheDocument()
    expect(screen.getByText('Rozwiązanie zostało zapisane.')).toBeInTheDocument()
  })

  it('does not show the form to a participant without a team', () => {
    render(
      <ParticipantTaskCard
        hackathonPublicId="hackathon-id"
        task={task}
        canSubmit={false}
        submissionsClosed={false}
      />,
    )

    expect(screen.queryByLabelText('Link do rozwiązania na GitHubie')).not.toBeInTheDocument()
  })
})
