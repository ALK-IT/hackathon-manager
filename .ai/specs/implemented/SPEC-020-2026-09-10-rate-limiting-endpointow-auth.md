# SPEC-020: Rate limiting endpointów auth

**Status:** Zaimplementowany  
**Data:** 2026-09-10  
**Autor:** Mateusz Guzowski

## Kontekst / Problem

Publiczne endpointy uwierzytelniania mogą być wywoływane automatycznie dużą liczbę razy. Bez
ograniczeń ułatwia to credential stuffing, masowe tworzenie kont, nadużywanie odświeżania sesji
oraz wielokrotne sprawdzanie tokenów weryfikacyjnych. Część auth posiadała wcześniej lokalne
limity, ale nie wszystkie wymagane endpointy korzystały ze wspólnego komponentu Redis.

## Rozwiązanie

Wspólny `SlidingWindowRateLimiter` używa atomowego skryptu Lua i ważonego licznika bieżącego
oraz poprzedniego okna do przechowywania w Redisie limitu dla każdego endpointu i klienta.
Zapobiega to krótkim skokom ruchu na granicy sztywnych okien przy zachowaniu stałego zużycia
pamięci na identyfikator. Zależności FastAPI uruchamiają limiter przed
logiką `/register`, `/login`, `/refresh` oraz `/verify-email`. Adres klienta jest hashowany
SHA-256 przed użyciem w kluczu Redis. Ta sama implementacja limitera obsługuje również
istniejące limity po adresie e-mail i loginie.

Skrypt jest rejestrowany przez klienta `redis-py` i przy kolejnych wywołaniach uruchamiany
poleceniem `EVALSHA`, dzięki czemu backend nie przesyła do Redisa całej treści Lua przy każdym
żądaniu. Jeżeli Redis nie zna skryptu, na przykład po restarcie, klient automatycznie obsługuje
odpowiedź `NOSCRIPT`, ładuje skrypt poleceniem `SCRIPT LOAD` i ponawia `EVALSHA`.

Po przekroczeniu limitu API zwraca HTTP `429`, kod błędu `RATE_LIMITED` oraz nagłówek
`Retry-After`. Limity i długości okien można nadpisać zmiennymi środowiskowymi `RATE_LIMIT_*`.
Domyślne wartości to:

- logowanie: 10 żądań na 60 sekund;
- rejestracja: 5 żądań na 3600 sekund;
- odświeżenie tokenu: 30 żądań na 60 sekund;
- weryfikacja e-maila: 20 żądań na 300 sekund.

Istniejące limity per adres e-mail dla nieudanych logowań, rejestracji i operacji odzyskiwania
konta pozostają zachowane jako dodatkowa warstwa ochrony.

Jeśli Redis jest niedostępny, chroniona operacja nie jest wykonywana, a API zwraca kontrolowaną
odpowiedź HTTP `503` z kodem `SERVICE_UNAVAILABLE`.

## Zakres

### W zakresie

- wykorzystanie współdzielonego limitera Redis przez wymagane endpointy auth;
- oddzielna przestrzeń kluczy i konfiguracja dla każdego endpointu;
- bezpieczna obsługa adresu klienta za zaufanym reverse proxy;
- wspólny kontrakt błędu `429 RATE_LIMITED`;
- kontrolowany błąd `503 SERVICE_UNAVAILABLE` podczas awarii Redis;
- walidacja dodatnich wartości konfiguracyjnych podczas startu aplikacji;
- testy konfiguracji, zależności, endpointów i odpowiedzi błędu.

### Poza zakresem

- rozproszona ochrona przed atakami prowadzonymi z wielu adresów IP;
- panel administracyjny do podglądu i zerowania liczników;
- dynamiczna zmiana limitów bez restartu aplikacji;
- zastąpienie limitów infrastrukturalnych oferowanych przez reverse proxy lub WAF.

## Wpływ

### Backend

Backend wymaga działającego Redis. Nowe zmienne `RATE_LIMIT_*` są opcjonalne, ponieważ mają
bezpieczne wartości domyślne. Przy wdrożeniu za zaufanym reverse proxy można włączyć istniejące
`TRUST_PROXY_HEADERS`, aby identyfikować rzeczywisty adres klienta.

### Frontend

Frontend nie zmienia formatu żądań. Może rozpoznać kod `RATE_LIMITED`, wykorzystać
`Retry-After` i poinformować użytkownika, kiedy ponowienie operacji będzie możliwe.

## Alternatywy

- Limitowanie wyłącznie w reverse proxy odrzucono, ponieważ środowiska lokalne i różne sposoby
  wdrożenia nie gwarantują tej samej konfiguracji.
- Liczniki w pamięci procesu odrzucono, ponieważ nie są współdzielone pomiędzy replikami i
  znikają po restarcie aplikacji.
- Jeden globalny limit dla całego auth odrzucono, ponieważ endpointy mają różne ryzyko i
  oczekiwaną częstotliwość użycia.
