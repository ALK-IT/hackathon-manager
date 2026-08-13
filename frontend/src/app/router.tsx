import { Navigate, Route, Routes } from 'react-router-dom'
import { LoginPage, RegisterPage } from '../features/auth'
import {
  CreateHackathonPage,
  HackathonDetailsPage,
  HackathonsPage,
} from '../features/hackathons'
import { RegistrationEntryPage } from '../features/registration'
import { AdminRoute } from './routes/AdminRoute'
import { ProtectedRoute } from './routes/ProtectedRoute'
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
      <Route path="/hackathons" element={<HackathonsPage />} />
      <Route
        path="/hackathons/create"
        element={
          <ProtectedRoute>
            <AdminRoute>
              <CreateHackathonPage />
            </AdminRoute>
          </ProtectedRoute>
        }
      />
      <Route path="/hackathons/:hackathonPublicId" element={<HackathonDetailsPage />} />
      <Route
        path="/hackathons/:hackathonPublicId/register"
        element={
          <ProtectedRoute>
            <RegistrationEntryPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
