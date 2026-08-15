import { AuthControls } from '../../auth'
import { HackathonList } from '../components/HackathonList'

export function HackathonsPage() {
  return (
    <main className="app-page">
      <header className="page-header">
        <h1>Hackathony</h1>
        <AuthControls />
      </header>
      <HackathonList />
    </main>
  )
}
