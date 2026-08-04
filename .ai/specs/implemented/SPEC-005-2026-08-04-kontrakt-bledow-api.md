# SPEC-005: Walidacja wejścia i spójny kontrakt błędów API

**Status:** Zaakceptowany
**Data:** 2026-08-04
**Autor:** matyyy12,
**Powiązane issue:** #43, #24

## Kontekst / Problem

Backend zwraca obecnie kilka różnych formatów błędów. Moduł hackathonów ma własne wyjątki
domenowe i handler zwracający `error_code`, natomiast auth nadal korzysta bezpośrednio z
`HTTPException` i zwraca wyłącznie pole `detail`. Domyślne błędy FastAPI, nieistniejące ścieżki,
nieobsługiwane metody oraz nieoczekiwane wyjątki również nie mają jednego kontraktu.

Frontend nie powinien podejmować decyzji przez porównywanie tekstu komunikatu, ponieważ tekst
może zostać poprawiony albo przetłumaczony. Potrzebuje stabilnego, maszynowo czytelnego
`error_code`, właściwego statusu HTTP i osobnego komunikatu przeznaczonego dla człowieka.

Na branchu istnieje częściowa implementacja dla CRUD-u hackathonów. Ten spec zastępuje ją
mechanizmem wspólnym dla całej aplikacji i ustala kontrakt dla przyszłych modułów rejestracji,
drużyn, zasobów oraz uprawnień.

## Proponowane rozwiązanie

### Podstawowy format odpowiedzi

Każdy błąd zwracany przez API ma przynajmniej dwa pola:

```json
{
  "error_code": "TEAM_FULL",
  "detail": "Team has reached its maximum size."
}
```

- `error_code` jest stabilnym identyfikatorem używanym przez frontend;
- `detail` jest komunikatem dla człowieka i może zostać później zmieniony lub przetłumaczony;
- klient nie może opierać logiki na treści `detail`;
- odpowiedź nie zawiera tracebacka, treści zapytania, tokenu, hasła ani szczegółów bazy danych.

### Błędy walidacji

Błędy walidacji Pydantic zachowują status `422 Unprocessable Entity` i mają rozszerzony format:

```json
{
  "error_code": "VALIDATION_ERROR",
  "detail": "Request validation failed.",
  "errors": [
    {
      "location": ["body", "max_team_size"],
      "message": "Input should be greater than or equal to 1",
      "type": "greater_than_equal"
    }
  ]
}
```

`location` pozostaje listą zamiast pojedynczego pola `field`, ponieważ może jednoznacznie
opisać błędy zagnieżdżonych obiektów, elementów listy, parametrów ścieżki, query i body. Frontend
może użyć ostatniego elementu jako nazwy prostego pola formularza.

Do odpowiedzi nie są kopiowane wartości wejściowe zwracane przez Pydantic w polu `input`, aby
przypadkowo nie odesłać ani nie zalogować hasła lub innej poufnej wartości.

### Wspólny wyjątek aplikacyjny

Powstaje wspólny moduł `src/errors.py` zawierający:

- bazową klasę `APIError`;
- typy odpowiedzi `ErrorResponse`, `ValidationErrorResponse` i `ValidationErrorItem`;
- katalog stabilnych kodów `ErrorCode`;
- handlery FastAPI dla błędów aplikacyjnych, walidacji, `HTTPException` i nieoczekiwanych
  wyjątków.

`APIError` przechowuje:

- `status_code`;
- `error_code`;
- domyślny `detail`, który może zostać bezpiecznie zastąpiony w konkretnej sytuacji.

Moduły domenowe mogą definiować czytelne podklasy, np. `TeamFullError(APIError)`, ale wszystkie
dziedziczą po wspólnej klasie. Router nie przechwytuje każdego wyjątku osobnym `try/except`.
Service zgłasza błąd domenowy, a globalny handler mapuje go na odpowiedź HTTP.

Istniejące `HackathonError` zostaje zastąpione lub zmienione tak, aby dziedziczyło po
`APIError`. Wyjątki auth również przechodzą na wspólny mechanizm. `HTTPException` pozostaje
obsługiwane dla wyjątków generowanych wewnętrznie przez FastAPI i Starlette, ale aplikacyjna
logika biznesowa nie powinna używać go bezpośrednio.

