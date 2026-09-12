import { apiRequest } from '../../../lib/api/client'
import type {
  MarkAllReadResponse,
  Notification,
  NotificationListResponse,
} from '../types'

export function getNotifications(signal?: AbortSignal) {
  return apiRequest<NotificationListResponse>('/api/notifications?limit=20&offset=0', {
    signal,
  })
}

export function markNotificationRead(publicId: string) {
  return apiRequest<Notification>(`/api/notifications/${publicId}/read`, {
    method: 'PATCH',
  })
}

export function markAllNotificationsRead() {
  return apiRequest<MarkAllReadResponse>('/api/notifications/read-all', {
    method: 'POST',
  })
}
