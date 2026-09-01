# SPEC-005: Drużyny tworzone podczas zgłoszenia na hackathon

**Status:** Zaimplementowany
**Data:** 2026-08-09
**Autor:** Mateusz Guzowski

## Kontekst / Problem

Zgłoszenie na hackathon zawiera odpowiedzi uczestnika na pytania organizatora. Hackathony mogą
jednak wymagać pracy w drużynach, a wcześniejszy pomysł zarządzania osobnymi członkostwami,
liderem, zaproszeniami oraz zmianami składu nadmiernie komplikował podstawowy zapis.

Potrzebny jest prosty mechanizm, w którym uczestnik podczas wysyłania własnej ankiety może:

- utworzyć drużynę i otrzymać kod dołączenia;
- dołączyć kodem do drużyny utworzonej przez inną osobę;
- wysłać zgłoszenie indywidualne.

Każda osoba nadal wysyła osobne zgłoszenie i może zostać później oceniona niezależnie od
pozostałych członków drużyny.

## Proponowane rozwiązanie

### Model danych

Model `Team` zawiera:

- wewnętrzne `id`, niewystępujące w API;
- publiczne `public_id` UUID;
- `hackathon_id` wskazujące hackathon;
- nazwę o długości do 200 znaków;
- generowany przez backend, globalnie unikalny `join_code` o długości 8 znaków;
- `created_at`.

Nazwa drużyny jest unikalna w obrębie jednego hackathonu przez constraint
`uq_team_hackathon_name`. Ta sama nazwa może wystąpić w różnych hackathonach. Model
`Registration` otrzymuje opcjonalne `team_id`. Członkami drużyny są użytkownicy posiadający
zgłoszenie wskazujące tę drużynę, dlatego nie powstaje osobny model `TeamMembership`.

Relacja ma postać:

```text
Hackathon 1 ─── * Team 1 ─── * Registration * ─── 1 User
```

Usunięcie zgłoszenia usuwa osobę z drużyny. Jeżeli było to ostatnie zgłoszenie przypisane do
drużyny, backend automatycznie usuwa pustą drużynę w tej samej transakcji. Drużyna nie ma lidera,
a w tej wersji nie można jej osobno edytować, usunąć ani zmienić przypisania po utworzeniu
zgłoszenia.

Hackathon posiada flagę `teams_enabled`, domyślnie ustawioną na `true`. Administrator ustawia ją
podczas tworzenia hackathonu, a właściciel może ją później zmienić przez `PATCH`. Wyłączenie
drużyn blokuje nowe operacje tworzenia i dołączania, ale nadal pozwala wysłać zgłoszenie
indywidualne z `team: null`.

### Kontrakt zgłoszenia

Nie powstaje osobny endpoint do tworzenia ani dołączania do drużyny. Operacja jest częścią:

```http
POST /api/hackathons/{hackathon_public_id}/registrations
```

Zgłoszenie indywidualne pomija pole `team` albo przekazuje `null`.

Utworzenie drużyny:

```json
{
  "answers": [
    {
      "question_public_id": "b2af28e1-0673-4fad-a198-9099f90975d8",
      "content": "Odpowiedź uczestnika"
    }
  ],
  "team": {
    "action": "create",
    "name": "Byte Buccaneers"
  }
}
```

Dołączenie do drużyny:

```json
{
  "answers": [
    {
      "question_public_id": "b2af28e1-0673-4fad-a198-9099f90975d8",
      "content": "Odpowiedź uczestnika"
    }
  ],
  "team": {
    "action": "join",
    "join_code": "ABCD1234"
  }
}
```

Pole `action` jest dyskryminatorem unii Pydantic i jednoznacznie wybiera schemat `create` albo
`join`. Nieznane pola są odrzucane. Nazwa jest przycinana z otaczających białych znaków, a kod
dołączenia dodatkowo normalizowany do wielkich liter.

Odpowiedź `201 Created` zawiera zgłoszenie oraz, jeśli wybrano drużynę:

```json
{
  "public_id": "c829e240-5902-4ae8-a05f-72319cfe8bdb",
  "status": "pending",
  "team": {
    "public_id": "ef58b3ec-c82e-489a-b547-e073c24e6ac6",
    "name": "Byte Buccaneers",
    "join_code": "ABCD1234"
  }
}
```

### Reguły biznesowe i transakcje