### Katalog kodów i statusów HTTP

Pierwsza wersja katalogu obejmuje aktualne błędy oraz kody zarezerwowane w issue #43 dla
następnych modułów:

| `error_code` | HTTP | Znaczenie |
|---|---:|---|
| `BAD_REQUEST` | 400 | Niepoprawne żądanie bez dokładniejszego kodu domenowego |
| `INVALID_CONFIRM_NAME` | 400 | Niepoprawna nazwa potwierdzająca operację |
| `INVALID_QR_TOKEN` | 400 | Niepoprawny lub uszkodzony token QR |
| `AUTHENTICATION_REQUIRED` | 401 | Brak, wygaśnięcie albo niepoprawny access token |
| `INVALID_CREDENTIALS` | 401 | Niepoprawny e-mail lub hasło |
| `PERMISSION_DENIED` | 403 | Zalogowany użytkownik nie ma wymaganych uprawnień |
| `ADMIN_REQUIRED` | 403 | Operacja jest dostępna wyłącznie dla administratora |
| `NOT_TEAM_MEMBER` | 403 | Użytkownik nie należy do wymaganej drużyny |
| `RESOURCE_NOT_ASSIGNED_TO_USER` | 403 | Zasób nie jest przypisany do użytkownika lub jego drużyny |
| `NOT_FOUND` | 404 | Nieznana ścieżka albo zasób bez dokładniejszego kodu |
| `HACKATHON_NOT_FOUND` | 404 | Hackathon nie istnieje lub nie jest widoczny dla użytkownika |
| `METHOD_NOT_ALLOWED` | 405 | Metoda HTTP nie jest obsługiwana dla ścieżki |
| `EMAIL_ALREADY_REGISTERED` | 409 | Konto z podanym adresem już istnieje |
| `REGISTRATION_CLOSED` | 409 | Rejestracja na hackathon jest zamknięta |
| `CAPACITY_FULL` | 409 | Brak wolnych miejsc na hackathonie |
| `ALREADY_REGISTERED` | 409 | Użytkownik jest już zarejestrowany |
| `TEAM_FULL` | 409 | Drużyna osiągnęła limit członków |
| `TEAM_NAME_TAKEN` | 409 | Nazwa drużyny jest już zajęta w danym hackathonie |
| `TEAM_CONFIRMATION_REQUIRED` | 409 | Dołączenie wymaga potwierdzenia wybranej drużyny |
| `RESOURCE_ALREADY_ASSIGNED` | 409 | Zasób został już przydzielony |
| `RESOURCE_REVOKED` | 409 | Zasób został cofnięty i nie może zostać odsłonięty |
| `REGISTRATION_ALREADY_OPEN` | 409 | Rejestracja jest już otwarta |
| `REGISTRATION_ALREADY_CLOSED` | 409 | Rejestracja jest już zamknięta |
| `VALIDATION_ERROR` | 422 | Walidacja requestu lub reguły danych nie powiodła się |
| `CONSENT_REQUIRED` | 422 | Wymagana zgoda uczestnika nie została udzielona |
| `INVALID_DATE_RANGE` | 422 | Zakres dat jest niepoprawny |
| `INVALID_TEAM_SIZE` | 422 | Rozmiar drużyny jest niepoprawny |
| `INTERNAL_ERROR` | 500 | Nieoczekiwany błąd backendu |

Kody dotyczące modułów, które jeszcze nie istnieją, są na tym etapie zarezerwowanym kontraktem.
Handler i bazowa klasa obsługują je od razu, natomiast konkretne miejsca ich zgłaszania oraz
testy ścieżek domenowych powstaną razem z odpowiednimi funkcjonalnościami.

Status HTTP opisuje ogólną kategorię wyniku, a `error_code` dokładny powód. W szczególności:

- `401` oznacza brak poprawnego uwierzytelnienia;
- `403` oznacza poprawnie rozpoznanego użytkownika bez uprawnienia do operacji;
- `404` może celowo ukrywać istnienie zasobu przed obcym użytkownikiem;
- `409` oznacza konflikt z aktualnym stanem zasobu;
- `422` oznacza dane, których nie można zaakceptować.

