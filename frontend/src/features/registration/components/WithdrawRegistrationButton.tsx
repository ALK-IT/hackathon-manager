import { useState } from 'react'
import { Alert, Button } from '../../../components/ui'
import { getWithdrawRegistrationErrorMessage } from '../utils/registrationMessages'
import type { Language } from '../../auth'

interface WithdrawRegistrationButtonProps {
  onWithdraw: () => Promise<void>
  language?: Language
}

export function WithdrawRegistrationButton({
  onWithdraw,
  language = 'pl',
}: WithdrawRegistrationButtonProps) {
  const [isWithdrawing, setIsWithdrawing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleWithdraw() {
    if (!window.confirm(language === 'en' ? 'Are you sure you want to withdraw?' : 'Czy na pewno chcesz się wycofać?')) return

    setError(null)
    setIsWithdrawing(true)
    try {
      await onWithdraw()
    } catch (requestError) {
      setError(getWithdrawRegistrationErrorMessage(requestError, language))
    } finally {
      setIsWithdrawing(false)
    }
  }

  return (
    <div className="withdraw-registration-action">
      {error && <Alert variant="error">{error}</Alert>}
      <Button
        type="button"
        variant="danger"
        disabled={isWithdrawing}
        onClick={() => void handleWithdraw()}
      >
        {isWithdrawing
          ? (language === 'en' ? 'Withdrawing…' : 'Wycofywanie…')
          : (language === 'en' ? 'Withdraw application' : 'Wycofaj zgłoszenie')}
      </Button>
    </div>
  )
}
