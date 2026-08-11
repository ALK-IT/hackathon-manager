# Specyfikacje — hackathon-manager

Ten projekt stosuje metodologię **spec-driven development**: przed implementacją nietrywialnej funkcjonalności lub istotnej zmiany architektonicznej powstaje krótka specyfikacja w tym katalogu.

Wzorowane na podejściu z [open-mercato](https://github.com/open-mercato/open-mercato) (`.ai/specs/`).

## Proces

1. Nowa funkcjonalność / istotna zmiana → `/new-spec` (skill Claude Code) przeprowadzi analizę wymagań i utworzy plik `SPEC-XXX-2026-07-24-krotki-tytul.md` na bazie [TEMPLATE.md](TEMPLATE.md). Można też zrobić to ręcznie.
2. Spec opisuje: problem, proponowane rozwiązanie, wpływ na frontend/backend, alternatywy.
3. Gdy spec ma status `Zaakceptowany` → `/spec-to-issues` rozbija go na konkretne issues na GitHubie i dodaje je do kanbanu.
4. Status specu: `Proponowany` → `Zaakceptowany` → `Zaimplementowany` (aktualizuj nagłówek pliku). Po zaimplementowaniu spec przenosi się do [implemented/](implemented/).
5. Pull request odnosi się do specu w opisie (patrz szablon PR) — agent AI (`ai-review`) ostrzeże, jeśli nietrywialny PR nie ma odniesienia do żadnego SPEC-a.
6. `/spec-status` — okresowy audyt: sprawdza, czy statusy speców zgadzają się z rzeczywistymi PR-ami/issues na GitHubie.

## Indeks specyfikacji

| # | Tytuł | Status | Plik |
|---|---|---|---|
| SPEC-001 | Hello World — szkielet frontend/backend | Zaimplementowany | [SPEC-001-hello-world.md](SPEC-001-hello-world.md) |
| SPEC-002 | Postgres + Redis + ORM — przykładowy szkielet architektury | Zaimplementowany | [implemented/SPEC-002-2026-07-24-postgres-redis-przyklad.md](implemented/SPEC-002-2026-07-24-postgres-redis-przyklad.md) |
| SPEC-003 | Rejestracja, logowanie i sesje JWT | Zaimplementowany | [implemented/SPEC-003-2026-08-03-logowanie-jwt.md](implemented/SPEC-003-2026-08-03-logowanie-jwt.md) |
| SPEC-004 | Frontend uwierzytelniania i routing | Zaimplementowany | [implemented/SPEC-004-2026-08-11-frontend-auth-routing.md](implemented/SPEC-004-2026-08-11-frontend-auth-routing.md) |
| SPEC-004 | CRUD hackathonów i kontekstowe uprawnienia organizatorów | Zaimplementowany | [implemented/SPEC-004-2026-08-03-crud-hackathonow.md](implemented/SPEC-004-2026-08-03-crud-hackathonow.md) |

Zasady utrzymania tego indeksu i współpracy z agentami AI: [AGENTS.md](AGENTS.md).
