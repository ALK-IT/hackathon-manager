# SPEC-003: Rejestracja, logowanie i sesje JWT

**Status:** Zaimplementowany
**Data:** 2026-08-03
**Ostatnia aktualizacja:** 2026-08-11
**Autorzy:** Patryk Nisgorski, Codex

## Kontekst / Problem

Backend nie miał modelu użytkownika ani mechanizmu uwierzytelniania. Nie było możliwe utworzenie konta, zalogowanie się ani powiązanie żądania API z konkretnym użytkownikiem. Mechanizm ten jest potrzebny przed wdrożeniem funkcji zależnych od konta, takich jak zespoły, zapisy na hackathony i uprawnienia administratora.

## Proponowane rozwiązanie

- Uwierzytelnianie e-mailem i hasłem zgodne z przepływem OAuth2 Password Bearer obsługiwanym przez FastAPI.
- Hasła przechowywane wyłącznie jako hashe Argon2 generowane przez `pwdlib`.
- Token dostępu JWT podpisywany algorytmem HS256 i zawierający:
  - `sub` — publiczny UUID użytkownika,
  - `iat` — czas wystawienia,
  - `exp` — czas wygaśnięcia,
  - `token_type=access` — rozróżnienie tokena dostępu od refresh tokena,
  - `sid` — identyfikator sesji łączący access token z refresh tokenem.
- Refresh token JWT zawierający dodatkowo `token_type=refresh` oraz unikalne `sid`. Refresh token jest jednorazowy: poprawne odświeżenie atomowo usuwa jego sesję z Redis i wydaje nową parę tokenów z nowym `sid`.
- Refresh token jest przekazywany wyłącznie w cookie `HttpOnly` o ścieżce `/api/auth`; atrybuty `Secure` i `SameSite` są konfigurowalne zależnie od środowiska.
- Sekret podpisujący pobierany z `JWT_SECRET_KEY` i mający co najmniej 32 znaki.
- Czas ważności tokena konfigurowany przez `ACCESS_TOKEN_EXPIRE_MINUTES`, domyślnie 30 minut.
- Czas ważności refresh tokena konfigurowany przez `REFRESH_TOKEN_EXPIRE_DAYS`, domyślnie 7 dni.
- Wylogowanie przez zapisanie skrótu SHA-256 tokena na liście unieważnionych tokenów w Redisie. Wpis wygasa razem z JWT, dzięki czemu Redis nie przechowuje go bezterminowo ani nie zawiera pełnego tokena.
- Podział kodu auth na model, schematy, repository, service, router, dependencies, konfigurację, stałe, wyjątki i funkcje pomocnicze.
- Odczyt użytkownika z PostgreSQL przy obsłudze chronionego endpointu, dzięki czemu późniejsze sprawdzanie roli nie będzie zależało od potencjalnie nieaktualnej wartości zapisanej w JWT.
- Sprawdzenie listy unieważnionych tokenów przed zaakceptowaniem JWT przez chroniony endpoint.

## Kontrakt API

### `POST /api/auth/register`

Przyjmuje JSON:

```json
{
  "name": "Jan Kowalski",
  "email": "jan@example.com",
  "password": "password123"
}
```

Walidacja:

- `name`: po usunięciu spacji od 3 do 100 znaków,
- `email`: poprawny format, usunięte skrajne spacje i zamiana na małe litery,
- `password`: od 8 do 128 znaków.

Zwraca `201 Created` oraz publiczne dane użytkownika: `public_id`, `name`, `email`, `created_at`. Nie zwraca wewnętrznego `id`, hasła ani `password_hash`. Zajęty e-mail zwraca `409 Conflict`.

### `POST /api/auth/login`

Przyjmuje formularz `application/x-www-form-urlencoded` zgodny z OAuth2:

- `username` — adres e-mail,
- `password` — hasło.

Zwraca:

```json
{
  "access_token": "<access-jwt>",
  "token_type": "bearer",
  "expires_in": 1800
}
```

Niepoprawny e-mail lub hasło zwraca `401 Unauthorized` z nagłówkiem `WWW-Authenticate: Bearer`. Dla nieistniejącego e-maila wykonywane jest sprawdzenie hasła względem sztucznego hasha, aby ograniczyć możliwość rozpoznawania istniejących kont na podstawie czasu odpowiedzi.

Login zapisuje w Redis sesję refresh jako `auth:refresh_session:<sid> -> 1` z TTL równym czasowi ważności refresh tokena. Pełna treść refresh tokena nie jest przechowywana po stronie serwera. Token trafia do przeglądarki przez nagłówek `Set-Cookie` i nie jest zwracany w JSON.

### `POST /api/auth/refresh`

Odczytuje refresh token z cookie `HttpOnly`; nie przyjmuje go w treści żądania.

