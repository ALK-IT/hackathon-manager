# SPEC-013: Frontendowy panel „Moje zasoby”

**Status:** Zaimplementowany
**Data:** 2026-08-27
**Autor:** zespół hackathon-manager
**Powiązane zadanie:** GitHub #50

## Kontekst / Problem

Uczestnik potrzebuje jednego miejsca, w którym zobaczy zasoby przypisane bezpośrednio do niego
albo do jego drużyny. Poufna wartość, początkowo klucz API, nie może być pobierana razem z listą
ani automatycznie ujawniana na ekranie.

Backendowa podstawa zasobów obejmuje modele, szyfrowanie, import i ręczny przydział. Panel
zależy dodatkowo od kontraktów planowanych w issue #49: listy własnych zasobów oraz jawnej
operacji `reveal`.

## Rozwiązanie

Chroniona trasa `/my-resources` prezentuje listę zasobów bieżącego użytkownika. Zakładka „Moje
zasoby” jest widoczna w głównej nawigacji po zalogowaniu. Każda karta pokazuje nazwę zasobu,
hackathon, typ, źródło przydziału, status i niesekretne metadane.

Wartość zasobu jest początkowo zastąpiona maską. Pierwsze kliknięcie „Pokaż” albo „Kopiuj”
wywołuje `reveal`. Otrzymana wartość pozostaje wyłącznie w stanie komponentu i nie trafia do
`localStorage`, `sessionStorage`, adresu URL ani cache aplikacji. Użytkownik może ponownie ukryć
wartość. Kolejne pokazanie w ramach tego samego montowania komponentu nie generuje następnego
zdarzenia `viewed`.

## Kontrakt API oczekiwany przez frontend

### Lista zasobów

`GET /api/my-resources`

```json
[
  {
    "public_id": "resource-item-public-id",
    "name": "OpenAI API key",
    "type": "api_key",
    "target": "team",
    "metadata": { "provider": "OpenAI" },
    "is_revoked": false,
    "hackathon": {
      "public_id": "hackathon-public-id",
      "name": "HackYeah"
    }
  }
]
```

`public_id` identyfikuje egzemplarz zasobu używany przez endpoint `reveal`. Lista nigdy nie
zwraca jawnej wartości.

### Ujawnienie wartości

`POST /api/resource-items/{resource_item_public_id}/reveal`

```json
{
  "value": "secret-value"
}
```

Frontend obsługuje `RESOURCE_REVOKED` oraz `RESOURCE_NOT_ASSIGNED_TO_USER`. Backend pozostaje
źródłem prawdy dla uprawnień i zapisuje zdarzenie `viewed`; kopiowanie jest wyłącznie zdarzeniem
klienckim i nie jest osobno audytowane.

## Zakres

**W zakresie:**

- chroniona trasa i strona `/my-resources`;
- zakładka w nawigacji zalogowanego użytkownika;
- lista zasobów indywidualnych i drużynowych;
- komponent karty zasobu i komponent bezpiecznej prezentacji wartości;
- maskowanie, pokazywanie, ukrywanie i kopiowanie;
- fallback do ręcznego kopiowania, gdy Clipboard API jest niedostępne albo odrzucone;
- stan zasobu cofniętego bez przycisków reveal/copy;
- stany ładowania, błędu, ponowienia i pustej listy;
- responsywny układ;
- testy API, komponentów i strony oraz Storybook karty.

**Poza zakresem:**

- endpointy `my-resources`, `reveal` i ich logika backendowa — issue #49;
- panel tworzenia, importowania i przydzielania zasobów;
- UI logów audytowych;
- revoke wykonywany przez frontend uczestnika;
- przechowywanie ujawnionych wartości po odświeżeniu albo opuszczeniu strony;
- typy zasobów inne niż `api_key`.

## Wpływ

- **Frontend:** nowy moduł `features/resources`, nawigacja aplikacji oraz chroniona trasa.
- **Backend:** brak zmian w tym branchu; wymagany jest kontrakt z issue #49.
- **Baza danych / API:** frontend nie zmienia bazy; definiuje oczekiwany format dwóch endpointów.
- **Bezpieczeństwo:** lista nie zawiera sekretów, reveal jest wykonywany dopiero na jawną akcję
  użytkownika, a wartość jest przechowywana tylko w pamięci komponentu.

## Decyzje

1. **Kopiowanie:** najpierw używamy `navigator.clipboard.writeText`; fallback wykorzystuje
   tymczasowe pole tekstowe. Przy niepowodzeniu wartość zostaje pokazana do ręcznego kopiowania.
2. **Widoczność:** po reveal wartość pozostaje widoczna do kliknięcia „Ukryj” albo opuszczenia
   strony. Kopiowanie nie wymusza automatycznego ukrycia.
3. **Moment reveal:** dopiero po „Pokaż” lub „Kopiuj”. Wartość jest pobierana najwyżej raz na
   montowanie karty.
4. **Zasób drużynowy:** każdy uprawniony członek drużyny może wykonać reveal; backend weryfikuje
   aktualne członkostwo i przypisuje audit `viewed` do użytkownika wykonującego operację.
5. **Stany strony:** wykorzystujemy istniejące `Spinner`, `Alert`, `Button` i `Card`, a elementy
   specyficzne dla zasobów pozostają w module `features/resources`.
6. **Nawigacja:** panel jest osobną zakładką widoczną dla zalogowanych użytkowników.

## Alternatywy rozważane

- **Wartość w odpowiedzi listy** — odrzucono, ponieważ samo otwarcie panelu ujawniałoby wszystkie
  sekrety i generowałoby niejednoznaczny audyt.
- **Przechowywanie ujawnionych wartości w storage przeglądarki** — odrzucono ze względu na
  ryzyko pozostawienia sekretów po zakończeniu sesji.
- **Jeden duży komponent strony** — odrzucono; logika nawigacji, karty i sekretu została
  rozdzielona i może być niezależnie testowana.
- **Logowanie kopiowania na backendzie** — odrzucono zgodnie z issue #50; wiarygodnym zdarzeniem
  audytowym jest tylko `reveal`.

## Testy

Testy obejmują ścieżki API, widoczność zakładki, listę, pusty stan, błąd i retry, aktywny oraz
cofnięty zasób, początkowe maskowanie, reveal, ponowne ukrycie, brak wielokrotnego reveal,
kopiowanie i fallback do ręcznego skopiowania.

## Changelog

- 2026-08-27 — opisano i zaimplementowano frontendowy panel „Moje zasoby”.
