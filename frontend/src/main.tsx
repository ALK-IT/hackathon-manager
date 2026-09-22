import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './app/App'
import { AppProvider } from './app/provider'
import { colorCssVariables } from './components/ui/tokens'

for (const [name, value] of Object.entries(colorCssVariables)) {
  document.documentElement.style.setProperty(name, value)
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppProvider>
      <App />
    </AppProvider>
  </StrictMode>,
)