### Błędy generowane przez FastAPI i Starlette

Globalny handler `HTTPException` normalizuje również błędy, których nie zgłasza bezpośrednio
service:

- brak tokenu z `OAuth2PasswordBearer` → `401 AUTHENTICATION_REQUIRED`;
- nieznana ścieżka → `404 NOT_FOUND`;
- nieobsługiwana metoda → `405 METHOD_NOT_ALLOWED`;
- inne znane statusy otrzymują bezpieczny kod ogólny.

Jeżeli `detail` dostarczone przez framework nie jest bezpiecznym tekstem, klient otrzymuje
ustalony komunikat ogólny. Nagłówki wymagane przez protokół, np. `WWW-Authenticate` dla `401`,
są zachowywane.

### Nieoczekiwane błędy i logowanie

Nieobsłużony wyjątek zwraca:

```json
{
  "error_code": "INTERNAL_ERROR",
  "detail": "An unexpected error occurred."
}
```

Pełny wyjątek jest logowany po stronie backendu przez `logger.exception`, ale nigdy nie trafia
do odpowiedzi API. Oczekiwane błędy domenowe i walidacyjne nie są logowane z tracebackiem.
W logach nie zapisujemy haseł, JWT, refresh cookie, wartości zasobów ani pełnego body requestu.

Format odpowiedzi pozostaje taki sam w środowisku developerskim i produkcyjnym. Tryb lokalny
może zwiększać szczegółowość logów, ale nie zmienia kontraktu wysyłanego klientowi.

### Dokumentacja OpenAPI

Modele `ErrorResponse` i `ValidationErrorResponse` są dostępne w schemacie OpenAPI. Routery
dokumentują wspólne odpowiedzi, szczególnie `401`, `403`, `404`, `409` i `422`, tam gdzie mogą
wystąpić. Nie powielamy pełnej tabeli wszystkich kodów przy każdym endpointcie; jej źródłem
prawdy pozostaje ten spec oraz katalog `ErrorCode` w kodzie.

### Testy

Powstaje wspólny plik testów kontraktu, np. `backend/tests/test_errors.py`. Testy obejmują:

- odpowiedź dla przykładowego `APIError`;
- parametryczne sprawdzenie kodów i odpowiadających im statusów;
- błąd walidacji body, query i parametru ścieżki;
- brak wymaganego pola, dodatkowe pole oraz uszkodzony JSON;
- brak lub niepoprawny access token (`401 AUTHENTICATION_REQUIRED`);
- brak uprawnień (`403 PERMISSION_DENIED`);
- nieznaną ścieżkę (`404 NOT_FOUND`);
- nieobsługiwaną metodę (`405 METHOD_NOT_ALLOWED`);
- nieoczekiwany wyjątek (`500 INTERNAL_ERROR`) bez ujawniania jego treści;
- zachowanie nagłówka `WWW-Authenticate` dla `401`;
- migrację istniejących błędów auth i hackathonów do wspólnego formatu.

Każdy kod faktycznie używany przez istniejący endpoint ma test statusu i ciała odpowiedzi.
Zarezerwowane kody przyszłych modułów otrzymują test wraz z implementacją swojej ścieżki.

## Zakres

**W zakresie:**

- wspólna klasa `APIError` i katalog `ErrorCode`;
- modele Pydantic odpowiedzi błędów;
- globalne handlery błędów domenowych, walidacji, `HTTPException` i błędów 500;
- ujednolicenie istniejących błędów auth i hackathonów;
- zachowanie nagłówków wymaganych dla odpowiedzi `401`;
- stabilny format błędów `404` i `405` generowanych przez framework;
- bezpieczne logowanie nieoczekiwanych wyjątków;
- podstawowa dokumentacja błędów w OpenAPI;
- testy kontraktu dla aktualnie obsługiwanych błędów;
- aktualizacja README lub dokumentacji API, jeżeli będzie potrzebna do wskazania kontraktu.

**Poza zakresem:**

