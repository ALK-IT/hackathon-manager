# SPEC-013: Zadania hackathonu i rozwiązania drużyn

**Status:** Zaakceptowany  
**Data:** 2026-09-03

## Kontekst / problem

Zaakceptowany uczestnik może wejść do strefy hackathonu i zobaczyć swoją drużynę, ale nie ma tam jeszcze opisu wydarzenia, zadań ani możliwości przesłania rozwiązania. Organizator potrzebuje również miejsca do tworzenia zadań i przeglądania oddanych linków.

## Rozwiązanie

- Każde zadanie otrzymuje własne `visible_from`. Zadanie jest widoczne dla uczestników od tej chwili; przy pominięciu pola API używa `start_date` hackathonu.
- Organizator, współorganizator lub administrator może tworzyć, edytować i usuwać zadania hackathonu.
- Wszystkie zadania są niezależne i mogą być rozwiązywane w dowolnej kolejności.
- Każda drużyna może posiadać jedno rozwiązanie dla danego zadania.
- Rozwiązaniem jest link do repozytorium w domenie `github.com`.
- Każdy zaakceptowany członek drużyny może utworzyć albo zmienić wspólne rozwiązanie. Check-in nie jest wymagany.
- Osoba wysyłająca ostatnią wersję rozwiązania jest zapisywana w `submitted_by_id`.
- Organizatorzy mogą pobrać listę rozwiązań dla konkretnego zadania.

## Zakres

### Wchodzi w zakres

- modele `HackathonTask` i `TaskSubmission`;
- unikalność rozwiązania dla pary `(task_id, team_id)`;
- CRUD zadań dla osób zarządzających hackathonem;
- upsert rozwiązania przez `PUT`;
- opis hackathonu, zadania i aktualne rozwiązania w strefie uczestnika;
- frontend strefy uczestnika z formularzem linku dla każdego zadania;
- testy backendu i frontendu.

### Nie wchodzi w zakres

- ocenianie i punktowanie rozwiązań;
- kolejność lub zależności między zadaniami;
- historia wersji linku;
- integracja z API GitHuba i sprawdzanie istnienia repozytorium;
- blokowanie wysyłki na podstawie obecności/check-inu;
- rozwiązania indywidualne dla uczestników bez drużyny.

## Kontrakt API

- `GET /api/hackathons/{hackathon_public_id}/tasks` — lista zadań; zarządzający widzą wszystkie, a zaakceptowani uczestnicy tylko już opublikowane.
- `POST /api/hackathons/{hackathon_public_id}/tasks` — utworzenie zadania.
- `PATCH /api/hackathons/{hackathon_public_id}/tasks/{task_public_id}` — edycja zadania.
- `DELETE /api/hackathons/{hackathon_public_id}/tasks/{task_public_id}` — usunięcie zadania.
- `PUT /api/hackathons/{hackathon_public_id}/tasks/{task_public_id}/submission` — utworzenie albo zmiana rozwiązania drużyny.
- `GET /api/hackathons/{hackathon_public_id}/tasks/{task_public_id}/submissions` — lista rozwiązań dla zarządzających.
- `GET /api/hackathons/{hackathon_public_id}/participant-area` — rozszerzona odpowiedź z opisem hackathonu, terminami, drużyną i opublikowanymi zadaniami.

## Wpływ na backend

- nowe tabele, relacje ORM i migracja Alembic;
- nowe schematy, repozytorium, serwis, zależność i router dla zadań;
- termin publikacji `visible_from` w modelu i schematach zadania;
- rozszerzenie strefy uczestnika;
- zapis rozwiązania jest wykonywany transakcyjnie, z blokadą drużyny i ograniczeniem unikalności w bazie jako zabezpieczeniem przed race condition.

## Wpływ na frontend

- strefa uczestnika wyświetla opis hackathonu i opublikowane zadania;
- widok zarządzania hackathonem pozwala dodać zadanie wraz z terminem publikacji;
- przy każdym zadaniu członek drużyny widzi aktualny link oraz może go utworzyć albo zmienić;
- uczestnik bez drużyny widzi zadania, ale nie formularz wysyłki.

## Alternatywy

- Jedno wspólne repozytorium na cały hackathon — odrzucone, ponieważ osobny link dla każdego zadania jest czytelniejszy.
- Rozwiązanie per uczestnik — odrzucone, ponieważ rozwiązanie należy do drużyny.
- Wymaganie aktywnego check-inu — odrzucone; obecność służy do potwierdzania fizycznego udziału i wydawania zasobów.
