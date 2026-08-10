export interface User {
  public_id: string
  name: string
  email: string
  created_at: string
}

export interface RegisterPayload {
  name: string
  email: string
  password: string
}
