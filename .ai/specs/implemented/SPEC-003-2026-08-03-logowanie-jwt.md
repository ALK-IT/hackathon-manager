# SPEC-003: Rejestracja i logowanie użytkowników przez JWT

**Status:** Zaimplementowany
**Data:** 2026-08-03
**Autor:** Codex

## Kontekst / Problem

Backend nie miał modelu użytkownika ani mechanizmu uwierzytelniania. Nie było możliwe utworzenie konta, zalogowanie się ani zabezpieczenie endpointu tak, aby zwracał dane osoby wykonującej żądanie. Aplikacja potrzebuje wspólnego mechanizmu identyfikacji użytkownika przed dodaniem ról, zespołów, zapisów na hackathony i innych funkcji zależnych od konta.

## Proponowane rozwiązanie

- Model SQLAlchemy `User` z wewnętrznym identyfikatorem, publicznym UUID, nazwą, unikalnym e-mailem, hashem hasła i datą utworzenia.
- Hasła przechowywane wyłącznie jako hashe Argon2 generowane przez `pwdlib`.
- Krótkotrwały token dostępu JWT podpisywany algorytmem HS256. Publiczny UUID użytkownika jest zapisywany w polu `sub`, a token zawiera czas wystawienia i wygaśnięcia.
- Sekret podpisujący pobierany z `JWT_SECRET_KEY`; aplikacja odrzuca sekret krótszy niż 32 znaki. Czas ważności jest konfigurowany przez `ACCESS_TOKEN_EXPIRE_MINUTES` i domyślnie wynosi 30 minut.
- Standardowy przepływ OAuth2 Password Bearer, dzięki czemu autoryzacja działa również w dokumentacji OpenAPI pod `/docs`.
- Podział odpowiedzialności na model, schematy Pydantic, repository, service i router.
- Sprawdzenie hasła względem sztucznego hasha również dla nieistniejącego e-maila, aby ograniczyć możliwość ustalania, które adresy mają konto, na podstawie czasu odpowiedzi.

## Zakres

**W zakresie:**

- `POST /api/auth/register` — rejestracja użytkownika przez `name`, `email` i `password`.
- `POST /api/auth/login` — logowanie formularzem OAuth2 (`username` zawiera e-mail).
- `GET /api/auth/me` — pobranie danych użytkownika na podstawie tokena Bearer.
- Normalizacja e-maila, walidacja danych i unikalność e-maila.
- Odpowiedzi `401 Unauthorized` dla niepoprawnych danych lub tokena oraz `409 Conflict` dla zajętego e-maila.
- Migracja Alembic `0002` tworząca tabelę `users`.
- Testy hashowania, tokenów, rejestracji i logowania.
- Konfiguracja lokalnego Dockera oraz Railway przez zmienne środowiskowe.

**Poza zakresem:**

- Refresh tokeny, wylogowanie i unieważnianie aktywnych tokenów.
- Weryfikacja adresu e-mail i reset hasła.
- Role, uprawnienia i konta administratorów.
- Logowanie przez Google, GitHub lub innych zewnętrznych dostawców.
- Formularze logowania i rejestracji we frontendzie.
- Ograniczanie liczby prób logowania (*rate limiting*) i blokowanie kont.

## Wpływ

- **Frontend:** bez zmian w interfejsie; frontend może korzystać z nowych endpointów i przesyłać token w nagłówku `Authorization: Bearer <token>`.
- **Backend:** moduły `src/auth/models.py`, `schemas.py`, `repository.py`, `service.py`, `router.py`, `dependencies.py`, `config.py`, `constants.py`, `exceptions.py` i `utils.py`; router uwierzytelniania jest podpięty do aplikacji FastAPI przez zbiorczy `api_router`.
- **Baza danych / API:** nowa tabela `users`, unikalny indeks publicznego UUID, unikalny e-mail oraz trzy endpointy `/api/auth/*`.
- **Konfiguracja:** nowe zmienne `JWT_SECRET_KEY` i `ACCESS_TOKEN_EXPIRE_MINUTES`; nowe zależności PyJWT, pwdlib z Argon2, python-multipart i email-validator.

## Alternatywy rozważane

- **Sesja przechowywana na serwerze i cookie** — odłożona; JWT jest prostsze do użycia przez oddzielny frontend i wystarcza dla obecnego API. Bezpieczne cookie może zostać rozważone przed wdrożeniem logowania w przeglądarce.
- **Zewnętrzny dostawca tożsamości** — odrzucony na tym etapie jako zbyt rozbudowany dla podstawowego konta użytkownika.
- **Bcrypt** — odrzucony na rzecz rekomendowanego przez `pwdlib` Argon2.
- **Refresh token od razu** — odłożony, aby pierwsza wersja nie wprowadzała przechowywania i rotacji dodatkowych tokenów.

## Changelog

- 2026-08-03 — utworzono spec po implementacji na prośbę właściciela projektu.
- 2026-08-03 — zaimplementowano model użytkownika, rejestrację, OAuth2 Password Bearer, JWT, endpoint `/me`, migrację i testy.
