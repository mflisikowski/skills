# Weryfikacja lighthouse-check przed automatyzacją audytu

Data: 2026-10-23.

## Wniosek

`lighthouse-check` jest przydatną podstawą do badania kompresji i poprawności odpowiedzi HTTP. Obecny pakiet nie definiuje jednak całego oczekiwanego zachowania: użytkownik podaje URL, agent przygotowuje narzędzia, wykonuje kontrolę wstępną i Lighthouse, a następnie zapisuje raport Markdown.

Przegląd obejmuje instrukcje i kod oraz wykonanie testów. Nie zmieniono opublikowanego skilla ani helpera. Nie wykonano audytu publicznej strony i nie uruchomiono Lighthouse.

## Założenie produktowe

Terminal i przeglądarka są narzędziami agenta. Użytkownik nie ma sam uruchamiać komend, eksportować wyników ani kopiować plików. Brakujące informacje agent odczytuje z projektu, a do użytkownika kieruje tylko pytania, których nie da się rozstrzygnąć z dostępnego kontekstu.

W tym badaniu brakowało adresu docelowej strony, ale nie przeszkadzało to w weryfikacji lokalnego skilla i jego helpera.

## Co działa

- Instrukcje każą agentowi uruchomić bundlowany helper; pokazana komenda jest instrukcją dla agenta, a nie obowiązkiem użytkownika.
- Helper wykonuje rzeczywiste GET i mierzy pobrane oraz odkodowane bajty.
- Porównuje odkodowane statyczne zasoby z wariantem `identity` i wykrywa różnice.
- Wykrywa błędne statusy i typy odpowiedzi, w tym HTML zwrócony zamiast JS.
- Rozdziela kompresję od wskazówek dotyczących minifikacji i ograniczeń renderowania.
- Zapisuje dowody JSON, ogranicza liczbę zasobów i czas żądania.
- Posiada testy oparte na lokalnym serwerze HTTP i rzeczywistym curl.

## 1. Potwierdzona luka: pominięty zasób z innego źródła może zakończyć się PASS

Miejsce: [preflight.py](../../skills/lighthouse-check/scripts/preflight.py), pętla odkrywania zasobów, obecnie linie 185–204.

Zewnętrzny skrypt lub arkusz powoduje ostrzeżenie i zostaje pominięty. Ten przypadek nie ustawia `coverage_incomplete`. Gdy pozostałe zbadane zasoby przejdą kontrolę, wynik może wynosić `PASS`. Instrukcja skilla mówi jednocześnie, że częściowy skan nie może przejść.

Scenariusz reprodukcji: strona ma lokalne, skompresowane JS i CSS oraz nieskompresowany skrypt na drugim lokalnym serwerze, reprezentującym inne źródło. Uruchomiono dwa warianty na tej samej stronie:

| Wariant | Wynik | Obserwacja |
| --- | --- | --- |
| Samo automatyczne odkrywanie | `PASS`, kod 0 | Skrypt z drugiego źródła pominięty z ostrzeżeniem. |
| Ten sam skrypt dopisany przez `--asset` | `BLOCKED`, kod 1 | Wykryto `Text response is not compressed`. |

Dowody: [podsumowanie](evidence/summary.json), [odkrywanie](evidence/discovery-only.json), [jawny zasób](evidence/explicit-cdn.json). Odtwarzalny scenariusz: [verify_preflight.py](verify_preflight.py).

Znaczenie: sam kod 0 nie wystarcza jako automatyczne potwierdzenie kompletności kontroli zasobów startowych. Ostrzeżenie ujawnia ograniczenie, ale instrukcje i status są niespójne.

Rekomendacja: określić badany zbiór i obsługę pominiętych adresów. Agent może rozszerzyć próbkę o jawnie odkryte, istotne zasoby z innych źródeł w ustalonych limitach. Jeżeli pozostają niezbadane zasoby wymagane przez przyjęty zakres, wynik pokrycia powinien to odzwierciedlać. Nie wymagać od użytkownika ręcznego dopisywania `--asset`.

## 2. Brak obowiązkowego artefaktu Markdown

Miejsce: sekcja Output w [SKILL.md](../../skills/lighthouse-check/SKILL.md), obecnie linie 93–98, oraz obsługa `--output` w helperze, obecnie linie 254–257.

Helper zapisuje JSON. Instrukcja wymaga podsumowania i ścieżek artefaktów, ale nie nakazuje zapisania pliku `.md` ani nie definiuje miejsca zapisu. Agent może więc zakończyć pracę samą odpowiedzią w rozmowie.

Rekomendacja: obowiązkowy raport Markdown także przy przerwaniu audytu. Raport powinien zawierać zakres, etap osiągnięty, dowody, problemy, zalecenia i ograniczenia oraz odnośniki do JSON. Brak pomiaru musi mieć przyczynę, a nie sztuczny wynik 0/100.

## 3. Ścieżka uruchomienia Lighthouse jest warunkowa

Miejsce: [SKILL.md](../../skills/lighthouse-check/SKILL.md), obecnie linie 75–82, oraz wymagania w README.

Skill może korzystać z zainstalowanego workflow Lighthouse i opisuje pomiary. Instalacja narzędzi jest jednak wyłączona z jego domyślnego zakresu; pakiet nie zawiera wykonawcy audytu. Nie gwarantuje to zakończenia zadania w projekcie, który nie ma jeszcze przygotowanego Lighthouse.

