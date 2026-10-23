# Automatyczny audyt dostarczania strony i Lighthouse

Status: resolved

Zatwierdzone przez użytkownika 2026-10-23: rozbudowa jednego skilla, dwa zadania w podanej kolejności oraz testy przez interfejs procesu i artefakty. Oba zadania zakończone; dowody są zapisane w ich sekcjach Completion evidence.

## Problem Statement

Użytkownik chce zlecić agentowi audyt strony i otrzymać opis wyników w pliku Markdown. Agent ma sam używać terminala i przeglądarki. Przed Lighthouse ma sprawdzić, co serwer faktycznie dostarcza: dokument HTML i jego zasoby.

Obecny published skill `lighthouse-check` zawiera działający helper kompresji, ale jego wynik nie zawsze odzwierciedla pominięte zasoby. Nie wymaga też raportu Markdown i nie określa całej ścieżki uruchomienia Lighthouse w nieprzygotowanym środowisku.

Dowody i kontekst: [research](research.md), [weryfikacja](verification.md).

## Solution

Proponowane rozwiązanie to rozbudowa istniejącego `lighthouse-check`. Użytkownik podaje URL i cel badania. Agent sam wykonuje preflight, potwierdza scenariusz, uruchamia Lighthouse i zapisuje raport Markdown wraz ze źródłowymi danymi.

Zlecenie kontroli wstępnej kończy się raportem preflight. Zlecenie pełnego audytu przechodzi przez obie fazy. Wynik opisuje osobno jakość wdrożenia, pokrycie kontroli i możliwość wykonania pomiaru. Każda ścieżka, również nieudana, kończy się zapisaniem raportu.

Rozbudowa istniejącego skilla została zatwierdzona. Postęp implementacji jest rejestrowany w zadaniach.

## User Stories

1. Jako użytkownik chcę podać URL zwykłym poleceniem, aby agent sam przeprowadził audyt.
2. Jako użytkownik chcę zlecić samą kontrolę serwowanych materiałów, aby poznać problemy przed pomiarem Lighthouse.
3. Jako użytkownik chcę, by agent sam odczytał dostępne narzędzia i ustawienia projektu, aby nie przygotowywać ręcznie środowiska.
4. Jako użytkownik chcę dostać plik Markdown również po nieudanym audycie, aby znać przyczynę i dalsze działanie.
5. Jako użytkownik chcę wiedzieć, jakie zasoby zbadano i jakie pominięto, aby poprawnie rozumieć zakres wyniku.
6. Jako użytkownik chcę wiedzieć, czy HTML, JS i CSS są dostępne, poprawnie oznaczone i kompresowane, aby wykryć błędy dostarczania strony.
7. Jako użytkownik chcę otrzymać obserwowane zasady cache i ich interpretację, aby odróżniać fakty od zaleceń optymalizacji.
8. Jako użytkownik chcę otrzymać rozmiary odpowiedzi i jasno nazwane czasy, aby wskazać ciężkie zasoby bez mylenia ich z metrykami Lighthouse.
9. Jako użytkownik chcę, aby agent potwierdził właściwą stronę i scenariusz, aby nie audytować przypadkowo logowania lub blokady dostępu.
10. Jako użytkownik chcę zachować bazowy pomiar mimo usterek wydajności, aby porównać go później z wynikiem po poprawkach.
11. Jako użytkownik chcę widzieć wersje, ustawienia, liczbę prób i rozrzut wyników, aby oceniać porównywalność pomiarów.
12. Jako użytkownik chcę zalecenia powiązane z dowodami i sposobem ponownej weryfikacji, aby wiedzieć, co poprawić i jak sprawdzić efekt.
13. Jako użytkownik chcę przekazać istniejący raport do analizy, aby otrzymać opis z wyraźnym wskazaniem czasu pomiaru i braku ewentualnej kontroli live.
14. Jako użytkownik chcę korzystać ze skilla po skopiowaniu całego jego katalogu do innego projektu, aby audyt nie zależał od plików lokalnego środowiska autora.

## Implementation Decisions

