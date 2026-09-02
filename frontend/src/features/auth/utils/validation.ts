const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function isValidEmail(email: string): boolean {
  return EMAIL_PATTERN.test(email.trim())
}

export interface LoginErrors {
  email?: string
  password?: string
}

export interface RegisterErrors extends LoginErrors {
  name?: string
  confirmPassword?: string
}

export function validateLogin(email: string, password: string): LoginErrors {
  const errors: LoginErrors = {}
  if (!isValidEmail(email)) errors.email = 'Podaj poprawny adres e-mail.'
  if (!password) errors.password = 'Podaj hasło.'
  return errors
}

export function validateRegister(
  name: string,
  email: string,
  password: string,
  confirmPassword: string,
): RegisterErrors {
  const errors: RegisterErrors = validateLogin(email, password)
  if (name.trim().length < 3) errors.name = 'Nazwa musi mieć co najmniej 3 znaki.'
  if (password.length < 8) errors.password = 'Hasło musi mieć co najmniej 8 znaków.'
  if (password !== confirmPassword) errors.confirmPassword = 'Hasła muszą być takie same.'
  return errors
}
