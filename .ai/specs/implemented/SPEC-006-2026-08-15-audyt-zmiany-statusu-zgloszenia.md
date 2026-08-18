# SPEC-006: Audyt ostatniej zmiany statusu zgłoszenia

**Status:** Zaimplementowany
**Data:** 2026-08-15
**Autor:** Patryk Nisgorski

## Kontekst / Problem

Status zgłoszenia może być zmieniany między `accepted` i `rejected`, ale dotychczas system nie
zapisywał, kto i kiedy podjął ostatnią decyzję. Utrudniało to wyjaśnienie aktualnego stanu
zgłoszenia.

## Rozwiązanie

Zgłoszenie przechowuje czas ostatniej zmiany statusu oraz opcjonalne wskazanie użytkownika,
który jej dokonał. Endpointy zwracające zgłoszenie udostępniają publiczny identyfikator i nazwę
tej osoby. Usunięcie konta osoby zmieniającej status zeruje wskazanie użytkownika, ale zachowuje
czas ostatniej zmiany.

## Zakres

**W zakresie:**

- pola `status_changed_at` i `status_changed_by_id` w tabeli `registrations`;
- ustawianie obu pól przy każdej zmianie statusu;
- zwracanie danych ostatniej zmiany w API;
- migracja Alembic i testy.

**Poza zakresem:**

- pełna historia wszystkich zmian statusu;
- blokowanie przejść między `accepted` i `rejected`;
- powiadomienia o zmianie decyzji.

## Wpływ

- **Frontend:** może wyświetlić osobę i czas ostatniej decyzji.
- **Backend:** serwis przekazuje wykonawcę zmiany do repozytorium.
- **Baza danych / API:** dwa nullable pola audytowe oraz bezpieczne podsumowanie użytkownika w
  odpowiedziach dotyczących zgłoszeń.

## Alternatywy rozważane

Pełną tabelę historii odłożono, ponieważ obecne wymaganie dotyczy wyłącznie ostatniej zmiany.
Przechowywanie nazwy użytkownika jako tekstu odrzucono na rzecz spójnego klucza obcego.

## Changelog

- 2026-08-15 — zaimplementowano audyt ostatniej zmiany statusu.
