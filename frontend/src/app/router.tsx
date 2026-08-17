import { Navigate, Route, Routes } from 'react-router-dom'
import { LoginPage, RegisterPage } from '../features/auth'
import { HackathonsPage } from '../features/hackathons'
import { PublicOnlyRoute } from './routes/PublicOnlyRoute'

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<HackathonsPage />} />
      <Route
        path="/login"
        element={
          <PublicOnlyRoute>
            <LoginPage />
          </PublicOnlyRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicOnlyRoute>
            <RegisterPage />
          </PublicOnlyRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
