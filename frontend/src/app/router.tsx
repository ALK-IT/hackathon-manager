import { Navigate, Route, Routes } from 'react-router-dom'
import {
  ForgotPasswordPage,
  LoginPage,
  RegisterPage,
  ResetPasswordPage,
  VerifyEmailPage,
} from '../features/auth'
import {
  CreateHackathonPage,
  EditHackathonPage,
  HackathonDetailsPage,
  HackathonsPage,
} from '../features/hackathons'
import {
  ParticipantAreaPage,
  RegistrationEntryPage,
  RegistrationQuestionsSetupPage,
} from '../features/registration'
import { ManageRegistrationsPage } from '../features/registration/pages/ManageRegistrationsPage'
import { AdminRoute } from './routes/AdminRoute'
import { ProtectedRoute } from './routes/ProtectedRoute'
import { PublicOnlyRoute } from './routes/PublicOnlyRoute'

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/hackathons" replace />} />
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
      <Route
        path="/forgot-password"
        element={
          <PublicOnlyRoute>
            <ForgotPasswordPage />
          </PublicOnlyRoute>
        }
      />
      <Route path="/verify-email" element={<VerifyEmailPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
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
        path="/hackathons/:hackathonPublicId/settings"
        element={
          <ProtectedRoute>
            <EditHackathonPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/hackathons/:hackathonPublicId/questions/setup"
        element={
          <ProtectedRoute>
            <AdminRoute>
              <RegistrationQuestionsSetupPage />
            </AdminRoute>
          </ProtectedRoute>
        }
      />
      <Route
        path="/hackathons/:hackathonPublicId/register"
        element={
          <ProtectedRoute>
            <RegistrationEntryPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/hackathons/:hackathonPublicId/registrations"
        element={
          <ProtectedRoute>
            <ManageRegistrationsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/hackathons/:hackathonPublicId/participant-area"
        element={
          <ProtectedRoute>
            <ParticipantAreaPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/hackathons" replace />} />
    </Routes>
  )
}