- Endpoint wymaga poprawnego access tokenu i pobiera użytkownika z zależności FastAPI.
- `user_id`, `hackathon_id`, `team_id`, status oraz kody nie są przyjmowane od klienta.
- Hackathon musi istnieć, nie może być soft-deleted i musi mieć otwarte zapisy.
- Użytkownik może mieć tylko jedno zgłoszenie w danym hackathonie.
- Utworzenie drużyny lub dołączenie kodem wymaga `teams_enabled: true` dla hackathonu.
- Kod musi wskazywać drużynę należącą do hackathonu z URL-a.
- Liczba aktywnych zgłoszeń (`pending` i `accepted`) przypisanych do drużyny musi być mniejsza od
  `max_team_size` hackathonu. Zgłoszenie ze statusem `rejected` zachowuje przypisanie do drużyny
  dla celów historii, ale zwalnia zajmowane miejsce.
- Ponowna zmiana statusu z `rejected` na `accepted` wymaga wolnego miejsca. Backend blokuje rekord
  drużyny, ponownie sprawdza limit i zwraca `TEAM_FULL`, jeżeli miejsce zostało już zajęte.
- Wyszukanie drużyny używa blokady `SELECT ... FOR UPDATE`. Równoczesne próby dołączenia do tej
  samej drużyny są serializowane, dzięki czemu nie przekroczą limitu członków.
- Utworzenie drużyny, odpowiedzi i zgłoszenia korzysta z jednej sesji oraz jednego commitu. Błąd
  dowolnej części powoduje rollback całości i nie pozostawia pustej drużyny.
- Kolizja losowo wygenerowanego `join_code` powoduje ponowienie generowania w savepoincie.
  Po wyczerpaniu limitu prób API zwraca kontrolowany błąd domenowy zamiast surowego błędu bazy.
- Usunięcie ostatniego zgłoszenia blokuje rekord drużyny i usuwa go atomowo, dzięki czemu pusta
  drużyna nie blokuje swojej nazwy na zawsze.

Limit `capacity` hackathonu nie ogranicza liczby wysłanych ankiet. Dotyczy docelowej liczby
przyjętych uczestników i zostanie wyegzekwowany w przyszłym mechanizmie akceptowania zgłoszeń.

### Błędy domenowe

API zwraca stabilny format:

```json
{
  "error_code": "TEAM_FULL",
  "detail": "Team has reached its maximum number of members."
}
```

Obsługiwane przypadki obejmują:

- `REGISTRATION_CLOSED` — `409`;
- `REGISTRATION_ALREADY_EXISTS` — `409`;
- `TEAM_NOT_FOUND` — `404`, również dla kodu należącego do innego hackathonu;
- `TEAM_FULL` — `409`;
- `TEAM_NAME_ALREADY_EXISTS` — `409`;
- `TEAMS_DISABLED` — `409`;
- `TEAM_JOIN_CODE_GENERATION_FAILED` — `503` po wyczerpaniu prób wygenerowania unikalnego kodu;
- `VALIDATION_ERROR` — `422` dla niepoprawnego lub nadmiarowego requestu.

Nieoczekiwane błędy integralności nie są błędnie przedstawiane jako duplikat zgłoszenia.
Constraint wywołujący `IntegrityError` jest rozpoznawany bez zwracania szczegółów bazy klientowi.

### Bezpieczeństwo

- Wszystkie operacje zgłoszenia są chronione przez `get_current_user` i Bearer JWT.
- API nie ujawnia wewnętrznych kluczy głównych ani kluczy obcych.
- Kod jest generowany przez moduł `secrets` z alfabetu pozbawionego niejednoznacznych znaków.
  Przestrzeń 31^8 kodów zapewnia około 40 bitów entropii.
- Wyszukiwanie kodu jest ograniczone jednocześnie kodem i `hackathon_id`; kod z innego wydarzenia
  zwraca taki sam błąd jak kod nieistniejący.
- Kod dołączenia pojawia się wyłącznie w odpowiedzi dla uwierzytelnionego użytkownika
  wysyłającego własne zgłoszenie. Twórca otrzymuje wygenerowany kod, a osoba dołączająca znała go
  już z requestu. W tej wersji nie istnieje publiczna lista drużyn ani endpoint wyszukujący
  drużynę po kodzie.
- Nazwa i kod mają ograniczoną długość, a dodatkowe pola requestu są odrzucane, co zapobiega
  mass assignment.

