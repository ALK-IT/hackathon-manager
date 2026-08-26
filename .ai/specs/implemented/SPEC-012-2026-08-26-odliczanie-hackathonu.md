# SPEC-012: Odliczanie na publicznej stronie hackathonu

**Status:** Zaimplementowany
**Data:** 2026-08-26
**Autor:** zespół hackathon-manager
**Powiązane zadanie:** GitHub #54

## Kontekst / Problem

Publiczna strona szczegółów prezentuje nazwę, opis oraz daty hackathonu, ale nie pokazuje w
czytelny sposób, ile czasu pozostało do wydarzenia. Issue #54 pierwotnie zakładało utworzenie
osobnego publicznego endpointu i trasy, jednak równoważne mechanizmy powstały wcześniej jako
`GET /api/hackathons/{public_id}` oraz frontendowa trasa `/hackathons/{public_id}` dostępna bez
logowania.

Brakującym elementem jest czysto frontendowe odliczanie na liście oraz stronie szczegółów,
które nie powinno generować kolejnych żądań do backendu.

## Rozwiązanie

Do wspólnych komponentów UI dodany zostaje `Countdown`. Komponent otrzymuje `startDate` i
`endDate`, a następnie oblicza pozostały czas lokalnie na podstawie `Date.now()`.

Zachowanie zależy od aktualnej fazy wydarzenia:

- przed `start_date` wyświetla „Do rozpoczęcia” i odlicza do startu;
- od `start_date` do `end_date` wyświetla „Do zakończenia” i odlicza do końca;
- po `end_date` wyświetla „Hackathon zakończony”;
- brak albo nieprawidłowa wartość `end_date` ukrywa komponent bez błędu strony.

Odliczanie pokazuje dni, godziny, minuty i sekundy. Stan aktualizuje się co sekundę przez
`setInterval`, który jest usuwany po odmontowaniu komponentu.

## Zakres

**W zakresie:**

- współdzielony komponent UI `Countdown`;
- aktualizacja odliczania co sekundę;
- rozróżnienie czasu do rozpoczęcia i czasu do zakończenia;
- stan zakończonego wydarzenia;
- bezpieczna obsługa brakującej lub nieprawidłowej daty końca;
- integracja z listą hackathonów i istniejącą publiczną stroną szczegółów;
- responsywny układ jednostek czasu;
- Storybook oraz testy jednostkowe z kontrolowanym zegarem;
- test integracji ze stroną szczegółów.

**Poza zakresem:**

- nowy endpoint backendowy;
- nowa publiczna trasa `/h/{public_id}`;
- zmiany modeli lub migracje bazy danych;
- polling backendu;
- cache w Redisie;
- SEO, dynamiczne metatagi i Open Graph;
- pełny landing page wydarzenia.

## Wpływ

- **Frontend:** nowy komponent w `components/ui` oraz jego użycie na kafelkach listy i w
  `HackathonDetailsPage`.
- **Backend:** brak zmian; daty pochodzą z istniejącego endpointu szczegółów.
- **Baza danych / API:** brak zmian kontraktu i brak migracji.

## Wydajność i cache

Frontend pobiera szczegóły hackathonu jeden raz po wejściu na stronę. Kolejne aktualizacje
odliczania są wykonywane lokalnie i nie wywołują API. Redis nie zmniejszyłby liczby żądań HTTP i
nie jest potrzebny dla prostego odczytu po `public_id`.

Cache HTTP lub cache danych we frontendzie może zostać dodany dopiero wtedy, gdy pomiary wykażą
problem wynikający z częstego ponownego otwierania strony. Obecny endpoint zawiera pola zależne
od użytkownika, dlatego nie powinien być współdzielony w publicznym cache CDN bez wcześniejszego
wydzielenia całkowicie publicznego kontraktu.

## Decyzje względem issue #54

1. **Publiczna odpowiedź:** wykorzystujemy istniejący kontrakt szczegółów. Ograniczenie go do
   nazwy, opisu i dat wymagałoby osobnego zadania backendowego dotyczącego publicznego DTO.
2. **Cel odliczania:** przed wydarzeniem liczymy do `start_date`, a w trakcie do `end_date`.
3. **Rate limiting i cache:** bez zmian; komponent nie wykonuje pollingu.
4. **Routing:** wykorzystujemy istniejącą trasę `/hackathons/{public_id}`, aby nie dublować
   publicznego widoku przez `/h/{public_id}`.
5. **Umiejscowienie:** `Countdown` jest współdzielonym komponentem UI i ma niezależne testy z
   `vi.useFakeTimers()`.
6. **SEO/share:** poza zakresem MVP.

## Alternatywy rozważane

- **Odliczanie wyłącznie do `end_date`** — odrzucono, ponieważ przed wydarzeniem bardziej
  użyteczna jest informacja o czasie pozostałym do rozpoczęcia.
- **Odświeżanie dat z backendu co sekundę** — odrzucono; daty nie zmieniają się w czasie
  odliczania, więc obliczenia mogą być wykonywane lokalnie.
- **Redis** — odrzucono jako niepotrzebny dla tej funkcjonalności i niewpływający na liczbę
  wywołań endpointu.
- **Osobna strona i endpoint publiczny** — odrzucono w tym zakresie, ponieważ istniejąca strona
  szczegółów jest już publiczna i obsługuje `404`.

## Testy

Testy sprawdzają:

- początkową wartość i zmianę po jednej sekundzie;
- odliczanie do rozpoczęcia;
- odliczanie do zakończenia trwającego hackathonu;
- komunikat po zakończeniu;
- ukrycie komponentu przy brakującej albo błędnej dacie;
- wyczyszczenie interwału po odmontowaniu;
- obecność komponentu na kafelku listy i stronie szczegółów.

## Changelog

- 2026-08-26 — opisano i zaimplementowano odliczanie na liście oraz publicznej stronie
  hackathonu.
