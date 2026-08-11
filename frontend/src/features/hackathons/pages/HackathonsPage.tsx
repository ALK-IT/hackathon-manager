import { Link, useNavigate } from 'react-router-dom'
import { Button } from '../../../components/ui'
import { useAuth } from '../../auth'
import { HackathonList } from '../components/HackathonList'

export function HackathonsPage() {
  const { user, isLoading, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/', { replace: true })
  }

  return (
    <main className="app-page">
      <header className="page-header">
        <div>
          <h1>Hackathony</h1>
          {user && <p>Zalogowano jako: {user.email}</p>}
        </div>
        {user ? (
          <Button type="button" variant="ghost" onClick={() => void handleLogout()}>
            Wyloguj się
          </Button>
        ) : (
          !isLoading && <Link to="/login">Zaloguj się</Link>
        )}
      </header>
      <HackathonList />
    </main>
  )
}
