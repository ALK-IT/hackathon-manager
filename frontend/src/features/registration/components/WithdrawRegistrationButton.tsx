import { useState } from 'react'
import { Alert, Button } from '../../../components/ui'
import { getWithdrawRegistrationErrorMessage } from '../utils/registrationMessages'

interface WithdrawRegistrationButtonProps {
  onWithdraw: () => Promise<void>
}

export function WithdrawRegistrationButton({
  onWithdraw,
}: WithdrawRegistrationButtonProps) {
  const [isWithdrawing, setIsWithdrawing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleWithdraw() {
    if (!window.confirm('Czy na pewno chcesz się wycofać?')) return

    setError(null)
    setIsWithdrawing(true)
    try {
      await onWithdraw()
    } catch (requestError) {
      setError(getWithdrawRegistrationErrorMessage(requestError))
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
        {isWithdrawing ? 'Wycofywanie…' : 'Wycofaj zgłoszenie'}
      </Button>
    </div>
  )
}
