import { useNavigate } from 'react-router-dom'
import { Button } from '../../../components/ui'
import { useAuth } from '../../auth'
import { HackathonList } from '../components/HackathonList'

export function HackathonsPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <main className="app-page">
      <header className="page-header">
        <div>
          <h1>Hackathony</h1>
          <p>Zalogowano jako: {user?.email}</p>
        </div>
        <Button type="button" variant="ghost" onClick={() => void handleLogout()}>
          Wyloguj się
        </Button>
      </header>
      <HackathonList />
    </main>
  )
}
