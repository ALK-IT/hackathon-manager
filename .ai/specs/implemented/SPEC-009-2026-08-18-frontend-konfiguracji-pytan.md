# SPEC-009: Frontend konfiguracji pytań rekrutacyjnych

**Status:** Proponowany
**Data:** 2026-08-18
**Autor:** zespół hackathon-manager

## Kontekst / Problem

Backend udostępnia organizatorom możliwość tworzenia, pobierania i usuwania pytań
rekrutacyjnych hackathonu, ale frontend nie oferuje jeszcze interfejsu do zarządzania tymi
pytaniami. Organizator potrzebuje prostego miejsca, w którym przygotuje formularz zgłoszeniowy
przed rozpoczęciem zapisów.

## Proponowane rozwiązanie

Dodać chronioną stronę konfiguracji pytań pod adresem:

```text
/hackathons/{hackathon_public_id}/questions/setup
```

Strona będzie dostępna dla zalogowanych administratorów i użyje istniejącego kontraktu API:

- `GET /api/hackathons/{hackathon_public_id}/questions` — pobranie pytań;
- `POST /api/hackathons/{hackathon_public_id}/questions` — dodanie pytania;
- `DELETE /api/hackathons/{hackathon_public_id}/questions/{question_public_id}` — usunięcie
  pytania.

Interfejs pokaże listę pytań, pozwoli dodać treść pytania z oznaczeniem wymaganej odpowiedzi oraz
usunąć istniejące pytanie. Błędy API będą tłumaczone na komunikaty odpowiednie dla użytkownika,
a operacje zapisu będą sygnalizowały stan ładowania i odświeżały listę po powodzeniu.

## Zakres

**W zakresie:**

- strona konfiguracji pytań rekrutacyjnych;
- routing strony i ochrona przez istniejące `ProtectedRoute` oraz `AdminRoute`;
- typy TypeScript dla pytań i payloadu tworzenia;
- funkcje klienta API do tworzenia i usuwania pytania;
- pobieranie i wyświetlanie istniejących pytań;
- dodawanie pytań wymaganych i opcjonalnych;
- usuwanie pytań z potwierdzeniem;
- obsługa błędów, pustej listy i stanów ładowania;
- testy klienta API, strony i routingu.

**Poza zakresem:**

- zmiany modeli, serwisów i endpointów backendu;
- edycja istniejącego pytania;
- masowe tworzenie pytań z jednego formularza;
- formularz uczestnika odpowiadający na pytania;
- panel przeglądania i oceniania zgłoszeń;
- zarządzanie współorganizatorami;
- zmiana momentu zablokowania pytań po otwarciu zapisów.

## Wpływ

- **Frontend:** nowa strona i trasa w module rejestracji, funkcje klienta API, typy, komunikaty
  błędów oraz testy.
- **Backend:** brak zmian; frontend korzysta z istniejących endpointów modułu `registration`.
- **Baza danych / API:** brak zmian w kontrakcie; używane są istniejące zasoby pytań.

## Alternatywy rozważane

- **Dodanie pytań bez osobnej strony** — odrzucone, ponieważ konfiguracja jest osobnym zadaniem
  organizatora i powinna mieć bezpośredni, możliwy do zapisania adres.
- **Masowe tworzenie pytań w pierwszej wersji** — odłożone, ponieważ pojedyncze operacje lepiej
  pasują do obecnego interfejsu i pozwalają niezależnie obsługiwać błędy.
- **Edycja pytań po otwarciu zapisów** — odrzucona; istniejąca reguła backendu blokuje zmianę
  formularza po rozpoczęciu rejestracji.

## Changelog

- 2026-08-18 — utworzono spec dla frontendowej konfiguracji pytań rekrutacyjnych.
