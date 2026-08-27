import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as clipboard from '../utils/clipboard'
import { ResourceSecret } from './ResourceSecret'

describe('ResourceSecret', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('reveals and hides a secret without fetching it twice', async () => {
    const onReveal = vi.fn().mockResolvedValue('sk-secret-value')
    render(<ResourceSecret onReveal={onReveal} />)

    expect(screen.getByLabelText('Wartość zasobu')).toHaveTextContent('••••••••••••••••')
    fireEvent.click(screen.getByRole('button', { name: 'Pokaż' }))

    expect(await screen.findByText('sk-secret-value')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Ukryj' }))
    expect(screen.getByLabelText('Wartość zasobu')).toHaveTextContent('••••••••••••••••')

    fireEvent.click(screen.getByRole('button', { name: 'Pokaż' }))
    expect(await screen.findByText('sk-secret-value')).toBeInTheDocument()
    expect(onReveal).toHaveBeenCalledTimes(1)
  })

  it('reveals and copies a hidden secret', async () => {
    const onReveal = vi.fn().mockResolvedValue('sk-secret-value')
    const copy = vi.spyOn(clipboard, 'copyToClipboard').mockResolvedValue()
    render(<ResourceSecret onReveal={onReveal} />)

    fireEvent.click(screen.getByRole('button', { name: 'Kopiuj' }))

    await waitFor(() => expect(copy).toHaveBeenCalledWith('sk-secret-value'))
    expect(screen.getByRole('status')).toHaveTextContent('Skopiowano klucz.')
    expect(screen.getByLabelText('Wartość zasobu')).toHaveTextContent('••••••••••••••••')
  })

  it('keeps the value visible when clipboard copying fails', async () => {
    vi.spyOn(clipboard, 'copyToClipboard').mockRejectedValue(new Error('Clipboard denied'))
    render(<ResourceSecret onReveal={vi.fn().mockResolvedValue('manual-secret')} />)

    fireEvent.click(screen.getByRole('button', { name: 'Kopiuj' }))

    expect(await screen.findByText('manual-secret')).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Skopiuj widoczny klucz ręcznie')
  })
})
