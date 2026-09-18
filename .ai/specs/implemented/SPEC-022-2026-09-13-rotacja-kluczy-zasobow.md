# SPEC-022: Rotacja kluczy szyfrowania zasobów

**Status:** Zaimplementowany
**Data:** 2026-09-13
**Autor:** Patryk Nisgorski

## Kontekst / Problem

Zmiana pojedynczego klucza Fernet uniemożliwiała odczyt wcześniej zapisanych zasobów.

## Rozwiązanie

Backend używa `MultiFernet` z kluczami `nowy,stary,...`. Skrypt administracyjny ponownie
szyfruje wszystkie `resource_items` pierwszym kluczem w jednej transakcji.

## Zakres

**W zakresie:** lista kluczy, kompatybilność z pojedynczym kluczem, skrypt rotacji, testy i
procedura w `SECURITY.md`.

**Poza zakresem:** automatyczna cykliczna rotacja i endpoint HTTP.

## Wpływ

- Backend: `MultiFernet` i skrypt `python -m scripts.rotate_resource_encryption`.
- Konfiguracja: opcjonalne `RESOURCE_ENCRYPTION_KEYS`.
- Baza, API i frontend: bez zmian.

## Alternatywy

Endpoint administracyjny odrzucono, ponieważ zwiększałby powierzchnię ataku. Skrypt operacyjny
jest prostszy i nie wystawia rotacji przez HTTP.
