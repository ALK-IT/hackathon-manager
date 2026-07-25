import { expect, test } from '@playwright/test'

// Przykladowy E2E: caly stack (frontend + backend + Postgres + Redis, przez
// docker compose) - sprawdza, ze dane naprawde plyna z bazy przez API do UI,
// nie tylko ze komponenty renderuja sie w izolacji (to robia testy jednostkowe).
test('frontend wyswietla hackathony z prawdziwego backendu i bazy', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByRole('heading', { name: 'Hackathony' })).toBeVisible()
  // "HackYeah 2026" pochodzi z seeda w migracji Alembic (0001_create_hackathons.py) -
  // jego obecnosc potwierdza, ze zadzialal caly przekroj: Postgres -> repository -> service -> API -> UI.
  await expect(page.getByText(/HackYeah 2026/)).toBeVisible()
})
