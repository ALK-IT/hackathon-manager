# SPEC-026: Ustawienia użytkownika

**Status:** Zaimplementowany
**Data:** 2026-09-12
**Autor:** Patryk Nisgorski

## Kontekst / Problem

Użytkownik nie może zmienić username ani języka interfejsu z poziomu profilu. Zmiana hasła
jest dostępna tylko przez osobny ekran odzyskiwania konta.

## Proponowane rozwiązanie

Profil prowadzi do osobnej podstrony ustawień pozwalającej zmienić username i język
polski/angielski.
Preferencja języka jest przechowywana w bazie i zwracana w odpowiedzi `/api/auth/me`.
Angielski jest językiem domyślnym, a przełącznik `ENG / POL` na stronie głównej zapisuje
wybór w koncie zalogowanego użytkownika albo lokalnie dla gościa.
Zmiana hasła korzysta z istniejącego procesu wysyłania jednorazowego linku resetującego na
zweryfikowany adres e-mail konta.

## Zakres

**W zakresie:**

- trwała zmiana username użytkownika;
- wybór języka polskiego lub angielskiego;
- pełna lokalizacja tekstów systemowych wszystkich widoków, walidacji i komunikatów błędów;
- wysłanie linku do zmiany hasła na e-mail konta;
- testy backendu i frontendu.

**Poza zakresem:**

- zmiana adresu e-mail;
- zmiana kolorów i motywu;
- ustawianie hasła bez potwierdzenia przez e-mail;
- tłumaczenie treści tworzonych przez organizatorów.

## Wpływ

- Frontend: przycisk na profilu, osobna podstrona ustawień i mechanizm tłumaczeń `pl/en`.
- Backend: aktualizacja bieżącego użytkownika przez chroniony endpoint.
- Baza danych / API: kolumna `users.language`, rozszerzenie `/api/auth/me`.

## Alternatywy rozważane

Rozważono zapisywanie języka wyłącznie w przeglądarce, ale ustawienie nie byłoby wtedy
synchronizowane między urządzeniami.

## Changelog

- 2026-09-12 — dodano zmianę nazwy, języka i wysyłanie linku zmiany hasła.
- 2026-09-13 — rozszerzono lokalizację `pl/en` na wszystkie widoki i komunikaty frontendu.
- 2026-09-13 — ustawiono angielski jako domyślny i dodano przełącznik `ENG / POL`.
