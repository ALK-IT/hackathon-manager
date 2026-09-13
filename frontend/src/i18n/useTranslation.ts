import { useContext, useSyncExternalStore } from 'react'
import { AuthContext } from '../features/auth/context/AuthContext'
import type { Language } from '../features/auth'

export const LANGUAGE_STORAGE_KEY = 'hackathon-manager-language'
const LANGUAGE_CHANGE_EVENT = 'hackathon-manager-language-change'

export function getStoredLanguage(): Language {
  if (typeof window === 'undefined') return 'en'
  return window.localStorage.getItem(LANGUAGE_STORAGE_KEY) === 'pl' ? 'pl' : 'en'
}

export function setStoredLanguage(language: Language): void {
  window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language)
  document.documentElement.lang = language
  window.dispatchEvent(new Event(LANGUAGE_CHANGE_EVENT))
}

function subscribeToStoredLanguage(callback: () => void): () => void {
  window.addEventListener(LANGUAGE_CHANGE_EVENT, callback)
  window.addEventListener('storage', callback)
  return () => {
    window.removeEventListener(LANGUAGE_CHANGE_EVENT, callback)
    window.removeEventListener('storage', callback)
  }
}

const translations = {
  pl: {
    hackathons: 'Hackathony',
    loggedInAs: 'Zalogowano jako',
    role: 'Rola',
    profile: 'Mój profil',
    createHackathon: 'Utwórz hackathon',
    logout: 'Wyloguj się',
    login: 'Zaloguj się',
    filters: 'Filtry',
    date: 'Termin',
    all: 'Wszystkie',
    upcoming: 'Nadchodzące',
    started: 'Rozpoczęte',
    registration: 'Rejestracja',
    open: 'Otwarta',
    closed: 'Zamknięta',
    list: 'Lista hackathonów',
    loadingHackathons: 'Ładowanie hackathonów…',
    loadHackathonsError: 'Nie udało się pobrać hackathonów. Spróbuj ponownie.',
    retry: 'Spróbuj ponownie',
    noHackathons: 'Brak hackathonów do wyświetlenia.',
    previousPage: 'Poprzednia strona',
    nextPage: 'Następna strona',
    page: 'Strona',
    registrationLabel: 'Rejestracja',
    registrationOpen: 'otwarta',
    registrationClosed: 'zamknięta',
    applicationStatus: 'Status zgłoszenia',
    pending: 'oczekujące',
    accepted: 'zaakceptowane',
    rejected: 'odrzucone',
    profilePending: 'Oczekuje',
    profileAccepted: 'Przyjęty',
    profileRejected: 'Odrzucony',
    enterHackathon: 'Przejdź do hackathonu',
    register: 'Zarejestruj się',
    applications: 'Zgłoszenia',
    settings: 'Ustawienia',
    backToProfile: '← Wróć do profilu',
    backToHackathons: '← Wszystkie hackathony',
    yourProfile: 'Twój profil',
    participant: 'Uczestnik',
    administrator: 'Administrator',
    memberSince: 'W serwisie od',
    yourEvents: 'Twoje wydarzenia',
    appliedHackathons: 'Hackathony, na które aplikujesz',
    loadingProfile: 'Pobieramy hackathony…',
    profileLoadError: 'Nie udało się pobrać Twoich hackathonów.',
    noEvents: 'Jeszcze nie ma tu żadnych wydarzeń',
    noEventsDescription: 'Gdy wyślesz pierwsze zgłoszenie, hackathon pojawi się w tym miejscu.',
    findHackathon: 'Znajdź hackathon',
    eventDetailsFallback: 'Szczegóły wydarzenia znajdziesz na stronie hackathonu.',
    team: 'Zespół',
    accountSettings: 'Ustawienia konta',
    username: 'Username',
    language: 'Język',
    polish: 'Polski',
    english: 'English',
    saveSettings: 'Zapisz ustawienia',
    saving: 'Zapisywanie…',
    settingsSaved: 'Ustawienia zostały zapisane.',
    settingsError: 'Nie udało się zapisać ustawień.',
    password: 'Hasło',
    passwordDescription: 'Wyślemy bezpieczny link do zmiany hasła na adres Twojego konta.',
    sendPasswordLink: 'Wyślij link do zmiany hasła',
    sending: 'Wysyłanie…',
    passwordLinkSent: 'Link do zmiany hasła został wysłany na Twój e-mail.',
    passwordLinkError: 'Nie udało się wysłać linku do zmiany hasła.',
    email: 'E-mail', name: 'Nazwa', description: 'Opis', cancel: 'Anuluj', now: 'Teraz',
    signInTitle: 'Logowanie', noAccount: 'Nie masz konta?', signUp: 'Zarejestruj się',
    signingIn: 'Logowanie…', forgotPassword: 'Nie pamiętasz hasła?', resendActivation: 'Wyślij ponownie link aktywacyjny',
    accountCreated: 'Konto zostało utworzone. Sprawdź e-mail i potwierdź konto.',
    registrationTitle: 'Rejestracja', haveAccount: 'Masz już konto?', confirmPassword: 'Powtórz hasło', creatingAccount: 'Tworzenie konta…', createAccount: 'Utwórz konto',
    resetPassword: 'Reset hasła', rememberPassword: 'Pamiętasz hasło?', genericEmailSent: 'Jeśli konto istnieje, wysłaliśmy link do zmiany hasła.', sendLink: 'Wyślij link',
    setNewPassword: 'Ustaw nowe hasło', passwordChangedQuestion: 'Hasło zostało zmienione?', newPassword: 'Nowe hasło', repeatNewPassword: 'Powtórz nowe hasło', changePassword: 'Zmień hasło', passwordChanged: 'Hasło zostało zmienione. Możesz się zalogować.', requestNewLink: 'Poproś o nowy link',
    verifyAccount: 'Potwierdzenie konta', verifiedAccountQuestion: 'Masz już potwierdzone konto?', verifyingAccount: 'Potwierdzanie konta…', accountVerified: 'Konto zostało potwierdzone.', goToLogin: 'Przejdź do logowania', sendNewLink: 'Wyślij nowy link',
    invalidEmail: 'Podaj poprawny adres e-mail.', enterPassword: 'Podaj hasło.', shortUsername: 'Nazwa musi mieć co najmniej 3 znaki.', shortPassword: 'Hasło musi mieć co najmniej 8 znaków.', passwordsDiffer: 'Hasła muszą być takie same.',
    hackathonSettings: 'Ustawienia hackathonu', loadingSettings: 'Ładowanie ustawień…', startHackathon: 'Rozpoczęcie hackathonu', endHackathon: 'Zakończenie hackathonu', registrationOpens: 'Otwarcie zapisów', registrationCloses: 'Zamknięcie zapisów', optional: 'opcjonalne', participantLimit: 'Limit uczestników', maxTeamSize: 'Maksymalna wielkość drużyny', saveHackathonSettings: 'Zapisz ustawienia', creating: 'Tworzenie…',
    backToList: 'Wróć do listy hackathonów', loadingDetails: 'Ładowanie szczegółów hackathonu…', term: 'Termin', organizer: 'Organizator', participantLimitLabel: 'Limit uczestników', coOrganizers: 'Współorganizatorzy', noCoOrganizers: 'Brak współorganizatorów.', addCoOrganizer: 'Dodaj współorganizatora', adding: 'Dodawanie…', userName: 'Nazwa użytkownika', userSearchPlaceholder: 'Zacznij wpisywać username', searching: 'Wyszukiwanie…',
    tasks: 'Zadania', loadingTasks: 'Ładowanie zadań…', noTasks: 'Nie dodano jeszcze zadań.', visibleFrom: 'Widoczne od', taskName: 'Nazwa zadania', taskDescription: 'Opis zadania', visibleToParticipantsFrom: 'Widoczne dla uczestników od', hackathonStart: 'Start hackathonu', addTask: 'Dodaj zadanie',
    loadingApplications: 'Ładowanie zgłoszeń…', noApplications: 'Brak zgłoszeń.', viewApplication: 'Obejrzyj zgłoszenie', applicationsPagination: 'Stronicowanie zgłoszeń', status: 'Status', answers: 'Odpowiedzi', noAnswers: 'Brak odpowiedzi.', accept: 'Akceptuj', reject: 'Odrzuć',
    participantArea: 'Strefa uczestnika', loadingParticipantArea: 'Ładowanie strefy uczestnika…', members: 'Członkowie', noTeam: 'Nie należysz do żadnej drużyny.', noPublishedTasks: 'Nie opublikowano jeszcze żadnych zadań.', solution: 'Rozwiązanie', githubSolutionLink: 'Link do rozwiązania na GitHubie', updateLink: 'Zaktualizuj link', submitLink: 'Wyślij link', submissionsClosed: 'Termin wysyłania rozwiązań minął.', solutionSaved: 'Rozwiązanie zostało zapisane.',
    hackathonRegistration: 'Rejestracja na hackathon', loadingForm: 'Ładowanie formularza…', existingApplication: 'Masz już zgłoszenie do tego hackathonu.', applicationSent: 'Zgłoszenie zostało wysłane.', joinCode: 'Kod dołączenia', enterHackathonButton: 'Wejdź do hackathonu', questions: 'Pytania', noExtraQuestions: 'Ten hackathon nie zawiera dodatkowych pytań.', noTeamOption: 'Bez drużyny', createTeam: 'Utwórz drużynę', joinTeam: 'Dołącz do drużyny', teamName: 'Nazwa drużyny', teamCode: 'Kod drużyny', submitApplication: 'Wyślij zgłoszenie',
    registrationQuestions: 'Pytania rejestracyjne', question: 'Pytanie', required: 'Wymagane', removeQuestion: 'Usuń pytanie', addQuestion: 'Dodaj pytanie', maxQuestions: 'Możesz dodać maksymalnie 50 pytań.', saveQuestions: 'Zapisz pytania',
    skip: 'Pomiń', completeEveryQuestion: 'Uzupełnij treść każdego pytania.',
    checkingSession: 'Sprawdzanie sesji…', profileNavigation: 'Nawigacja profilu',
    changeLanguage: 'Zmień język',
  },
  en: {
    hackathons: 'Hackathons',
    loggedInAs: 'Signed in as',
    role: 'Role',
    profile: 'My profile',
    createHackathon: 'Create hackathon',
    logout: 'Sign out',
    login: 'Sign in',
    filters: 'Filters',
    date: 'Date',
    all: 'All',
    upcoming: 'Upcoming',
    started: 'Started',
    registration: 'Registration',
    open: 'Open',
    closed: 'Closed',
    list: 'Hackathon list',
    loadingHackathons: 'Loading hackathons…',
    loadHackathonsError: 'Could not load hackathons. Try again.',
    retry: 'Try again',
    noHackathons: 'No hackathons to display.',
    previousPage: 'Previous page',
    nextPage: 'Next page',
    page: 'Page',
    registrationLabel: 'Registration',
    registrationOpen: 'open',
    registrationClosed: 'closed',
    applicationStatus: 'Application status',
    pending: 'pending',
    accepted: 'accepted',
    rejected: 'rejected',
    profilePending: 'Pending',
    profileAccepted: 'Accepted',
    profileRejected: 'Rejected',
    enterHackathon: 'Enter hackathon',
    register: 'Register',
    applications: 'Applications',
    settings: 'Settings',
    backToProfile: '← Back to profile',
    backToHackathons: '← All hackathons',
    yourProfile: 'Your profile',
    participant: 'Participant',
    administrator: 'Administrator',
    memberSince: 'Member since',
    yourEvents: 'Your events',
    appliedHackathons: 'Hackathons you applied to',
    loadingProfile: 'Loading hackathons…',
    profileLoadError: 'Could not load your hackathons.',
    noEvents: 'No events here yet',
    noEventsDescription: 'Your first hackathon will appear here after you apply.',
    findHackathon: 'Find a hackathon',
    eventDetailsFallback: 'See the hackathon page for event details.',
    team: 'Team',
    accountSettings: 'Account settings',
    username: 'Username',
    language: 'Language',
    polish: 'Polski',
    english: 'English',
    saveSettings: 'Save settings',
    saving: 'Saving…',
    settingsSaved: 'Settings have been saved.',
    settingsError: 'Could not save settings.',
    password: 'Password',
    passwordDescription: 'We will send a secure password-change link to your account email.',
    sendPasswordLink: 'Send password-change link',
    sending: 'Sending…',
    passwordLinkSent: 'A password-change link has been sent to your email.',
    passwordLinkError: 'Could not send the password-change link.',
    email: 'Email', name: 'Name', description: 'Description', cancel: 'Cancel', now: 'Now',
    signInTitle: 'Sign in', noAccount: "Don't have an account?", signUp: 'Sign up', signingIn: 'Signing in…', forgotPassword: 'Forgot your password?', resendActivation: 'Resend activation link', accountCreated: 'Your account was created. Check your email and verify it.',
    registrationTitle: 'Sign up', haveAccount: 'Already have an account?', confirmPassword: 'Confirm password', creatingAccount: 'Creating account…', createAccount: 'Create account',
    resetPassword: 'Reset password', rememberPassword: 'Remember your password?', genericEmailSent: 'If the account exists, we sent a password-change link.', sendLink: 'Send link',
    setNewPassword: 'Set a new password', passwordChangedQuestion: 'Password changed?', newPassword: 'New password', repeatNewPassword: 'Repeat new password', changePassword: 'Change password', passwordChanged: 'Your password has been changed. You can sign in.', requestNewLink: 'Request a new link',
    verifyAccount: 'Verify account', verifiedAccountQuestion: 'Already verified your account?', verifyingAccount: 'Verifying account…', accountVerified: 'Your account has been verified.', goToLogin: 'Go to sign in', sendNewLink: 'Send a new link',
    invalidEmail: 'Enter a valid email address.', enterPassword: 'Enter your password.', shortUsername: 'Username must be at least 3 characters.', shortPassword: 'Password must be at least 8 characters.', passwordsDiffer: 'Passwords must match.',
    hackathonSettings: 'Hackathon settings', loadingSettings: 'Loading settings…', startHackathon: 'Hackathon start', endHackathon: 'Hackathon end', registrationOpens: 'Registration opens', registrationCloses: 'Registration closes', optional: 'optional', participantLimit: 'Participant limit', maxTeamSize: 'Maximum team size', saveHackathonSettings: 'Save settings', creating: 'Creating…',
    backToList: 'Back to hackathon list', loadingDetails: 'Loading hackathon details…', term: 'Date', organizer: 'Organizer', participantLimitLabel: 'Participant limit', coOrganizers: 'Co-organizers', noCoOrganizers: 'No co-organizers.', addCoOrganizer: 'Add co-organizer', adding: 'Adding…', userName: 'Username', userSearchPlaceholder: 'Start typing a username', searching: 'Searching…',
    tasks: 'Tasks', loadingTasks: 'Loading tasks…', noTasks: 'No tasks have been added yet.', visibleFrom: 'Visible from', taskName: 'Task name', taskDescription: 'Task description', visibleToParticipantsFrom: 'Visible to participants from', hackathonStart: 'Hackathon start', addTask: 'Add task',
    loadingApplications: 'Loading applications…', noApplications: 'No applications.', viewApplication: 'View application', applicationsPagination: 'Application pagination', status: 'Status', answers: 'Answers', noAnswers: 'No answers.', accept: 'Accept', reject: 'Reject',
    participantArea: 'Participant area', loadingParticipantArea: 'Loading participant area…', members: 'Members', noTeam: 'You are not on a team.', noPublishedTasks: 'No tasks have been published yet.', solution: 'Solution', githubSolutionLink: 'GitHub solution link', updateLink: 'Update link', submitLink: 'Submit link', submissionsClosed: 'The solution submission deadline has passed.', solutionSaved: 'Solution saved.',
    hackathonRegistration: 'Hackathon registration', loadingForm: 'Loading form…', existingApplication: 'You already applied to this hackathon.', applicationSent: 'Your application has been submitted.', joinCode: 'Join code', enterHackathonButton: 'Enter hackathon', questions: 'Questions', noExtraQuestions: 'This hackathon has no additional questions.', noTeamOption: 'No team', createTeam: 'Create a team', joinTeam: 'Join a team', teamName: 'Team name', teamCode: 'Team code', submitApplication: 'Submit application',
    registrationQuestions: 'Registration questions', question: 'Question', required: 'Required', removeQuestion: 'Remove question', addQuestion: 'Add question', maxQuestions: 'You can add up to 50 questions.', saveQuestions: 'Save questions',
    skip: 'Skip', completeEveryQuestion: 'Complete every question.',
    checkingSession: 'Checking session…', profileNavigation: 'Profile navigation',
    changeLanguage: 'Change language',
  },
} as const

export function useTranslation() {
  const auth = useContext(AuthContext)
  const storedLanguage = useSyncExternalStore<Language>(
    subscribeToStoredLanguage,
    getStoredLanguage,
    () => 'en',
  )
  const language = auth?.user?.language ?? storedLanguage
  return { language, t: translations[language] }
}

export function getTranslations(language: Language = 'en') {
  return translations[language]
}
