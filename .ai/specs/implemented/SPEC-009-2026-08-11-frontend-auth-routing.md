# SPEC-009: Frontend uwierzytelniania i routing

**Status:** Zaimplementowany
**Data:** 2026-08-11
**Autorzy:** Patryk Nisgorski, Codex

## Kontekst / Problem

Frontend nie miał klienta API obsługującego sesję użytkownika, formularzy logowania i rejestracji ani routingu rozróżniającego strony publiczne i chronione. Lista hackathonów była połączona bezpośrednio z głównym komponentem aplikacji i nie zapewniała spójnej obsługi sesji.

Potrzebna jest funkcjonalna, testowalna warstwa frontendu korzystająca z backendowego auth opisanego w `SPEC-003`. Zakres obejmuje prosty układ stron; docelowy design zostanie przygotowany osobno.

## Proponowane rozwiązanie

- Organizacja kodu według odpowiedzialności:
  - `app/` — provider aplikacji, router i zabezpieczenia tras,
  - `components/ui/` — współdzielone podstawowe komponenty,
  - `features/auth/` — API, komponenty, kontekst, hook, strony, typy i walidacja auth,
  - `features/hackathons/` — API, komponenty, strona i typy hackathonów,
  - `lib/api/` — wspólny klient HTTP i typy odpowiedzi,
  - `config/` — konfiguracja bazowego URL API,
  - `test/` — wspólna konfiguracja testów.
- Klient API oparty na `fetch`, który:
  - korzysta z `VITE_API_URL`, domyślnie `http://localhost:8000`,
  - dołącza access token jako `Authorization: Bearer`,
  - wysyła cookie przez `credentials: "include"`,
  - parsuje odpowiedzi JSON i `error_code`,
  - po `401` wykonuje jedną próbę odświeżenia sesji i ponawia pierwotne żądanie,
  - współdzieli jedno trwające żądanie refresh między równoległymi żądaniami.
- Access token jest przechowywany wyłącznie w pamięci aplikacji. Refresh token pozostaje w cookie `HttpOnly` zarządzanym przez backend i nie jest dostępny dla JavaScript.
- `AuthProvider` odtwarza sesję przy starcie aplikacji przez `/api/auth/refresh` oraz `/api/auth/me`, a hook `useAuth` udostępnia użytkownika, stan ładowania i operacje `login`, `register`, `logout`.
- Routing przez `react-router-dom` obejmuje publiczne `/login` i `/register`, chronione `/hackathons` oraz przekierowania z `/` i nieznanych ścieżek.
- Formularze logowania i rejestracji mają walidację klienta, stan wysyłania oraz mapowanie błędów API na komunikaty.
- Lista hackathonów używa osobnego `HackathonListItem` i zachowuje kontrakt API z `main`: `id` oraz `name`.
- Interfejs wykorzystuje proste komponenty `Alert`, `Button`, `Card` i `Spinner`, bez tworzenia docelowego designu.

## Kontrakt z backendem

- `POST /api/auth/register` — tworzy użytkownika.
- `POST /api/auth/login` — zwraca access token i ustawia refresh cookie `HttpOnly`.
- `POST /api/auth/refresh` — odczytuje i obraca refresh cookie oraz zwraca nowy access token.
- `POST /api/auth/logout` — kończy sesję i usuwa refresh cookie.
- `GET /api/auth/me` — zwraca bieżącego użytkownika dla access tokena.
- `GET /api/hackathons` — zwraca listę obiektów z polami `id` i `name`.

Frontend nie odczytuje refresh tokena i nie zapisuje tokenów w `localStorage` ani `sessionStorage`.

## Zakres

**W zakresie:**

- Klient API z obsługą Bearer tokena, `error_code`, refresh i pojedynczego retry.
- Typy TypeScript dla użytkownika, hackathonu, formularzy, tokena i błędów API.
- Kontekst uwierzytelniania, `AuthProvider` i hook `useAuth`.
- Odtwarzanie sesji z refresh cookie po przeładowaniu strony.
- Formularze logowania i rejestracji z walidacją klienta.
- Routing i zabezpieczenia tras.
- Podział listy hackathonów na stronę, listę i pojedynczy element.
- Stany ładowania, pustej listy i błędu z możliwością ponowienia.
- Testy klienta API, auth, routingu i listy hackathonów.
- Node 20 oraz zależności zgodne z tą wersją środowiska.
- Lokalny development w Docker Compose z bind mountem źródeł i osobnym volume dla `node_modules`, odseparowany od konfiguracji CI.

**Poza zakresem:**

- Docelowy projekt graficzny i rozbudowa design systemu.
- Formularz zgłoszenia uczestnika i pytania rekrutacyjne.
- Widoki organizatora do zarządzania zgłoszeniami.
- Logowanie przez zewnętrznych dostawców.
- Reset hasła, weryfikacja e-maila i zarządzanie profilem.
- Przechowywanie tokenów w Web Storage.

## Wpływ

- **Frontend:** nowa struktura feature-based, wspólny klient API, centralny stan auth i routing aplikacji.
- **Backend:** brak zmian logiki biznesowej; frontend korzysta z istniejących endpointów i cookie `HttpOnly`.
- **Baza danych:** brak zmian.
- **API:** żądania przeglądarki wysyłają credentials, a chronione żądania używają access tokena Bearer.
- **Docker/CI:** lokalny override udostępnia hot reload i named volume, natomiast CI buduje obraz bez montowania katalogu roboczego runnera.

## Kryteria akceptacji

- Użytkownik może utworzyć konto i przejść do logowania.
- Użytkownik może się zalogować i przejść do `/hackathons`.
- Niepoprawne dane formularzy są odrzucane przed wysłaniem żądania.
- Błędy backendu z `error_code` są mapowane na komunikaty.
- Niezalogowany użytkownik nie może otworzyć `/hackathons`.
- Zalogowany użytkownik nie może otworzyć `/login` ani `/register`.
- Po przeładowaniu strony sesja jest odtwarzana z refresh cookie bez użycia Web Storage.
- Po `401` klient wykonuje najwyżej jeden refresh i jeden retry pierwotnego żądania.
- Wylogowanie czyści access token w pamięci również przy błędzie sieciowym.
- Lista hackathonów pokazuje ładowanie, pustą listę, błąd z ponowieniem albo dane z API.
- `npm ci` działa bez `sudo` i bez plików `node_modules` należących do roota.
- `npm test`, `npm run lint` i `npm run build` przechodzą na Node 20.

## Alternatywy rozważane

- **Tokeny w `localStorage`** — odrzucone ze względu na możliwość odczytania przez kod uruchomiony w wyniku XSS.
- **Refresh token dostępny dla JavaScript** — odrzucony; wybrano cookie `HttpOnly`.
- **Stan auth w komponentach stron** — odrzucony ze względu na duplikację logiki sesji.
- **Zewnętrzna biblioteka stanu** — odrzucona; React Context wystarcza dla tego zakresu.
- **Bind mount frontendu w bazowym Compose używanym przez CI** — odrzucony, ponieważ Docker może utworzyć hostowy `node_modules` z właścicielem `root`.
- **Docelowy design w tej zmianie** — odłożony; obecne komponenty zapewniają tylko podstawowy układ i stany.

## Changelog

- 2026-08-11 — utworzono spec po implementacji klienta API, auth providera, formularzy, routingu, listy hackathonów i testów.
- 2026-08-11 — zachowano Node 20, przypięto kompatybilne zależności oraz rozdzielono Compose lokalny od CI.
