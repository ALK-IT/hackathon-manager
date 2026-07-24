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

- **CodeQL** — statyczna analiza (JS/TS + Python) na każdym PR i cotygodniowo.
- **Gitleaks** — skan sekretów w commitach na każdym PR.
- **Dependency audit** — `npm audit` / `pip-audit` na każdym PR i cotygodniowo.
- **Dependabot** — automatyczne PR-y z aktualizacjami zależności (npm, pip, actions).
- **AI security review** — lokalny agent (`scripts/ai-agents/`) uruchamiany etykietą `ai-review`, sprawdza OWASP Top 10 w diffie PR-a.
- **Branch protection** na `main` — wymagane review, przechodzące CI, brak force-push.

## Zasady dla współtwórców

- Nigdy nie commituj kluczy/haseł/tokenów — używaj GitHub Secrets / zmiennych środowiskowych (`.env`, w `.gitignore`).
- Waliduj i sanityzuj wszystkie dane wejściowe (użytkownika, API).
- Nowe zależności — sprawdź, czy nie mają znanych podatności (`npm audit`, `pip-audit` uruchomią się automatycznie w CI).
- Zgłaszaj wątpliwości bezpieczeństwa etykietą `security` na issue/PR.
