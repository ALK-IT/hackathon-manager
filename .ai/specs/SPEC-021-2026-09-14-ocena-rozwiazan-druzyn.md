# SPEC-021: Ocena rozwiązań drużyn

**Status:** Zaakceptowany  
**Data:** 2026-09-14  
**Autor:** Mateusz Guzowski

## Kontekst / problem

Moduł zadań pozwala osobom zarządzającym hackathonem publikować zadania, a zaakceptowanym
uczestnikom przesyłać po jednym linku do rozwiązania dla każdej pary drużyna–zadanie. System
nie przechowuje jednak oceny ani informacji zwrotnej, przez co organizator musi oceniać
rozwiązania poza aplikacją.

Panel obecności QR pokazuje już zaakceptowanych uczestników pogrupowanych według drużyn oraz
informację, kto fizycznie pojawił się na wydarzeniu. Jest naturalnym punktem wejścia do
przeglądania rozwiązań podczas hackathonu, ale rozwiązanie i jego ocena należą do całej drużyny,
a nie do pojedynczego uczestnika.

## Rozwiązanie

Każde `TaskSubmission` może otrzymać ocenę punktową od 0 do 10 oraz opcjonalny feedback.
Zapisywane są także czas wystawienia oceny i osoba oceniająca. Brak wartości `score` oznacza,
że rozwiązanie nie zostało jeszcze ocenione.

Ocenianie jest dostępne dopiero po zakończeniu hackathonu (`now >= end_date`). Wcześniejsza
próba zwraca `409 TASK_EVALUATION_NOT_OPEN`. Podczas wydarzenia organizator może przeglądać
rozwiązania, a uczestnicy mogą zmieniać linki. Po zakończeniu linki są zablokowane, więc
nie implementujemy czyszczenia oceny po zmianie linku.

Uczestnik widzi ocenę i feedback własnej drużyny od razu po ich zapisaniu. Osobny etap
publikacji wyników jest poza zakresem tej wersji.

Widok obecności organizatora zostanie rozszerzony o możliwość rozwinięcia rozwiązań danej
drużyny. Status check-inu jest informacją pomocniczą i nie wpływa na możliwość podglądu ani
oceny rozwiązania.

## Model danych

`TaskSubmission` otrzymuje pola:

- `score: Decimal | None` — wynik od `0.00` do `10.00`, z dokładnością do dwóch miejsc po
  przecinku i ograniczeniem zakresu również w bazie;
- `feedback: str | None` — opcjonalna informacja zwrotna;
- `evaluated_at: datetime | None` — ustawiane dopiero podczas zapisu oceny;
- `evaluated_by_id: int | None` — klucz obcy do `users.id` z `ON DELETE SET NULL`.

Istniejące pole `Hackathon.evaluations_published_at` z wcześniejszego etapu prac nie jest
używane w tej wersji. Usunięcie go wymaga osobnej migracji porządkowej.

## Kontrakt API

- `PATCH /api/hackathons/{hackathon_public_id}/tasks/{task_public_id}/submissions/{submission_public_id}/evaluation`
  — tworzy albo aktualizuje ocenę rozwiązania po zakończeniu hackathonu;
- `GET /api/hackathons/{hackathon_public_id}/task-submissions` — zwraca osobie zarządzającej
  wszystkie rozwiązania hackathonu wraz z zadaniem, drużyną i oceną, bez wykonywania osobnego
  żądania dla każdego zadania;
- istniejąca strefa uczestnika zwraca ocenę jego drużyny od razu po zapisaniu oceny.

Zbiorcza odpowiedź zawiera `task` (public_id, title), `team` (public_id, name), autora,
link, daty i `evaluation`. Brak oceny oznacza `evaluation: null`; wynik `0` jest oceną.
Wyniki są sortowane po identyfikatorze drużyny, zadania i rozwiązania.

Obie listy rozwiązań (`task-submissions` oraz `tasks/{task_public_id}/submissions`)
zwracają `{items, total, limit, offset}`. Parametr `limit` ma domyślnie 50 i zakres 1–100,
a `offset` domyślnie 0 i minimum 0. `total` opisuje wszystkie wyniki po filtrowaniu,
także gdy strona jest pusta. Paginacja odbywa się w bazie danych.
Zbiorczy endpoint przyjmuje opcjonalne filtry `team_public_id`, `task_public_id` i
`evaluated` (true — ocenione, false — nieocenione, brak — wszystkie). Filtry łączą się
przez AND i nie pozwalają wyjść poza wskazany hackathon. Niepasujący UUID zwraca pustą listę.
Ocena 0 zalicza się do ocenionych. Lista jednego zadania ma stabilne sortowanie
po `updated_at DESC, id`. Frontend korzysta ze zbiorczego endpointu `task-submissions`.

