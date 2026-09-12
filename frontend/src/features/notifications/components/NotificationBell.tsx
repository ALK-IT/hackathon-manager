import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Spinner } from '../../../components/ui'
import {
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '../api/notificationsApi'
import type { Notification } from '../types'

const dateFormatter = new Intl.DateTimeFormat('pl-PL', {
  day: 'numeric',
  month: 'short',
  hour: '2-digit',
  minute: '2-digit',
})

export function NotificationBell() {
  const navigate = useNavigate()
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const activeController = useRef<AbortController | null>(null)

  useEffect(() => {
    let active = true

    async function load() {
      activeController.current?.abort()
      const controller = new AbortController()
      activeController.current = controller
      try {
        const result = await getNotifications(controller.signal)
        if (!active) return
        setNotifications(result.items)
        setUnreadCount(result.unread_count)
        setError(null)
      } catch (requestError) {
        if (
          active &&
          !(requestError instanceof DOMException && requestError.name === 'AbortError')
        ) {
          setError('Nie udało się pobrać powiadomień.')
        }
      } finally {
        if (active && !controller.signal.aborted) setIsLoading(false)
      }
    }

    function handleFocus() {
      setIsLoading(true)
      void load()
    }

    void load()
    window.addEventListener('focus', handleFocus)
    return () => {
      active = false
      activeController.current?.abort()
      window.removeEventListener('focus', handleFocus)
    }
  }, [])

  async function openNotification(notification: Notification) {
    if (!notification.read_at) {
      setNotifications((items) =>
        items.map((item) =>
          item.public_id === notification.public_id
            ? { ...item, read_at: new Date().toISOString() }
            : item,
        ),
      )
      setUnreadCount((count) => Math.max(0, count - 1))
      try {
        await markNotificationRead(notification.public_id)
      } catch {
        setError('Nie udało się oznaczyć powiadomienia jako przeczytane.')
      }
    }

    setIsOpen(false)
    if (notification.target_url) navigate(notification.target_url)
  }

  async function markAllRead() {
    try {
      await markAllNotificationsRead()
      const readAt = new Date().toISOString()
      setNotifications((items) => items.map((item) => ({ ...item, read_at: item.read_at ?? readAt })))
      setUnreadCount(0)
      setError(null)
    } catch {
      setError('Nie udało się oznaczyć wszystkich powiadomień jako przeczytane.')
    }
  }

  return (
    <div className="notification-center">
      <button
        className="notification-bell"
        type="button"
        aria-label={`Powiadomienia, nieprzeczytane: ${unreadCount}`}
        aria-expanded={isOpen}
        onClick={() => setIsOpen((open) => !open)}
      >
        <span aria-hidden="true">🔔</span>
        {unreadCount > 0 && <span className="notification-badge">{unreadCount > 99 ? '99+' : unreadCount}</span>}
      </button>

      {isOpen && (
        <section className="notification-panel" aria-label="Powiadomienia">
          <div className="notification-panel-header">
            <h2>Powiadomienia</h2>
            {unreadCount > 0 && (
              <Button type="button" variant="ghost" onClick={() => void markAllRead()}>
                Oznacz wszystkie
              </Button>
            )}
          </div>
          {isLoading && <div className="notification-state"><Spinner /> Pobieranie…</div>}
          {error && <p className="notification-error" role="alert">{error}</p>}
          {!isLoading && notifications.length === 0 && (
            <p className="notification-state">Nie masz jeszcze powiadomień.</p>
          )}
          <div className="notification-list">
            {notifications.map((notification) => (
              <button
                className={`notification-item${notification.read_at ? '' : ' notification-item--unread'}`}
                type="button"
                key={notification.public_id}
                onClick={() => void openNotification(notification)}
              >
                <span className="notification-item-heading">
                  <strong>{notification.title}</strong>
                  {!notification.read_at && <span className="notification-unread-dot" aria-label="Nieprzeczytane" />}
                </span>
                <span>{notification.message}</span>
                <time dateTime={notification.created_at}>
                  {dateFormatter.format(new Date(notification.created_at))}
                </time>
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
