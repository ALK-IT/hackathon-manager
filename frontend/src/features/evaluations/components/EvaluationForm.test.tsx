import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../../../lib/api/client'
import { saveEvaluation } from '../api/evaluationsApi'
import { evaluation, submission } from '../testFixtures'
import { EvaluationForm } from './EvaluationForm'

vi.mock('../api/evaluationsApi', () => ({ saveEvaluation: vi.fn() }))

describe('EvaluationForm', () => {
  beforeEach(() => vi.resetAllMocks())
  it('saves zero, trims feedback and prevents duplicate requests', async () => {
    let resolve!: (value: typeof evaluation) => void
    vi.mocked(saveEvaluation).mockReturnValue(new Promise((done) => { resolve = done }))
    const onSaved = vi.fn()
    render(<EvaluationForm hackathonId="hack" submission={submission} onSaved={onSaved} />)
    fireEvent.change(screen.getByLabelText('Ocena (0–10)'), { target: { value: '0' } })
    fireEvent.change(screen.getByLabelText('Feedback (opcjonalnie)'), { target: { value: '  Dobra próba  ' } })
    const button = screen.getByRole('button', { name: 'Zapisz ocenę' })
    fireEvent.submit(button.closest('form')!)
    fireEvent.submit(button.closest('form')!)
    expect(saveEvaluation).toHaveBeenCalledTimes(1)
    expect(saveEvaluation).toHaveBeenCalledWith('hack', 'task-1', 'submission-1', { score: 0, feedback: 'Dobra próba' })
    resolve(evaluation)
    await waitFor(() => expect(onSaved).toHaveBeenCalledOnce())
  })
  it.each(['', '-1', '11', '1.234'])('rejects invalid score %s before calling API', (value) => {
    render(<EvaluationForm hackathonId="hack" submission={submission} onSaved={vi.fn()} />)
    fireEvent.change(screen.getByLabelText('Ocena (0–10)'), { target: { value } })
    fireEvent.submit(screen.getByRole('button', { name: 'Zapisz ocenę' }).closest('form')!)
    expect(saveEvaluation).not.toHaveBeenCalled()
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })
  it('prefills existing evaluation and preserves edits on a server error', async () => {
    vi.mocked(saveEvaluation).mockRejectedValue(new ApiError(409, { error_code: 'TASK_EVALUATION_NOT_OPEN' }))
    render(<EvaluationForm hackathonId="hack" submission={{ ...submission, evaluation }} onSaved={vi.fn()} />)
    expect(screen.getByLabelText('Ocena (0–10)')).toHaveValue(0)
    fireEvent.change(screen.getByLabelText('Ocena (0–10)'), { target: { value: '8.5' } })
    fireEvent.click(screen.getByRole('button', { name: 'Zapisz ocenę' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('dopiero po zakończeniu')
    expect(screen.getByLabelText('Ocena (0–10)')).toHaveValue(8.5)
  })
})
