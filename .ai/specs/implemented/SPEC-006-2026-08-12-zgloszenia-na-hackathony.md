# SPEC-006: Zgłoszenia uczestników na hackathony

**Status:** Zaimplementowany
**Data:** 2026-08-12
**Autor:** zespół hackathon-manager

## Kontekst / Problem

Uczestnik potrzebuje możliwości wysłania jednego zgłoszenia na wybrany hackathon wraz z
odpowiedziami na pytania rekrutacyjne. Organizatorzy muszą móc zarządzać pytaniami, przeglądać
zgłoszenia i odpowiedzi oraz zaakceptować albo odrzucić uczestnika. Operacje muszą respektować
uprawnienia do konkretnego hackathonu i jego rzeczywiste okno zapisów.

## Rozwiązanie

Backend udostępnia moduł `registration` z warstwami router → service → repository oraz modelami:

- `RegistrationQuestion` — pytanie przypisane do hackathonu, wymagane albo opcjonalne;
- `Registration` — zgłoszenie użytkownika ze statusem `pending`, `accepted` lub `rejected`;
- `RegistrationAnswer` — odpowiedź łącząca zgłoszenie z pytaniem.

Każdy użytkownik może mieć najwyżej jedno zgłoszenie na dany hackathon. Podczas wysyłania
zgłoszenia serwis sprawdza aktualny stan zapisów przez `Hackathon.is_registration_open_at()`,
przynależność pytań do hackathonu, komplet wymaganych odpowiedzi oraz brak duplikatów pytań.

Administrator, właściciel i współorganizator hackathonu mogą zarządzać pytaniami, przeglądać
zgłoszenia wraz z danymi uczestników i odpowiedziami oraz zmieniać status na `accepted` albo
`rejected`. Uczestnik może pobrać i usunąć własne zgłoszenie.

## Endpointy API

- `GET /api/hackathons/{hackathon_public_id}/questions` — pobranie pytań przez zalogowanego
  użytkownika.
- `POST /api/hackathons/{hackathon_public_id}/questions` — dodanie pytania przez osobę
  zarządzającą hackathonem.
- `POST /api/hackathons/{hackathon_public_id}/questions/bulk` — dodanie od 1 do 50 pytań w
  jednej operacji przez osobę zarządzającą hackathonem.
- `DELETE /api/hackathons/{hackathon_public_id}/questions/{question_public_id}` — usunięcie
  pytania przez osobę zarządzającą hackathonem.
- `POST /api/hackathons/{hackathon_public_id}/registrations` — wysłanie zgłoszenia przez
  uczestnika.
- `GET /api/hackathons/{hackathon_public_id}/registrations` — lista zgłoszeń i odpowiedzi dla
  osób zarządzających hackathonem.
- `GET /api/hackathons/{hackathon_public_id}/registrations/me` — własne zgłoszenie uczestnika.
- `DELETE /api/registrations/{registration_public_id}` — usunięcie zgłoszenia przez jego autora
  albo osobę zarządzającą hackathonem.
- `PATCH /api/registrations/{registration_public_id}/status` — akceptacja albo odrzucenie
  zgłoszenia przez osobę zarządzającą hackathonem.

Wszystkie endpointy modułu wymagają uwierzytelnienia.

## Walidacja i błędy

Moduł zwraca stabilne `error_code`, między innymi:

- `QUESTION_NOT_FOUND`;
- `REGISTRATION_PERMISSION_DENIED`;
- `INVALID_REGISTRATION_QUESTION`;
- `MISSING_REQUIRED_ANSWERS`;
- `REGISTRATION_ALREADY_EXISTS`;
- `REGISTRATION_CLOSED`;
- `REGISTRATION_NOT_FOUND`.

Ograniczenia unikalności w bazie zabezpieczają jedno zgłoszenie użytkownika na hackathon oraz
jedną odpowiedź na dane pytanie w ramach zgłoszenia. Operacje zapisu wykonują rollback po
błędzie.

## Zakres

**W zakresie:**

- modele pytań, zgłoszeń i odpowiedzi;
- tworzenie i usuwanie pytań rekrutacyjnych;
- pobieranie pytań przez uczestnika;
- tworzenie i usuwanie zgłoszenia;
- pobieranie własnego zgłoszenia;
- lista zgłoszeń wraz z uczestnikami, pytaniami i odpowiedziami;
- akceptowanie i odrzucanie zgłoszeń;
- kontrola aktualnego okna rejestracji;
- autoryzacja administratora, właściciela i współorganizatora;
- migracja Alembic oraz testy endpointów, serwisów i repozytoriów.

**Poza zakresem:**

- formularz zgłoszeniowy i panel organizatora we frontendzie;
- zgłoszenia zespołowe;
- limity zaakceptowanych uczestników i automatyczne pilnowanie pojemności;
- powiadomienia e-mail o zmianie statusu;
- edycja wysłanego zgłoszenia;
- przywracanie statusu zgłoszenia do `pending` przez API.

## Wpływ

- **Frontend:** brak interfejsu w tej zmianie; udostępniono kontrakty API potrzebne do późniejszego
  formularza uczestnika i panelu organizatora.
- **Backend:** nowy moduł `src/registration`, router, zależności, serwisy, repozytoria, schematy
  Pydantic, wyjątki domenowe oraz rejestracja globalnej obsługi błędów.
- **Baza danych:** tabele `questions`, `registrations` i `answers`, enum statusu, klucze obce z
  usuwaniem kaskadowym oraz ograniczenia unikalności. Wspólna migracja scalająca łączy gałęzie
  zgłoszeń, drużyn i zaplanowanego okna rejestracji. Migracja `0008` dodaje nullable pola
  `status_changed_at` i `status_changed_by_id`; usunięcie użytkownika zeruje wskazanie autora
  decyzji przez `ON DELETE SET NULL`.
- **API:** nowe chronione endpointy pod `/api/hackathons/...` i `/api/registrations/...`.

## Alternatywy rozważane

- **Odpowiedzi jako JSON w zgłoszeniu** — odrzucono, ponieważ osobne rekordy zapewniają klucze
  obce, spójność z pytaniami i prostsze pobieranie szczegółów.
- **Wiele zgłoszeń użytkownika na jeden hackathon** — odrzucono; jedno aktywne zgłoszenie jest
  chronione również constraintem bazy danych.
- **Uprawnienia wyłącznie dla globalnego administratora** — odrzucono na rzecz kontekstowych
  uprawnień właściciela i współorganizatorów wydarzenia.
- **Sprawdzanie tylko flagi `registration_open`** — odrzucono; zgłoszenie musi respektować także
  `registration_opens_at` i `registration_deadline`.

## Testy

Testy obejmują kontrakty HTTP, uprawnienia, walidację odpowiedzi, zamknięte zapisy, duplikaty
zgłoszeń, zmianę statusu, rollback transakcji i rzeczywiste operacje repozytoriów na PostgreSQL.

## Changelog

- 2026-08-12 — opisano zaimplementowany moduł zgłoszeń uczestników.
