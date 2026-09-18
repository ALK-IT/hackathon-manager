# SPEC-011: Frontend pytań rejestracyjnych i ustawień hackathonu

**Status:** Zaimplementowany
**Data:** 2026-08-22
**Autorzy:** Patryk Nisgorski

## Kontekst / Problem

Po utworzeniu hackathonu organizator nie miał w interfejsie miejsca do skonfigurowania pytań
rejestracyjnych. Brakowało również formularza zmiany podstawowych ustawień istniejącego
hackathonu, mimo że backend udostępniał już wymagane endpointy.

## Rozwiązanie

Administrator konfiguruje pytania bezpośrednio w formularzu tworzenia hackathonu. Hackathon
i jego pytania są zapisywane atomowo w jednej transakcji, dzięki czemu ustawienie otwarcia
rejestracji na bieżący moment nie blokuje późniejszego żądania zapisu pytań.

Kafelek hackathonu pokazuje przycisk `Ustawienia`, gdy `access_level` ma wartość `owner` lub
`co_organizer`. Strona ustawień pobiera aktualne dane i zapisuje zmiany przez `PATCH`.
Tworzenie i edycja korzystają ze wspólnego komponentu `HackathonForm`, dzięki czemu pola,
normalizacja danych oraz walidacja nie są powielane.

## Zakres

**W zakresie:**

- dodawanie, usuwanie i oznaczanie pytań jako wymaganych w formularzu tworzenia;
- atomowe tworzenie hackathonu i początkowych pytań;
- edycja nazwy, opisu, terminów, limitu uczestników i maksymalnej wielkości drużyny;
- dostęp do ustawień dla właściciela i współorganizatora;
- wspólny formularz tworzenia i edycji hackathonu;
- testy komponentów, nawigacji i kontraktów klienta API.

**Poza zakresem:**

- zmiana pytań po otwarciu rejestracji;
- edycja istniejącego pytania po jego zapisaniu;
- zmiany modelu bazy danych;
- zarządzanie zgłoszeniami uczestników.

## Wpływ

- **Frontend:** nowe strony konfiguracji pytań i ustawień, wspólny `HackathonForm` oraz warunkowy
  przycisk na kafelku hackathonu.
- **Backend:** `HackathonCreate` przyjmuje opcjonalną listę początkowych pytań.
- **API:** `POST /api/hackathons` tworzy hackathon razem z pytaniami; istniejące endpointy
  odczytu i edycji pozostają bez zmian.
- **Baza danych:** bez zmian.

## Alternatywy rozważane

Rozważono osobne formularze tworzenia i edycji, ale prowadziły do powielenia tych samych pól i
rozbieżnej walidacji. Rozważono również zapisywanie każdego pytania osobnym żądaniem; wybrano
istniejący endpoint zbiorczy, aby ograniczyć kod klienta i liczbę operacji sieciowych.

## Changelog

- 2026-08-22 — dodano konfigurację pytań po utworzeniu hackathonu.
- 2026-08-22 — dodano edycję ustawień dla właściciela i współorganizatora.
- 2026-08-22 — wydzielono wspólny formularz tworzenia i edycji.
- 2026-09-13 — przeniesiono pytania do formularza tworzenia i zapisano je atomowo z hackathonem.
