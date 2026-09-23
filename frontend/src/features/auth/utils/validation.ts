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

export function validateLogin(email: string, password: string, language: 'pl' | 'en' = 'pl'): LoginErrors {
  const errors: LoginErrors = {}
  if (!isValidEmail(email)) errors.email = language === 'en' ? 'Enter a valid email address.' : 'Podaj poprawny adres e-mail.'
  if (!password) errors.password = language === 'en' ? 'Enter your password.' : 'Podaj hasło.'
  return errors
}

export function validateRegister(
  name: string,
  email: string,
  password: string,
  confirmPassword: string, language: 'pl' | 'en' = 'pl',
): RegisterErrors {
  const errors: RegisterErrors = validateLogin(email, password, language)
  if (name.trim().length < 3) errors.name = language === 'en' ? 'Username must be at least 3 characters.' : 'Nazwa musi mieć co najmniej 3 znaki.'
  if (password.length < 8) errors.password = language === 'en' ? 'Password must be at least 8 characters.' : 'Hasło musi mieć co najmniej 8 znaków.'
  if (password !== confirmPassword) errors.confirmPassword = language === 'en' ? 'Passwords must match.' : 'Hasła muszą być takie same.'
  return errors
}