Poprawny refresh token atomowo pobiera i usuwa swoją sesję z Redis poleceniem `GETDEL`, a endpoint zwraca nowy access token i ustawia obrócony refresh token w cookie. Nowa para otrzymuje nowe `sid`, dlatego stary refresh token jest jednorazowy i jego ponowne użycie zwraca `401 Unauthorized`. `401` zwracane jest także przy braku cookie oraz dla tokena uszkodzonego, wygasłego, wylogowanego, tokena niewłaściwego typu lub użytkownika, który już nie istnieje.

### `POST /api/auth/logout`

Opcjonalnie przyjmuje nagłówek:

```text
Authorization: Bearer <token>
```

Poprawny, niewygasły access token zostaje unieważniony do końca swojego czasu ważności, a powiązana z jego `sid` sesja refresh jest usuwana. Endpoint usuwa także sesję refresh wskazaną przez cookie i kasuje samo cookie. Wylogowanie jest idempotentne i zwraca `204 No Content` również przy braku albo niepoprawnym tokenie.

Redis przechowuje klucz z prefiksem `auth:revoked_access_token:` i skrótem SHA-256 tokena oraz TTL wyliczonym na podstawie pola `exp`. Pełna treść JWT nie jest zapisywana w Redisie.

### `GET /api/auth/me`

Wymaga nagłówka:

```text
Authorization: Bearer <token>
```

Po sprawdzeniu, czy JWT nie został unieważniony, oraz zweryfikowaniu podpisu i daty wygaśnięcia pobiera użytkownika z PostgreSQL po `public_id`. Zwraca ten sam publiczny schemat co rejestracja. Brak, uszkodzenie, wygaśnięcie lub wcześniejsze unieważnienie tokena oraz brak użytkownika zwracają `401 Unauthorized`.

## Model danych i migracje

Tabela `users` zawiera:

- `id` — wewnętrzny klucz główny,
- `public_id` — unikalny UUID używany poza bazą,
- `name`,
- `email` — wartość unikalna,
- `password_hash`,
- `created_at`,
- `role` — enum `USER`/`ADMIN`, wymagany przez bazę.

Enum Pythona ma wartości tekstowe `user` i `admin`, natomiast PostgreSQL przechowuje etykiety `USER` i `ADMIN`, zgodnie z mapowaniem SQLAlchemy.

- Migracja `0002` tworzy tabelę `users` i indeks publicznego UUID.
- Migracja `0003` tworzy typ `user_role`, dodaje kolumnę `role` i przypisuje istniejącym rekordom `USER`.
- Po migracji `0003` baza nie ma stałego `server_default` dla roli. Nowi użytkownicy otrzymują `UserRole.USER` przez domyślną wartość modelu SQLAlchemy.
- Migracja `0003` toleruje lokalny stan, w którym typ lub kolumna powstały wcześniej przez `Base.metadata.create_all()`.

Pole `role` nie jest obecnie zwracane przez `UserRead`, zapisywane w JWT ani używane do autoryzacji endpointów.

## Zakres

**W zakresie:**

- Model użytkownika i migracje `0002` oraz `0003`.
- Rejestracja, logowanie i pobranie bieżącego użytkownika.
- Normalizacja i walidacja danych rejestracyjnych.
- Unikalność e-maila i obsługa równoległej próby rejestracji tego samego adresu.
- Hashowanie i weryfikacja haseł przez Argon2.
- Wystawianie i weryfikacja krótkotrwałych tokenów JWT.
- Wystawianie refresh tokenów, jednorazowa rotacja i rozróżnianie typów tokenów.
- Przekazywanie refresh tokena w cookie `HttpOnly` i usuwanie cookie podczas logout.
- Wylogowanie i unieważnianie pojedynczych tokenów dostępu przy użyciu Redis.
- Unieważnianie sesji refresh powiązanej z access tokenem podczas logout.
- Podstawowa rola `USER`/`ADMIN` przechowywana w bazie.
- Konfiguracja lokalnego Dockera i Railway przez zmienne środowiskowe.
- Testy jednostkowe logiki auth i tokenów.

**Poza zakresem:**

- Autoryzacja endpointów na podstawie `role`.
- Endpointy do nadawania roli `ADMIN` i zarządzania użytkownikami.
- Udostępnianie roli w odpowiedziach API lub umieszczanie jej w JWT.
- Unieważnianie wszystkich sesji i tokenów użytkownika jedną operacją.
- Wykrywanie całej rodziny skradzionych refresh tokenów po próbie ponownego użycia starego tokena.
- Weryfikacja adresu e-mail i reset hasła.
- Logowanie przez Google, GitHub lub innych zewnętrznych dostawców.
- Klient, formularze i routing uwierzytelniania we frontendzie — opisane w `SPEC-004`.
- Ograniczanie liczby prób logowania (*rate limiting*) i blokowanie kont.

