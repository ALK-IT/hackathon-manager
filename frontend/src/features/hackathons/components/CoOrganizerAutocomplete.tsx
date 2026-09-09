import { useEffect, useId, useState } from 'react'
import { Alert } from '../../../components/ui'
import { FormField } from '../../auth/components/FormField'
import { searchCoOrganizerCandidates } from '../api/hackathonsApi'
import type { UserSummary } from '../types'

interface CoOrganizerAutocompleteProps {
  hackathonPublicId: string
  query: string
  selectedCandidate: UserSummary | null
  error?: string
  onQueryChange: (query: string) => void
  onCandidateSelect: (candidate: UserSummary) => void
}

export function CoOrganizerAutocomplete({
  hackathonPublicId,
  query,
  selectedCandidate,
  error,
  onQueryChange,
  onCandidateSelect,
}: CoOrganizerAutocompleteProps) {
  const inputId = useId()
  const candidatesId = `${inputId}-candidates`
  const [candidates, setCandidates] = useState<UserSummary[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)

  useEffect(() => {
    const normalizedQuery = query.trim()
    if (normalizedQuery.length < 2 || selectedCandidate?.name === query) {
      setCandidates([])
      setSearchError(null)
      setIsSearching(false)
      return
    }

    const controller = new AbortController()
    const timeoutId = window.setTimeout(async () => {
      setIsSearching(true)
      setSearchError(null)

      try {
        const results = await searchCoOrganizerCandidates(
          hackathonPublicId,
          normalizedQuery,
          controller.signal,
        )
        setCandidates(results)
      } catch (requestError) {
        if (requestError instanceof Error && requestError.name === 'AbortError') return
        setCandidates([])
        setSearchError('Nie udało się wyszukać użytkowników.')
      } finally {
        if (!controller.signal.aborted) setIsSearching(false)
      }
    }, 300)

    return () => {
      window.clearTimeout(timeoutId)
      controller.abort()
    }
  }, [hackathonPublicId, query, selectedCandidate])

  return (
    <>
      <FormField
        id={inputId}
        label="Nazwa użytkownika"
        value={query}
        error={error}
        placeholder="Zacznij wpisywać imię i nazwisko"
        autoComplete="off"
        role="combobox"
        aria-autocomplete="list"
        aria-controls={candidatesId}
        aria-expanded={candidates.length > 0}
        required
        onChange={(event) => onQueryChange(event.target.value)}
      />
      {isSearching && <p role="status">Wyszukiwanie…</p>}
      {searchError && <Alert variant="error">{searchError}</Alert>}
      {candidates.length > 0 && (
        <ul id={candidatesId} className="co-organizer-candidates" role="listbox">
          {candidates.map((candidate) => (
            <li key={candidate.public_id}>
              <button
                type="button"
                role="option"
                aria-selected={selectedCandidate?.public_id === candidate.public_id}
                onClick={() => {
                  onCandidateSelect(candidate)
                  setCandidates([])
                }}
              >
                {candidate.name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </>
  )
}
