import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '../api/notificationsApi'
import { NotificationBell } from './NotificationBell'

vi.mock('../api/notificationsApi', () => ({
  getNotifications: vi.fn(),
  markNotificationRead: vi.fn(),
  markAllNotificationsRead: vi.fn(),
}))

function CurrentPath() {
  return <span data-testid="current-path">{useLocation().pathname}</span>
}

describe('NotificationBell', () => {
  beforeEach(() => {
    vi.mocked(getNotifications).mockReset()
    vi.mocked(markNotificationRead).mockReset()
    vi.mocked(markAllNotificationsRead).mockReset()
  })

  it('shows unread notifications and marks one read when it is opened', async () => {
    vi.mocked(getNotifications).mockResolvedValue({
      unread_count: 1,
      items: [{
        public_id: 'notification-1',
        kind: 'registration_status_changed',
        title: 'Zgłoszenie zaakceptowane',
        message: 'Twoje zgłoszenie zostało zaakceptowane.',
        target_url: '/hackathons/hackathon-1',
        read_at: null,
        created_at: '2026-09-12T12:00:00Z',
      }],
    })
    vi.mocked(markNotificationRead).mockResolvedValue({
      public_id: 'notification-1',
      kind: 'registration_status_changed',
      title: 'Zgłoszenie zaakceptowane',
      message: 'Twoje zgłoszenie zostało zaakceptowane.',
      target_url: '/hackathons/hackathon-1',
      read_at: '2026-09-12T12:01:00Z',
      created_at: '2026-09-12T12:00:00Z',
    })

    render(
      <MemoryRouter>
        <NotificationBell />
        <CurrentPath />
      </MemoryRouter>,
    )

    const bell = await screen.findByRole('button', { name: 'Powiadomienia, nieprzeczytane: 1' })
    fireEvent.click(bell)
    fireEvent.click(screen.getByRole('button', { name: /Zgłoszenie zaakceptowane/ }))

    await waitFor(() => expect(markNotificationRead).toHaveBeenCalledWith('notification-1'))
    await waitFor(() =>
      expect(screen.getByTestId('current-path')).toHaveTextContent('/hackathons/hackathon-1'),
    )
  })

  it('refreshes notifications when the window regains focus', async () => {
    vi.mocked(getNotifications).mockResolvedValue({ items: [], unread_count: 0 })

    render(<MemoryRouter><NotificationBell /></MemoryRouter>)
    await waitFor(() => expect(getNotifications).toHaveBeenCalledTimes(1))
    fireEvent.focus(window)
    await waitFor(() => expect(getNotifications).toHaveBeenCalledTimes(2))
  })
})
