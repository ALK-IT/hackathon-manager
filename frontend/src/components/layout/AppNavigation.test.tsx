import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { AppNavigation } from './AppNavigation'

function renderNavigation() {
  return render(
    <MemoryRouter>
      <AppNavigation />
    </MemoryRouter>,
  )
}

describe('AppNavigation', () => {
  it('shows the hackathons link without a global resources link', () => {
    renderNavigation()

    expect(screen.getByRole('link', { name: 'Hackathony' })).toHaveAttribute(
      'href',
      '/hackathons',
    )
    expect(screen.queryByRole('link', { name: 'Moje zasoby' })).not.toBeInTheDocument()
  })
})
