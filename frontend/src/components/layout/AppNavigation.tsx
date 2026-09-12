import { NavLink } from 'react-router-dom'

export function AppNavigation() {
  return (
    <nav className="app-navigation" aria-label="Główna nawigacja">
      <NavLink to="/hackathons">Hackathony</NavLink>
    </nav>
  )
}
