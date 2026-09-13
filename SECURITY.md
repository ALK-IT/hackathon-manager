# Polityka bezpieczeństwa — hackathon-manager

## Zgłaszanie podatności

Nie zgłaszaj podatności bezpieczeństwa jako publiczny issue. Zamiast tego:

1. Otwórz [prywatne zgłoszenie (Security Advisory)](https://github.com/ALK-IT/hackathon-manager/security/advisories/new), albo
2. Napisz bezpośrednio do właściciela repozytorium (@kwarpechowski).

## Co jest w zakresie

- Kod w `frontend/` i `backend/`.
- Konfiguracja CI/CD (`.github/workflows/`).
- Infrastruktura Docker (`docker-compose.yml`, `Dockerfile`).

## Mechanizmy bezpieczeństwa w tym repo

- **CodeQL** — statyczna analiza (JS/TS + Python) na każdym PR i cotygodniowo. **Wymaga GitHub Advanced Security** — na prywatnym repo z planem Free workflow jest automatycznie pomijany (nie failuje), aktywuje się sam gdy repo jest publiczne albo organizacja ma GHAS.
- **Gitleaks** — skan sekretów w commitach na każdym PR (OSS, działa zawsze, bez licencji/planu).
- **Dependency audit** — `npm audit` / `pip-audit` na każdym PR i cotygodniowo.
- **Dependabot** — automatyczne PR-y z aktualizacjami zależności (npm, pip, actions).
- **AI security review** — lokalny agent (`scripts/ai-agents/`) uruchamiany etykietą `ai-review`, sprawdza OWASP Top 10 w diffie PR-a.
- **Branch protection** na `main` — wymagane review, przechodzące CI, brak force-push. **Uwaga:** na prywatnym repo z planem Free organizacji GitHub też tego nie wymusza technicznie (wymaga GitHub Team+) — zasady zostają jako konwencja zespołu.

## Zasady dla współtwórców

- Nigdy nie commituj kluczy/haseł/tokenów — używaj GitHub Secrets / zmiennych środowiskowych (`.env`, w `.gitignore`).
- Waliduj i sanityzuj wszystkie dane wejściowe (użytkownika, API).
- Nowe zależności — sprawdź, czy nie mają znanych podatności (`npm audit`, `pip-audit` uruchomią się automatycznie w CI).
- Zgłaszaj wątpliwości bezpieczeństwa etykietą `security` na issue/PR.

## Rotacja klucza szyfrowania zasobów

`RESOURCE_ENCRYPTION_KEYS` to lista kluczy Fernet oddzielonych przecinkami. Pierwszy klucz
szyfruje nowe wartości, a pozostałe służą do odszyfrowania starszych danych. Pojedynczy
`RESOURCE_ENCRYPTION_KEY` pozostaje obsługiwany dla kompatybilności.

1. Wygeneruj nowy klucz: `python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'`.
2. Wdróż backend z `RESOURCE_ENCRYPTION_KEYS=<nowy>,<stary>`. Nie usuwaj starego klucza.
3. Zrób kopię bazy i uruchom `docker compose exec backend python -m scripts.rotate_resource_encryption`.
4. Po poprawnej rotacji wdróż konfigurację zawierającą tylko nowy klucz.
5. Usuń stary klucz z menedżera sekretów po sprawdzeniu odczytu zasobów.

Skrypt przetwarza rekordy partiami w jednej transakcji. Błąd odszyfrowania wycofuje całą
operację. Do rotacji muszą być skonfigurowane jednocześnie nowy i stary klucz.
