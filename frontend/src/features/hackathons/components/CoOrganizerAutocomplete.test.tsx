import { fireEvent, render, screen } from '@testing-library/react'
import { useState } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { searchCoOrganizerCandidates } from '../api/hackathonsApi'
import type { UserSummary } from '../types'
import { CoOrganizerAutocomplete } from './CoOrganizerAutocomplete'

vi.mock('../api/hackathonsApi', () => ({
  searchCoOrganizerCandidates: vi.fn(),
}))

const candidate = {
  public_id: 'c68d217a-0ee7-4bc3-b25f-cad078df0da7',
  name: 'Jan Kowalski',
}

function TestAutocomplete() {
  const [query, setQuery] = useState('')
  const [selectedCandidate, setSelectedCandidate] = useState<UserSummary | null>(null)

  return (
    <CoOrganizerAutocomplete
      hackathonPublicId="hackathon-id"
      query={query}
      selectedCandidate={selectedCandidate}
      onQueryChange={(nextQuery) => {
        setQuery(nextQuery)
        setSelectedCandidate(null)
      }}
      onCandidateSelect={(selected) => {
        setQuery(selected.name)
        setSelectedCandidate(selected)
      }}
    />
  )
}

describe('CoOrganizerAutocomplete', () => {
  beforeEach(() => {
    vi.mocked(searchCoOrganizerCandidates).mockReset()
    vi.mocked(searchCoOrganizerCandidates).mockResolvedValue([candidate])
  })

  it('searches by name and keeps the selected candidate', async () => {
    render(<TestAutocomplete />)

    fireEvent.change(screen.getByLabelText('Nazwa użytkownika'), {
      target: { value: 'Jan' },
    })
    fireEvent.click(await screen.findByRole('option', { name: 'Jan Kowalski' }))

    expect(searchCoOrganizerCandidates).toHaveBeenCalledWith(
      'hackathon-id',
      'Jan',
      expect.any(AbortSignal),
    )
    expect(screen.getByLabelText('Nazwa użytkownika')).toHaveValue('Jan Kowalski')
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  })
})
