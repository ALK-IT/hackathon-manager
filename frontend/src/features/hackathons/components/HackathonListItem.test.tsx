import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { Hackathon } from '../types'
import { HackathonListItem } from './HackathonListItem'

const hackathon: Hackathon = {
  id: 1,
  name: 'Test Hackathon',
}

describe('HackathonListItem', () => {
  it('renders the hackathon id and name', () => {
    render(<HackathonListItem hackathon={hackathon} />)

    expect(screen.getByRole('listitem')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '#1 — Test Hackathon' })).toBeInTheDocument()
  })
})
