# SPEC-004: CRUD hackathonów i kontekstowe uprawnienia organizatorów

**Status:** Zaimplementowany
**Data:** 2026-08-03
**Autor:** Codex

## Kontekst / Problem

Dotychczasowy moduł hackathonów był wyłącznie przykładowym szkieletem. Model zawierał tylko
wewnętrzne `id` i nazwę, a jedyny endpoint zwracał wszystkim użytkownikom tę samą listę
przechowywaną pod jednym kluczem w Redisie. Nie było możliwości tworzenia, pobierania
szczegółów, edytowania ani usuwania wydarzeń. Brakowało również właściciela, identyfikatorów
publicznych, walidacji, autoryzacji i stabilnego kontraktu błędów.

Projekt potrzebuje kompletnego CRUD-u, który nie ujawnia wewnętrznych identyfikatorów bazy,
rozróżnia właściciela i współorganizatorów oraz chroni każdą operację access tokenem JWT.

## Proponowane rozwiązanie

### Model danych

Model `Hackathon` zawiera:

- wewnętrzne `id`, które nie jest zwracane przez API;
- unikalne `public_id` UUID używane w URL-ach i odpowiedziach;
- `organizer_id` wskazujące jednego właściciela wydarzenia;
- `name`, `description`, `start_date` i `end_date`;
- `registration_open`, `capacity` i `max_team_size`;
- pola soft-delete: `is_deleted` i `deleted_at`;
- `created_at` oraz automatycznie aktualizowane `updated_at`;
- relację wielu współorganizatorów przez tabelę `hackathon_co_organizers`.

Właścicielem zostaje administrator tworzący wydarzenie. Identyfikator właściciela jest pobierany
z użytkownika rozpoznanego na podstawie JWT i nigdy nie jest przyjmowany z requestu. Zarówno
użytkownik z rolą `USER`, jak i `ADMIN` może w przyszłości zostać współorganizatorem.

Baza danych oraz schematy Pydantic egzekwują:

- niepustą nazwę;
- daty zawierające strefę czasową;
- `end_date > start_date`;
- dodatnie `capacity`, jeżeli limit został podany;
- dodatnie `max_team_size`;
- `max_team_size <= capacity`, jeżeli wydarzenie ma limit uczestników.

### Uprawnienia

- Wszystkie endpointy hackathonów wymagają poprawnego access tokenu.
- Tylko użytkownik z rolą `ADMIN` może utworzyć hackathon.
- Właściciel widzi wydarzenie i może je edytować, usunąć oraz otworzyć lub zamknąć zapisy.
- Współorganizator widzi wydarzenie, ale nie może zmieniać jego konfiguracji.
- Użytkownik niezwiązany z wydarzeniem otrzymuje `404 HACKATHON_NOT_FOUND` przy próbie odczytu.
- Soft-deleted hackathony są pomijane przez wszystkie zwykłe zapytania.

Lista `GET /api/hackathons` zawiera wydarzenia, których zalogowany użytkownik jest właścicielem
lub współorganizatorem. Pole odpowiedzi `access_level` (`owner` albo `co_organizer`) pozwala
frontendowi dopasować interfejs bez zwracania globalnej roli przez `/api/auth/me`.

### Endpointy

- `GET /api/hackathons` — lista dostępnych wydarzeń.
- `POST /api/hackathons` — utworzenie wydarzenia, wyłącznie przez administratora.
- `GET /api/hackathons/{public_id}` — prywatne szczegóły dla właściciela lub współorganizatora.
- `PATCH /api/hackathons/{public_id}` — częściowa edycja przez właściciela.
- `DELETE /api/hackathons/{public_id}` — soft-delete przez właściciela.
- `POST /api/hackathons/{public_id}/open-registration` — otwarcie zapisów.
- `POST /api/hackathons/{public_id}/close-registration` — zamknięcie zapisów.

Publiczny endpoint pod `/api/public/hackathons` świadomie nie jest częścią tej wersji.

Usuwanie wymaga requestu z dokładną nazwą wydarzenia:

