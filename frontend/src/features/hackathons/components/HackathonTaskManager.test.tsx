import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  createHackathonTask,
  getHackathonTasks,
  updateHackathonTask,
} from '../api/hackathonsApi'
import { HackathonTaskManager } from './HackathonTaskManager'

vi.mock('../api/hackathonsApi', () => ({
  createHackathonTask: vi.fn(),
  getHackathonTasks: vi.fn(),
  updateHackathonTask: vi.fn(),
}))

const hackathonPublicId = 'hackathon-id'
const hackathonStartDate = '2099-09-01T10:00:00Z'
const hackathonEndDate = '2099-09-02T18:00:00Z'

function renderManager() {
  return render(
    <HackathonTaskManager
      hackathonPublicId={hackathonPublicId}
      hackathonStartDate={hackathonStartDate}
      hackathonEndDate={hackathonEndDate}
    />,
  )
}

describe('HackathonTaskManager', () => {
  beforeEach(() => {
    vi.mocked(createHackathonTask).mockReset()
    vi.mocked(getHackathonTasks).mockReset()
    vi.mocked(updateHackathonTask).mockReset()
    vi.mocked(getHackathonTasks).mockResolvedValue([])
  })

  it('loads and displays existing tasks', async () => {
    vi.mocked(getHackathonTasks).mockResolvedValue([
      {
        public_id: 'task-id',
        title: 'Publiczne API',
        description: 'Zbuduj API dla aplikacji.',
        criteria: [{ name: 'Jakość', description: 'Czytelność', max_points: 10 }],
        visible_from: '2099-09-01T12:00:00Z',
        created_at: '2099-08-01T10:00:00Z',
        updated_at: '2099-08-01T10:00:00Z',
      },
    ])

    renderManager()

    expect(await screen.findByText('Publiczne API')).toBeInTheDocument()
    expect(screen.getByText('Zbuduj API dla aplikacji.')).toBeInTheDocument()
    expect(screen.getByText('Jakość — 10 pkt')).toBeInTheDocument()
    expect(getHackathonTasks).toHaveBeenCalledWith(
      hackathonPublicId,
      expect.any(AbortSignal),
    )
  })

  it('creates a task using normalized form values', async () => {
    vi.mocked(createHackathonTask).mockResolvedValue({
      public_id: 'new-task-id',
      title: 'Frontend',
      description: 'Zbuduj interfejs.',
      criteria: [{ name: 'UX', description: '', max_points: 20 }],
      visible_from: '2099-09-01T14:00:00Z',
      created_at: '2099-08-01T10:00:00Z',
      updated_at: '2099-08-01T10:00:00Z',
    })
    renderManager()

    await screen.findByText('Nie dodano jeszcze zadań.')
    fireEvent.change(screen.getByLabelText('Nazwa zadania'), {
      target: { value: '  Frontend  ' },
    })
    fireEvent.change(screen.getByLabelText('Opis zadania'), {
      target: { value: '  Zbuduj interfejs.  ' },
    })
    fireEvent.change(screen.getByLabelText('Widoczne dla uczestników od'), {
      target: { value: '2099-09-01T16:00' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Dodaj kryterium' }))
    fireEvent.change(screen.getByLabelText('Nazwa kryterium'), { target: { value: ' UX ' } })
    fireEvent.change(screen.getByLabelText('Maksymalna liczba punktów'), { target: { value: '20' } })
    fireEvent.click(screen.getByRole('button', { name: 'Dodaj zadanie' }))

    await waitFor(() =>
      expect(createHackathonTask).toHaveBeenCalledWith(hackathonPublicId, {
        title: 'Frontend',
        description: 'Zbuduj interfejs.',
        visible_from: new Date('2099-09-01T16:00').toISOString(),
        criteria: [{ name: 'UX', description: '', max_points: 20 }],
      }),
    )
    expect(await screen.findByText('Zadanie zostało dodane.')).toBeInTheDocument()
    expect(screen.getByText('Frontend')).toBeInTheDocument()
  })

  it('edits a task without replacing its public id', async () => {
    const existing = {
      public_id: 'task-id', title: 'API', description: 'Stary opis',
      criteria: [{ name: 'Kod', description: '', max_points: 10 }],
      visible_from: '2099-09-01T12:00:00Z', created_at: '', updated_at: '',
    }
    vi.mocked(getHackathonTasks).mockResolvedValue([existing])
    vi.mocked(updateHackathonTask).mockResolvedValue({
      ...existing, title: 'API v2', criteria: [{ name: 'Kod', description: '', max_points: 15 }],
    })
    renderManager()

    fireEvent.click(await screen.findByRole('button', { name: 'Edytuj zadanie' }))
    fireEvent.change(screen.getByLabelText('Nazwa zadania'), { target: { value: 'API v2' } })
    fireEvent.change(screen.getByLabelText('Maksymalna liczba punktów'), { target: { value: '15' } })
    fireEvent.click(screen.getByRole('button', { name: 'Zapisz zmiany' }))

    await waitFor(() => expect(updateHackathonTask).toHaveBeenCalledWith(
      hackathonPublicId, 'task-id', expect.objectContaining({
        title: 'API v2', criteria: [{ name: 'Kod', description: '', max_points: 15 }],
      }),
    ))
    expect(await screen.findByText('Zadanie zostało zaktualizowane.')).toBeInTheDocument()
    expect(screen.getByText('API v2')).toBeInTheDocument()
  })
})
