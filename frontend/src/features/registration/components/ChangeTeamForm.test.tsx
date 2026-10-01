import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ChangeTeamForm } from './ChangeTeamForm'
import { changeMyTeam } from '../api/registrationApi'
import { ApiError } from '../../../lib/api/client'

vi.mock('../api/registrationApi', () => ({ changeMyTeam: vi.fn() }))

describe('ChangeTeamForm', () => {
  beforeEach(() => { vi.mocked(changeMyTeam).mockReset() })
  it('requires confirmation and refreshes after success', async () => {
    vi.mocked(changeMyTeam).mockResolvedValue(undefined)
    const changed = vi.fn()
    render(<ChangeTeamForm hackathonPublicId="event" startDate="2099-01-01" onChanged={changed} />)
    fireEvent.click(screen.getByText('Zmień drużynę'))
    fireEvent.change(screen.getByLabelText('Kod nowej drużyny'), { target: { value: 'new12345' } })
    fireEvent.click(screen.getByText('Akceptuj'))
    expect(changeMyTeam).not.toHaveBeenCalled()
    expect(screen.getByText(/Czy na pewno/)).toBeInTheDocument()
    fireEvent.click(screen.getByText('Potwierdź zmianę drużyny'))
    await waitFor(() => expect(changed).toHaveBeenCalledOnce())
    expect(changeMyTeam).toHaveBeenCalledWith('event', 'NEW12345')
  })
  it('does not send when cancelled', () => {
    render(<ChangeTeamForm hackathonPublicId="event" startDate="2099-01-01" onChanged={vi.fn()} />)
    fireEvent.click(screen.getByText('Zmień drużynę'))
    fireEvent.click(screen.getByText('Anuluj'))
    expect(changeMyTeam).not.toHaveBeenCalled()
  })
  it('hides the action after the start', () => {
    render(<ChangeTeamForm hackathonPublicId="event" startDate="2000-01-01" onChanged={vi.fn()} />)
    expect(screen.queryByText('Zmień drużynę')).not.toBeInTheDocument()
  })
  it('shows the backend error without refreshing the team', async () => {
    vi.mocked(changeMyTeam).mockRejectedValue(new ApiError(409, { error_code: 'TEAM_FULL' }))
    const changed = vi.fn()
    render(<ChangeTeamForm hackathonPublicId="event" startDate="2099-01-01" onChanged={changed} />)
    fireEvent.click(screen.getByText('Zmień drużynę'))
    fireEvent.change(screen.getByLabelText('Kod nowej drużyny'), { target: { value: 'NEW12345' } })
    fireEvent.click(screen.getByText('Akceptuj'))
    fireEvent.click(screen.getByText('Potwierdź zmianę drużyny'))
    expect(await screen.findByRole('alert')).toHaveTextContent('Ta drużyna jest już pełna.')
    expect(changed).not.toHaveBeenCalled()
    expect(screen.getByLabelText('Kod nowej drużyny')).toBeEnabled()
  })
  it('prevents duplicate requests while saving', async () => {
    let finish!: () => void
    vi.mocked(changeMyTeam).mockImplementation(() => new Promise<void>((resolve) => { finish = resolve }))
    render(<ChangeTeamForm hackathonPublicId="event" startDate="2099-01-01" onChanged={vi.fn()} />)
    fireEvent.click(screen.getByText('Zmień drużynę'))
    fireEvent.change(screen.getByLabelText('Kod nowej drużyny'), { target: { value: 'NEW12345' } })
    fireEvent.click(screen.getByText('Akceptuj'))
    const button = screen.getByText('Potwierdź zmianę drużyny')
    fireEvent.click(button)
    fireEvent.click(button)
    expect(button).toBeDisabled()
    expect(changeMyTeam).toHaveBeenCalledOnce()
    finish()
    await waitFor(() => expect(button).toBeEnabled())
  })
})
