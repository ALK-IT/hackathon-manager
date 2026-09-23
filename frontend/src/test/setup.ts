import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

window.localStorage.setItem('hackathon-manager-language', 'pl')

afterEach(() => {
  cleanup()
  window.localStorage.setItem('hackathon-manager-language', 'pl')
})