- Zachować nazwę i katalog istniejącego published skilla. Wydzielić fazy wewnątrz jego instrukcji i helperów, zachowując pakiet samowystarczalny.
- Agent wykonuje komendy i zarządza artefaktami. Pyta tylko o brakujący URL, dostęp lub scenariusz, jeśli nie da się ich ustalić z projektu i polecenia.
- Zachować istniejący interfejs kontroli HTTP, jeśli jego zmiana nie jest konieczna. Rozszerzenia danych powinny być addytywne; ewentualne zmiany znaczenia statusów wymagają jawnego opisania.
- Odkrywanie zasobów pozostaje ograniczone. Agent rozlicza pominięte adresy i może uzupełniać badanie o znane zasoby z innych źródeł w przyjętych limitach. Pominięcie zasobu należącego do zadeklarowanego zakresu wpływa na kompletność wyniku.
- Jawnie odróżniać kontrolę HTTP, obserwacje przeglądarki i wyniki Lighthouse. Dane jednego etapu nie zastępują dowodów pozostałych etapów.
- Pierwszy zakres preflight obejmuje dokument, wykryte JS/CSS, statusy, MIME, kompresję, rozmiary, obserwowane polityki cache oraz rozróżnione czasy i informacje o przekierowaniach, o ile wykonawca je udostępnia. Ograniczenia kodeków i pokrycia muszą trafić do raportu.
- Rozszerzenie interpretacji cache musi uwzględniać różnice między HTML, zasobami wersjonowanymi i odpowiedziami prywatnymi. Samo zachowanie nagłówka nie jest dowodem wykonania kontroli jego poprawności.
- W audycie diagnostycznym brak kompresji lub nieefektywny cache nie zatrzymuje sam w sobie pomiaru. Utrudnia pozytywną ocenę wdrożenia. Niedostępność właściwej strony albo niepotwierdzony scenariusz wstrzymują miarodajny pomiar tej strony.
- Preferować istniejące narzędzia projektu. Gdy ich brakuje, przygotować odizolowane narzędzia audytu w ramach uprawnień środowiska. Wybór wersji utrwalić i zapisać w wynikach; przygotowanie audytu nie zmienia zależności aplikacji.
- Lighthouse i przeglądarka muszą mieć zapisane wersje. Sprawdzić ich wymagania w źródłach przed implementacją. Po weryfikacji źródeł przez OpenSRC przypięto Lighthouse 13.5.0 w manifeście odizolowanych narzędzi.
- Domyślny pierwszy zakres: anonimowa nawigacja publicznej strony, profil mobilny, trzy kolejne pomiary przy tych samych ustawieniach. Zapisywać wszystkie próby, mediany metryk i rozrzut. Wybór ten jest proponowaną konfiguracją workflow, a nie wymogiem Lighthouse. Desktop lub inna liczba prób mogą wynikać z polecenia.
- Zachować źródłowe dane każdego pomiaru. Raport Markdown powstaje na ich podstawie i nie wymyśla wyników przy błędzie lub brakujących danych.
- Raport w języku rozmowy zawiera podsumowanie, zakres, warunki, gotowość, ustalenia preflight, wyniki Lighthouse, zalecenia z priorytetami i weryfikacją, ograniczenia oraz odnośniki do artefaktów. Oddziela obserwacje od interpretacji i nie liczy tego samego problemu dwa razy.
- Zachować analizę dostarczonych raportów. Bez kontroli live wynik opisuje historyczny pomiar, a nie bieżące wdrożenie.
- Utrzymać wymagania katalogu, bundlowanej licencji i odkrywalności wymaganych zasobów.

## Testing Decisions

Zatwierdzony punkt kontroli to wywołanie helpera lub wykonawcy jako procesu i sprawdzenie jego wyniku oraz wygenerowanych artefaktów. Dla zachowania całego skilla sprawdzić realizację naturalnego zlecenia przez agenta.

- Rozbudować istniejące testy z lokalnym serwerem i rzeczywistym curl: poprawna kompresja, jej brak, błędne MIME, niedostępne zasoby, różne reprezentacje, limity pokrycia i zasób z drugiego źródła.
- Sprawdzać znaczenie danych, statusów i odnośników; unikać testów zależnych od dokładnej redakcji raportu.
- Sprawdzić kompletność artefaktów po prawidłowym pomiarze oraz po awarii wykonawcy, braku narzędzi i niedostępności strony.
- Co najmniej jeden przypadek wykonać z rzeczywistym Lighthouse i przeglądarką na kontrolowanej stronie. Dane zastępcze nie dowodzą działania pomiaru.
- Porównać dwie kontrolowane wersje dostarczania zasobów i sprawdzić, że raport prawidłowo opisuje zmierzone różnice, bez założenia dokładnego wzrostu punktacji.
- Sprawdzić pakiet po przeniesieniu do innego katalogu oraz przeprowadzić walidację repozytorium.
- Końcowo przeprowadzić audyt reprezentatywnej strony wskazanej przez użytkownika. Adres będzie potrzebny przy tym sprawdzeniu, nie przy tworzeniu lokalnych testów.

## Out of Scope

- Automatyczne poprawianie konfiguracji serwera lub kodu badanej aplikacji.
- Deployment, publikacja skilla, operacje GitHub i zmiany systemowe niezwiązane z wykonaniem audytu.
- Pełny crawl witryny, test obciążeniowy oraz audyt bezpieczeństwa.
- Automatyczne pokonywanie CAPTCHA, konfiguracja kont i budowa ogólnego mechanizmu uwierzytelniania.
- Zastąpienie danych rzeczywistych użytkowników laboratoryjnymi wynikami Lighthouse.

## Further Notes

Użytkownik wskazał https://test-wybieramsen.nekk.pl/. Agent wykonał tam trzy pomiary mobilne, kontrolę HTTP i analizę wyników; [gotowy raport](artifacts/wybieram-sen-01/report.md) jest lokalnym artefaktem generowanym.

### Zrealizowany podział na zadania

1. **Wiarygodny preflight z raportem Markdown.** Bez blokad. Użytkownik zleca kontrolę URL i otrzymuje raport oraz JSON ze spójną oceną pokrycia. Usunięta jest potwierdzona rozbieżność przy pominiętym zasobie z innego źródła. Testy obejmują oba lokalne źródła i granice zadeklarowanego zakresu.
2. **Pełny audyt wykonywany przez agenta.** Zablokowane przez zadanie 1. Agent przygotowuje lub wykorzystuje narzędzia, przeprowadza odpowiedni scenariusz, wykonuje Lighthouse i oddaje wspólny raport z danymi źródłowymi. Raport powstaje także po przerwaniu procesu. Kryteria obejmują rzeczywisty pomiar, zachowanie przy błędzie, analizę istniejących raportów i działanie pakietu po przeniesieniu.

Zadania: [01 — Preflight i Markdown](issues/01-preflight-markdown.md), [02 — Automatyczny audyt Lighthouse](issues/02-automated-lighthouse.md).
