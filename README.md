# hackathon-manager

Aplikacja do zarządzania hakatonami

Projekt studencki ALK. Monorepo zawierające frontend (React) i backend (FastAPI).

## Struktura repozytorium

```
hackathon-manager/
├── frontend/                  # React + Vite + TypeScript + Storybook (design system)
│   ├── src/design-system/     # Katalog komponentów UI (Button, tokens...)
│   └── src/features/          # Funkcjonalności (np. hackathons/)
├── backend/                   # FastAPI + Python (SQLAlchemy async + Alembic + Redis)
│   ├── src/auth/              # Użytkownicy, JWT, router, schema, model, service i repository
│   ├── src/hackathons/        # Hackathony: router, schema, model, service i repository
│   ├── src/registration/      # Pytania i zgłoszenia uczestników
│   ├── src/teams/             # Drużyny tworzone lub wybierane podczas zgłoszenia
│   ├── src/system/            # Endpointy systemowe, np. healthcheck
│   ├── src/database.py        # Połączenie i sesje SQLAlchemy
│   └── src/main.py            # Punkt wejścia aplikacji FastAPI
│   └── alembic/               # Migracje schematu bazy
├── .ai/specs/                 # Specyfikacje (spec-driven development)
├── scripts/ai-agents/         # Lokalni AI agenci: code/security/UX review
├── .github/                   # Workflows (CI, CodeQL, gitleaks, audyt zależności), szablony PR/issue, CODEOWNERS
├── .claude/                   # Konfiguracja Claude Code
├── docker-compose.yml         # Uruchomienie całości w Dockerze
├── SECURITY.md                # Polityka bezpieczeństwa
└── CONTRIBUTING.md            # Workflow pracy, branże, etykiety, kanban
```

## Sposób pracy (spec-driven development)

