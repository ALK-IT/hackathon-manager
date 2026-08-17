import { expect, test } from '@playwright/test'

// Konto powstaje przez API jako przygotowanie danych. W przeglądarce testujemy
// wyłącznie logowanie i odtworzenie sesji z refresh cookie po przeładowaniu.
test('uzytkownik moze sie zalogowac', async ({ page, request }) => {
  const email = `e2e-${Date.now()}@example.com`
  const password = 'password123'
  const apiUrl = process.env.E2E_API_URL ?? 'http://localhost:8000'

  const registerResponse = await request.post(`${apiUrl}/api/auth/register`, {
    data: { name: 'E2E User', email, password },
  })
  expect(registerResponse.status()).toBe(201)

  await page.goto('/login')
  await page.getByLabel('E-mail').fill(email)
  await page.getByLabel('Hasło').fill(password)
  await page.getByRole('button', { name: 'Zaloguj się' }).click()

  await expect(page).toHaveURL(/\/$/)
  await expect(page.getByText(`Zalogowano jako: ${email}`)).toBeVisible()

  await page.reload()

  await expect(page).toHaveURL(/\/$/)
  await expect(page.getByText(`Zalogowano jako: ${email}`)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Wyloguj się' })).toBeVisible()
})
