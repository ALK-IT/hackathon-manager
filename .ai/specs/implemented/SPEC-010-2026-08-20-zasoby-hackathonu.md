# SPEC-010: Zasoby hackathonu i ręczny przydział

**Status:** Zaimplementowany
**Data:** 2026-08-20
**Autor:** Patryk Nisgorski

## Kontekst / Problem

Organizator potrzebuje puli poufnych zasobów, początkowo kluczy API, z której może ręcznie
przydzielać egzemplarze uczestnikom albo drużynom. Wartości nie mogą być przechowywane ani
zwracane w postaci jawnej.

## Rozwiązanie

Moduł `resources` udostępnia modele `Resource`, `ResourceItem`, `ResourceAssignment` i
`ResourceAuditLog`. W fazie pierwszej obsługiwane są wyłącznie zasoby `api_key`, ręczna
dystrybucja oraz odbiorcy `individual` i `team`. Importowane wartości są szyfrowane Fernetem
kluczem z `RESOURCE_ENCRYPTION_KEY`.

Przydział wskazuje dokładnie jeden cel: zgłoszenie uczestnika albo drużynę. Ograniczenie jest
egzekwowane przez walidację API i constraint bazy danych. Wszystkie odwołania API używają
`public_id`; wewnętrzne identyfikatory nie są ujawniane.

Widok uczestników pozwala organizatorowi wybrać pulę indywidualną i przydzielić pierwszy wolny
egzemplarz jednej osobie albo atomowo wielu osobom. Operacja zbiorcza z interfejsu obejmuje tylko
uczestników z potwierdzoną obecnością, natomiast pojedynczy przydział pozostaje dostępny również
dla osoby nieobecnej. Ponowienie żądania pomija aktywne przydziały zamiast tworzyć duplikaty.

Cofnięcie dostępu ustawia czas odwołania na przydziale i trwale unieważnia egzemplarz. Klucz,
który mógł zostać wcześniej ujawniony, nie wraca do puli i nie może zostać przekazany innej osobie.
Przydział wielu egzemplarzy jest chroniony blokadą puli i transakcją: brak wystarczającej liczby
wolnych elementów odrzuca całą operację bez częściowych zmian.

## Endpointy API

- `POST /api/hackathons/{hackathon_public_id}/resources` — tworzy zasób, opcjonalnie razem
  z początkową pulą szyfrowanych egzemplarzy;
- `GET /api/hackathons/{hackathon_public_id}/resources` — zwraca pule wraz z liczbą wszystkich
  i dostępnych egzemplarzy;
- `POST /api/hackathons/{hackathon_public_id}/resources/{resource_public_id}/items` — importuje
  i szyfruje egzemplarze;
- `POST /api/hackathons/{hackathon_public_id}/resources/{resource_public_id}/assignments` —
  przydziela wskazany egzemplarz uczestnikowi albo drużynie;
- `GET /api/hackathons/{hackathon_public_id}/resources/{resource_public_id}/participant-assignments`
  — zwraca aktywne indywidualne przydziały;
- `POST /api/hackathons/{hackathon_public_id}/resources/{resource_public_id}/participant-assignments`
  — atomowo przydziela wolne egzemplarze wskazanym zgłoszeniom;
- `DELETE /api/hackathons/{hackathon_public_id}/resources/{resource_public_id}/participant-assignments/{registration_public_id}`
  — cofa indywidualny przydział.

Operacje są dostępne właścicielowi i współorganizatorom hackathonu.

## Zakres

**W zakresie:**

- modele, relacje ORM i migracje Alembic;
- Fernet i konfiguracja klucza przez zmienną środowiskową;
- tworzenie zasobu i szyfrowany import egzemplarzy;
- ręczny przydział egzemplarza do zgłoszenia uczestnika albo drużyny;
- zbiorczy przydział wolnych egzemplarzy zaakceptowanym uczestnikom;
- lista aktywnych indywidualnych przydziałów;
- trwałe cofnięcie indywidualnego przydziału;
- obsługa zarządzania zasobami w widoku obecności uczestników;
- tworzenie indywidualnej puli wraz z początkowymi, szyfrowanymi kluczami w jednej transakcji;
- blokada ponownego przydziału wykorzystanego lub unieważnionego egzemplarza;
- testy modeli, szyfrowania, uprawnień i endpointów.

**Poza zakresem:**

- reveal, `my-resources` i obsługa dziennika audytowego;
- zbiorcza dystrybucja zasobów skierowanych do drużyn;
- automatyczny przydział, `pool_unique` i `single_shared`;
- typy `voucher` i `file` oraz przechowywanie plików w S3.

## Alternatywy

- Przydzielanie wskazanego `ResourceItem` z frontendu odrzucono dla widoku uczestników, ponieważ
  ujawniałoby warstwie UI szczegóły puli i wymagałoby wielu podatnych na wyścigi żądań.
- Cofnięty egzemplarz mógłby wracać do puli, ale nie jest to bezpieczne dla sekretów, które
  uczestnik mógł już skopiować.
- Osobne żądanie dla każdego obecnego uczestnika zastąpiono jednym atomowym przydziałem
  zbiorczym, aby uniknąć częściowego sukcesu i nadmiernej liczby zapytań.

## Wpływ

- **Backend/API:** chronione endpointy inwentaryzacji, przydziału zbiorczego, odczytu aktywnych
  przydziałów i cofania zasobów.
- **Frontend:** wybór puli w widoku uczestników, indywidualne przydzielanie i cofanie oraz
  zbiorcze wysyłanie wyłącznie osobom obecnym.
- **Baza danych:** migracja `0012` tworzy fundament zasobów, a append-only migracja `0013`
  rozszerza przydział o alternatywnego odbiorcę drużynowego.
- **Bezpieczeństwo:** jawne wartości są przyjmowane wyłącznie podczas importu, natychmiast
  szyfrowane i nigdy nie są zwracane w odpowiedzi.

## Changelog

- 2026-08-20 — dodano zasoby, szyfrowany import i przydział participant/team.
- 2026-09-12 — dodano zarządzanie indywidualnymi zasobami z widoku obecności uczestników.
