# SPEC-019: Potwierdzanie obecności uczestników kodem QR

**Status:** Zaimplementowany
**Data:** 2026-09-07
**Autor:** Patryk Nisgorski

## Kontekst / Problem

Organizator musi wiedzieć, którzy zaakceptowani uczestnicy faktycznie pojawili się na
hackathonie. Ta informacja będzie później mogła służyć między innymi do wydawania zasobów
wyłącznie obecnym osobom. Ręczne wyszukiwanie każdego zgłoszenia byłoby powolne i podatne na
błędy, dlatego uczestnik powinien sam potwierdzić obecność przez zeskanowanie krótkotrwałego
kodu QR udostępnionego na miejscu.

## Rozwiązanie

Backend udostępnia sesje check-in przypisane do hackathonu. Organizator, współorganizator albo
administrator tworzy sesję o czasie ważności od 1 do 60 minut. W odpowiedzi otrzymuje token,
który może zostać umieszczony w kodzie QR. Utworzenie nowej sesji dezaktywuje poprzednią aktywną
sesję tego hackathonu.

W bazie przechowywany jest wyłącznie hash SHA-256 tokenu. Jawny token jest zwracany tylko przy
utworzeniu sesji. Zalogowany uczestnik przesyła go do endpointu check-in. Operacja jest dostępna
wyłącznie dla uczestnika z zaakceptowanym zgłoszeniem do wskazanego hackathonu. Ponowne
przesłanie poprawnego tokenu jest idempotentne i zwraca istniejące potwierdzenie zamiast tworzyć
duplikat.

Organizatorzy mogą pobrać listę wszystkich potwierdzeń obecności złożonych w kolejnych sesjach
danego hackathonu. Lista zawiera dane uczestnika, publiczny identyfikator zgłoszenia i czas
potwierdzenia.

Osobny przegląd obecności zwraca wszystkich zaakceptowanych uczestników, również tych, którzy
nie wykonali check-inu. Dla każdego uczestnika zawiera drużynę, status obecności oraz opcjonalny
czas potwierdzenia. Dzięki temu brak check-inu nie powoduje zniknięcia osoby z danych dostępnych
organizatorowi.

## Endpointy API

- `POST /api/hackathons/{hackathon_public_id}/check-in-sessions` — tworzy krótkotrwałą sesję i
  jednorazowo zwraca jawny token;
- `PUT /api/hackathons/{hackathon_public_id}/check-ins/me` — potwierdza obecność zalogowanego
  uczestnika;
- `GET /api/hackathons/{hackathon_public_id}/check-ins` — zwraca organizatorom listę obecnych
  uczestników;
- `GET /api/hackathons/{hackathon_public_id}/attendance` — zwraca wszystkich zaakceptowanych
  uczestników wraz ze statusem obecności i drużyną.

Wszystkie endpointy wymagają access tokenu. Tworzenie sesji i odczyt listy są dostępne
właścicielowi, współorganizatorom oraz administratorom. Sam check-in wymaga zaakceptowanego
zgłoszenia uczestnika.

## Zakres

**W zakresie:**

- modele `CheckInSession` i `CheckIn` wraz z migracją Alembic;
- tylko jedna aktywna sesja na hackathon;
- generowanie bezpiecznego losowego tokenu i przechowywanie wyłącznie jego hasha;
- ograniczony czas ważności sesji;
- indywidualne, idempotentne potwierdzanie obecności;
- lista obecnych uczestników dla osób zarządzających hackathonem;
- przegląd wszystkich zaakceptowanych uczestników ze statusem obecności;
- frontend generujący i skanujący kod QR;
- frontendowy panel uczestników pogrupowanych według drużyn;
- ograniczenie tworzenia sesji i check-inu do czasu trwania hackathonu;
- testy backendu i frontendu.

**Poza zakresem:**

- zbiorowe potwierdzanie obecności całej drużyny;
- automatyczne wydawanie zasobów po check-inie;
- osobny widok statusu obecności dla uczestnika;
- działające akcje przydzielania i cofania zasobów w panelu obecności.

Docelowo organizator może przydzielić albo cofnąć zasoby pojedynczemu zaakceptowanemu
uczestnikowi niezależnie od jego statusu obecności. Akcja zbiorcza „Wyślij obecnym” obejmuje
wyłącznie uczestników, którzy potwierdzili obecność. W tej wersji przyciski przedstawiają
planowany interfejs, ale pozostają nieaktywne do czasu dodania brakujących operacji backendu.

## Wpływ

- **Frontend:** generuje kod QR, pozwala uczestnikowi go zeskanować oraz pokazuje organizatorowi
  wszystkich zaakceptowanych uczestników. Obecność jest oznaczona małym statusem i zieloną
  kropką, a uczestnicy pozostają pogrupowani według drużyn.
- **Backend/API:** nowy moduł `attendance` i cztery chronione endpointy.
- **Baza danych:** nowe tabele `check_in_sessions` i `check_ins`; unikalne ograniczenia gwarantują
  jedną aktywną sesję na hackathon oraz jedno potwierdzenie na zgłoszenie.
- **Bezpieczeństwo:** jawne tokeny sesji nie są zapisywane; krótki czas ważności ogranicza skutki
  ich przechwycenia.

## Alternatywy rozważane

Rozważono ręczne oznaczanie uczestników przez organizatora oraz potwierdzanie całych drużyn.
Pierwsze rozwiązanie utrudnia obsługę większego wydarzenia, a drugie nie potwierdza fizycznej
obecności konkretnej osoby. Pierwsza wersja działa więc indywidualnie i pozostawia integrację
drużynową na później.

## Changelog

- 2026-09-07 — opisano zaimplementowany backend indywidualnego check-inu QR.
- 2026-09-09 — dodano backendowy przegląd wszystkich zaakceptowanych uczestników ze statusem
  obecności.
- 2026-09-10 — dodano frontend generowania i skanowania QR oraz panel obecności uczestników.
