export interface Notification {
  public_id: string
  kind: string
  title: string
  message: string
  target_url: string | null
  read_at: string | null
  created_at: string
}

export interface NotificationListResponse {
  items: Notification[]
  unread_count: number
}

export interface MarkAllReadResponse {
  updated_count: number
}