```json
{
  "confirm_name": "Hackathon AI"
}
```

Poprawne usunięcie zwraca `204 No Content`. Rekord pozostaje w bazie z `is_deleted=True` oraz
czasem w `deleted_at`.

Otwieranie i zamykanie rejestracji odbywa się przez osobne endpointy zamiast pola dostępnego w
`PATCH`. Pozwala to później bez zmiany kontraktu uruchomić logikę grupowania uczestników przy
zamknięciu zapisów.

### Kontrakty wejścia i odpowiedzi

Zastosowane schematy Pydantic:

- `HackathonCreate`;
- `HackathonUpdate`;
- `HackathonDeleteRequest`;
- `HackathonListItem`;
- `HackathonRead`;
- `HackathonRegistrationStateRead`;
- `UserSummary`.

Schematy requestów zabraniają dodatkowych pól przez `extra="forbid"`. Klient nie może ustawiać
`public_id`, właściciela, współorganizatorów, stanu soft-delete ani pól czasowych zarządzanych
przez backend. `capacity: null` usuwa limit uczestników, natomiast pozostałe pola modelu nie mogą
zostać ustawione na `null`.

Odpowiedzi nie ujawniają wewnętrznych `id` ani `organizer_id`. Organizator i współorganizatorzy
są reprezentowani przez `public_id` oraz nazwę.

Błędy domenowe mają stabilne pola:

```json
{
  "error_code": "HACKATHON_NOT_FOUND",
  "detail": "Hackathon does not exist or you do not have access to it."
}
```

Walidacja requestu zwraca `VALIDATION_ERROR` wraz z listą błędnych pól. Pozostałe kody obejmują
m.in. `ADMIN_REQUIRED`, `INVALID_DATE_RANGE`, `INVALID_TEAM_SIZE`,
`INVALID_CONFIRM_NAME`, `REGISTRATION_ALREADY_OPEN` i `REGISTRATION_ALREADY_CLOSED`.

Operacje dostępne wyłącznie właścicielowi wyszukują wydarzenie jednocześnie po `public_id`,
`organizer_id` i stanie soft-delete. Nieistniejący, usunięty oraz należący do innej osoby
hackathon zwracają ten sam błąd `HACKATHON_NOT_FOUND`. Zapobiega to wykorzystywaniu odpowiedzi
`403` i `404` do sprawdzania, czy cudzy UUID wskazuje istniejący zasób.

### Architektura

Moduł zachowuje przepływ:

```text
router → service → repository → PostgreSQL
```

- Router odpowiada za HTTP, zależności FastAPI i mapowanie modeli na schematy odpowiedzi.
- Service zawiera logikę biznesową, zleca lookup ograniczony do właściciela i zmienia stan
  wydarzenia.
- Repository jest jedyną warstwą wykonującą zapytania SQLAlchemy.
- Relacje organizatora i współorganizatorów są pobierane przez `selectinload`, co zapobiega N+1
  oraz próbom niejawnego wykonywania zapytań podczas serializacji async.

## Decyzja dotycząca cache

Cache listy hackathonów z `SPEC-002` został świadomie usunięty z tego endpointu. Stary klucz
`hackathons:list` był wspólny dla wszystkich użytkowników, natomiast nowa lista zależy od tego,
czy użytkownik jest właścicielem lub współorganizatorem. Pozostawienie wspólnego klucza mogłoby
zwrócić jednej osobie dane przeznaczone dla innej.

Bezpieczny cache wymagałby osobnego klucza, np.:

```text
hackathons:list:user:{user_public_id}
```

oraz invalidacji cache wszystkich powiązanych osób po:

- utworzeniu, edycji lub usunięciu hackathonu;
- otwarciu albo zamknięciu rejestracji;
- dodaniu lub usunięciu współorganizatora.

Przy zakładanej skali i niewielkiej liczbie wydarzeń na użytkownika indeksowane zapytanie do
PostgreSQL jest wystarczające. Dodanie cache teraz zwiększyłoby złożoność, uzależniło podstawowy
odczyt od dostępności Redisa i stworzyło ryzyko zwracania nieaktualnych uprawnień. Redis pozostaje
w projekcie i może zostać wykorzystany później dla danych wspólnych dla wielu odbiorców, np.
publicznej listy wydarzeń albo często odpytywanych statystyk.

