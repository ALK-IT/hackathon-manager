export interface ApiValidationError {
  location: Array<string | number>
  message: string
  type: string
}

export interface ApiErrorPayload {
  error_code?: string
  detail?: string
  errors?: ApiValidationError[]
}

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
}
