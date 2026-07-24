# SPEC-002: Postgres + Redis + ORM — przykładowy szkielet architektury

**Status:** Zaimplementowany
**Data:** 2026-07-24
**Autor:** setup (Claude Code)

## Kontekst / Problem

Backend miał tylko endpoint `/api/hello` bez żadnej trwałej bazy danych ani cache'a. Zespół potrzebuje przykładu, jak w tym projekcie wygląda "właściwa" warstwa danych (ORM, migracje, cache), żeby dalej rozbudowywać aplikację (zespoły, uczestnicy, zgłoszenia itd.) według tego samego wzorca zamiast wymyślać architekturę od zera przy każdym nowym endponcie.

## Proponowane rozwiązanie

Minimalny, ale kompletny pionowy przekrój (vertical slice) przez całą architekturę na jednej, celowo prostej encji **Hackathon** (`id`, `name`):

- **Postgres** jako baza danych, **SQLAlchemy 2.0 (async, `asyncpg`)** jako ORM, **Alembic** do migracji schematu.
- **Redis** jako cache — wzorzec *cache-aside* na liście hackathonów (odczyt: cache → miss → DB → zapisz do cache; invalidacja przy zmianie danych).
- **Wzorzec Repository** (`app/repositories/`) — cała komunikacja z bazą przez repozytorium, nigdy bezpośrednio z routera.
- **Wzorzec Service** (`app/services/`) — logika biznesowa (w tym decyzja "cache czy baza") oddzielona od repozytorium i od warstwy HTTP.
- Endpoint `GET /api/hackathons` zwraca listę `{id, name}` — router → service → (cache | repository) → DB.
- Frontend: minimalny komponent listujący hackathony (tylko `id` + `name`, zero stylowania poza tym co już jest w design-systemie).
- Docker Compose: usługi `postgres` i `redis` z healthcheckami, `backend` łączy się przez zmienne środowiskowe `DATABASE_URL` / `REDIS_URL`.
- CI (`backend-ci`): kontenery usług Postgres + Redis, żeby testy integracyjne repozytorium/serwisu faktycznie uderzały w prawdziwą bazę (nie mocki).

## Zakres

**W zakresie:**
- Jedna encja (`Hackathon`: `id`, `name`), jedna migracja Alembic, jeden seed (3 przykładowe rekordy).
- Jeden endpoint odczytu (`GET /api/hackathons`) z cache-aside w Redis.
- Repository + Service dla tej jednej encji, jako wzorzec do skopiowania.
- Minimalny frontend wyświetlający listę (bez stylowania, bez paginacji, bez wyszukiwania).
- Jeden test integracyjny (repository + service, z realną bazą w CI).

**Poza zakresem (celowo — do zrobienia przez studentów):**
- CRUD (create/update/delete) dla `Hackathon` i jakiekolwiek inne encje (zespoły, uczestnicy, zgłoszenia).
- Walidacja wejścia, obsługa błędów, kody stanu inne niż 200.
- Autentykacja/autoryzacja.
- Paginacja, filtrowanie, sortowanie.
- Invalidacja cache przy zapisie (nie ma zapisu — jeszcze).
- Stylowanie frontendu listy, obsługa błędów sieciowych w UI, loading states.
- Testy jednostkowe serwisu z mockiem repozytorium (jest tylko integracyjny).

Zobacz issues z etykietą `spec-needed`/powiązane z SPEC-002 — to konkretne zadania na start.

## Wpływ

- **Frontend:** nowy komponent `src/features/hackathons/HackathonList.tsx` + test, wpięty w `App.tsx`.
- **Backend:** `app/db.py` (silnik/sesja SQLAlchemy), `app/cache.py` (klient Redis), `app/models.py` (model `Hackathon`), `app/repositories/hackathon_repository.py`, `app/services/hackathon_service.py`, nowy endpoint w `app/main.py`, katalog `alembic/` z jedną migracją.
- **Baza danych / API:** nowa tabela `hackathons` (`id serial primary key`, `name text not null`). Nowy endpoint `GET /api/hackathons`.
- **Infrastruktura:** `docker-compose.yml` (usługi `postgres`, `redis`), `backend-ci.yml` (service containers), `backend/requirements.txt` (sqlalchemy, asyncpg, alembic, redis), `backend/.env.example`.

## Alternatywy rozważane

- **SQLModel zamiast SQLAlchemy** — odrzucone: czyste SQLAlchemy 2.0 jest bardziej rozpowszechnione i łatwiej znaleźć dokumentację/pomoc przy nauce.
- **Bez Alembic (tylko `create_all`)** — odrzucone: studenci i tak będą potrzebować migracji przy pierwszej zmianie schematu, lepiej mieć to od początku jako wzorzec.
- **Więcej encji od razu (Team, Participant)** — odrzucone: cel to pokazać wzorzec na jednym prostym przykładzie, nie zbudować gotową aplikację za studentów.

## Changelog

- 2026-07-24 — utworzono i zaimplementowano spec (Hackathon: Postgres/SQLAlchemy/Alembic/Redis/Repository/Service, minimalny frontend)
