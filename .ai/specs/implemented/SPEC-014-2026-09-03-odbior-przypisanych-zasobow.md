# SPEC-014: Odbiór i odsłanianie przypisanych zasobów

**Status:** Zaimplementowany
**Data:** 2026-09-03
**Powiązane zadanie:** GitHub #49

## Kontekst / Problem

Panel „Moje zasoby” posiada komponenty prezentujące zasoby, ale potrzebuje bezpiecznego API,
które zwróci wyłącznie zasoby przypisane zalogowanemu użytkownikowi lub jego zaakceptowanej
drużynie. Sekret nie może być pobierany razem z listą.

## Rozwiązanie

`GET /api/my-resources` zwraca metadane przypisanych egzemplarzy bez ich wartości. Dostęp
indywidualny wynika z zaakceptowanego zgłoszenia użytkownika, a drużynowy z aktualnego,
zaakceptowanego zgłoszenia przypisanego do danej drużyny.

`POST /api/resource-items/{resource_item_public_id}/reveal` ponownie sprawdza uprawnienia,
odrzuca zasób cofnięty, odszyfrowuje wartość i zapisuje zdarzenie `viewed` w audycie. Lista
zasobów nie zapisuje zdarzenia i nigdy nie odszyfrowuje wartości.

## Zakres

**W zakresie:**

- lista własnych zasobów indywidualnych i drużynowych;
- metadane zasobu i hackathonu bez sekretu;
- jawne odsłonięcie wartości przez uprawnionego użytkownika;
- obsługa `RESOURCE_NOT_ASSIGNED_TO_USER` i `RESOURCE_REVOKED`;
- audyt `viewed` bez zapisywania sekretu;
- testy dostępu indywidualnego, drużynowego, obcego i cofniętego zasobu.

**Poza zakresem:**

- endpoint cofania zasobu;
- zmiana istniejącego endpointu ręcznego przydziału;
- automatyczny przydział i uzależnienie dostępu od check-inu;
- cache sekretów lub metadanych w Redisie.

## Wpływ

- **Backend:** dwa chronione endpointy, zapytania ograniczone do bieżącego użytkownika i audyt.
- **Frontend:** istniejący panel korzysta bezpośrednio z nowego kontraktu.
- **Baza danych:** bez migracji; wykorzystywane są istniejące modele przydziałów i audytu.
- **Bezpieczeństwo:** sekret jest odszyfrowywany dopiero po osobnej, autoryzowanej operacji.

## Alternatywy

- Zwracanie sekretów w liście odrzucono, ponieważ ujawniałoby wszystkie wartości bez działania
  użytkownika i uniemożliwiałoby wiarygodny audyt.
- Osobny endpoint dla zasobów drużyny odrzucono, ponieważ jeden endpoint może bezpiecznie
  połączyć oba źródła uprawnień i uprościć frontend.
