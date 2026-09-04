# SPEC-013: Potwierdzanie konta i reset hasła przez e-mail

**Status:** Zaimplementowany
**Data:** 2026-09-02
**Autor:** Patryk Nisgorski

## Kontekst / Problem

Nowe konto można było używać bez potwierdzenia adresu e-mail, a użytkownik, który zapomniał
hasła, nie miał bezpiecznej ścieżki odzyskania dostępu.

## Rozwiązanie

Po rejestracji backend wysyła jednorazowy link potwierdzający adres. Niepotwierdzone konto nie
może się zalogować. Formularz „Nie pamiętasz hasła?” wysyła osobny, krótko ważny link pozwalający
ustawić nowe hasło. Surowe tokeny istnieją tylko w linkach; Redis przechowuje ich skróty SHA-256.

Wiadomości są wysyłane przez SMTP. Lokalny Docker Compose uruchamia MailHog, którego skrzynka jest
dostępna pod `http://localhost:8025`. Migracja oznacza konta istniejące przed wdrożeniem jako
potwierdzone, aby nie odciąć obecnych użytkowników.

Limity adresu IP bazują domyślnie na adresie bezpośredniego klienta połączenia. Nagłówek
`X-Real-IP` jest uwzględniany wyłącznie po świadomym włączeniu `TRUST_PROXY_HEADERS` w środowisku,
w którym aplikacja jest dostępna tylko przez zaufany reverse proxy. Limit identyfikatora logowania
zlicza wyłącznie nieudane próby, aby poprawne logowania nie umożliwiały blokowania konta.

## Zakres

**W zakresie:**

- wysłanie linku potwierdzającego po rejestracji i możliwość ponownej wysyłki;
- blokada logowania do czasu potwierdzenia adresu;
- bezpieczna, nieujawniająca istnienia konta prośba o reset hasła;
- jednorazowe tokeny potwierdzenia i resetu z czasem ważności;
- unieważnienie starszych tokenów sesji po zmianie hasła;
- strony frontendu do potwierdzenia adresu, zamówienia resetu i ustawienia nowego hasła;
- testy backendu i frontendu.

**Poza zakresem:**

- zmiana adresu e-mail zalogowanego użytkownika;
- zewnętrzna kolejka wiadomości i śledzenie dostarczenia;
- logowanie bezhasłowe.

Wysyłka SMTP pozostaje synchroniczna, więc czas odpowiedzi może różnić się dla istniejącego konta.
Pełne wyrównanie czasu wymaga przeniesienia wysyłki do kolejki. Rejestracja zwraca `409` dla
istniejącego adresu zgodnie z dotychczasowym kontraktem produktu; ukrywanie istnienia kont na tym
endpointcie również pozostaje poza zakresem. Limity identyfikatora dla resetu hasła i ponownej
wysyłki pozostają celowo aktywne, aby ograniczać mail bombing; kompromisem jest możliwość
krótkotrwałego zablokowania wiadomości dla wskazanego adresu. Okno jest ograniczone do pięciu
minut, a niezależny limit IP utrudnia masowe nadużycie z jednego źródła.

## Wpływ

- **Backend:** nowe endpointy auth, klient SMTP i jednorazowe tokeny w Redisie.
- **Frontend:** trzy publiczne strony i link odzyskiwania hasła na ekranie logowania.
- **Baza danych:** `users.email_verified_at` i `users.auth_version`.
- **Infrastruktura:** MailHog tylko dla lokalnego środowiska Docker Compose.

## Alternatywy

Rozważono osobną tabelę tokenów. Redis już jest wymaganym elementem aplikacji i obsługuje TTL oraz
atomowe zużycie tokenu, dlatego pozwala osiągnąć ten sam cel przy mniejszej liczbie modeli i
migracji.

## Changelog

- 2026-09-02 — dodano potwierdzanie konta i reset hasła przez SMTP.
- 2026-09-04 — utwardzono obsługę adresu klienta, atomową rotację tokenów i limity logowania.
