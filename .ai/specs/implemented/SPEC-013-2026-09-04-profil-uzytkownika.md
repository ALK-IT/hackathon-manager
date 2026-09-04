# SPEC-013: Profil użytkownika i lista własnych hackathonów

**Status:** Zaimplementowany
**Data:** 2026-09-04
**Autor:** Patryk Nisgorski

## Kontekst / Problem

Zalogowany użytkownik nie miał osobnego widoku podsumowującego dane konta i zgłoszenia na
hackathony. Informacje o imieniu, adresie e-mail, roli i dacie utworzenia konta były dostępne w
sesji, lecz aplikacja nie prezentowała ich jako profilu. Brakowało również jednego miejsca, w
którym uczestnik mógł sprawdzić wszystkie własne zgłoszenia, ich statusy oraz przypisane drużyny.

Lista zgłoszeń profilu zawiera dane prywatne, dlatego endpoint musi wymagać uwierzytelnienia i
filtrować wyniki według użytkownika ustalonego na podstawie sesji. Klient nie może wskazać
identyfikatora innego użytkownika ani uzyskać jego zgłoszeń przez zmianę parametrów żądania.

## Rozwiązanie

- Chroniona strona `/profile` prezentuje dane zalogowanego użytkownika oraz listę hackathonów, na
  które wysłał zgłoszenie.
- `GET /api/profile/hackathons` pobiera użytkownika z zależności uwierzytelniającej i zwraca
  wyłącznie zgłoszenia powiązane z jego wewnętrznym identyfikatorem.
- Każda pozycja zawiera identyfikatory zgłoszenia i hackathonu, dane wydarzenia, status zgłoszenia,
  datę ostatniej zmiany statusu oraz opcjonalną drużynę.
- Lista jest sortowana malejąco według daty rozpoczęcia hackathonu i pomija usunięte hackathony.
- Frontend obsługuje stany ładowania, błędu oraz pustej listy, a karta prowadzi do szczegółów
  hackathonu.

## Kontrakt API i bezpieczeństwo

`GET /api/profile/hackathons`:

- wymaga prawidłowego uwierzytelnienia; bez niego zwraca `401`;
- nie przyjmuje identyfikatora użytkownika w ścieżce, query ani body;
- filtruje zgłoszenia przez `current_user.id`, co zapobiega IDOR i ujawnieniu danych innego
  uczestnika;
- zwraca `200` i pustą listę, jeżeli bieżący użytkownik nie ma zgłoszeń.

Izolacja danych i wymagane uwierzytelnienie są pokryte osobnymi testami endpointu z jawnymi
asercjami identyfikatorów zwróconych i niewidocznych rekordów.

## Zakres

**W zakresie:**

- widok profilu z danymi bieżącego użytkownika;
- chroniona trasa `/profile` i odnośnik z listy hackathonów;
- endpoint listujący wyłącznie zgłoszenia bieżącego użytkownika;
- prezentacja statusu zgłoszenia i opcjonalnej drużyny;
- stany ładowania, błędu i pustej listy;
- testy renderowania profilu, odpowiedzi `401` oraz izolacji danych między użytkownikami.

**Poza zakresem:**

- edycja danych konta, adresu e-mail lub hasła;
- przesyłanie zdjęcia profilowego;
- usuwanie konta;
- publiczne profile i wyszukiwanie użytkowników;
- zarządzanie zgłoszeniem bezpośrednio ze strony profilu.

## Wpływ

- **Frontend:** nowy moduł `features/profile`, chroniona strona profilu, klient API i style widoku.
- **Backend:** nowy endpoint w module rejestracji oraz metoda pobierająca zgłoszenia bieżącego
  użytkownika.
- **Baza danych:** brak migracji; używane są istniejące relacje użytkowników, zgłoszeń, drużyn i
  hackathonów.
- **API:** nowy chroniony endpoint `GET /api/profile/hackathons`.

## Kryteria akceptacji

- Zalogowany użytkownik widzi swoje imię, e-mail, rolę i datę utworzenia konta.
- Profil pokazuje wszystkie własne zgłoszenia wraz ze statusem i opcjonalną drużyną.
- Brak zgłoszeń jest przedstawiony jako czytelny pusty stan.
- Niezalogowane żądanie do endpointu profilu otrzymuje `401`.
- Odpowiedź nie zawiera zgłoszeń ani hackathonów należących do innego użytkownika.
- Usunięte hackathony nie są zwracane.

## Alternatywy rozważane

- **Identyfikator użytkownika w URL** — odrzucony, ponieważ profil dotyczy wyłącznie bieżącej sesji
  i taki kontrakt zwiększałby ryzyko IDOR.
- **Filtrowanie zgłoszeń po stronie frontendu** — odrzucone, ponieważ ujawniałoby klientowi dane
  innych użytkowników; izolacja musi być wymuszona w zapytaniu backendu.
- **Rozszerzenie publicznej listy hackathonów o dane profilu** — odrzucone ze względu na inny zakres
  uprawnień i odpowiedzialności endpointu.

## Changelog

- 2026-09-04 — udokumentowano zaimplementowany profil użytkownika i kontrakt bezpieczeństwa API.
- 2026-09-04 — dodano jawne testy wymagania uwierzytelnienia i ochrony przed IDOR.