## Wpływ

- **Frontend:** odpowiedź logowania zawiera access token, natomiast refresh token jest zarządzany przez przeglądarkę jako cookie `HttpOnly`. Implementację klienta opisuje `SPEC-004`.
- **Backend:** moduły w `src/auth/`: `models.py`, `schemas.py`, `repository.py`, `service.py`, `router.py`, `dependencies.py`, `config.py`, `constants.py`, `exceptions.py` i `utils.py`.
- **Baza danych:** tabela `users`, unikalny indeks `public_id`, unikalny e-mail, typ `user_role` i wymagana kolumna `role`.
- **Redis:** krótkotrwałe wpisy blokujące wylogowane tokeny oraz aktywne sesje refresh. Niedostępność Redis uniemożliwia bezpieczne logowanie, odświeżanie i sprawdzenie unieważnienia tokenu.
- **Konfiguracja:** `JWT_SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `AUTH_COOKIE_SECURE`, `AUTH_COOKIE_SAMESITE`, `FRONTEND_ORIGINS` oraz zależności PyJWT, pwdlib z Argon2, python-multipart i email-validator. CORS dopuszcza credentials dla skonfigurowanych originów.

## Kryteria akceptacji

- Poprawna rejestracja zwraca `201`, zapisuje użytkownika i nie ujawnia hasha hasła.
- Rejestracja istniejącego e-maila zwraca `409`.
- Poprawne dane logowania zwracają access token i ustawiają refresh token w cookie `HttpOnly`; refresh token nie występuje w JSON.
- Refresh token nie może zostać użyty jako access token ani access token jako refresh token.
- Poprawne refresh cookie wydaje nowy access token, obraca refresh token, a ponowne użycie starego tokena zwraca `401`.
- Niepoprawne dane logowania zwracają `401` bez ujawniania, czy e-mail istnieje.
- Poprawny token umożliwia pobranie użytkownika przez `/api/auth/me`.
- Niepoprawny lub wygasły token zwraca `401`.
- Logout zwraca `204`, usuwa refresh cookie i jego sesję, a dla poprawnego access tokena zapisuje wyłącznie jego skrót z TTL oraz powoduje odrzucanie tokena przez chronione endpointy.
- Wpis unieważnienia automatycznie znika z Redis po pierwotnym czasie wygaśnięcia JWT.
- Nowy użytkownik otrzymuje rolę `USER`.
- Istniejący użytkownicy po migracji `0003` mają rolę `USER`.
- Alembic osiąga rewizję `0003` i nie wykrywa dalszych zmian modelu względem bazy.
- Ruff, Black i testy auth przechodzą.

## Alternatywy rozważane

- **Pełna sesja serwerowa bez JWT** — odłożona. Access JWT upraszcza autoryzację API, a Redis przechowuje tylko stan potrzebny do rotacji refresh tokenów i unieważniania access tokenów.
- **Zewnętrzny dostawca tożsamości** — odrzucony na tym etapie jako zbyt rozbudowany dla podstawowego konta użytkownika.
- **Bcrypt** — odrzucony na rzecz Argon2 obsługiwanego przez `pwdlib`.
- **Refresh token wielokrotnego użytku bez stanu serwerowego** — odrzucony, ponieważ przejęty token działałby aż do `exp` i nie dałoby się go unieważnić podczas logout.
- **Refresh token zwracany w JSON** — odrzucony, ponieważ frontend musiałby udostępnić go kodowi JavaScript. Wybrano cookie `HttpOnly` z konfigurowalnymi `Secure`, `SameSite` i originami CORS.
- **Rola w JWT** — odłożona, aby zmiana roli nie wymagała oczekiwania na wygaśnięcie wcześniej wydanego tokena.

## Changelog

- 2026-08-03 — utworzono spec po implementacji na prośbę właściciela projektu.
- 2026-08-03 — zaimplementowano model użytkownika, rejestrację, OAuth2 Password Bearer, JWT, endpoint `/me`, migrację `0002` i testy.
- 2026-08-03 — dodano `UserRole`, pole `User.role` i odporną na częściowy stan lokalny migrację `0003`.
- 2026-08-03 — doprecyzowano kontrakt API, model danych, zakres roli i kryteria akceptacji.
- 2026-08-03 — dodano logout oraz czasową listę unieważnionych tokenów JWT w Redisie.
- 2026-08-03 — dodano jednorazowe refresh tokeny, rotację sesji w Redis oraz unieważnianie refresh tokena podczas logout.
- 2026-08-03 — uproszczono rotację refresh tokena do `GETDEL` i nowego `sid`, usuwając własny skrypt Lua.
- 2026-08-11 — przeniesiono refresh token z odpowiedzi JSON do cookie `HttpOnly`, dodano konfigurację cookie i CORS oraz powiązano frontend z `SPEC-004`.
