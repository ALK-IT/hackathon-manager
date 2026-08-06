import { expect, test } from '@playwright/test'

const API_URL = process.env.E2E_API_URL ?? 'http://localhost:8000'

test('frontend dziala, a lista hackathonow wymaga uwierzytelnienia', async ({
  page,
  request,
}) => {
  const response = await request.get(`${API_URL}/api/hackathons`)

  expect(response.status()).toBe(401)

  await page.goto('/')

  await expect(page.getByRole('heading', { name: 'Hackathony' })).toBeVisible()
})