Rate limiting pozostaje przekrojowym zadaniem dla całego API. Nie jest dodawany wyłącznie do
modułu drużyn; przed produkcyjnym otwarciem API należy ograniczyć częstotliwość endpointów auth
oraz tworzenia zgłoszeń.

### Architektura

Moduł zachowuje podział:

```text
registration router
    → RegistrationService
        → TeamService
            → TeamRepository
                → PostgreSQL
```

`src/teams/` posiada model, schematy, repozytorium, serwis, wyjątki i generator kodów, ale nie ma
routera. Samodzielny router pozwalałby tworzyć osierocone drużyny lub zmieniać skład poza
transakcją zgłoszenia, czego obecny model biznesowy nie przewiduje.

## Zakres

**W zakresie:**

- opcjonalne drużyny w zgłoszeniach;
- tworzenie drużyny i dołączanie kodem w jednym endpointcie ze zgłoszeniem;
- generowanie i normalizacja kodu;
- limit członków na podstawie `max_team_size`;
- blokada współbieżnych prób dołączenia;
- unikalność nazwy w ramach hackathonu;
- atomowy zapis drużyny, zgłoszenia i odpowiedzi;
- automatyczne usuwanie drużyny po usunięciu jej ostatniego zgłoszenia;
- możliwość wyłączenia drużyn dla konkretnego hackathonu;
- ponawianie generowania kodu po kolizji;
- sprawdzenie otwartych zapisów;
- stabilne błędy domenowe;
- migracja Alembic oraz testy jednostkowe i integracyjne;
- odizolowana, nietrwała baza do lokalnych testów backendu.

**Poza zakresem:**

- lider drużyny i osobna tabela członkostw;
- zaproszenia przypisane do konkretnego użytkownika;
- ręczne opuszczanie, zmiana i usuwanie drużyny;
- osobny router lub CRUD drużyn;
- lista drużyn i widok ich członków dla organizatora;
- akceptowanie i odrzucanie zgłoszeń;
- egzekwowanie `capacity` przed akceptacją;
- sortowanie zgłoszeń według drużyn;
- frontend;
- rate limiting całego API.

## Wpływ

- **Frontend:** formularz zgłoszenia może pominąć drużynę, wysłać nazwę nowej drużyny albo kod
  istniejącej. Po utworzeniu powinien pokazać użytkownikowi zwrócony `join_code`.
- **Backend:** dodany moduł `src/teams/`; `RegistrationService` deleguje obsługę drużyny do
  `TeamService`; błędy drużyn są mapowane na JSON przez handler FastAPI.
- **Baza danych:** migracja `3cae343ea484` tworzy tabelę `teams`, indeksy i opcjonalny klucz
  `registrations.team_id`, a migracja `0010` dodaje flagę `hackathons.teams_enabled`. Migracje
  przechodzą pełny cykl upgrade/downgrade/upgrade.
- **Testy:** osobne testy serwisu drużyn oraz testy jednostkowe i integracyjne całego przepływu
  zgłoszenia. Lokalne testy Docker korzystają z osobnego PostgreSQL w `tmpfs`.

## Alternatywy rozważane

- **`TeamMembership` i lider drużyny** — odrzucone jako zbędne dla składu wynikającego ze
  zgłoszeń uczestników.
- **Osobne endpointy `POST /teams` i `POST /teams/join`** — odrzucone, ponieważ umożliwiałyby
  drużyny bez zgłoszeń i wymagały dodatkowej synchronizacji transakcji.
- **Dołączanie po samej nazwie** — odrzucone ze względu na literówki, możliwość podszycia się pod
  zespół oraz trudniejszy komunikat dla użytkownika.
- **Akceptowanie całej drużyny jednocześnie** — odłożone; w tej wersji organizator ocenia każde
  zgłoszenie niezależnie.

## Changelog

- 2026-08-09 — uzgodniono uproszczony model bez lidera i osobnych członkostw.
- 2026-08-09 — dodano model, migrację, schematy, repozytorium i serwis drużyn.
- 2026-08-09 — zintegrowano wybór drużyny z atomowym tworzeniem zgłoszenia.
- 2026-08-09 — dodano blokadę limitu członków, obsługę błędów i testy bezpieczeństwa.
- 2026-08-09 — zweryfikowano pełny cykl migracji i odizolowano lokalną bazę testową.
- 2026-08-17 — dodano retry kolizji kodu, automatyczne sprzątanie pustych drużyn, filtrowanie
  zgłoszeń soft-deleted hackathonów i przełącznik `teams_enabled`.
