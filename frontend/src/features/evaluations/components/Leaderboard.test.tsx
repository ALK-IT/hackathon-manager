import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, expect, it, vi } from 'vitest'
import { getLeaderboard, setLeaderboardVisibility } from '../api/evaluationsApi'
import { Leaderboard } from './Leaderboard'

vi.mock('../api/evaluationsApi', () => ({
  getLeaderboard: vi.fn(),
  setLeaderboardVisibility: vi.fn(),
}))

beforeEach(() => {
  vi.mocked(getLeaderboard).mockReset()
  vi.mocked(getLeaderboard).mockResolvedValue({ items: [
    { rank: 1, team_public_id: 'alpha', team_name: 'Alpha', total_score: 18.5, evaluated_tasks: 2 },
    { rank: 2, team_public_id: 'beta', team_name: 'Beta', total_score: 8, evaluated_tasks: 1 },
  ] })
  vi.mocked(setLeaderboardVisibility).mockResolvedValue({ visible: true })
})

it('lets a manager publish the leaderboard for participants', async () => {
  render(<Leaderboard hackathonId="hack" canManage />)
  fireEvent.click(await screen.findByRole('button', { name: 'Pokaż uczestnikom' }))
  await waitFor(() => expect(setLeaderboardVisibility).toHaveBeenCalledWith('hack', true))
  expect(await screen.findByRole('button', { name: 'Ukryj przed uczestnikami' })).toBeInTheDocument()
})

it('shows ranked teams and reloads after changing the number of places', async () => {
  render(<Leaderboard hackathonId="hack" />)
  expect(await screen.findByText('Alpha')).toBeInTheDocument()
  expect(screen.getByText('18.5')).toBeInTheDocument()
  expect(getLeaderboard).toHaveBeenCalledWith('hack', 10, expect.any(AbortSignal))

  fireEvent.change(screen.getByLabelText('Pokaż pierwszych miejsc'), { target: { value: '5' } })
  await waitFor(() => expect(getLeaderboard).toHaveBeenLastCalledWith(
    'hack', 5, expect.any(AbortSignal),
  ))
})
