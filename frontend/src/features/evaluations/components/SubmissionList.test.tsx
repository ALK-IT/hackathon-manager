import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getSubmissions } from '../api/evaluationsApi'
import { submission } from '../testFixtures'
import { SubmissionList } from './SubmissionList'

vi.mock('../api/evaluationsApi', () => ({ getSubmissions: vi.fn(), saveEvaluation: vi.fn() }))
const page = { items: [submission], total: 21, limit: 20, offset: 0 }

describe('SubmissionList', () => {
  beforeEach(() => vi.resetAllMocks())
  it('loads only the selected page and hides forms during the event', async () => {
    vi.mocked(getSubmissions).mockResolvedValueOnce(page).mockResolvedValueOnce({ ...page, offset: 20 })
    render(<SubmissionList hackathonId="hack" teamId="team" canEvaluate={false} />)
    expect(await screen.findByText('Drużyna Alfa — Zadanie API')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Zapisz ocenę' })).not.toBeInTheDocument()
    expect(getSubmissions).toHaveBeenCalledTimes(1)
    fireEvent.click(screen.getByRole('button', { name: 'Następna strona' }))
    await waitFor(() => expect(getSubmissions).toHaveBeenLastCalledWith('hack', expect.objectContaining({ offset: 20, limit: 20, teamPublicId: 'team' })))
    expect(await screen.findByText('Strona 2 z 2')).toBeInTheDocument()
  })
  it('recovers when the last page disappears after refresh', async () => {
    vi.mocked(getSubmissions).mockResolvedValueOnce(page)
      .mockResolvedValueOnce({ ...page, offset: 20 })
      .mockResolvedValueOnce({ items: [], total: 0, limit: 20, offset: 20 })
      .mockResolvedValueOnce({ items: [], total: 0, limit: 20, offset: 0 })
    render(<SubmissionList hackathonId="hack" canEvaluate />)
    await screen.findByText('Drużyna Alfa — Zadanie API')
    fireEvent.click(screen.getByRole('button', { name: 'Następna strona' }))
    await screen.findByText('Strona 2 z 2')
    fireEvent.click(screen.getByRole('button', { name: 'Odśwież rozwiązania' }))
    expect(await screen.findByText('Brak przesłanych rozwiązań dla wybranych filtrów.')).toBeInTheDocument()
    expect(getSubmissions).toHaveBeenLastCalledWith('hack', expect.objectContaining({ offset: 0 }))
  })
  it('aborts an obsolete request and ignores its late response', async () => {
    let resolve!: (value: typeof page) => void
    vi.mocked(getSubmissions).mockReturnValueOnce(new Promise((done) => { resolve = done }))
      .mockResolvedValueOnce({ items: [], total: 0, limit: 20, offset: 0 })
    const view = render(<SubmissionList key="old" hackathonId="old" canEvaluate={false} />)
    const signal = vi.mocked(getSubmissions).mock.calls[0][1].signal
    view.rerender(<SubmissionList key="new" hackathonId="new" canEvaluate={false} />)
    await screen.findByText('Brak przesłanych rozwiązań dla wybranych filtrów.')
    await act(async () => resolve(page))
    expect(signal?.aborted).toBe(true)
    expect(screen.queryByText('Drużyna Alfa — Zadanie API')).not.toBeInTheDocument()
  })
  it('allows retrying a failed request', async () => {
    vi.mocked(getSubmissions).mockRejectedValueOnce(new Error('network')).mockResolvedValueOnce(page)
    render(<SubmissionList hackathonId="hack" canEvaluate />)
    await screen.findByRole('alert')
    fireEvent.click(screen.getByRole('button', { name: 'Odśwież rozwiązania' }))
    expect(await screen.findByRole('button', { name: 'Zapisz ocenę' })).toBeInTheDocument()
  })
})
