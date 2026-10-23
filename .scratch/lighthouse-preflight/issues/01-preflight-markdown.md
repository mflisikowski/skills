# 01 — Wiarygodny preflight z raportem Markdown

Status: resolved
Blocked by: none
Type: task

## What to build

Agent wykonuje kontrolę URL i tworzy raport Markdown wraz z dowodami JSON. Ocena pokrycia ujawnia pominięte zasoby i pozostaje zgodna z instrukcjami skilla. Zakres wynika z [zatwierdzonej specyfikacji](../spec.md).

## Acceptance criteria

- [x] Pominięte zasoby z innego źródła nie pozwalają uznać zadeklarowanego pokrycia za kompletne; jawnie dodane zasoby są rozliczane poprawnie.
- [x] Ograniczony zakres, brak JS/CSS i awaria połączenia mają wyraźną interpretację bez fałszywego potwierdzenia kompletności.
- [x] Powstają Markdown i JSON również przy negatywnym wyniku kontroli.
- [x] Raport zawiera dowody, ograniczenia i zalecenia; odróżnia jakość transportu od możliwości pomiaru.
- [x] Rejestrowane są dostępne czasy etapów, protokół i nagłówki cache wraz z ostrożną interpretacją.
- [x] Zachowano istniejący interfejs helpera i poprawne dotychczasowe zachowanie.
- [x] Testy z rzeczywistymi żądaniami do lokalnych serwerów i repozytoryjna walidacja przechodzą.

## Comments

- 2026-10-23: Użytkownik zatwierdził podział i testowanie przez interfejs procesu oraz wygenerowane artefakty.

## Completion evidence

- Test regresji najpierw potwierdził fałszywy `PASS`, a po poprawce sprawdził `INCONCLUSIVE` dla pominiętego zasobu i `PASS` po objęciu go badaniem.
- Testy potwierdziły pliki Markdown i JSON dla `PASS`, `BLOCKED` oraz `INCONCLUSIVE`.
- Wszystkie 20 testów helpera przeszły z rzeczywistym curl i lokalnym serwerem; zachowano 17 wcześniejszych kontraktów.
- Repozytoryjny `python3 scripts/check.py` przeszedł walidację katalogu, 5 testów walidatora, 6 testów procesu audytu i 20 testów helpera. Testy przeglądarkowe były sprawdzane osobno.