Przed implementacją nietrywialnej funkcjonalności powstaje krótki spec w [.ai/specs/](.ai/specs/README.md) (wzorowane na [open-mercato](https://github.com/open-mercato/open-mercato)). Specy: [SPEC-001 — Hello World](.ai/specs/SPEC-001-hello-world.md), [SPEC-002 — Postgres + Redis + ORM](.ai/specs/implemented/SPEC-002-2026-07-24-postgres-redis-przyklad.md). Pełny workflow pracy (branże, commity, PR, kanban, etykiety): [CONTRIBUTING.md](CONTRIBUTING.md).

W Claude Code dostępne są skille do tego procesu: `/new-spec` (analiza wymagań → spec), `/spec-to-issues` (spec → GitHub issues + kanban), `/spec-status` (audyt statusów speców vs PR-y/issues).

## Kanban / zadania / czas pracy

Tablica projektu (GitHub Projects): https://github.com/orgs/ALK-IT/projects/2
Issues: [github.com/ALK-IT/hackathon-manager/issues](https://github.com/ALK-IT/hackathon-manager/issues) — zgłoszenia przez szablony (bug / propozycja funkcjonalności).

Tablica ma pola **Szacowany czas (h)** i **Rzeczywisty czas (h)** na każdej karcie — wypełniaj przed startem i po zamknięciu zadania. Do granularnego logu w czasie: komentuj issue/PR w formacie `⏱ 2h - co robiłeś`; skill `/time-report` w Claude Code zlicza to per osoba i per zadanie.

## Design system

Wspólne komponenty UI żyją w [frontend/src/design-system/](frontend/src/design-system/) (tokeny w `tokens.ts`, np. `Button`). Katalog komponentów w Storybooku:

```bash
cd frontend
npm run storybook
```

Wdrożony Storybook (auto po push do `main`, workflow `storybook-pages`): https://alk-it.github.io/hackathon-manager/

Nowy współdzielony komponent UI → dodaj go tutaj (nie duplikuj w miejscu użycia) + plik `.stories.tsx`.

## Baza danych i cache (Postgres + Redis)

Przykładowy, celowo minimalny wzorzec architektury na jednej encji (`Hackathon`: `id`, `name`) — reszta (CRUD, walidacja, kolejne encje, testy jednostkowe) to zadanie dla zespołu. Szczegóły i "co dalej": [SPEC-002](.ai/specs/implemented/SPEC-002-2026-07-24-postgres-redis-przyklad.md).

- **ORM:** SQLAlchemy 2.0 (async, `asyncpg`) — wspólna baza modeli w `backend/src/models.py`, modele funkcji w `backend/src/*/models.py`.
- **Migracje:** Alembic (`backend/alembic/`). Nowa migracja: `cd backend && alembic revision -m "opis"`, zastosowanie: `alembic upgrade head` (Docker robi to automatycznie przy starcie kontenera).
- **Wzorce:** kod jest grupowany według funkcji w `src/auth/`, `src/hackathons/` itd. Każda funkcja może zawierać własne `router.py`, `schemas.py`, `models.py`, `repository.py` i `service.py`.
- **Endpoint przykładowy:** `GET /api/hackathons` — lista `{id, name}`, cache w Redis (60s TTL).
- **Lokalnie bez Dockera:** potrzebujesz uruchomionego Postgresa i Redisa (patrz `docker-compose.yml` dla danych dostępowych) albo po prostu `docker compose up postgres redis`.

## Logowanie użytkownika

- `POST /api/auth/register` — rejestracja przez JSON (`name`, `email`, `password`).
- `POST /api/auth/login` — logowanie formularzem OAuth2 (`username` = e-mail, `password` = hasło).
- `GET /api/auth/me` — dane zalogowanego użytkownika, wymagany nagłówek `Authorization: Bearer <token>`.

Hasła są przechowywane jako hashe Argon2. JWT wymaga zmiennej `JWT_SECRET_KEY` zawierającej co najmniej 32 znaki. Bezpieczną wartość można wygenerować poleceniem `openssl rand -hex 32`. Czas ważności tokena ustawia opcjonalna zmienna `ACCESS_TOKEN_EXPIRE_MINUTES` (domyślnie 30 minut).

## AI agenci (code review / security review / UX review)

Dodanie etykiety **`ai-review`** do pull requesta uruchamia (po odpaleniu lokalnego watchera) automatyczny przegląd: code review, security review, a dla zmian w `frontend/` — dodatkowo UX/design-system review. Działa lokalnie przez Claude Code (subskrypcja, bez kosztów per token w CI). Szczegóły: [scripts/ai-agents/README.md](scripts/ai-agents/README.md).

## Discord

Powiadomienia na Discordzie: nowy/zmergowany PR, nowe/zamknięte issue, czerwone CI lub nieudany deploy (workflow `discord-notify`), oraz — lokalnie — gdy agent AI skończy review. Wymaga webhooka Discorda: sekret repo `DISCORD_WEBHOOK_URL` (dla Actions) + lokalny `scripts/ai-agents/.env` (dla agentów AI). Instrukcja: [scripts/ai-agents/README.md](scripts/ai-agents/README.md#discord-opcjonalnie).

## Bezpieczeństwo

CodeQL, gitleaks (skan sekretów) i audyt zależności (`npm audit` / `pip-audit`) uruchamiają się automatycznie na każdym PR — patrz [SECURITY.md](SECURITY.md) po pełny opis mechanizmów i zasady zgłaszania podatności.

## Quickstart

### Wymagania

- Docker z Docker Compose — zalecany wariant uruchomienia całego projektu,
- Python 3.12 — wymagany przy uruchamianiu backendu poza Dockerem,
- Node.js 22 i npm — wymagane przy uruchamianiu frontendu poza Dockerem.

### Docker Compose (zalecane)

Uruchom wszystkie usługi wraz z migracjami bazy:

```bash
docker compose up --build
```

Po uruchomieniu dostępne są:

- frontend: http://localhost:5173,
- backend: http://localhost:8000,
- interaktywna dokumentacja OpenAPI: http://localhost:8000/docs,
- specyfikacja OpenAPI JSON: http://localhost:8000/openapi.json.

Opcjonalnie utwórz administratora, przykładowy hackathon, pytania, zasoby i rejestracje:

```bash
docker compose exec backend python -m scripts.seed
```
### Dane przykładowe (quickstart)

Po uruchomieniu kontenerów można jedną komendą utworzyć lokalnego administratora,
hackathon z pytaniami, zasoby oraz przykładowe rejestracje:

```bash
docker compose exec backend python -m scripts.seed
```

Skrypt jest idempotentny, więc można uruchamiać go wielokrotnie. Dane logowania:

- administrator: `admin@local.dev` / `Admin123!`
- uczestnik: `anna@local.dev` / `Participant123!`

Hasło administratora można zmienić przez `SEED_ADMIN_PASSWORD`, np.
`docker compose exec -e SEED_ADMIN_PASSWORD='inne-hasło' backend python -m scripts.seed`.
Seed jest przeznaczony wyłącznie do lokalnego developmentu, odmawia działania na zdalnej bazie
i nie uruchamia się automatycznie.

Zatrzymanie: `docker compose down`. Rebuild po zmianie zależności: `docker compose up --build`.

Skrypt seedujący jest idempotentny. Tworzy konta `admin@local.dev` / `Admin123!` oraz
`anna@local.dev` / `Participant123!`. Hasło administratora można nadpisać zmienną
`SEED_ADMIN_PASSWORD`. Seed służy wyłącznie do lokalnego developmentu.

Zatrzymanie usług:

```bash
docker compose down
```

Dodanie `-v` (`docker compose down -v`) usuwa również lokalną bazę danych.

### Uruchomienie bez Dockera

Najpierw uruchom PostgreSQL i Redis. Można wykorzystać tylko usługi infrastrukturalne z Compose:

```bash
docker compose up -d postgres redis
```

Skonfiguruj i uruchom backend:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

export DATABASE_URL='postgresql+asyncpg://hackathon:hackathon@localhost:5432/hackathon_manager'
export REDIS_URL='redis://localhost:6379/0'
export JWT_SECRET_KEY='local-development-secret-key-at-least-32-characters'
export RESOURCE_ENCRYPTION_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"

alembic upgrade head
uvicorn src.main:app --reload
```

Polecenie powyżej generuje nowy klucz Fernet przeznaczony do lokalnego developmentu.

W drugim terminalu uruchom frontend:

```bash
cd frontend
npm ci
VITE_API_URL=http://localhost:8000 npm run dev
```

### Zmienne środowiskowe

| Zmienna | Wymagana | Wartość lokalna / opis |
|---|---:|---|
| `DATABASE_URL` | produkcja | Adres PostgreSQL; lokalnie domyślnie `postgresql+asyncpg://hackathon:hackathon@localhost:5432/hackathon_manager`. |
| `REDIS_URL` | produkcja | Adres Redis; lokalnie domyślnie `redis://localhost:6379/0`. |
| `JWT_SECRET_KEY` | tak | Sekret JWT o długości co najmniej 32 znaków. Wygeneruj np. przez `openssl rand -hex 32`. |
| `RESOURCE_ENCRYPTION_KEY` | tak | Klucz Fernet służący do szyfrowania wartości zasobów. |
| `FRONTEND_ORIGINS` | nie | Lista originów CORS oddzielona przecinkami; domyślnie `http://localhost:5173`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | nie | Czas ważności access tokena; domyślnie `30`. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | nie | Czas ważności refresh tokena; domyślnie `7`. |
| `AUTH_COOKIE_SECURE` | nie | Ustaw `true` przy HTTPS; domyślnie `false`. |
| `AUTH_COOKIE_SAMESITE` | nie | `lax`, `strict` albo `none`; domyślnie `lax`. |
| `VITE_API_URL` | nie | Adres backendu używany podczas budowania frontendu; domyślnie `http://localhost:8000`. |
| `TEST_DATABASE_URL` | testy | Adres oddzielnej bazy testowej, której nazwa musi kończyć się na `_test`. |

### Przykładowe zapytania

Healthcheck i publiczna lista hackathonów:

```bash
curl --fail http://localhost:8000/health
curl --fail http://localhost:8000/api/hackathons
```

Rejestracja i logowanie:

```bash
curl --fail-with-body \
  -X POST http://localhost:8000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"name":"Jan Kowalski","email":"jan@example.com","password":"Password123!"}'

curl --fail-with-body \
  -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -c cookies.txt \
  --data-urlencode 'username=jan@example.com' \
  --data-urlencode 'password=Password123!'
```

Odpowiedź logowania zawiera access token. Chronione endpointy wymagają nagłówka
`Authorization: Bearer <access_token>`, a refresh token jest ustawiany jako ciasteczko HTTP-only.

## Testy

```bash
# frontend (jednostkowe)
cd frontend && npm run test -- --run

# backend (korzysta z osobnej bazy postgres-test z docker-compose.yml)
docker compose run --build --rm backend pytest
```

**E2E (przykładowy smoke test):** sprawdza cały przekrój — frontend + backend + Postgres + Redis razem, przez `docker compose`:

```bash
docker compose -p hackathon-manager-e2e up -d --build
cd frontend
npx playwright install --with-deps chromium   # jednorazowo
npm run test:e2e
docker compose -p hackathon-manager-e2e down -v
```

Osobna nazwa projektu Compose sprawia, ze E2E korzysta z innego wolumenu niz lokalna baza
developerska. Testy backendu dodatkowo odmawiaja wykonania `drop_all()`, jezeli nazwa bazy nie
konczy sie na `_test`.

Odpala się automatycznie w CI (workflow `e2e`, niewymagany do mergu — informacyjny).

## Deploy

- **Frontend** — Vercel, automatyczny deploy po merge do `main` (workflow `deploy-frontend`). Root Directory w projekcie Vercel musi być ustawiony na `frontend` (patrz `frontend/vercel.json`).
- **Backend** — Railway, automatyczny deploy po merge do `main` (workflow `deploy-backend`). Wymaga jednorazowego setupu w Railway:
  1. Serwis backendu: **Settings → Source → Root Directory** = `backend`.
  2. W projekcie Railway dodaj: **+ New → Database → Add PostgreSQL** i **Add Redis** (osobne serwisy, `docker-compose.yml` obowiązuje tylko lokalnie).
  3. Serwis backendu → **Variables** → `DATABASE_URL` = `${{Postgres.DATABASE_URL}}`, `REDIS_URL` = `${{Redis.REDIS_URL}}`, `JWT_SECRET_KEY` = losowy sekret wygenerowany przez `openssl rand -hex 32`.

Wymagane sekrety repozytorium (Settings → Secrets and variables → Actions):

| Sekret | Do czego służy |
|---|---|
| `VERCEL_TOKEN` | Token dostępu Vercel |
| `VERCEL_ORG_ID` | ID organizacji Vercel |
| `VERCEL_PROJECT_ID` | ID projektu Vercel (frontend) |
| `RAILWAY_TOKEN` | Token dostępu Railway |
| `RAILWAY_SERVICE` | Nazwa/ID serwisu Railway (backend) |
| `DISCORD_WEBHOOK_URL` | Powiadomienia na Discordzie (opcjonalnie) |

## Zasady współpracy

Pełny opis w [CONTRIBUTING.md](CONTRIBUTING.md). W skrócie:

- Praca na branchach `feat/...` / `fix/...` / `chore/...`, zmiany trafiają do `main` przez pull request.
- Wymagane: 2 zatwierdzenia review (w tym code owners), przejście CI (`frontend-ci`, `backend-ci`), rozwiązanie wszystkich konwersacji.
- Zobacz [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md) i [CODEOWNERS](.github/CODEOWNERS) — zaktualizuj właścicieli kodu.

## Licencja

MIT — zobacz [LICENSE](LICENSE).
