# SPEC-004: CRUD hackathonów i kontekstowe uprawnienia organizatorów

**Status:** Zaimplementowany
**Data:** 2026-08-03
**Autor:** Mateusz Guzowski

## Kontekst / Problem

Dotychczasowy moduł hackathonów był wyłącznie przykładowym szkieletem. Model zawierał tylko
wewnętrzne `id` i nazwę, a jedyny endpoint zwracał wszystkim użytkownikom tę samą listę
przechowywaną pod jednym kluczem w Redisie. Nie było możliwości tworzenia, pobierania
szczegółów, edytowania ani usuwania wydarzeń. Brakowało również właściciela, identyfikatorów
publicznych, walidacji, autoryzacji i stabilnego kontraktu błędów.

Projekt potrzebuje kompletnego CRUD-u, który nie ujawnia wewnętrznych identyfikatorów bazy,
rozróżnia właściciela i współorganizatorów, publicznie udostępnia katalog wydarzeń i chroni
operacje zarządzania access tokenem JWT.

## Proponowane rozwiązanie

### Model danych

Model `Hackathon` zawiera:

- wewnętrzne `id`, które nie jest zwracane przez API;
- unikalne `public_id` UUID używane w URL-ach i odpowiedziach;
- `organizer_id` wskazujące jednego właściciela wydarzenia;
- `name`, `description`, `start_date` i `end_date`;
- `registration_open`, `registration_opens_at`, `registration_deadline`, `capacity` i
  `max_team_size`;
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
- `registration_opens_at < registration_deadline < start_date`.

Jeżeli administrator nie poda `registration_deadline` podczas tworzenia, backend wylicza go jako
`start_date - 48 godzin`. `registration_opens_at` jest wymagane przy tworzeniu; frontend może
ustawić wybraną datę albo użyć przycisku „Teraz”, który wysyła bieżący czas. Administrator może
ustawić okno zapisów w `POST`, a właściciel hackathonu może je później zmienić przez `PATCH`,
niezależnie od swojej aktualnej globalnej roli. Współorganizator nie może zmieniać terminów.

### Uprawnienia

- Lista aktywnych hackathonów i szczegóły pojedynczego wydarzenia są dostępne bez logowania.
- Jeżeli publiczny odczyt otrzyma token, musi on być poprawny; token nieprawidłowy lub wygasły
  zwraca `401` zamiast traktowania żądania jak anonimowe.
- Tylko użytkownik z rolą `ADMIN` może utworzyć hackathon.
- Każdy użytkownik, również niezalogowany, widzi wydarzenia z otwartymi zapisami i może pobrać
  szczegóły nieusuniętego wydarzenia po jego `public_id`.
- Właściciel może edytować wydarzenie, usunąć je oraz otworzyć lub zamknąć zapisy.
- Współorganizator może znaleźć wydarzenie na liście zarządzanych, ale nie może zmieniać jego
  konfiguracji.
- Soft-deleted hackathony są pomijane przez wszystkie zwykłe zapytania.

Lista `GET /api/hackathons` zawiera nieusunięte wydarzenia, których zapisy są aktualnie otwarte:
flaga ręczna jest włączona oraz aktualny czas mieści się pomiędzy `registration_opens_at` i
`registration_deadline`. Anonimowy odbiorca otrzymuje
`access_level: viewer`; dla zalogowanej osoby poziom jest wyliczany na podstawie jej relacji z
wydarzeniem. Osobna lista
`GET /api/hackathons/managed` zawiera wydarzenia, których zalogowany użytkownik jest właścicielem
lub współorganizatorem. Pole odpowiedzi `access_level` (`owner`, `co_organizer` albo `viewer`)
pozwala frontendowi dopasować interfejs bez zwracania globalnej roli przez `/api/auth/me`.

### Endpointy

- `GET /api/hackathons` — publiczna lista wydarzeń z aktualnie otwartymi zapisami.
- `GET /api/hackathons/managed` — lista wydarzeń zarządzanych jako właściciel lub
  współorganizator.
- `POST /api/hackathons` — utworzenie wydarzenia, wyłącznie przez administratora.
- `GET /api/hackathons/{public_id}` — publiczne szczegóły aktywnego wydarzenia.
- `PATCH /api/hackathons/{public_id}` — częściowa edycja przez właściciela.
- `DELETE /api/hackathons/{public_id}` — soft-delete przez właściciela.
- `POST /api/hackathons/{public_id}/open-registration` — otwarcie zapisów.
- `POST /api/hackathons/{public_id}/close-registration` — zamknięcie zapisów.

