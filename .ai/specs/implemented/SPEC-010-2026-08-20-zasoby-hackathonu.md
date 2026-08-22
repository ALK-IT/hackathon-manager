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

## Endpointy API

- `POST /api/hackathons/{hackathon_public_id}/resources` — tworzy zasób;
- `POST /api/hackathons/{hackathon_public_id}/resources/{resource_public_id}/items` — importuje
  i szyfruje egzemplarze;
- `POST /api/hackathons/{hackathon_public_id}/resources/{resource_public_id}/assignments` —
  przydziela egzemplarz uczestnikowi albo drużynie.

Operacje są dostępne wyłącznie właścicielowi hackathonu (`Hackathon.organizer`).

## Zakres

**W zakresie:**

- modele, relacje ORM i migracje Alembic;
- Fernet i konfiguracja klucza przez zmienną środowiskową;
- tworzenie zasobu i szyfrowany import egzemplarzy;
- ręczny przydział egzemplarza do zgłoszenia uczestnika albo drużyny;
- blokada ponownego przydziału wykorzystanego lub unieważnionego egzemplarza;
- testy modeli, szyfrowania, uprawnień i endpointów.

**Poza zakresem:**

- revoke, reveal, `my-resources` i obsługa dziennika audytowego;
- automatyczny przydział, `pool_unique` i `single_shared`;
- typy `voucher` i `file` oraz przechowywanie plików w S3.

## Wpływ

- **Backend/API:** nowy moduł i trzy chronione endpointy zasobów.
- **Baza danych:** migracja `0012` tworzy fundament zasobów, a append-only migracja `0013`
  rozszerza przydział o alternatywnego odbiorcę drużynowego.
- **Bezpieczeństwo:** jawne wartości są przyjmowane wyłącznie podczas importu, natychmiast
  szyfrowane i nigdy nie są zwracane w odpowiedzi.

## Changelog

- 2026-08-20 — dodano zasoby, szyfrowany import i przydział participant/team.
