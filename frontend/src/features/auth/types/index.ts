export type Language = 'pl' | 'en'

export interface User {
  public_id: string
  name: string
  email: string
  created_at: string
  role: 'user' | 'admin'
  language: Language
}

export interface RegisterPayload {
  name: string
  email: string
  password: string
}

export interface UserSettingsPayload {
  name: string
  language: Language
}
