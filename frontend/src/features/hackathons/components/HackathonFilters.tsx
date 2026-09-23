import type { HackathonFilters as Filters } from '../types'
import type { Language } from '../../auth'
import { getTranslations } from '../../../i18n/useTranslation'

interface HackathonFiltersProps {
  filters: Filters
  language?: Language
  onChange: (filters: Filters) => void
}

function toFilterValue(value: string): boolean | undefined {
  if (value === 'true') return true
  if (value === 'false') return false
  return undefined
}

export function HackathonFilters({ filters, language = 'pl', onChange }: HackathonFiltersProps) {
  const t = getTranslations(language)
  return (
    <aside className="hackathon-filters" aria-labelledby="hackathon-filters-heading">
      <h2 id="hackathon-filters-heading">{t.filters}</h2>
      <label htmlFor="upcoming-filter">{t.date}</label>
      <select
        id="upcoming-filter"
        value={filters.upcoming === undefined ? '' : String(filters.upcoming)}
        onChange={(event) =>
          onChange({ ...filters, upcoming: toFilterValue(event.target.value) })
        }
      >
        <option value="">{t.all}</option>
        <option value="true">{t.upcoming}</option>
        <option value="false">{t.started}</option>
      </select>

      <label htmlFor="registration-filter">{t.registration}</label>
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
        <option value="">{t.all}</option>
        <option value="true">{t.open}</option>
        <option value="false">{t.closed}</option>
      </select>
    </aside>
  )
}
