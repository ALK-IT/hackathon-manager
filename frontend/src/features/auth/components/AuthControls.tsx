import { Link, useNavigate } from 'react-router-dom'
import { Button } from '../../../components/ui'
import { useAuth } from '../hooks/useAuth'

export function AuthControls() {
  const { user, isLoading, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/', { replace: true })
  }

  if (isLoading) return null
  if (!user) return <Link to="/login">Zaloguj się</Link>

  return (
    <div>
      <p>Zalogowano jako: {user.email}</p>
      <Button type="button" variant="ghost" onClick={() => void handleLogout()}>
        Wyloguj się
      </Button>
    </div>
  )
}
