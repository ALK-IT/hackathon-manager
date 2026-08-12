import { expect, test } from '@playwright/test'

const API_URL = process.env.E2E_API_URL ?? 'http://localhost:8000'

test('frontend dziala, a lista hackathonow jest publiczna', async ({
  page,
  request,
}) => {
  const response = await request.get(`${API_URL}/api/hackathons`)

  expect(response.status()).toBe(200)
  expect(await response.json()).toEqual(expect.any(Array))

  await page.goto('/')

  await expect(page.getByRole('heading', { name: 'Hackathony' })).toBeVisible()
  await expect(page.getByRole('status')).toBeHidden()
  await expect(page.getByRole('alert')).toHaveCount(0)
})
