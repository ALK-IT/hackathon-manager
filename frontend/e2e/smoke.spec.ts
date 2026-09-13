import { expect, test } from '@playwright/test'

interface HackathonPage {
  items: Array<{ name: string }>
  total: number
  limit: number
  offset: number
}

test('frontend works, the hackathon list is public and the language can be changed', async ({ page }) => {
  const hackathonsResponsePromise = page.waitForResponse((response) => {
    const url = new URL(response.url())
    return url.pathname === '/api/hackathons' && response.request().method() === 'GET'
  })

  await page.goto('/')
  const response = await hackathonsResponsePromise

  expect(response.status()).toBe(200)
  const hackathonPage = (await response.json()) as HackathonPage
  expect(hackathonPage.items).toEqual(expect.any(Array))
  expect(hackathonPage.total).toEqual(expect.any(Number))
  const hackathons = hackathonPage.items

  await expect(page.getByRole('heading', { name: 'Hackathons' })).toBeVisible()
  await expect(page.getByText('Loading hackathons…')).toBeHidden()
  await expect(page.getByRole('alert')).toHaveCount(0)

  if (hackathons.length === 0) {
    await expect(page.getByText('No hackathons to display.')).toBeVisible()
  } else {
    await expect(page.getByRole('link', { name: hackathons[0].name })).toBeVisible()
  }

  await page.getByRole('button', { name: 'Change language' }).click()
  await expect(page.getByRole('heading', { name: 'Hackathony' })).toBeVisible()
})