### Widoki frontendu

- `/hackathons/:id/solutions` — widok organizatora, współorganizatora lub administratora;
  podczas wydarzenia tylko podgląd, po końcu także formularze ocen 0–10 i feedbacku.
- Link przy drużynie w panelu obecności wybiera filtr drużyny. Lista ma strony po 20
  rozwiązań oraz filtry zadania i stanu oceny. Zmiana filtrów resetuje stronę,
  zapis oceny odświeża wyniki (także przy filtrze „nieocenione”).
- Strefa uczestnika po końcu wydarzenia udostępnia „Zobacz wyniki” i odświeżanie:
  zadania, własne linki, oceny oraz feedback. Rozróżniamy brak rozwiązania i brak oceny.
- Przycisk na kafelku zaakceptowanego uczestnika po końcu prowadzi do wyników.
- Czas jest sprawdzany lokalnie, bez cyklicznego odpytywania API. Backend pozostaje
  autorytetem dla uprawnień i dat. Nie zapisujemy rozwiązań ani ocen w localStorage.
- Indywidualny udział bez drużyny oraz automatyczne tworzenie drużyn jednoosobowych
  pozostają poza zakresem. Nie zmieniamy backendu zapisów ani zasobów.

Endpointy zarządzające wykorzystują istniejące `can_manage_hackathon()`. Przy pobieraniu i
ocenianiu backend sprawdza cały łańcuch `submission → task → hackathon`, aby identyfikatory
zasobów z różnych hackathonów nie mogły zostać połączone w jednym żądaniu.

## Zakres

**W zakresie:**

- pola oceny, feedbacku i audytu oceniającego;
- migracja Alembic wraz z ograniczeniem zakresu punktów;
- zapis i edycja oceny przez właściciela, współorganizatora lub administratora;
- prezentacja uczestnikowi wyłącznie oceny jego drużyny po zapisaniu;
- zbiorczy odczyt rozwiązań dla panelu organizatora;
- połączenie rozwiązań drużyn z frontendowym panelem obecności QR;
- testy modelu, repozytorium, serwisu, endpointów i interfejsu.

**Poza zakresem:**

- oddzielna publikacja i ukrywanie zapisanych ocen;
- ranking i leaderboard drużyn;
- automatyczne sumowanie i wyłanianie zwycięzców;
- definiowanie kryteriów lub wag ocen przez organizatora;
- historia kolejnych wersji oceny i linku;
- automatyczna analiza repozytorium GitHub;
- uzależnianie prawa do oceny albo widoczności rozwiązania od check-inu;
- indywidualne oceny członków drużyny.

## Wpływ

- **Frontend:** panel obecności grupuje dane według drużyn i umożliwia rozwinięcie ich rozwiązań,
  zapis punktów i feedbacku po zakończeniu wydarzenia. Uczestnik widzi zapisaną ocenę
  we własnej strefie.
- **Backend:** moduł `hackathon_tasks` otrzymuje obsługę ocen, zbiorczy odczyt rozwiązań,
  oraz blokadę oceniania przed końcem wydarzenia.
- **Baza danych:** nowe nullable pola w `task_submissions` i `hackathons`, klucz obcy osoby
  oceniającej oraz ograniczenie `score` do zakresu 0–10.
- **Bezpieczeństwo:** zapis ocen i zbiorczy odczyt rozwiązań są dostępne wyłącznie
  zarządzającym, a uczestnik może odczytać tylko wyniki własnej drużyny.

## Alternatywy rozważane

- Osobna tabela ocen — odrzucona dla pierwszej wersji, ponieważ jedno rozwiązanie ma jedną
  aktualną ocenę i nie przechowujemy historii zmian.
- Ocena per uczestnik — odrzucona, ponieważ `TaskSubmission` jest wspólne dla drużyny.
- Osobne kryteria z wagami — odłożone jako przyszłe rozszerzenie; prosta skala 0–10 pozwala
  domknąć podstawowy przepływ bez narzucania systemu oceniania organizatorowi.
- Pobieranie zgłoszeń osobno dla każdego zadania — odrzucone w panelu organizatora, ponieważ
  prowadzi do liczby żądań zależnej od liczby zadań.

## Changelog

- 2026-09-15 — dodano frontend podglądu, oceniania i wyników. Weryfikacja:
  144 testy frontendu, build i ESLint; test przeglądarkowy zapisu oceny oraz
  odczytu wyników na kontrolowanych atrapach API. Bez zmian backendu i prawdziwych danych.

- 2026-09-14 — doprecyzowano ocenianie po końcu wydarzenia, bez osobnej publikacji;
  dodano zbiorczy odczyt i jawne składanie odpowiedzi z oceną.
- 2026-09-14 — utworzono spec oceny rozwiązań i integracji z panelem obecności QR.
