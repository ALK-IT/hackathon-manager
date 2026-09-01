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
| SPEC-004 | CRUD hackathonów i kontekstowe uprawnienia organizatorów | Zaimplementowany | [implemented/SPEC-004-2026-08-03-crud-hackathonow.md](implemented/SPEC-004-2026-08-03-crud-hackathonow.md) |
| SPEC-005 | Drużyny tworzone podczas zgłoszenia na hackathon | Zaimplementowany | [implemented/SPEC-005-2026-08-09-druzyny-w-zgloszeniach.md](implemented/SPEC-005-2026-08-09-druzyny-w-zgloszeniach.md) |
| SPEC-006 | Zgłoszenia uczestników na hackathony | Zaimplementowany | [implemented/SPEC-006-2026-08-12-zgloszenia-na-hackathony.md](implemented/SPEC-006-2026-08-12-zgloszenia-na-hackathony.md) |
| SPEC-007 | Audyt ostatniej zmiany statusu zgłoszenia | Zaimplementowany | [implemented/SPEC-007-2026-08-15-audyt-zmiany-statusu-zgloszenia.md](implemented/SPEC-007-2026-08-15-audyt-zmiany-statusu-zgloszenia.md) |
| SPEC-008 | Strategia testów backendu i przepływy E2E | Zaimplementowany | [implemented/SPEC-008-2026-08-16-strategia-testow-backendu-e2e.md](implemented/SPEC-008-2026-08-16-strategia-testow-backendu-e2e.md) |
| SPEC-009 | Frontend uwierzytelniania i routing | Zaimplementowany | [implemented/SPEC-009-2026-08-11-frontend-auth-routing.md](implemented/SPEC-009-2026-08-11-frontend-auth-routing.md) |
| SPEC-010 | Zasoby hackathonu i ręczny przydział | Zaimplementowany | [implemented/SPEC-010-2026-08-20-zasoby-hackathonu.md](implemented/SPEC-010-2026-08-20-zasoby-hackathonu.md) |
| SPEC-011 | Frontend pytań rejestracyjnych i ustawień hackathonu | Zaimplementowany | [implemented/SPEC-011-2026-08-22-frontend-pytan-i-ustawien-hackathonu.md](implemented/SPEC-011-2026-08-22-frontend-pytan-i-ustawien-hackathonu.md) |
| SPEC-013 | Spójny kontrakt błędów API | Zaimplementowany | [implemented/SPEC-013-2026-08-24-spojny-kontrakt-bledow-api.md](implemented/SPEC-013-2026-08-24-spojny-kontrakt-bledow-api.md) |

Zasady utrzymania tego indeksu i współpracy z agentami AI: [AGENTS.md](AGENTS.md).
