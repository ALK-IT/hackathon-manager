# SPEC-027: Podsumowanie uczestnictwa w hackathonie

**Status:** Zaimplementowany

## Kontekst / Problem

Organizator potrzebuje liczników całego hackathonu, niezależnych od paginacji listy uczestników.

## Rozwiązanie

`GET /api/hackathons/{public_id}/summary` zwraca:

- `accepted`: liczba zaakceptowanych zgłoszeń;
- `teams`: liczba różnych drużyn z co najmniej jednym zaakceptowanym zgłoszeniem;
- `present`: zaakceptowane zgłoszenia z check-inem;
- `absent`: `accepted - present` (jeszcze niepotwierdzona obecność).

Zapytanie agreguje zgłoszenia jednego hackathonu, używając LEFT JOIN do check-inów
i COUNT DISTINCT dla drużyn. Check-in jest unikalny dla zgłoszenia, więc join nie
mnoży wierszy. Puste wydarzenie zwraca zera. Wygaśnięcie/dezaktywacja sesji QR
nie odbiera już potwierdzonej obecności. Zgłoszenia pending/rejected są pomijane.

## Zakres

Backend, schemat odpowiedzi, autoryzacja, testy integracyjne i komponent frontendowy
`AttendanceSummaryPanel` nad listą uczestników. Liczniki pobierane są przy wejściu
do widoku i na żądanie przyciskiem „Odśwież podsumowanie”, bez pollingu.
Komponent ma osobne stany ładowania/błędu i ponawianie żądania; błąd podsumowania
nie blokuje listy. Zmiana hackathonu anuluje stare żądanie i resetuje liczniki.
Bez cache, migracji i filtrowania po aktualnej stronie listy.

## Uprawnienia

Właściciel, współorganizator lub globalny administrator — wspólne `can_manage_hackathon`.
Anonimowy użytkownik: 401; inny zalogowany użytkownik: 403 `PERMISSION_DENIED`.
Nieistniejący/usunięty hackathon: 404 `HACKATHON_NOT_FOUND`.
Reguły odpowiadają dostępowi do listy obecności; endpoint nie wymaga trwającego wydarzenia.

## Wpływ na frontend/backend

Frontend wyświetla liczniki bez pobierania wszystkich stron uczestników.
Backend wykonuje jedno zapytanie agregujące po weryfikacji dostępu.

## Alternatywy

Liczenie w przeglądarce wymaga pobrania wszystkich stron. Trzy osobne zapytania
agregujące są zbędne, skoro pojedyncze zapytanie daje spójny zestaw liczników.

## Testy

Uprawnienia właściciela/współorganizatora/admina, odmowa dla obcych i anonimowych,
brak/usunięcie hackathonu, puste wydarzenie, różne statusy zgłoszeń, wiele osób
w drużynie, pusta drużyna, zgłoszenie indywidualne, check-iny w różnych sesjach
oraz izolacja od innego hackathonu.
