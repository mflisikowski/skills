# 02 — Pełny audyt Lighthouse wykonywany przez agenta

Status: resolved
Blocked by: 01 — Wiarygodny preflight z raportem Markdown
Type: task

## What to build

Użytkownik podaje URL, a agent sam przeprowadza preflight i Lighthouse oraz oddaje raport Markdown ze źródłowymi danymi. Zakres wynika z [zatwierdzonej specyfikacji](../spec.md).

## Acceptance criteria

- [x] Agent wykrywa lub przygotowuje odizolowane narzędzia, bez zmiany zależności aplikacji.
- [x] Domyślnie wykonuje trzy kolejne pomiary mobilne, zapisuje każdą próbę, warunki, wersje, mediany i rozrzut; obsługuje jawny wybór desktopu lub liczby prób.
- [x] Sprawdza dostępność właściwego scenariusza w przeglądarce; problemy kompresji nie zatrzymują same w sobie diagnostycznego pomiaru.
- [x] Niedostępność strony, błędny scenariusz, brak narzędzi i awaria pomiaru kończą się raportem z przyczyną i zachowanymi dowodami.
- [x] Raport w języku rozmowy zawiera wyniki, dowody, priorytety, zalecenia i sposób weryfikacji poprawek.
- [x] Analiza istniejących raportów działa bez kontroli live i oznacza historyczny charakter danych.
- [x] Rzeczywisty Lighthouse i przeglądarka działają na kontrolowanej stronie; porównano dwa warianty dostarczania materiałów bez zakładania konkretnego wzrostu punktacji.
- [x] Pakiet działa po przeniesieniu, zasoby i licencja są kompletne, katalog i dokumentacja odpowiadają nowemu zachowaniu.
- [x] Audyt reprezentatywnej publicznej strony zostaje wykonany po otrzymaniu jej URL; brak adresu nie blokuje implementacji ani lokalnej walidacji.

## Comments

- 2026-10-23: Użytkownik zatwierdził rozszerzenie istniejącego skilla oraz proponowane domyślne ustawienia.
- 2026-10-23: Użytkownik wskazał https://test-wybieramsen.nekk.pl/ do końcowego audytu.

## Completion evidence

- `python3 scripts/check.py`: katalog poprawny, 5 testów walidatora, 8 testów procesu audytu i 20 testów HTTP przeszło. Trzy testy rzeczywistej przeglądarki są domyślnie pomijane i zostały wykonane osobno.
- Rzeczywisty test po przeniesieniu całego katalogu skilla: trzy przebiegi mobile oraz jeden desktop. Zbadano gzip i brak kompresji; treść JS miała odpowiednio 998 B i 380 023 B, a oba audyty diagnostyczne się zakończyły. Nie porównywano punktacji między różnymi profilami.
- Włączona ścieżka `LIGHTHOUSE_TEST_BOOTSTRAP=1` przygotowała Lighthouse w pustym katalogu bez zmiany zależności aplikacji. Dowody testu: `../artifacts/live-03/` (artefakty generowane, ignorowane przez Git).
- Testy prawdziwej przeglądarki potwierdziły raport dla niewłaściwej treści i brakującego Chrome. Osobny test zachowania fragmentu URL przeszedł z rzeczywistym Lighthouse.
- Przegląd dwóch osi wykrył trzy odrębne usterki: utratę fragmentu URL, możliwość nadpisania importowanego źródła oraz błąd renderowania przy nieprawidłowych polach. Wszystkie naprawiono; testy regresji najpierw potwierdziły błąd, a następnie przeszły. [Wynik przeglądu](../review.md).
- Agent wykonał trzy mobilne pomiary wskazanej strony oraz uzupełniającą kontrolę 23 adresów HTTP. [Gotowy raport po polsku](../artifacts/wybieram-sen-01/report.md), dane i logi są zachowane lokalnie.
- Publiczny przebieg potwierdził potrzebę kontroli JS i API niewidocznych w początkowym skanie HTML. Instrukcja wymaga teraz porównania z `network-requests`, zachowania osobnego preflightu uzupełniającego oraz jawnego oznaczenia jego czasu względem Lighthouse.
- Mediany dla strony testowej: Performance 76, Accessibility 97, Best Practices 100, SEO 69; LCP około 4,29 s. Potwierdzono nieskompresowane JSON API; blokada indeksowania środowiska testowego pozostała częścią opisanego scenariusza.
