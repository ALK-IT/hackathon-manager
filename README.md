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
│   ├── app/repositories/      # Wzorzec Repository (dostęp do bazy)
│   ├── app/services/          # Wzorzec Service (logika biznesowa, cache)
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

- **ORM:** SQLAlchemy 2.0 (async, `asyncpg`) — modele w `backend/app/models/`.
- **Migracje:** Alembic (`backend/alembic/`). Nowa migracja: `cd backend && alembic revision -m "opis"`, zastosowanie: `alembic upgrade head` (Docker robi to automatycznie przy starcie kontenera).
- **Wzorce:** Repository (`app/repositories/`, cała komunikacja z bazą) + Service (`app/services/`, logika biznesowa i cache-aside w Redis). Router (`app/main.py`) woła tylko service, nigdy repozytorium/bazy bezpośrednio.
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

## Wymagania

- Node.js 20+
- Python 3.12+
- Docker + Docker Compose (opcjonalnie, do uruchomienia całości jedną komendą)

## Uruchomienie w Dockerze

Najprostszy sposób odpalenia całości (frontend + backend):

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000 (dokumentacja API: http://localhost:8000/docs)

Zatrzymanie: `docker compose down`. Rebuild po zmianie zależności: `docker compose up --build`.

## Uruchomienie lokalne (bez Dockera)

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

### Backend

```bash
cd backend
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

## Testy

```bash
# frontend (jednostkowe)
cd frontend && npm run test -- --run

# backend (integracyjne, wymaga Postgres+Redis - patrz docker-compose.yml)
cd backend && pytest
```

**E2E (przykładowy smoke test):** sprawdza cały przekrój — frontend + backend + Postgres + Redis razem, przez `docker compose`:

```bash
docker compose up -d --build
cd frontend
npx playwright install --with-deps chromium   # jednorazowo
npm run test:e2e
docker compose down -v
```

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
