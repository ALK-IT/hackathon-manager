# Strategia testów backendu

Testy backendu dzielimy według granicy odpowiedzialności:

- **jednostkowe** testują logikę serwisów z repozytoriami zastąpionymi mockami;
- **integracyjne** testują endpoint HTTP, serializację, autoryzację, transakcję i rzeczywiste
  ograniczenia PostgreSQL;
- **E2E backendu** wykonują pełną historię kilku użytkowników przez prawdziwe endpointy,
  oddzielne sesje żądań, PostgreSQL i izolowaną bazę Redis nr 15;
- test repozytorium jest integracyjny, jeżeli wykonuje zapytania na prawdziwej bazie.

Nie mockujemy repozytorium w testach endpointów głównej ścieżki. Dzięki temu test potwierdza cały
przekrój: router → service → repository → PostgreSQL → odpowiedź HTTP. Redis należy uruchomić
razem ze stackiem, jeżeli testowana ścieżka korzysta z cache.

## Uruchamianie

Pełny zestaw w środowisku Docker Compose:

```bash
docker compose run --build --rm backend pytest
docker compose run --build --rm backend ruff check src tests
```

Przy działającym kontenerze:

```bash
docker compose exec backend pytest
docker compose exec backend ruff check src tests
```

Tylko pełne przepływy E2E:

```bash
docker compose exec backend pytest tests/e2e -v
```

`TEST_DATABASE_URL` musi wskazywać bazę, której nazwa kończy się na `_test`. Fixture `session`
odmawia pracy na innej bazie, przed każdym testem odtwarza schemat z metadanych SQLAlchemy i po
teście zamyka sesję. Zapobiega to zależności testów od kolejności wykonania.

## Fixture'y i factory

- Wspólne fixture'y infrastruktury (`session`, `api_client`, `force_authenticate`) znajdują się w
  `tests/conftest.py`.
- Factory współdzielone przez cały moduł umieszczamy w `tests/<moduł>/factories.py` albo
  `tests/<moduł>/conftest.py`.
- Helper używany tylko w jednym pliku może pozostać lokalny, np. `create_user`,
  `create_hackathon` i `create_question` w testach endpointów rejestracji.
- Factory musi pozwalać nadpisać dane istotne dla scenariusza i domyślnie tworzyć poprawny,
  minimalny obiekt.

## Kontrakty błędów

Każdy obsługiwany błąd domenowy testujemy na granicy HTTP. Test sprawdza co najmniej:

```python
assert response.status_code == expected_status
assert response.json()["error_code"] == expected_error_code
```

Jeżeli `detail` jest częścią stabilnego kontraktu, sprawdzamy całe ciało. Błędy walidacji
Pydantic mają wspólny kod `VALIDATION_ERROR`. Test serwisu osobno potwierdza warunek wywołujący
wyjątek oraz rollback, gdy operacja rozpoczęła transakcję.

## Macierz pokrycia

| Obszar | Integracyjne API/DB | Jednostkowe service | Status |
|---|---|---|---|
| Rejestracja: utworzenie, zamknięte zapisy, duplikat | tak | tak | zaimplementowane |
| Rejestracja: wymagane/obce pytania | tak | tak | zaimplementowane |
| Rejestracja: consent i limit pojemności | nie | nie | brak tych reguł w domenie/API |
| Drużyna: create, join, full, name taken | tak, przez utworzenie zgłoszenia | tak | zaimplementowane |
| Drużyna: confirm, leave, remove | nie | nie | brak operacji i endpointów |
| Jedna drużyna użytkownika na hackathon | tak, przez unique zgłoszenia użytkownika | tak | obecny model używa `Registration.team_id` |
| `unique(user_id, hackathon_id)` | tak | mapowanie błędu w service | zaimplementowane |
| `unique(hackathon_id, normalized_name)` | nie | nie | model ma tylko `unique(hackathon_id, name)` |
| Zasób: add/import/assign/revoke/reveal/permission | nie | nie | brak modułu zasobów |

Po dodaniu brakującej funkcji jej PR powinien jednocześnie zmienić odpowiedni wiersz na
„zaimplementowane” i dodać test głównej ścieżki, błędów oraz constraintów. Testy nie powinny
zakładać kontraktu funkcji, której nie ma jeszcze w modelu, migracji i API.
