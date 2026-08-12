import type { HackathonFilters as Filters } from '../types'

interface HackathonFiltersProps {
  filters: Filters
  onChange: (filters: Filters) => void
}

function toFilterValue(value: string): boolean | undefined {
  if (value === 'true') return true
  if (value === 'false') return false
  return undefined
}

export function HackathonFilters({ filters, onChange }: HackathonFiltersProps) {
  return (
    <aside className="hackathon-filters" aria-labelledby="hackathon-filters-heading">
      <h2 id="hackathon-filters-heading">Filtry</h2>
      <label htmlFor="upcoming-filter">Termin</label>
      <select
        id="upcoming-filter"
        value={filters.upcoming === undefined ? '' : String(filters.upcoming)}
        onChange={(event) =>
          onChange({ ...filters, upcoming: toFilterValue(event.target.value) })
        }
      >
        <option value="">Wszystkie</option>
        <option value="true">Nadchodzące</option>
        <option value="false">Rozpoczęte</option>
      </select>

      <label htmlFor="registration-filter">Rejestracja</label>
      <select
        id="registration-filter"
        value={
          filters.registrationOpen === undefined ? '' : String(filters.registrationOpen)
        }
        onChange={(event) =>
          onChange({
            ...filters,
            registrationOpen: toFilterValue(event.target.value),
          })
        }
      >
        <option value="">Wszystkie</option>
        <option value="true">Otwarta</option>
        <option value="false">Zamknięta</option>
      </select>
    </aside>
  )
}
