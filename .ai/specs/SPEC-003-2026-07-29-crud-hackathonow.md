# SPEC-003: CRUD hackathonów z walidacją i invalidacją cache

**Status:** Zaakceptowany
**Data:** 2026-07-29
**Autor:** matyyy12

## Kontekst / Problem

Backend udostępnia obecnie tylko odczyt listy hackathonów przez
`GET /api/hackathons`. Brakuje możliwości tworzenia, edycji i usuwania rekordów.
Lista jest przechowywana w Redisie zgodnie ze wzorcem cache-aside, więc każda
zmiana danych w PostgreSQL musi unieważniać cache, aby kolejne odczyty nie
zwracały nieaktualnych danych.

## Proponowane rozwiązanie

- Rozszerzyć `HackathonRepository` o operacje tworzenia, aktualizacji i usuwania.
- Rozszerzyć `HackathonService` o odpowiadające im operacje biznesowe.
- Po każdej udanej zmianie danych usunąć klucz `hackathons:list` z Redisa.
- Dodać modele Pydantic oddzielające dane wejściowe i odpowiedzi API od modeli
  SQLAlchemy.
- Udostępnić endpointy `POST`, `PATCH` i `DELETE` dla zasobu hackathonów.
- Zwracać `404 Not Found`, gdy aktualizowany lub usuwany rekord nie istnieje,
  oraz standardowe `422 Unprocessable Entity` dla błędów walidacji.

## Zakres

**W zakresie:**

- `POST /api/hackathons` zwracający `201 Created`.
- `PATCH /api/hackathons/{hackathon_id}` zwracający zaktualizowany rekord.
- `DELETE /api/hackathons/{hackathon_id}` zwracający `204 No Content`.
- Walidacja dodatniego identyfikatora hackathonu.
- Walidacja nazwy: usunięcie zewnętrznych spacji, długość od 1 do 200 znaków,
  odrzucenie `null` i pustego żądania `PATCH`.
- Odpowiedzi `404 Not Found` dla nieistniejącego identyfikatora przy `PATCH`
  i `DELETE`.
- Invalidacja klucza `hackathons:list` po udanym `POST`, `PATCH` i `DELETE`.
- Zachowanie istniejącego mechanizmu cache-aside dla listy hackathonów.

**Poza zakresem:**

- Autentykacja i autoryzacja endpointów.
- Wymuszanie unikalności nazwy hackathonu.
- Zmiany modelu bazy danych i nowa migracja Alembic.
- Zmiany frontendu.
- Automatyczne testy CRUD-u; zostaną dodane w osobnym zadaniu.
- Paginacja, filtrowanie, wyszukiwanie i sortowanie.

## Kryteria akceptacji

- Poprawny `POST` zapisuje rekord w PostgreSQL i zwraca jego `id` oraz nazwę.
- Poprawny `PATCH` aktualizuje nazwę i zwraca aktualny stan rekordu.
- Poprawny `DELETE` usuwa rekord i zwraca pustą odpowiedź z kodem `204`.
- Nieistniejący rekord przy `PATCH` lub `DELETE` powoduje odpowiedź `404` z
  czytelnym polem `detail`.
- Nieprawidłowe body lub identyfikator powodują odpowiedź `422` bez wykonania
  operacji zapisu.
- Następny `GET /api/hackathons` po każdej udanej zmianie zwraca aktualne dane,
  a nie poprzednią wartość z cache.

## Wpływ

- **Frontend:** brak zmian.
- **Backend:** nowy `app/schemas.py`; nowe metody w
  `app/repositories/hackathon_repository.py` i
  `app/services/hackathon_service.py`; nowe endpointy w `app/main.py`.
- **Baza danych / API:** bez zmian schematu bazy; trzy nowe operacje HTTP na
  istniejącym zasobie `/api/hackathons`.
- **Cache:** usuwanie klucza `hackathons:list` po udanej zmianie danych; następny
  odczyt odbudowuje cache z PostgreSQL.

## Alternatywy rozważane

- **`PUT` zamiast `PATCH`** — odrzucone, ponieważ aktualizacja częściowa będzie
  łatwiejsza do rozszerzenia po dodaniu kolejnych pól hackathonu.
- **Bezpośrednia edycja listy JSON w Redisie** — odrzucona jako bardziej złożona
  i podatna na rozjazdy z PostgreSQL. Invalidacja całego klucza jest prostsza i
  bezpieczna dla obecnej skali aplikacji.
- **Modele Pydantic bezpośrednio w `main.py`** — odrzucone, aby nie mieszać
  kontraktów API z routingiem i modelami SQLAlchemy.

## Powiązane zadania

- GitHub issue #22 — CRUD dla Hackathon (`POST`/`PATCH`/`DELETE`).
- Osobne issue dotyczące invalidacji cache przy zmianach danych.

## Changelog

- 2026-07-29 — utworzono i zaakceptowano spec; implementacja przygotowana na
  branchu `feat/22-hackathon-crud`.
