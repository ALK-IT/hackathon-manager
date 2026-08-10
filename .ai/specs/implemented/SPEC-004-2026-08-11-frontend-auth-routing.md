# SPEC-004: Frontend uwierzytelniania i routing

**Status:** Zaimplementowany
**Data:** 2026-08-11
**Autorzy:** Patryk Nisgorski, Codex

## Kontekst / Problem

Frontend nie miał klienta API obsługującego sesję użytkownika, formularzy logowania i rejestracji ani routingu rozróżniającego strony publiczne i chronione. Lista hackathonów była połączona bezpośrednio z głównym komponentem aplikacji i nie zapewniała spójnej obsługi ładowania, błędów oraz ponowienia żądania.

Potrzebna jest funkcjonalna, testowalna warstwa frontendu korzystająca z backendowego auth opisanego w `SPEC-003`. Zakres obejmuje jedynie prosty układ stron; docelowy design zostanie przygotowany osobno.

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
  - bezpiecznie parsuje odpowiedzi JSON i `error_code`,
  - po `401` wykonuje jedną próbę odświeżenia sesji i ponawia pierwotne żądanie,
  - współdzieli jedno trwające żądanie refresh między równoległymi żądaniami.
- Access token jest przechowywany wyłącznie w pamięci aplikacji. Refresh token pozostaje w cookie `HttpOnly` zarządzanym przez backend i nie jest dostępny dla JavaScript.
- `AuthProvider` odtwarza sesję przy starcie aplikacji przez `/api/auth/refresh` oraz `/api/auth/me`, a hook `useAuth` udostępnia użytkownika, stan ładowania i operacje `login`, `register`, `logout`.
- Routing przez `react-router-dom`:
  - `/login` i `/register` — dostępne tylko dla niezalogowanych,
  - `/hackathons` — trasa chroniona,
  - `/` i nieznane ścieżki — przekierowanie do właściwego przepływu.
- Formularze logowania i rejestracji mają walidację klienta, stan wysyłania oraz mapowanie błędów API na czytelne komunikaty.
- Lista hackathonów używa osobnego `HackathonListItem` i obsługuje ładowanie, pustą listę, błąd oraz ponowienie żądania.
- Interfejs wykorzystuje proste komponenty `Alert`, `Button`, `Card` i `Spinner`, bez tworzenia docelowego designu.

## Kontrakt z backendem

- `POST /api/auth/register` — tworzy użytkownika.
- `POST /api/auth/login` — przyjmuje formularz OAuth2, zwraca access token i ustawia refresh cookie `HttpOnly`.
- `POST /api/auth/refresh` — odczytuje i obraca refresh cookie oraz zwraca nowy access token.
- `POST /api/auth/logout` — kończy sesję i usuwa refresh cookie.
- `GET /api/auth/me` — zwraca bieżącego użytkownika dla access tokena.
- `GET /api/hackathons` — zwraca listę hackathonów dla zalogowanego użytkownika.

Frontend nie odczytuje refresh tokena i nie zapisuje tokenów w `localStorage` ani `sessionStorage`.

## Zakres

**W zakresie:**

- Klient API z obsługą Bearer tokena, `error_code`, refresh i pojedynczego retry.
- Typy TypeScript dla `User`, `Hackathon`, danych formularzy, tokena dostępu i błędów API.
- Kontekst uwierzytelniania, `AuthProvider` i hook `useAuth`.
- Odtwarzanie sesji z refresh cookie po przeładowaniu strony.
- Formularze logowania i rejestracji z walidacją klienta.
- Trasy `/login`, `/register`, `/hackathons` oraz zabezpieczenia tras.
- Podział listy hackathonów na stronę, listę i pojedynczy element.
- Stany ładowania, pustej listy i błędu z możliwością ponowienia.
- Testy jednostkowe i komponentowe klienta API, auth, routingu oraz listy hackathonów.
- Podstawowe uruchamianie frontendu w Docker Compose z bind mountem źródeł i osobnym volume dla `node_modules`.

**Poza zakresem:**

- Docelowy projekt graficzny, responsywny layout i rozbudowa design systemu.
- Formularz zgłoszenia uczestnika na hackathon i obsługa pytań rekrutacyjnych.
- Widoki organizatora do zarządzania zgłoszeniami, pytaniami i ich statusami.
- Logowanie przez zewnętrznych dostawców.
- Reset hasła, weryfikacja adresu e-mail i zarządzanie profilem.
- Przechowywanie access lub refresh tokena w Web Storage.

## Wpływ

- **Frontend:** nowa struktura feature-based, wspólny klient API, centralny stan auth i routing aplikacji. Komponenty stron pozostają proste wizualnie.
- **Backend:** brak nowej logiki biznesowej wymaganej przez frontend. Frontend zależy od kontraktu cookie `HttpOnly`, poprawnej konfiguracji CORS z credentials i endpointów auth opisanych w `SPEC-003`.
- **Baza danych:** brak zmian.
- **API:** wszystkie żądania przeglądarki wysyłają credentials; chronione żądania dodatkowo używają access tokena w nagłówku Bearer.
- **Docker:** kod frontendu może być montowany do kontenera podczas developmentu, a zależności są chronione osobnym named volume `frontend-node-modules`.

## Kryteria akceptacji

- Użytkownik może utworzyć konto, a po sukcesie zostaje przekierowany do logowania.
- Użytkownik może się zalogować i przejść do `/hackathons`.
- Niepoprawne dane formularza są odrzucane przed wysłaniem żądania.
- Błędy backendu z `error_code` są mapowane na zrozumiałe komunikaty.
- Niezalogowany użytkownik nie może otworzyć `/hackathons`.
- Zalogowany użytkownik nie może ponownie otworzyć `/login` ani `/register`.
- Po przeładowaniu strony sesja jest odtwarzana z refresh cookie bez użycia Web Storage.
- Po `401` klient wykonuje najwyżej jeden refresh i jeden retry pierwotnego żądania.
- Wylogowanie czyści access token w pamięci i prowadzi do `/login` również wtedy, gdy żądanie logout zakończy się błędem sieciowym.
- Lista hackathonów pokazuje stan ładowania, pustą listę, błąd z przyciskiem ponowienia albo dane z API.
- `npm test`, `npm run lint` i `npm run build` przechodzą.

## Alternatywy rozważane

- **Tokeny w `localStorage`** — odrzucone, ponieważ skrypt uruchomiony w wyniku XSS mógłby je odczytać. Access token pozostaje w pamięci, a refresh token w cookie `HttpOnly`.
- **Refresh token obsługiwany bezpośrednio przez JavaScript** — odrzucony, aby ograniczyć możliwość jego kradzieży przez XSS.
- **Stan auth wyłącznie w komponentach stron** — odrzucony, ponieważ prowadziłby do duplikacji logiki sesji i utrudniał zabezpieczanie tras.
- **Pełny framework zarządzania stanem** — odrzucony na tym etapie; React Context wystarcza dla niewielkiego globalnego stanu sesji.
- **Docelowy design w ramach tej zmiany** — odłożony. Obecne komponenty zapewniają jedynie czytelny układ i wymagane stany interfejsu.

## Changelog

- 2026-08-11 — utworzono spec po implementacji klienta API, auth providera, formularzy, routingu, listy hackathonów i testów frontendu.
- 2026-08-11 — zapisano decyzję o przechowywaniu access tokena w pamięci i refresh tokena w cookie `HttpOnly`.
