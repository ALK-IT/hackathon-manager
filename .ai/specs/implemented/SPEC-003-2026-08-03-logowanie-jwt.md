# SPEC-003: Rejestracja i logowanie użytkowników przez JWT

**Status:** Zaimplementowany
**Data:** 2026-08-03
**Autorzy:** Patryk Nisgorski, Codex

## Kontekst / Problem

Backend nie miał modelu użytkownika ani mechanizmu uwierzytelniania. Nie było możliwe utworzenie konta, zalogowanie się ani powiązanie żądania API z konkretnym użytkownikiem. Mechanizm ten jest potrzebny przed wdrożeniem funkcji zależnych od konta, takich jak zespoły, zapisy na hackathony i uprawnienia administratora.

## Proponowane rozwiązanie

- Uwierzytelnianie e-mailem i hasłem zgodne z przepływem OAuth2 Password Bearer obsługiwanym przez FastAPI.
- Hasła przechowywane wyłącznie jako hashe Argon2 generowane przez `pwdlib`.
- Token dostępu JWT podpisywany algorytmem HS256 i zawierający:
  - `sub` — publiczny UUID użytkownika,
  - `iat` — czas wystawienia,
  - `exp` — czas wygaśnięcia.
- Sekret podpisujący pobierany z `JWT_SECRET_KEY` i mający co najmniej 32 znaki.
- Czas ważności tokena konfigurowany przez `ACCESS_TOKEN_EXPIRE_MINUTES`, domyślnie 30 minut.
- Podział kodu auth na model, schematy, repository, service, router, dependencies, konfigurację, stałe, wyjątki i funkcje pomocnicze.
- Odczyt użytkownika z PostgreSQL przy obsłudze chronionego endpointu, dzięki czemu późniejsze sprawdzanie roli nie będzie zależało od potencjalnie nieaktualnej wartości zapisanej w JWT.

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
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 1800
}
```

Niepoprawny e-mail lub hasło zwraca `401 Unauthorized` z nagłówkiem `WWW-Authenticate: Bearer`. Dla nieistniejącego e-maila wykonywane jest sprawdzenie hasła względem sztucznego hasha, aby ograniczyć możliwość rozpoznawania istniejących kont na podstawie czasu odpowiedzi.

### `GET /api/auth/me`

Wymaga nagłówka:

```text
Authorization: Bearer <token>
```

Po zweryfikowaniu podpisu i daty wygaśnięcia JWT pobiera użytkownika z PostgreSQL po `public_id`. Zwraca ten sam publiczny schemat co rejestracja. Brak, uszkodzenie lub wygaśnięcie tokena oraz brak użytkownika zwracają `401 Unauthorized`.

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
- Podstawowa rola `USER`/`ADMIN` przechowywana w bazie.
- Konfiguracja lokalnego Dockera i Railway przez zmienne środowiskowe.
- Testy jednostkowe logiki auth i tokenów.

**Poza zakresem:**

- Autoryzacja endpointów na podstawie `role`.
- Endpointy do nadawania roli `ADMIN` i zarządzania użytkownikami.
- Udostępnianie roli w odpowiedziach API lub umieszczanie jej w JWT.
- Refresh tokeny, rotacja tokenów, wylogowanie i unieważnianie aktywnych tokenów.
- Weryfikacja adresu e-mail i reset hasła.
- Logowanie przez Google, GitHub lub innych zewnętrznych dostawców.
- Formularze logowania i rejestracji we frontendzie.
- Ograniczanie liczby prób logowania (*rate limiting*) i blokowanie kont.

## Wpływ

- **Frontend:** bez zmian w interfejsie; frontend może korzystać z endpointów `/api/auth/*` i przesyłać token w nagłówku `Authorization`.
- **Backend:** moduły w `src/auth/`: `models.py`, `schemas.py`, `repository.py`, `service.py`, `router.py`, `dependencies.py`, `config.py`, `constants.py`, `exceptions.py` i `utils.py`.
- **Baza danych:** tabela `users`, unikalny indeks `public_id`, unikalny e-mail, typ `user_role` i wymagana kolumna `role`.
- **Konfiguracja:** `JWT_SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES` oraz zależności PyJWT, pwdlib z Argon2, python-multipart i email-validator.

## Kryteria akceptacji

- Poprawna rejestracja zwraca `201`, zapisuje użytkownika i nie ujawnia hasha hasła.
- Rejestracja istniejącego e-maila zwraca `409`.
- Poprawne dane logowania zwracają podpisany token Bearer z czasem wygaśnięcia.
- Niepoprawne dane logowania zwracają `401` bez ujawniania, czy e-mail istnieje.
- Poprawny token umożliwia pobranie użytkownika przez `/api/auth/me`.
- Niepoprawny lub wygasły token zwraca `401`.
- Nowy użytkownik otrzymuje rolę `USER`.
- Istniejący użytkownicy po migracji `0003` mają rolę `USER`.
- Alembic osiąga rewizję `0003` i nie wykrywa dalszych zmian modelu względem bazy.
- Ruff, Black i testy auth przechodzą.

## Alternatywy rozważane

- **Sesja serwerowa i cookie** — odłożone. JWT upraszcza komunikację oddzielnego frontendu z API. Bezpieczne cookie powinno zostać ponownie rozważone przed implementacją logowania w przeglądarce.
- **Zewnętrzny dostawca tożsamości** — odrzucony na tym etapie jako zbyt rozbudowany dla podstawowego konta użytkownika.
- **Bcrypt** — odrzucony na rzecz Argon2 obsługiwanego przez `pwdlib`.
- **Refresh token w pierwszej wersji** — odłożony, ponieważ wymaga bezpiecznego przechowywania, rotacji i mechanizmu unieważniania.
- **Rola w JWT** — odłożona, aby zmiana roli nie wymagała oczekiwania na wygaśnięcie wcześniej wydanego tokena.

## Changelog

- 2026-08-03 — utworzono spec po implementacji na prośbę właściciela projektu.
- 2026-08-03 — zaimplementowano model użytkownika, rejestrację, OAuth2 Password Bearer, JWT, endpoint `/me`, migrację `0002` i testy.
- 2026-08-03 — dodano `UserRole`, pole `User.role` i odporną na częściowy stan lokalny migrację `0003`.
- 2026-08-03 — doprecyzowano kontrakt API, model danych, zakres roli i kryteria akceptacji.
