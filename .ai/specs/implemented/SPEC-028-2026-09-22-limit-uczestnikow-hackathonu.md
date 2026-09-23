# SPEC-028: Egzekwowanie limitu uczestników hackathonu

Status: Zaimplementowany
Issue: #152

## Kontekst / problem

Pole `capacity` nie ograniczało akceptacji zgłoszeń. Można było również
zmniejszyć limit poniżej liczby zaakceptowanych uczestników.

## Rozwiązanie

Limit dotyczy wyłącznie zgłoszeń ACCEPTED, także bez drużyny. PENDING i REJECTED
nie zajmują miejsc. `capacity=null` oznacza brak limitu. Wysyłanie nowych zgłoszeń
pozostaje możliwe przy zapełnionym hackathonie, jeśli rejestracja jest otwarta.
Ponowne ustawienie ACCEPTED nie zajmuje kolejnego miejsca. Odrzucenie lub usunięcie
zaakceptowanego zgłoszenia zwalnia miejsce.

Akceptacja i edycja hackathonu blokują ten sam wiersz hackathonu przez SELECT FOR
NO KEY UPDATE do końca transakcji. Ta blokada nie koliduje ze sprawdzaniem klucza
obcego podczas tworzenia zgłoszeń. Status zgłoszenia jest ponownie odczytywany z blokadą
po uzyskaniu blokady hackathonu. Kolejność blokad: hackathon, zgłoszenie, drużyna.
Odczyty blokujące odświeżają obiekty w identity map SQLAlchemy. Liczenie ACCEPTED
odbywa się w bazie po uzyskaniu blokady; Redis nie jest źródłem prawdy.

Przekroczenie limitu lub obniżenie capacity poniżej liczby ACCEPTED zwraca
409 CAPACITY_FULL. Nie zapisuje zmian i nie wysyła powiadomień.
Dotychczasowe uprawnienia oraz ograniczenia czasowe pozostają bez zmian.

## Zakres i wpływ

Backend: repozytoria, dwa serwisy, wyjątek i testy, w tym równoległe transakcje.
Nie zmieniamy schematu bazy, nie potrzeba migracji. Frontend korzysta z obecnej
obsługi błędów API. Brak listy rezerwowej, automatycznej akceptacji i zmiany UI.

## Alternatywy

Samo COUNT bez blokady nie chroni ostatniego miejsca przed wyścigiem.
Limit wszystkich zgłoszeń blokowałby kandydatów oczekujących i odrzuconych.
Licznik w Redisie utrudniałby spójność z transakcją PostgreSQL.
