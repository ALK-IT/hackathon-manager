import { useState } from 'react'
import { Alert, Button } from '../../../components/ui'
import { copyToClipboard } from '../utils/clipboard'
import { getRevealErrorMessage } from '../utils/resourceMessages'

interface ResourceSecretProps {
  onReveal: () => Promise<string>
}

const MASKED_VALUE = '••••••••••••••••'

export function ResourceSecret({ onReveal }: ResourceSecretProps) {
  const [value, setValue] = useState<string | null>(null)
  const [isVisible, setIsVisible] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copyMessage, setCopyMessage] = useState<string | null>(null)

  async function getValue() {
    if (value !== null) return value

    setIsLoading(true)
    setError(null)
    try {
      const revealedValue = await onReveal()
      setValue(revealedValue)
      return revealedValue
    } catch (revealError) {
      setError(getRevealErrorMessage(revealError))
      return null
    } finally {
      setIsLoading(false)
    }
  }

  async function handleVisibility() {
    setCopyMessage(null)
    if (isVisible) {
      setIsVisible(false)
      return
    }

    const revealedValue = await getValue()
    if (revealedValue !== null) setIsVisible(true)
  }

  async function handleCopy() {
    setCopyMessage(null)
    const revealedValue = await getValue()
    if (revealedValue === null) return

    try {
      await copyToClipboard(revealedValue)
      setCopyMessage('Skopiowano klucz.')
    } catch {
      setIsVisible(true)
      setCopyMessage('Nie udało się skopiować. Skopiuj widoczny klucz ręcznie.')
    }
  }

  return (
    <div className="resource-secret">
      <div className="resource-secret-row">
        <code className="resource-secret-value" aria-label="Wartość zasobu">
          {isVisible && value !== null ? value : MASKED_VALUE}
        </code>
        <div className="resource-secret-actions">
          <Button
            type="button"
            variant="ghost"
            disabled={isLoading}
            onClick={() => void handleCopy()}
          >
            Kopiuj
          </Button>
          <Button
            type="button"
            variant="ghost"
            disabled={isLoading}
            onClick={() => void handleVisibility()}
          >
            {isLoading ? 'Pobieranie…' : isVisible ? 'Ukryj' : 'Pokaż'}
          </Button>
        </div>
      </div>
      {error && <Alert variant="error">{error}</Alert>}
      {copyMessage && <p role="status">{copyMessage}</p>}
    </div>
  )
}
