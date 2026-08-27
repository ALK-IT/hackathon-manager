import { NavLink } from 'react-router-dom'
import { useAuth } from '../../features/auth'

export function AppNavigation() {
  const { user } = useAuth()

  return (
    <nav className="app-navigation" aria-label="Główna nawigacja">
      <NavLink to="/hackathons">Hackathony</NavLink>
      {user && <NavLink to="/my-resources">Moje zasoby</NavLink>}
    </nav>
  )
}