Nie powstaje osobny prefiks `/api/public`. Publiczny odczyt korzysta z tych samych adresów co
odczyt uwierzytelniony, dzięki czemu klient ma jeden kontrakt odpowiedzi.

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
zamknięciu zapisów. Zapisy otwierają się automatycznie po osiągnięciu `registration_opens_at` i
zamykają po osiągnięciu `registration_deadline`. Odpowiedzi poza tym oknem zwracają
`registration_open: false`, nawet jeżeli techniczna flaga w bazie nadal ma wartość `true`.
Właściciel nie może ponownie otworzyć zapisów po terminie (`REGISTRATION_DEADLINE_PASSED`).
Ręczne `open-registration` ustawia `registration_opens_at` na aktualny czas, natomiast
`close-registration` wyłącza zapisy. Zmiana `registration_opens_at` przez PATCH ponownie włącza
zaplanowane zapisy.
Nie jest wymagany scheduler: stan jest obliczany i egzekwowany na podstawie aktualnego czasu.
Przyszły endpoint tworzenia zgłoszenia musi użyć tej samej walidacji domenowej.

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
przez backend. Klient podaje `registration_opens_at` i może podać `registration_deadline` przy
tworzeniu lub edycji. Oba terminy muszą zawierać strefę czasową i tworzyć poprawne okno przed
rozpoczęciem wydarzenia. `capacity: null` usuwa limit uczestników, natomiast pozostałe pola
modelu nie mogą zostać ustawione na `null`.

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

Cache listy hackathonów z `SPEC-002` został świadomie usunięty z tego endpointu. Zestaw wydarzeń
z otwartymi zapisami jest wspólny dla wszystkich użytkowników, ale pole `access_level` nadal zależy od
konkretnej zalogowanej osoby (anonimowo zawsze ma wartość `viewer`), a lista `/managed` jest w
całości zależna od jej uprawnień. Cache gotowych
odpowiedzi pod jednym kluczem mógłby zwrócić nieprawidłowy poziom dostępu.

Bezpieczny cache wymagałby osobnego klucza, np.:

```text
hackathons:list:user:{user_public_id}
```

oraz invalidacji cache wszystkich powiązanych osób po:

- utworzeniu, edycji lub usunięciu hackathonu;
- otwarciu albo zamknięciu rejestracji;
- zmianie terminu zamknięcia zapisów;
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

- pełny CRUD hackathonu z publicznym katalogiem i publicznymi szczegółami;
- model właściciela i tabela współorganizatorów;
- tworzenie wyłącznie przez administratora;
- odczyt hackathonów z aktualnie otwartymi zapisami oraz osobna lista zarządzanych wydarzeń;
- poziomy dostępu `owner`, `co_organizer` i `viewer`;
- soft-delete potwierdzany nazwą;
- otwieranie i zamykanie rejestracji;
- automatyczne, konfigurowalne okno zapisów z domyślnym zamknięciem 48 godzin przed wydarzeniem;
- walidacja Pydantic i constrainty PostgreSQL;
- stabilny format błędów;
- migracje Alembic `0004`, `0005` i `0006`;
- testy schematów, serwisu, uprawnień i kontraktów HTTP.

**Poza zakresem:**

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
  właściciela i nie mogą istnieć w nowym modelu. Migracja `0005` dodaje
  `registration_deadline`, uzupełnia istniejące rekordy wartością 48 godzin przed startem i
  dodaje constraint chroniący kolejność dat. Migracja `0006` dodaje `registration_opens_at`,
  bezpiecznie uzupełnia istniejące rekordy i dodaje constraint całego okna zapisów.
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
- **Okresowe zadanie zamykające zapisy** — nie jest wymagane do zapewnienia poprawności;
  deadline jest sprawdzany przy każdej operacji, więc awaria schedulera nie otworzy zapisów po
  terminie.

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
- 2026-08-11 — katalog i szczegóły udostępniono wszystkim zalogowanym użytkownikom, dodano
  poziom `viewer` oraz osobny endpoint `/api/hackathons/managed`.
- 2026-08-11 — katalog i szczegóły udostępniono również bez logowania; opcjonalny, ale
  nieprawidłowy token nadal zwraca `401`.
- 2026-08-11 — dodano konfigurowalny `registration_deadline`, domyślnie 48 godzin przed startem,
  automatyczne obliczanie efektywnego stanu zapisów oraz migrację `0005`.
- 2026-08-11 — dodano `registration_opens_at`, automatyczne otwieranie zapisów, ręczne „otwórz
  teraz”, filtrowanie publicznej listy według bieżącego okna oraz migrację `0006`.
