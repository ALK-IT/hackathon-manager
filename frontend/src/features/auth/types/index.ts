export interface User {
  public_id: string
  name: string
  email: string
  created_at: string
  role: 'user' | 'admin'
}

export interface RegisterPayload {
  name: string
  email: string
  password: string
}