Decyzja może zostać zmieniona po wykonaniu pomiarów wydajności. Wtedy należy zastosować
cache-aside z kluczami per użytkownik oraz centralną invalidacją po udanym commicie bazy.

## Zakres

**W zakresie:**

- pełny prywatny CRUD hackathonu;
- model właściciela i tabela współorganizatorów;
- tworzenie wyłącznie przez administratora;
- odczyt właściciela i współorganizatorów;
- soft-delete potwierdzany nazwą;
- otwieranie i zamykanie rejestracji;
- walidacja Pydantic i constrainty PostgreSQL;
- stabilny format błędów;
- migracja Alembic `0004`;
- testy schematów, serwisu, uprawnień i kontraktów HTTP.

**Poza zakresem:**

- publiczna lista i publiczne szczegóły hackathonów;
- endpointy dodawania oraz usuwania współorganizatorów;
- zgłoszenia uczestników i ich przeglądanie przez współorganizatorów;
- przywracanie soft-deleted wydarzeń;
- automatyczna retencja danych;
- paginacja, wyszukiwanie i filtrowanie listy;
- cache listy hackathonów;
- zmiany we frontendzie.

## Wpływ

- **Frontend:** bez zmian w tej implementacji; dostępny jest nowy kontrakt API z `public_id` i
  `access_level`.
- **Backend:** rozbudowane moduły `src/hackathons/`, relacje w `src/auth/models.py`, obsługa
  stabilnych błędów w `src/main.py` oraz usunięcie starej logiki cache z modułu hackathonów.
- **Baza danych:** migracja `0004` rozbudowuje `hackathons`, dodaje constrainty, indeksy i tabelę
  `hackathon_co_organizers`. Usuwa trzy demonstracyjne rekordy z `0001`, ponieważ nie miały
  właściciela i nie mogą istnieć w nowym modelu.
- **Testy:** osobne pliki dla endpointów, serwisu i repozytorium w `tests/hackathons/`,
  korzystające ze współdzielonych fixtures i fabryk danych testowych. Testy obejmują także
  rzeczywiste zapytania repozytorium do odizolowanej bazy PostgreSQL.

## Alternatywy rozważane

- **Jeden globalny cache listy** — odrzucony ze względu na możliwość ujawnienia cudzych danych.
- **Cache per użytkownik od razu** — odłożony do czasu pomiarów; wymaga złożonej invalidacji.
- **Hard-delete** — odrzucony na rzecz przywracalnego soft-delete.
- **Wewnętrzne `id` w API** — odrzucone na rzecz publicznego UUID.
- **Globalna rola `ORGANIZER`** — odrzucona; `ADMIN` daje możliwość tworzenia, a właściciel i
  współorganizator są rolami zależnymi od konkretnego wydarzenia.
- **Zmiana `registration_open` przez `PATCH`** — odrzucona na rzecz jawnych operacji domenowych.

## Changelog

- 2026-08-03 — uzgodniono model, endpointy, uprawnienia i kontrakty request/response.
- 2026-08-03 — zaimplementowano CRUD, soft-delete, stan rejestracji i współorganizatorów.
- 2026-08-03 — usunięto cache prywatnej listy i udokumentowano warunki jego przyszłego dodania.
- 2026-08-03 — migracje sprawdzono przez upgrade/downgrade, a CRUD przetestowano integracyjnie
  na odizolowanej bazie PostgreSQL.
- 2026-08-05 — po rebase uporządkowano testy zgodnie ze strukturą modułu auth i dodano testy
  repozytorium, widoczności, soft-delete oraz pełnego kontraktu endpointów.
- 2026-08-10 — operacje właściciela ujednolicono do `404` dla zasobów nieistniejących,
  usuniętych i należących do innego użytkownika, aby nie ujawniać ich istnienia.
