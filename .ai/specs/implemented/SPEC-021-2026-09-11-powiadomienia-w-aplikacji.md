# SPEC-021: Powiadomienia w aplikacji

**Status:** Zaimplementowany
**Data:** 2026-09-11
**Autor:** Patryk Nisgorski

## Kontekst / Problem

Uczestnik otrzymuje e-mail po zmianie statusu zgłoszenia, ale po wejściu do aplikacji nie ma
widocznej historii decyzji ani informacji o nowych zdarzeniach.

## Rozwiązanie

Powiadomienie in-app jest zapisywane w tej samej transakcji co zmiana statusu zgłoszenia. Globalny
panel dostępny dla zalogowanego użytkownika pobiera jego powiadomienia po wejściu do aplikacji oraz
po powrocie do karty przeglądarki. Nie działa okresowy polling ani proces w tle.

Użytkownik może otworzyć powiadomienie, przejść do powiązanego hackathonu, oznaczyć pojedynczą
wiadomość jako przeczytaną albo oznaczyć wszystkie jako przeczytane.

## Zakres

**W zakresie:**

- tabela trwałych powiadomień przypisanych do użytkownika;
- utworzenie powiadomienia po rzeczywistej zmianie statusu na zaakceptowany lub odrzucony;
- endpoint listy wraz z liczbą nieprzeczytanych;
- oznaczanie pojedynczego lub wszystkich powiadomień jako przeczytane;
- globalny dzwonek i panel powiadomień we frontendzie;
- testy backendu i frontendu.

**Poza zakresem:**

- WebSocket, SSE i okresowy polling;
- zewnętrzne kolejki oraz Celery;
- inne rodzaje powiadomień niż zmiana statusu zgłoszenia;
- usuwanie i archiwizacja powiadomień.

## Wpływ

- **Frontend:** globalny panel powiadomień widoczny po zalogowaniu.
- **Backend:** nowy moduł `notifications` i integracja z serwisem rejestracji.
- **Baza danych:** nowa tabela `notifications`.
- **API:** endpointy listowania i oznaczania powiadomień jako przeczytane.

## Alternatywy

Rozważono cykliczny polling oraz WebSockety. Pobieranie przy wejściu i odzyskaniu fokusu jest
prostsze, nie generuje stałego ruchu i spełnia wymaganie pokazania nowych wiadomości przy odwiedzeniu
aplikacji.

## Changelog

- 2026-09-11 — dodano trwałe powiadomienia o zmianie statusu zgłoszenia.
