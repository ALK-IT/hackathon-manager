# SPEC-031: Samodzielna zmiana drużyny

Status: Zaimplementowany
Issue: #189

## Problem

Zmiana drużyny wymagała wycofania i ponownego wysłania zgłoszenia.

## Rozwiązanie i zakres

PATCH `/api/hackathons/{public_id}/registrations/me/team`, body `join_code`, sukces 204.
Tylko własne ACCEPTED, aktywny hackathon z włączonymi drużynami, przed start_date.
Kod musi wskazywać drużynę tego samego hackathonu. PENDING i ACCEPTED zajmują
miejsca, REJECTED nie. Ten sam kod jest bezpiecznym no-op. Nie zmieniamy statusu,
odpowiedzi, identyfikatora zgłoszenia ani obecności.

Transakcja blokuje hackathon, zgłoszenie i obie drużyny (rosnąco po id).
Po uzyskaniu blokad ponownie sprawdza termin. Nieudana zmiana jest wycofywana.
Usuwa starą drużynę tylko bez jakichkolwiek zgłoszeń, zasobów i rozwiązań;
historia nie jest kasowana. Zasoby przypisane drużynie nie przenoszą się z osobą.

## Frontend

Komponent ChangeTeamForm przy drużynie w ParticipantAreaPage, neutralne przyciski.
Kod → Akceptuj → jawne potwierdzenie → zapis → odświeżenie widoku.
Brak przycisku po rozpoczęciu. Blokada wielokrotnego wysłania, obsługa błędów,
teksty PL/EN. Brak zmian w HackathonDetailsPage.

## Alternatywy i wpływ

Wycofanie zgłoszenia traci akceptację; zmiany podczas wydarzenia komplikują dostęp
do rozwiązań i zasobów — poza zakresem. Nie potrzeba migracji. Testy backendu
obejmują autoryzację, limity i równoległe zmiany, frontend potwierdzenie i anulowanie.