Rekomendacja dla przyszłego skilla: agent wykrywa istniejące narzędzia i przeglądarkę, odczytuje wersje i wybiera odtwarzalny sposób uruchomienia. Gdy potrzebne jest przygotowanie narzędzi, robi to w ramach autoryzacji i uprawnień środowiska. Nie zmienia zależności aplikacji tylko po to, by przeprowadzić pomiar. Zapisuje wersje i ustawienia obok wyników.

Nie stwierdzono, że Lighthouse jest niedostępny na tym komputerze; oceniono brak kompletnej procedury w samym skillu.

## 4. Akceptacja wdrożenia i pomiar diagnostyczny wymagają osobnych reguł

Miejsce: [SKILL.md](../../skills/lighthouse-check/SKILL.md), obecnie linie 57–61.

Obecna instrukcja zatrzymuje domyślny audyt na `BLOCKED` lub `INCONCLUSIVE`. Pomiar bazowy mimo porażki wymaga osobnej prośby użytkownika. Jest to świadoma reguła akceptacji wdrożenia, a nie wykazany błąd helpera.

W przyszłym skillu do ogólnego audytu taki warunek może zatrzymać pracę już na braku kompresji, choć właśnie wpływ tej usterki warto zmierzyć. Regułę należy dobrać do celu:

- Przy akceptacji: usterka transportu może blokować pozytywny werdykt.
- Przy audycie diagnostycznym: zachować usterkę i kontynuować pomiar, jeśli oczekiwana strona jest dostępna i scenariusz da się potwierdzić.
- Gdy oczekiwana treść jest niedostępna albo zastąpiona inną stroną: wstrzymać pomiar docelowej strony i zapisać przyczynę.

Raport powinien oddzielać gotowość do pomiaru, kompletność pokrycia i jakość wdrożenia.

## 5. Helper sprawdza przede wszystkim kompresję

Są to granice obecnego zakresu, a nie naruszenia jego deklarowanego celu:

- `Cache-Control` i `ETag` są zachowywane, ale helper nie ocenia polityki cache ani rewalidacji.
- Zapisywany jest `time_total`; brak rozbicia na DNS, połączenie, TLS i pierwszy bajt oraz brak wynegocjowanej wersji HTTP w raporcie.
- Odkrywanie obejmuje wybrane odwołania w HTML. Nie obejmuje automatycznie obrazów, fontów, zależności CSS i zasobów dodanych przez JS.
- Odpowiedź HTML ze statusem 200 nie jest samodzielnym potwierdzeniem oczekiwanej treści. Obecny skill kieruje w tym celu do kontroli w przeglądarce, ale tej fazy nie wykonano w niniejszym badaniu.

Przyszły raport powinien wyraźnie oddzielać to, co zmierzono przez HTTP, od obserwacji z przeglądarki i danych Lighthouse.

## Walidacja wykonana przez agenta

Polecenie repozytoryjne: `python3 scripts/check.py`.

- Walidacja katalogu: poprawna.
- Testy walidatora: 5/5 poprawnych.
- Testy helpera: 17/17 poprawnych.
- Dodatkowa reprodukcja z dwoma lokalnymi źródłami: potwierdzono różnicę `PASS` → `BLOCKED` po jawnym dodaniu pominiętego skryptu.

Sandbox początkowo uniemożliwił otwarcie lokalnego portu. Testy i reprodukcję wykonano po eskalacji uprawnienia do lokalnych serwerów testowych. Nie kontaktowano się z publiczną stroną użytkownika.

Podstawa techniczna została sprawdzona przez OpenSRC: lista cache, a następnie ścieżki i odpowiednie źródła:

- `lighthouse@13.5.0`: `cli/cli-flags.js`, `core/config/default-config.js`, `core/lib/lh-error.js`.
- `github.com/curl/curl@curl-8_7_1`: `docs/cmdline-opts/compressed.md`, `src/tool_writeout.c`.
- `github.com/python/cpython@v3.14.8`: `Lib/http/server.py`, `Lib/subprocess.py`.

Rzeczywisty Python: 3.14.8. Rzeczywisty curl: 8.7.1 z zlib; lista funkcji tego wykonawcy nie zawiera Brotli ani zstd. Ten przebieg weryfikuje więc gzip, a nie wszystkie kodeki Chrome. Repozytorium nie przypina wersji wykonawczej Lighthouse; wersja 13.5.0 jest odczytaną wersją źródeł.

## Następny zakres implementacji

Zachować istniejący helper jako punkt wyjścia. Najpierw ujednolicić zasady pokrycia i raportowania. Następnie dodać agentowi kompletną ścieżkę wykonania Lighthouse, zapis danych i utworzenie raportu Markdown. Test wykonany na reprezentatywnej stronie powinien potwierdzić, że użytkownik podaje tylko cel oraz URL i otrzymuje plik bez ręcznej obsługi narzędzi.

To wynik weryfikacji i propozycja dalszej pracy; opisane rozszerzenia nie zostały jeszcze zaimplementowane.

## Późniejsza implementacja

Po zatwierdzeniu specyfikacji rozpoczęto zadania [01](issues/01-preflight-markdown.md) i [02](issues/02-automated-lighthouse.md). Opisane wyżej wyniki `PASS` → `BLOCKED` dokumentują stan przed poprawką. Skrypt reprodukcji sprawdza teraz poprawione zachowanie: `INCONCLUSIVE` przy pominięciu zewnętrznego zasobu oraz `BLOCKED` po objęciu nieskompresowanego skryptu badaniem. Końcowe dowody będą rejestrowane w zadaniach.
