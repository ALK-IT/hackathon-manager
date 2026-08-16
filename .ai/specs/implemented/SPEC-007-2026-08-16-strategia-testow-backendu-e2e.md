# SPEC-007: Strategia testów backendu i przepływy E2E

**Status:** Zaimplementowany
**Data:** 2026-08-16
**Autorzy:** Patryk Nisgorski, Codex

## Kontekst / Problem

Backend miał testy endpointów, repozytoriów i serwisów, ale brakowało spójnego opisu ich
odpowiedzialności oraz testów przechodzących przez pełną historię kilku użytkowników. Część
testów endpointów współdzieliła jedną sesję SQLAlchemy, co mogło ukrywać problemy z relacjami
ładowanymi leniwie, niewystępujące dopóki obiekt pozostawał w pamięci sesji.

Definition of Done wymaga co najmniej jednego automatycznego testu głównej ścieżki. Potrzebne są
również stabilne zasady testowania constraintów PostgreSQL, kontraktów `error_code`, transakcji
i funkcji dodawanych w kolejnych modułach.

## Proponowane rozwiązanie

Strategia składa się z trzech warstw:

1. **Testy jednostkowe** sprawdzają logikę serwisu z repozytorium zastąpionym mockiem. Służą do
   szybkiego testowania decyzji domenowych, wywołań zależności i rollbacku.
2. **Testy integracyjne** uruchamiają endpoint albo repozytorium z prawdziwym PostgreSQL. Testują
   serializację, autoryzację, constrainty, mapowanie wyjątków na status HTTP i `error_code`.
3. **Backendowe E2E** wykonują pełny proces wyłącznie przez API, bez mockowania auth, serwisów i
   repozytoriów. Każde żądanie dostaje osobną sesję SQLAlchemy, a tokeny korzystają z prawdziwego,
   izolowanego Redis.

Szczegółowe zasady uruchamiania, fixture'ów i rozbudowy macierzy pokrycia znajdują się w
`backend/tests/README.md`.

### Struktura

```text
backend/tests/
├── README.md
├── conftest.py
├── auth/
├── hackathons/
├── registration/
├── teams/
└── e2e/
    ├── conftest.py
    ├── helpers.py
    ├── test_auth_session_flow.py
    ├── test_hackathon_management_flow.py
    └── test_registration_team_flow.py
```

### Izolacja E2E

- PostgreSQL jest odtwarzany przed każdym testem przez główny fixture `session`.
- Nazwa testowej bazy musi kończyć się na `_test`; fixture odmawia usunięcia innej bazy.
- Każde żądanie HTTP korzysta z nowej sesji utworzonej przez `async_sessionmaker`.
- E2E używa bazy Redis nr 15, czyszczonej przed i po każdym scenariuszu, dzięki czemu nie usuwa
  sesji z developerskiej bazy Redis nr 0.
- Użytkownicy rejestrują się i logują przez prawdziwe endpointy. Administrator jest jedynym
  bootstrapowanym rekordem, ponieważ API nie udostępnia nadawania roli administratora.

### Zaimplementowane przepływy E2E

- **Sesja auth:** rejestracja → logowanie → `/me` → rotacja refresh tokena → logout → odrzucenie
  unieważnionego access tokena i refresh cookie.
- **Zarządzanie hackathonem:** utworzenie → lista zarządzanych → edycja → otwarcie zapisów →
  publiczna lista → zamknięcie zapisów → soft-delete → brak publicznego dostępu.
- **Zgłoszenie i drużyna:** utworzenie pytań → rejestracja dwóch uczestników → utworzenie drużyny
  przez pierwszego → dołączenie kodem przez drugiego → lista organizatora → akceptacja i
  odrzucenie → odczyt własnych statusów oraz wspólnej drużyny.

E2E zgłoszeń wykrył brak eager loadingu `Registration.team`. Repozytorium pobiera teraz relację
drużyny przez `selectinload` dla listy zgłoszeń, własnego zgłoszenia i odczytu używanego przy
zmianie statusu. Zapobiega to `MissingGreenlet` oraz odpowiedzi `500` podczas serializacji.

## Zakres

**W zakresie:**

- dokument strategii testowej;
- fixture'y prawdziwego PostgreSQL i izolowanego Redis;
- osobna sesja bazy dla każdego żądania E2E;
- pełne przepływy auth, zarządzania hackathonem oraz zgłoszenia z drużyną;
- integracyjne testy wszystkich obecnie obsługiwanych kodów błędów rejestracji i drużyn;
- test constraintu jednego zgłoszenia użytkownika na hackathon;
- poprawka eager loadingu drużyny wykryta przez E2E;
- uruchamianie przez `pytest` i kontrola przez Ruff.

**Poza zakresem:**

- frontendowe E2E w przeglądarce;
- testy consent i limitu zaakceptowanych uczestników, których domena jeszcze nie implementuje;
- operacje drużyn `confirm`, `leave` i `remove`, których nie ma w API;
- `unique(hackathon_id, normalized_name)`, ponieważ obecny model przechowuje tylko `name`;
- przepływ zasobów `add/import/assign/revoke/reveal`, dopóki moduł zasobów nie istnieje;
- testy wydajnościowe, obciążeniowe i chaos testing.

## Wpływ

- **Frontend:** brak zmian; frontendowe Playwright E2E pozostaje osobną warstwą.
- **Backend:** nowy katalog `tests/e2e`, wspólne helpery oraz eager loading relacji drużyny.
- **Baza danych:** brak zmian schematu; testy korzystają wyłącznie z bazy zakończonej `_test`.
- **Redis:** E2E korzysta z izolowanej bazy nr 15 i czyści ją między testami.
- **API:** brak nowych endpointów; istniejące procesy są sprawdzane przez publiczny kontrakt HTTP.

## Kryteria akceptacji

- E2E nie zastępuje auth ani serwisów mockami.
- Każde żądanie E2E korzysta z osobnej sesji SQLAlchemy.
- Przepływy auth, zarządzania hackathonem oraz zgłoszenia z drużyną przechodzą na PostgreSQL i
  Redis uruchomionych przez Docker Compose.
- Wszystkie obsługiwane kody błędów rejestracji i drużyn mają test statusu HTTP oraz
  `error_code`.
- `pytest` i `ruff check src tests` przechodzą.
- Brakujące domeny są jawnie oznaczone w macierzy i otrzymają E2E razem z implementacją.

## Alternatywy rozważane

- **Jeden ogromny test całej aplikacji** — odrzucony, ponieważ utrudnia diagnozę awarii i tworzy
  zależność wszystkich procesów od jednego scenariusza.
- **Mockowanie tokenów w E2E** — odrzucone, ponieważ nie sprawdza sesji Redis, refresh ani revoke.
- **Wspólna sesja SQLAlchemy dla wszystkich żądań** — odrzucona, ponieważ ukrywa brak eager
  loadingu i nie odpowiada zachowaniu aplikacji produkcyjnej.
- **Redis DB 0** — odrzucona, aby test nie usuwał aktywnych sesji developerskich.
- **Puste lub pominięte testy przyszłych modułów** — odrzucone; test powstaje razem z działającym
  kontraktem modelu, migracji i API.

## Changelog

- 2026-08-16 — dodano strategię, trzy przepływy E2E i poprawkę eager loadingu drużyny.
