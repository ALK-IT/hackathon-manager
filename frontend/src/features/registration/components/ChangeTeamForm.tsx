import { useRef, useState } from 'react'
import { Alert, Button } from '../../../components/ui'
import { ApiError } from '../../../lib/api/client'
import { useTranslation } from '../../../i18n/useTranslation'
import { useHasEnded } from '../../evaluations/utils'
import { changeMyTeam } from '../api/registrationApi'

type Props = {
  hackathonPublicId: string
  startDate: string
  onChanged: () => void
}

export function ChangeTeamForm({ hackathonPublicId, startDate, onChanged }: Props) {
  const { language } = useTranslation()
  const en = language === 'en'
  const hasStarted = useHasEnded(startDate)
  const [open, setOpen] = useState(false)
  const [code, setCode] = useState('')
  const [confirming, setConfirming] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pending = useRef(false)

  async function confirm() {
    if (pending.current || hasStarted) return
    pending.current = true
    setBusy(true)
    setError(null)
    try {
      await changeMyTeam(hackathonPublicId, code.trim().toUpperCase())
      onChanged()
    } catch (cause) {
      const messages: Record<string, string> = {
        TEAM_FULL: en ? 'The team is full.' : 'Ta drużyna jest już pełna.',
        TEAM_NOT_FOUND: en ? 'No team with this code in this hackathon.' : 'Nie ma drużyny z tym kodem w tym hackathonie.',
        TEAM_CHANGE_LOCKED: en ? 'The hackathon has already started.' : 'Hackathon już się rozpoczął. Nie można zmienić drużyny.',
        TEAMS_DISABLED: en ? 'Teams are disabled.' : 'Drużyny są wyłączone.',
        REGISTRATION_NOT_ACCEPTED: en ? 'Your registration must be accepted.' : 'Twoje zgłoszenie musi być zaakceptowane.',
      }
      setError(cause instanceof ApiError && cause.errorCode && messages[cause.errorCode]
        ? messages[cause.errorCode]
        : en ? 'Could not change team. Try again.' : 'Nie udało się zmienić drużyny. Spróbuj ponownie.')
      setConfirming(false)
    } finally {
      pending.current = false
      setBusy(false)
    }
  }

  if (hasStarted) return null
  if (!open) return <Button variant="ghost" onClick={() => setOpen(true)}>{en ? 'Change team' : 'Zmień drużynę'}</Button>

  return <form onSubmit={(event) => { event.preventDefault(); if (!confirming) { setError(null); setConfirming(true) } }}>
    <label>
      {en ? 'New team join code' : 'Kod nowej drużyny'}
      <input value={code} minLength={8} maxLength={8} required disabled={busy || confirming}
        onChange={(event) => setCode(event.target.value.trim().toUpperCase())} />
    </label>
    {error && <Alert variant="error">{error}</Alert>}
    {confirming ? <>
      <p>{en ? `Are you sure you want to move to the team with code ${code}? Your accepted registration will be preserved.` : `Czy na pewno chcesz przejść do drużyny z kodem ${code}? Twoje zaakceptowane zgłoszenie zostanie zachowane.`}</p>
      <Button type="button" variant="ghost" disabled={busy} onClick={() => void confirm()}>{en ? 'Confirm team change' : 'Potwierdź zmianę drużyny'}</Button>
      <Button type="button" variant="ghost" disabled={busy} onClick={() => setConfirming(false)}>{en ? 'Back' : 'Wróć'}</Button>
    </> : <Button type="submit" variant="ghost">{en ? 'Accept' : 'Akceptuj'}</Button>}
    <Button type="button" variant="ghost" disabled={busy} onClick={() => { setOpen(false); setConfirming(false); setError(null) }}>{en ? 'Cancel' : 'Anuluj'}</Button>
  </form>
}