- implementacja endpointów rejestracji uczestników, drużyn, zasobów i QR;
- frontendowe mapowanie `error_code` na polskie komunikaty;
- internacjonalizacja tekstu `detail`;
- rate limiting oraz blokowanie kont;
- zewnętrzny system observability, request ID i centralny audit log;
- szczegółowe przykłady każdego kodu przy każdym endpointcie OpenAPI;
- zmiany w modelach i migracje bazy danych.

## Wpływ

- **Frontend:** otrzymuje jeden stabilny kontrakt i może reagować na `error_code` zamiast
  parsować `detail`. Implementacja UI nie jest częścią tego zadania.
- **Backend:** powstaje wspólne `src/errors.py`; `src/main.py` rejestruje globalne handlery,
  a moduły auth i hackathonów korzystają ze wspólnej klasy błędu.
- **Baza danych:** brak zmian i brak migracji.
- **API:** zmienia się ciało części istniejących odpowiedzi błędów, szczególnie auth oraz
  domyślnych odpowiedzi FastAPI. Statusy HTTP pozostają zgodne ze znaczeniem błędów.
- **Testy:** powstają testy przekrojowe kontraktu i aktualizowane są asercje istniejących
  endpointów.

## Kryteria akceptacji

- Każdy błąd API zwracany przez istniejące endpointy zawiera `error_code` oraz tekstowy `detail`.
- Walidacja Pydantic zwraca `422 VALIDATION_ERROR` z bezpieczną listą `errors`.
- Błędy `401`, `403`, `404` i `405` mają spójny format; `401` zachowuje
  `WWW-Authenticate: Bearer`.
- Istniejące moduły auth i hackathonów używają wspólnego mechanizmu zamiast niezależnych
  formatów.
- Nieoczekiwany wyjątek zwraca `500 INTERNAL_ERROR` bez ujawnienia treści wyjątku.
- OpenAPI zawiera modele wspólnych odpowiedzi błędów.
- Testy kontraktu oraz dotychczasowe testy backendu przechodzą.
- `ruff check .`, `black --check .` i `pytest` są zielone.
- Issue #43 zostaje zamknięte; #24 może zostać zamknięte jako zastąpione pełniejszym kontraktem.

## Alternatywy rozważane

- **RFC 7807 Problem Details** — poprawny standard, ale odrzucony w tej wersji, ponieważ
  istniejąca specyfikacja produktu i frontend oczekują prostego `{error_code, detail}`.
- **Bezpośrednie `HTTPException` w routerach** — odrzucone, ponieważ miesza logikę domenową z
  transportem HTTP i utrudnia zachowanie jednego formatu.
- **Osobny handler dla każdego modułu** — odrzucony; prowadziłby do duplikacji i rozjazdu
  odpowiedzi auth, hackathonów, drużyn i zasobów.
- **Jedno pole `field` dla walidacji** — odrzucone na rzecz `location`, które obsługuje także
  zagnieżdżone dane, listy, path i query.
- **Zwracanie szczegółów wyjątku w trybie developerskim** — odrzucone, aby środowiska miały
  identyczny kontrakt i aby przypadkowo nie ujawniać sekretów.
- **Jedna centralna tabela wszystkich komunikatów dla każdego błędu** — odrzucona. Kod i status
  są stabilne centralnie, natomiast bezpieczny `detail` może zależeć od konkretnej domeny.

## Dodatkowe decyzje

- Domyślnym językiem `detail` pozostaje angielski, zgodnie z aktualnym API. Frontend mapuje
  `error_code` na polskie komunikaty, dlatego nie jest zależny od języka tekstu backendu.
- Kody przyszłych modułów są zarezerwowane w tym specu, ale trafiają do `ErrorCode` w kodzie
  dopiero wtedy, gdy zaczynają być używane. Zapobiega to utrzymywaniu martwych elementów enumu,
  a jednocześnie chroni nazwy kodów przed przypadkową zmianą kontraktu.

## Changelog

- 2026-08-04 — utworzono proponowany spec dla issue #43 i #24.
- 2026-08-04 — ujednolicono decyzje dotyczące formatu walidacji, wyjątków domenowych, statusów
  HTTP, bezpiecznych błędów 500, logowania, OpenAPI i testów.
- 2026-08-04 — zaakceptowano spec i rozpoczęto migrację błędów modułu hackathonów.
