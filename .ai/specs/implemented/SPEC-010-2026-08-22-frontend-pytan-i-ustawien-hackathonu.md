# SPEC-010: Frontend pytań rejestracyjnych i ustawień hackathonu

**Status:** Zaimplementowany
**Data:** 2026-08-22
**Autorzy:** Patryk Nisgorski

## Kontekst / Problem

Po utworzeniu hackathonu organizator nie miał w interfejsie miejsca do skonfigurowania pytań
rejestracyjnych. Brakowało również formularza zmiany podstawowych ustawień istniejącego
hackathonu, mimo że backend udostępniał już wymagane endpointy.

## Rozwiązanie

Po utworzeniu hackathonu administrator jest kierowany na stronę konfiguracji pytań. Może dodać
wiele pytań, oznaczyć je jako wymagane, usunąć pozycje przed zapisem albo pominąć ten krok.
Pytania są wysyłane jednym żądaniem do istniejącego endpointu zbiorczego.

Kafelek hackathonu pokazuje przycisk `Ustawienia`, gdy `access_level` ma wartość `owner` lub
`co_organizer`. Strona ustawień pobiera aktualne dane i zapisuje zmiany przez `PATCH`.
Tworzenie i edycja korzystają ze wspólnego komponentu `HackathonForm`, dzięki czemu pola,
normalizacja danych oraz walidacja nie są powielane.

## Zakres

**W zakresie:**

- przekierowanie z tworzenia hackathonu do konfiguracji pytań;
- dodawanie, usuwanie i oznaczanie pytań jako wymaganych przed zbiorczym zapisem;
- możliwość pominięcia konfiguracji pytań;
- edycja nazwy, opisu, terminów, limitu uczestników i maksymalnej wielkości drużyny;
- dostęp do ustawień dla właściciela i współorganizatora;
- wspólny formularz tworzenia i edycji hackathonu;
- testy komponentów, nawigacji i kontraktów klienta API.

**Poza zakresem:**

- zmiana pytań po otwarciu rejestracji;
- edycja istniejącego pytania po jego zapisaniu;
- nowe endpointy lub zmiany modelu bazy danych;
- zarządzanie zgłoszeniami uczestników.

## Wpływ

- **Frontend:** nowe strony konfiguracji pytań i ustawień, wspólny `HackathonForm` oraz warunkowy
  przycisk na kafelku hackathonu.
- **Backend:** bez zmian; frontend używa istniejących endpointów pytań i hackathonów.
- **API:** `POST /api/hackathons/{id}/questions/bulk`, `GET /api/hackathons/{id}` oraz
  `PATCH /api/hackathons/{id}`.
- **Baza danych:** bez zmian.

## Alternatywy rozważane

Rozważono osobne formularze tworzenia i edycji, ale prowadziły do powielenia tych samych pól i
rozbieżnej walidacji. Rozważono również zapisywanie każdego pytania osobnym żądaniem; wybrano
istniejący endpoint zbiorczy, aby ograniczyć kod klienta i liczbę operacji sieciowych.

## Changelog

- 2026-08-22 — dodano konfigurację pytań po utworzeniu hackathonu.
- 2026-08-22 — dodano edycję ustawień dla właściciela i współorganizatora.
- 2026-08-22 — wydzielono wspólny formularz tworzenia i edycji.
