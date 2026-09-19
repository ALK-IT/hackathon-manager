# SPEC-026: Paginacja obecności i drużyn

**Status:** Zaimplementowany
**Data:** 2026-09-14

## Kontekst / problem

Listy obecności, check-inów i drużyn pobierają wszystkie rekordy hackathonu.
Przy większym wydarzeniu zwiększa to koszt zapytań i rozmiar odpowiedzi.

## Rozwiązanie

Endpointy `GET /api/hackathons/{hackathon_public_id}/attendance`,
`GET /api/hackathons/{hackathon_public_id}/check-ins` i
`GET /api/hackathons/{hackathon_public_id}/teams` przyjmują `limit` (domyślnie 50,
zakres 1–100) oraz `offset` (domyślnie 0, minimum 0).
Odpowiedź ma format `{items, total, limit, offset}`, zgodny z listą hackathonów.
`total` liczy wszystkie pasujące rekordy przed paginacją, również dla pustej strony.
Ograniczenie liczby rekordów następuje w SQL, przed załadowaniem relacji.

`attendance` nadal zwraca zaakceptowanych uczestników, obecnych i nieobecnych,
uporządkowanych po ID zgłoszenia. `check-ins` obejmuje wszystkie sesje wydarzenia,
także nieaktywne, z sortowaniem po `checked_in_at, id`.
`teams` stronicuje całe drużyny (`name, id`), zachowując wszystkich zaakceptowanych
członków każdej zwróconej drużyny. Drużyna nigdy nie jest dzielona między strony.

## Zakres

- trzy endpointy, ich schematy, serwisy i repozytoria;
- dotychczasowe uprawnienia właściciela, współorganizatora i administratora;
- testy paginacji, walidacji, izolacji hackathonów i kompletności drużyn.

Poza zakresem: nowe filtry, zmiany check-inów, przypisywanie zasobów.

## Wpływ

- **Backend:** zamiast surowej listy zwracana jest strona z metadanymi; brak migracji.
- **Frontend:** panel QR obsługuje strony po 20 elementów oraz widoki „Uczestnicy”
  i „Drużyny”. Odczytuje `items` i liczniki z `total`, pobiera tylko wybraną stronę.
  W widoku uczestników grupowanie dotyczy bieżącej strony (z opisem w UI), a widok
  drużyn pokazuje pełne składy. Odświeżanie zachowuje stronę, chyba że ta już nie istnieje.
  Zmiana hackathonu/widoku resetuje stronę; wcześniejsze żądania są anulowane.
  Klient `check-ins` także obsługuje strony, lecz nie ma osobnego widoku w tym panelu.
  Przyciski zasobów nadal są nieaktywne. Przyszłe operacje „dla wszystkich” muszą
  objąć pełen zbiór odbiorców po stronie backendu, niezależnie od bieżącej strony.
- **Bezpieczeństwo:** uprawnienia sprawdzane przed pobraniem i policzeniem wyników;
  licznik uwzględnia wyłącznie wskazany hackathon i dotychczasowe warunki widoczności.

## Alternatywy

- Paginacja w pamięci — odrzucona, nie ogranicza obciążenia bazy.
- Cursor pagination — odłożona, limit/offset jest już konwencją projektu.
- Paginacja członków drużyny — odrzucona, rozbija kompletność grup w widoku.

## Walidacja

Testy obejmują kolejne strony, brak powtórzeń przy stałych danych, offset poza końcem,
puste listy, błędne parametry, rekordy innego hackathonu i dotychczasowe uprawnienia.
Przy równoległych zmianach danych limit/offset nie gwarantuje niezmiennego obrazu listy.

Weryfikacja: 71 testów attendance/teams i pełny backend (478 testów) przeszły;
Black i Ruff bez błędów.

Po integracji panelu QR: 127 testów frontendu, `npm run build` i `npm run lint`
przeszły. Testy obejmują nawigację stron, odświeżanie, zmniejszenie liczby wyników,
błędy pobierania, anulowanie nieaktualnych żądań oraz widok pełnych drużyn.
