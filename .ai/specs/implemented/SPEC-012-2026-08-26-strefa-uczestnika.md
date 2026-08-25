# SPEC-012: Strefa uczestnika i status zgłoszenia na liście hackathonów

**Status:** Zaimplementowany
**Data:** 2026-08-26
**Autor:** zespół hackathon-manager

## Kontekst / Problem

Po wysłaniu zgłoszenia użytkownik nie widział na liście hackathonów jego aktualnego statusu.
Zaakceptowany uczestnik nie miał również osobnego miejsca, w którym mógł wejść do hackathonu
i sprawdzić swoją drużynę oraz jej członków.

Interfejs musiał informować o stanie zgłoszenia bez wykonywania osobnego zapytania HTTP dla
każdego kafelka. Jednocześnie dane dostępne dopiero po akceptacji nie mogły zostać ujawnione
użytkownikom bez zaakceptowanego zgłoszenia.

## Rozwiązanie

Publiczna lista hackathonów została rozszerzona o opcjonalne pole `my_registration_status`.
Dla zalogowanego użytkownika backend pobiera jego status zgłoszenia razem z listą hackathonów
za pomocą jednego zapytania SQL z `LEFT JOIN`. Dla użytkownika niezalogowanego oraz osoby bez
zgłoszenia pole ma wartość `null`.

Frontend wyświetla na kafelku status `pending`, `accepted` albo `rejected`. Przycisk zapisania
jest dostępny tylko wtedy, gdy użytkownik nie ma jeszcze zgłoszenia i rejestracja jest otwarta.
Po akceptacji kafelek udostępnia przycisk prowadzący do strefy uczestnika.

Strefa uczestnika korzysta z chronionego endpointu, który sprawdza zgłoszenie bieżącego
użytkownika. Dostęp otrzymuje wyłącznie osoba ze statusem `accepted`. Odpowiedź zawiera
podstawowe dane hackathonu oraz opcjonalną drużynę. Lista członków drużyny obejmuje tylko osoby
z zaakceptowanymi zgłoszeniami.

## Endpointy i kontrakty API

### Lista hackathonów

`GET /api/hackathons`

Endpoint pozostaje publiczny. Każdy element odpowiedzi zawiera dodatkowe pole:

```json
{
  "my_registration_status": "pending | accepted | rejected | null"
}
```

Jeżeli żądanie zawiera prawidłowe opcjonalne uwierzytelnienie, status dotyczy bieżącego
użytkownika. Brak uwierzytelnienia nie powoduje błędu i zwraca `null`.

### Strefa uczestnika

`GET /api/hackathons/{hackathon_public_id}/participant-area`

Endpoint wymaga uwierzytelnienia oraz zaakceptowanego zgłoszenia użytkownika na wskazany
hackathon. Przykładowa odpowiedź dla uczestnika należącego do drużyny:

```json
{
  "public_id": "00000000-0000-0000-0000-000000000000",
  "name": "Hackathon",
  "team": {
    "public_id": "00000000-0000-0000-0000-000000000000",
    "name": "Drużyna",
    "members": [
      {
        "public_id": "00000000-0000-0000-0000-000000000000",
        "name": "Jan Kowalski"
      }
    ]
  }
}
```

Dla zaakceptowanego uczestnika bez drużyny pole `team` ma wartość `null`.

## Uprawnienia i błędy

- brak tokenu przy wejściu do strefy uczestnika kończy się błędem uwierzytelnienia;
- brak zgłoszenia zwraca `404` oraz `REGISTRATION_NOT_FOUND`;
- zgłoszenie o statusie innym niż `accepted` zwraca `403` oraz
  `REGISTRATION_NOT_ACCEPTED`;
- dane drużyny nie są zwracane przed zaakceptowaniem zgłoszenia;
- lista członków nie pokazuje osób ze statusem `pending` ani `rejected`.

## Zakres

**W zakresie:**

- status własnego zgłoszenia w odpowiedzi listy hackathonów;
- pobieranie listy hackathonów i statusu jednym zapytaniem SQL;
- prezentacja statusu na kafelku hackathonu;
- nawigacja zaakceptowanego uczestnika do strefy uczestnika;
- chroniony endpoint strefy uczestnika;
- prezentacja drużyny i zaakceptowanych członków;
- obsługa uczestnika zaakceptowanego bez drużyny;
- testy repozytorium, serwisu, endpointów i komponentów frontendu.

**Poza zakresem:**

- komunikacja i czat drużynowy;
- zasoby, harmonogram oraz materiały dostępne po wejściu do hackathonu;
- zmiana drużyny z poziomu strefy uczestnika;
- zaproszenia nowych członków i usuwanie członków;
- wyświetlanie danych osób oczekujących lub odrzuconych;
- cache statusów zgłoszeń w Redisie.

## Wpływ

- **Frontend:** kafelki pokazują status własnego zgłoszenia, a zaakceptowani uczestnicy otrzymują
  przycisk wejścia do nowej strony prezentującej drużynę.
- **Backend:** lista hackathonów zwraca pary hackathon–status, a moduł `registration` udostępnia
  serwis i endpoint strefy uczestnika. Moduł `teams` pobiera zaakceptowanych członków drużyny.
- **Baza danych:** bez nowej migracji; wykorzystano istniejące relacje hackathonów, zgłoszeń,
  drużyn i użytkowników.
- **API:** rozszerzono istniejący kontrakt listy hackathonów i dodano jeden chroniony endpoint.

## Cache i wydajność

Status zgłoszenia nie jest zapisywany w Redisie. Jest to wartość zależna od użytkownika i może
zmienić się po decyzji organizatora, więc cache wymagałby kluczy per użytkownik oraz poprawnej
inwalidacji po każdej zmianie statusu, utworzeniu albo usunięciu zgłoszenia.

Aktualna implementacja pobiera listę hackathonów i status bieżącego użytkownika jednym
zapytaniem z `LEFT JOIN`, dzięki czemu nie występuje problem N+1. Cache może zostać rozważony
dopiero po pomiarach wskazujących, że to zapytanie jest rzeczywistym wąskim gardłem.

## Alternatywy rozważane

- **Osobne zapytanie o status dla każdego kafelka** — odrzucono z powodu wielu żądań HTTP i
  problemu N+1.
- **Osobny endpoint zwracający wszystkie statusy użytkownika** — odrzucono, ponieważ frontend
  musiałby synchronizować dwa niezależne żądania, mimo że status jest bezpośrednio związany z
  elementem listy.
- **Cache per użytkownik w Redisie** — odrzucono na tym etapie ze względu na koszt poprawnej
  inwalidacji i brak potwierdzonego problemu wydajnościowego.
- **Pokazywanie całej drużyny również dla zgłoszeń oczekujących** — odrzucono, ponieważ skład
  widoczny w strefie uczestnika powinien obejmować wyłącznie przyjętych uczestników.

## Testy

Testy obejmują:

- status zgłoszenia zalogowanego użytkownika na liście hackathonów;
- wartość `null` dla użytkownika bez zgłoszenia;
- pobieranie statusów bez dodatkowych zapytań per hackathon;
- dostęp do strefy przez zaakceptowanego uczestnika;
- odmowę dostępu dla zgłoszenia oczekującego lub odrzuconego;
- błąd dla użytkownika bez zgłoszenia;
- odpowiedź dla uczestnika bez drużyny;
- filtrowanie członków drużyny do zaakceptowanych zgłoszeń;
- prezentację statusu, przycisku i danych drużyny we frontendzie.

## Changelog

- 2026-08-26 — opisano zaimplementowaną strefę uczestnika i status zgłoszenia na liście
  hackathonów.
