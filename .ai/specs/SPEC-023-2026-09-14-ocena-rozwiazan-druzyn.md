# SPEC-023: Ocena rozwiązań drużyn

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

Oceny pozostają robocze i są widoczne wyłącznie właścicielowi hackathonu, współorganizatorom
oraz administratorom do czasu jawnej publikacji wyników. Moment publikacji jest zapisywany w
polu `Hackathon.evaluations_published_at`. Po publikacji uczestnik może zobaczyć wyłącznie
oceny i feedback dotyczące rozwiązań własnej drużyny.

Zmiana linku rozwiązania po jego wcześniejszym ocenieniu unieważnia ocenę: `score`, `feedback`,
`evaluated_at` i `evaluated_by_id` są czyszczone. Zapobiega to pozostawieniu oceny dotyczącej
starszej wersji rozwiązania.

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

`Hackathon` otrzymuje pole:

- `evaluations_published_at: datetime | None` — `None` oznacza wyniki robocze.

## Kontrakt API

- `PATCH /api/hackathons/{hackathon_public_id}/tasks/{task_public_id}/submissions/{submission_public_id}/evaluation`
  — tworzy albo aktualizuje ocenę rozwiązania;
- `POST /api/hackathons/{hackathon_public_id}/evaluations/publish` — publikuje wyniki
  uczestnikom;
- `GET /api/hackathons/{hackathon_public_id}/task-submissions` — zwraca osobie zarządzającej
  wszystkie rozwiązania hackathonu wraz z zadaniem, drużyną i oceną, bez wykonywania osobnego
  żądania dla każdego zadania;
- istniejąca strefa uczestnika zwraca ocenę jego drużyny dopiero po publikacji wyników.

Endpointy zarządzające wykorzystują istniejące `can_manage_hackathon()`. Przy pobieraniu i
ocenianiu backend sprawdza cały łańcuch `submission → task → hackathon`, aby identyfikatory
zasobów z różnych hackathonów nie mogły zostać połączone w jednym żądaniu.

## Zakres

**W zakresie:**

- pola oceny, feedbacku, audytu oceniającego i publikacji wyników;
- migracja Alembic wraz z ograniczeniem zakresu punktów;
- zapis i edycja oceny przez właściciela, współorganizatora lub administratora;
- jawna publikacja wyników na poziomie hackathonu;
- prezentacja uczestnikowi wyłącznie oceny jego drużyny po publikacji;
- zbiorczy odczyt rozwiązań dla panelu organizatora;
- połączenie rozwiązań drużyn z frontendowym panelem obecności QR;
- testy modelu, repozytorium, serwisu, endpointów i interfejsu.

**Poza zakresem:**

- ranking i leaderboard drużyn;
- automatyczne sumowanie i wyłanianie zwycięzców;
- definiowanie kryteriów lub wag ocen przez organizatora;
- historia kolejnych wersji oceny i linku;
- automatyczna analiza repozytorium GitHub;
- uzależnianie prawa do oceny albo widoczności rozwiązania od check-inu;
- indywidualne oceny członków drużyny.

## Wpływ

- **Frontend:** panel obecności grupuje dane według drużyn i umożliwia rozwinięcie ich rozwiązań,
  zapis punktów i feedbacku oraz publikację wyników. Uczestnik widzi ocenę we własnej strefie
  dopiero po publikacji.
- **Backend:** moduł `hackathon_tasks` otrzymuje obsługę ocen, zbiorczy odczyt rozwiązań,
  kontrolę publikacji oraz czyszczenie nieaktualnej oceny po zmianie linku.
- **Baza danych:** nowe nullable pola w `task_submissions` i `hackathons`, klucz obcy osoby
  oceniającej oraz ograniczenie `score` do zakresu 0–10.
- **Bezpieczeństwo:** zapis i roboczy odczyt ocen są dostępne wyłącznie zarządzającym, a
  uczestnik może odczytać tylko opublikowane wyniki własnej drużyny.

## Alternatywy rozważane

- Osobna tabela ocen — odrzucona dla pierwszej wersji, ponieważ jedno rozwiązanie ma jedną
  aktualną ocenę i nie przechowujemy historii zmian.
- Ocena per uczestnik — odrzucona, ponieważ `TaskSubmission` jest wspólne dla drużyny.
- Osobne kryteria z wagami — odłożone jako przyszłe rozszerzenie; prosta skala 0–10 pozwala
  domknąć podstawowy przepływ bez narzucania systemu oceniania organizatorowi.
- Pobieranie zgłoszeń osobno dla każdego zadania — odrzucone w panelu organizatora, ponieważ
  prowadzi do liczby żądań zależnej od liczby zadań.

## Changelog

- 2026-09-14 — utworzono spec oceny rozwiązań i integracji z panelem obecności QR.
