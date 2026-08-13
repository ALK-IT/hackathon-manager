# SPEC-007: Zbiorcze tworzenie pytań po utworzeniu hackathonu

**Status:** Zaimplementowany
**Data:** 2026-08-13
**Autor:** zespół hackathon-manager

## Kontekst / Problem

Administrator tworzący hackathon powinien od razu przejść do przygotowania formularza
zgłoszeniowego. API pojedynczego pytania wymagałoby wielu żądań i mogłoby pozostawić częściowo
zapisany formularz, gdy jedno z nich zakończy się błędem.

## Rozwiązanie

Po poprawnym `POST /api/hackathons` frontend pobiera `public_id` utworzonego hackathonu i
przekierowuje administratora na stronę tworzenia pytań. Edytor pozwala dodawać i usuwać pytania,
określać ich treść oraz wymagalność, a następnie wysyła całą listę jednym żądaniem.

Backend udostępnia `POST /api/hackathons/{hackathon_public_id}/questions/bulk`. Serwis sprawdza
uprawnienia administratora, właściciela albo współorganizatora i zapisuje wszystkie pytania w
jednej transakcji. Istniejący endpoint pojedynczego pytania pozostaje bez zmian.

## Zakres

**W zakresie:**

- przekierowanie po utworzeniu hackathonu do edytora pytań;
- dodawanie i usuwanie roboczych pytań w interfejsie;
- walidacja treści i oznaczenie pytania jako wymaganego;
- zbiorcze utworzenie pytań jednym żądaniem i jedną transakcją;
- możliwość pominięcia pytań i powrotu do listy hackathonów;
- testy endpointu, serwisu, klienta API i strony frontendu.

**Poza zakresem:**

- edycja już zapisanych pytań;
- wybór pytań z historii innych hackathonów;
- zmiana kolejności pytań metodą przeciągania;
- usuwanie istniejących pytań z poziomu nowego edytora.

## Wpływ

- **Frontend:** nowa strona i komponent pytania w `features/registration`, nowa trasa oraz
  przekierowanie po utworzeniu hackathonu.
- **Backend:** nowy kontrakt zbiorczego żądania, endpoint i metoda serwisu/repozytorium.
- **Baza danych / API:** bez migracji; nowe pytania korzystają z istniejącej tabeli `questions`.

## Alternatywy

- Osobne żądanie dla każdego pytania odrzucono z powodu ryzyka częściowego zapisu.
- Dodawanie pytań bezpośrednio do `POST /api/hackathons` odrzucono, ponieważ przepływ ma dwie
  strony, a endpointy pytań należą do modułu zgłoszeń.
- Zmianę istniejącego `POST /questions` z obiektu na listę odrzucono jako niekompatybilną zmianę
  kontraktu.
