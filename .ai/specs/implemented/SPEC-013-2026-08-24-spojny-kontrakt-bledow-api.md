# SPEC-013: Spójny kontrakt błędów API

**Status:** Zaimplementowany
**Data:** 2026-08-24
**Autor:** matyyy12

## Kontekst / Problem

Backend zwraca już część błędów domenowych w formacie `error_code` + `detail`, ale
obsługa jest rozproszona pomiędzy domenami i `main.py`. Błędy uwierzytelniania,
standardowe błędy HTTP oraz nieoczekiwane wyjątki nadal mogą korzystać z domyślnego
formatu FastAPI. Klient API nie może więc zawsze podejmować decyzji na podstawie
stabilnego kodu i bywa zmuszony do sprawdzania statusu lub treści komunikatu.

## Proponowane rozwiązanie

Projekt będzie korzystał z własnego kontraktu zamiast RFC 7807. Każda odpowiedź błędu
zawiera co najmniej:

```json
{
  "error_code": "TEAM_FULL",
  "detail": "Team has reached its maximum number of members."
}
```

Błąd walidacji może zawierać wiele elementów, dlatego informacje o polach są zwracane
w tablicy `errors`:

```json
{
  "error_code": "VALIDATION_ERROR",
  "detail": "Request validation failed.",
  "errors": [
    {
      "location": ["body", "email"],
      "message": "value is not a valid email address",
      "type": "value_error"
    }
  ]
}
```

Wspólna klasa `APIError` przechowuje kod HTTP, maszynowy `error_code`, komunikat oraz
opcjonalne nagłówki. Wyjątki pozostają w modułach domenowych, lecz dziedziczą po tej
samej klasie bazowej. Jeden zestaw globalnych handlerów obsługuje wyjątki domenowe,
walidację Pydantic, standardowe `HTTPException` oraz nieoczekiwane błędy.

Brak lub nieważne uwierzytelnienie zwraca `AUTHENTICATION_REQUIRED` z kodem 401,
a brak uprawnień `PERMISSION_DENIED` z kodem 403. Odpowiedź 500 zawsze ma kod
`INTERNAL_ERROR` i ogólny komunikat; szczegóły wyjątku trafiają do logów, ale nie do
odpowiedzi, niezależnie od środowiska.

Źródłem prawdy dla kodów jest `ErrorCode` w `backend/src/common/errors.py`. Obejmuje
on obecne kody domenowe oraz kody przewidziane w issue #43 dla kolejnych funkcji,
takie jak `CAPACITY_FULL`, `CONSENT_REQUIRED`, `RESOURCE_REVOKED` i
`INVALID_QR_TOKEN`.

## Zakres

**W zakresie:**
- wspólne modele odpowiedzi błędów i enum `ErrorCode`;
- bazowy wyjątek `APIError`;
- globalne handlery błędów domenowych, walidacji, HTTP i błędów 500;
- migracja istniejących wyjątków auth, hackathonów, zgłoszeń i drużyn;
- ujednolicenie kodów `ALREADY_REGISTERED`, `TEAM_NAME_TAKEN` i
  `PERMISSION_DENIED` wraz z frontendem;
- zachowanie nagłówków wymaganych przez HTTP, w tym `WWW-Authenticate`;
- testy kontraktu dla obsługiwanych kategorii i kodów używanych przez endpointy.

**Poza zakresem:**
- implementowanie funkcji biznesowych, które w przyszłości użyją kodów zasobów,
  zgód, QR lub członkostwa w drużynie;
- ręczne dodawanie wszystkich możliwych odpowiedzi i przykładów do każdego endpointu
  OpenAPI; modele kontraktu są współdzielone, a pełny katalog OpenAPI może powstać
  osobno;
- zmiana tekstów komunikatów niezwiązanych z ujednoliceniem kodów.

## Wpływ

- Frontend: mapowanie błędów używa nowych stabilnych kodów `ALREADY_REGISTERED` oraz
  `TEAM_NAME_TAKEN`; struktura walidacji pozostaje zgodna z obecnym klientem.
- Backend: handlery zostają przeniesione z `main.py` do modułu wspólnego, a wyjątki
  domenowe dziedziczą po `APIError`.
- Baza danych / API: bez zmian w bazie i migracji; zmienia się kontrakt błędów auth,
  domyślnych 404/405 i błędów nieoczekiwanych oraz nazwy dwóch kodów domenowych.

## Mapowanie kategorii

| Kategoria | HTTP | `error_code` |
|---|---:|---|
| Brak lub nieważne uwierzytelnienie | 401 | `AUTHENTICATION_REQUIRED` |
| Brak uprawnień | 403 | `PERMISSION_DENIED` lub bardziej szczegółowy kod domenowy |
| Nieistniejąca trasa | 404 | `NOT_FOUND` |
| Niedozwolona metoda | 405 | `METHOD_NOT_ALLOWED` |
| Walidacja FastAPI/Pydantic | 422 | `VALIDATION_ERROR` |
| Konflikt biznesowy | 409 | kod domenowy, np. `TEAM_FULL` |
| Nieoczekiwany błąd serwera | 500 | `INTERNAL_ERROR` |

## Logowanie

Błędy domenowe 4xx nie są logowane ze stack trace'em przez globalny handler. Błędy
nieoczekiwane są logowane jako wyjątki wraz ze stack trace'em. Odpowiedź HTTP nigdy
nie zawiera tracebacka, zapytania SQL, sekretów ani tekstu surowego wyjątku 500.

## Alternatywy rozważane

- RFC 7807: odrzucone, ponieważ istniejąca specyfikacja produktu i frontend używają
  prostszego kontraktu `error_code` + `detail`.
- Jedna centralna lista wszystkich klas wyjątków: odrzucona, ponieważ wyjątki
  biznesowe powinny pozostać przy swoich domenach.
- Tabela mapująca każdy kod domenowy na HTTP: odrzucona na rzecz atrybutu klasy
  wyjątku, który jest czytelniejszy i zgodny z obecną architekturą.
- Zwracanie tracebacka w trybie developerskim: odrzucone ze względu na ryzyko wycieku
  danych; różnica między środowiskami dotyczy logowania, nie odpowiedzi API.

## Changelog

- 2026-08-24 — utworzono i zaakceptowano spec dla issue #43.
- 2026-08-24 — wdrożono wspólny kontrakt, globalne handlery i testy.
