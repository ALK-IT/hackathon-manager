# SPEC-012: Frontend zarządzania zgłoszeniami

**Status:** Zaimplementowany
**Data:** 2026-08-23
**Autor:** Patryk Nisgorski

## Kontekst / Problem

Backend umożliwia właścicielowi i współorganizatorowi hackathonu pobieranie zgłoszeń oraz zmianę
ich statusu, ale brakowało interfejsu pozwalającego wykonać te operacje w aplikacji. Organizator
musiałby korzystać bezpośrednio z API, aby zobaczyć uczestników, odpowiedzi i drużyny oraz podjąć
decyzję o przyjęciu lub odrzuceniu zgłoszenia.

## Rozwiązanie

Frontend udostępnia chronioną stronę
`/hackathons/{hackathon_public_id}/registrations`. Właściciel i współorganizator otwierają ją
przyciskiem „Zgłoszenia” widocznym na karcie zarządzanego hackathonu.

Strona pobiera zgłoszenia z istniejącego API stronami, prezentuje ich statusy i pozwala wybrać
zgłoszenie, aby zobaczyć:

- nazwę i adres e-mail uczestnika;
- drużynę, jeżeli zgłoszenie jest zespołowe;
- pytania rejestracyjne i udzielone odpowiedzi;
- aktualny status zgłoszenia.

Organizator może zaakceptować albo odrzucić wybrane zgłoszenie. Po poprawnej odpowiedzi API
status jest aktualizowany lokalnie bez przeładowania całej strony.

## Routing i uprawnienia

- `/` przekierowuje do kanonicznej trasy `/hackathons`;
- `/hackathons/{hackathon_public_id}/registrations` wymaga zalogowania;
- przycisk „Zgłoszenia” jest widoczny dla poziomów dostępu `owner` i `co_organizer`;
- użytkownik z poziomem `viewer` nie widzi przycisku;
- backend pozostaje źródłem kontroli uprawnień i odrzuca nieautoryzowane żądania.

## Integracja z API

- `GET /api/hackathons/{hackathon_public_id}/registrations?limit={limit}&offset={offset}` — pobranie
  strony zgłoszeń zarządzanego hackathonu;
- `PATCH /api/registrations/{registration_public_id}/status` — zmiana statusu na `accepted` albo
  `rejected`.

## Zakres

**W zakresie:**

- wejście do panelu z listy hackathonów;
- lista zgłoszeń wraz ze statusem;
- stronicowanie listy zgłoszeń;
- podgląd danych uczestnika, drużyny oraz odpowiedzi;
- akceptowanie i odrzucanie zgłoszeń;
- komunikaty ładowania, pustej listy i błędów;
- kanoniczne przekierowanie `/` do `/hackathons`;
- testy klienta API, widoczności przycisku i podstawowych operacji strony.

**Poza zakresem:**

- filtrowanie i sortowanie zgłoszeń w interfejsie;
- przywracanie statusu `pending`;
- masowe akceptowanie lub odrzucanie;
- powiadomienia uczestników o decyzji;
- osobny frontendowy guard sprawdzający dostęp do konkretnego hackathonu.

## Wpływ

- **Frontend:** nowa strona zarządzania, klient API, przycisk na karcie hackathonu i nowa chroniona
  trasa.
- **Backend:** bez zmian; frontend korzysta z istniejących endpointów i autoryzacji.
- **Baza danych:** bez zmian.

## Testy

Testy obejmują wywołania klienta API z parametrami stronicowania, widoczność przycisku dla
właściciela i współorganizatora, ukrycie przycisku przed zwykłym użytkownikiem, przechodzenie
między stronami, wyświetlenie odpowiedzi oraz zaakceptowanie zgłoszenia bez opuszczania strony.

## Changelog

- 2026-08-23 — dodano frontendowy panel zarządzania zgłoszeniami i kanoniczną trasę hackathonów.
- 2026-09-01 — dodano stronicowanie oraz obsługę błędów zmiany statusu.
