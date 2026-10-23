# Kontrola dostarczania strony przed audytem Lighthouse

Data badania: 2026-10-23.

Status: research i propozycja metody. Nie wykonano audytu konkretnej strony ani nie uruchomiono Lighthouse. Po doprecyzowaniu sposobu pracy oceniono istniejący skill; wynik znajduje się w [raporcie weryfikacji](verification.md).

## Doprecyzowany sposób pracy

Użytkownik podaje cel audytu i adres strony. Agent sam odczytuje pliki, uruchamia narzędzia, wykonuje kontrolę wstępną i Lighthouse oraz tworzy raport Markdown. Użytkownik nie obsługuje ręcznie terminala ani przeglądarki. Wcześniejsze ograniczenie odczytano zbyt szeroko jako zakaz używania tych narzędzi również przez agenta.

## Cel i rekomendacja

Przed pomiarem Lighthouse warto sprawdzić, co rzeczywiście otrzymuje klient: dokument HTML, odpowiedzi HTTP oraz wskazane w dokumencie zasoby. To pozwala ustalić, czy pomiar obejmie właściwą stronę, oraz opisać jakość dostarczania jej plików.

Rekomendowana kolejność:

1. Potwierdzić adres, badaną treść i scenariusz użytkownika.
2. Zebrać odpowiedzi HTTP i próbkę zasobów bez uruchamiania JavaScriptu.
3. Oddzielić przeszkody uniemożliwiające miarodajny pomiar od usterek wydajności.
4. Zachować stan początkowy i, jeśli warunki pozwalają, wykonać Lighthouse.
5. Po poprawkach powtórzyć pomiar w porównywalnych warunkach.

Jest to propozycja workflow na podstawie źródeł, a nie oficjalny wymagany etap Lighthouse. Dokumentacja Chrome zaleca rozpoczęcie optymalizacji od pomiaru bazowego. Brak kompresji lub duży plik są przydatnymi ustaleniami, a nie powodem do usuwania śladów stanu początkowego. [S1]

## Co sprawdzać

| Obszar | Dowód do zebrania | Interpretacja |
| --- | --- | --- |
| Właściwy adres i dokument | URL wejściowy i końcowy, przekierowania, status, fragmenty identyfikujące oczekiwaną treść | Sam status 200 nie dowodzi, że otrzymano właściwą stronę. Logowanie, komunikat błędu lub blokada dostępu wymagają wyjaśnienia. |
| Dostępność | Błędy DNS, połączenia, certyfikatu i odpowiedzi serwera | Gdy docelowego dokumentu nie da się pobrać, raport powinien opisać przeszkodę. Kod Lighthouse rozpoznaje błędy dokumentu i zabezpieczeń. [S2] |
| Typ i treść zasobów | Status, `Content-Type`, treść odpowiedzi dla HTML, CSS i JS | Należy wykrywać np. dokument HTML zwrócony pod adresem skryptu. Typ odpowiedzi opisuje sposób interpretacji danych. [S3] |
| Kompresja | Wysłane `Accept-Encoding`, otrzymane `Content-Encoding`, możliwość odkodowania, rozmiar reprezentacji zakodowanej i odkodowanej | Sprawdzać faktyczne odpowiedzi. HTML, CSS, JS i SVG są dobrymi kandydatami; bardzo małe pliki mogą nie skorzystać. [S4] |
| Cache | `Cache-Control`, `Vary`, ewentualne `ETag` lub `Last-Modified`; wynik odpowiedniego żądania warunkowego | Rozróżnić zasoby wersjonowane, HTML oraz odpowiedzi prywatne. Jedna polityka dla wszystkich plików byłaby niewłaściwa. [S5] |
| Reprezentacja po negocjacji | Warianty odpowiedzi dla zadeklarowanej obsługi kompresji, odpowiednie `Vary` | Klient i cache muszą otrzymywać zgodny wariant danych. Nie wystarczy sprawdzić nazwy pliku `.br` na dysku. [S3] |
| Opóźnienia i przekierowania | Czasy etapów połączenia, oczekiwania na pierwszy bajt i pobrania; łańcuch przekierowań | Zachować warunki pomiaru. Pojedynczy czas nie ustala przyczyny opóźnienia po stronie aplikacji. Dokument request latency obejmuje już część tych problemów. [S6] |
| Zasoby produkcyjne | Metadane wdrożenia lub konfiguracja builda, jeśli dostępne; obserwowane pliki i oznaki trybu developerskiego | Zewnętrzna odpowiedź może dawać wskazówki. Sama minifikacja nie potwierdza produkcyjnego builda; przy braku dowodu zapisać niepewność. Dokumentacja Chrome pokazuje znaczenie trybu produkcyjnego. [S1] |
| Dostarczony HTML | Odwołania do skryptów, arkuszy, obrazów i fontów; wskazówki ładowania | Można ocenić deklaracje i odkrywalność zasobów. Faktyczna kolejność ładowania wymaga późniejszej obserwacji przeglądarki. [S7] |
| Obrazy | Wymiary plików, format, bajty, `srcset`, `sizes`, deklaracje ładowania | Rozmiar i warianty można częściowo ocenić statycznie. Dobór obrazu do rzeczywistego widoku wymaga określonego urządzenia i renderowania. [S8] |
| Protokół HTTP | Protokół faktycznie wynegocjowany dla badanych połączeń | HTTP/2 lub HTTP/3 mogą pomóc. Brak HTTP/3 nie powinien sam blokować audytu. Chrome uwzględnia kontekst w swojej kontroli Modern HTTP. [S9] |

## Jak zbierać materiał

Poniższe punkty są propozycją implementacji przyszłego skilla. W tym researchu nie wykonywano takich żądań do strony użytkownika.

1. Pobierać dokument metodą GET i zachowywać metadane żądania oraz odpowiedzi. HEAD może służyć pomocniczo: nie zwraca treści i może pominąć część nagłówków. Nie potwierdzi zawartości dokumentu. [S3]
2. Zachować surowy HTML przed wykonaniem JavaScriptu, a następnie wyciągnąć wskazane w nim adresy zasobów. Pobierać ograniczoną próbkę, zaczynając od głównych skryptów i arkuszy. W raporcie podać zakres i limity tej próbki.
3. Wykonać badanie dla wskazanego scenariusza: np. anonimowy użytkownik na konkretnej podstronie. Zapisać stan zgód, język i uwierzytelnienie, jeśli mają zastosowanie. Wątpliwości co do oczekiwanej treści kierować do potwierdzenia.
4. Badać publiczny adres przez tę samą warstwę CDN lub proxy, przez którą docierają użytkownicy. Dodatkowe badanie originu, jeśli dostępne, oznaczyć jako osobny pomiar. CDN może zmieniać sposób dostarczania odpowiedzi. [S4]
5. Jeśli biblioteka HTTP automatycznie rozpakowuje odpowiedź, rozróżnić pobrane bajty reprezentacji od rozmiaru po dekompresji. `Content-Length`, gdy występuje przy zakodowanej odpowiedzi, odnosi się do postaci zakodowanej. [S10]
6. Dla cache zapisać obserwowane dyrektywy i adekwatny kontekst. Żądanie warunkowe z walidatorem pozwala sprawdzić rewalidację, jeżeli serwer ją obsługuje. Powtórny GET bez cache klienta nie potwierdza działania cache przeglądarki. [S5]
7. Dla czasów zebrać kilka kolejnych próbek i zachować ich rozrzut oraz położenie klienta. Liczbę próbek ustalić jako parametr metody. Nie przedstawiać czasu klienta HTTP jako wyniku Lighthouse ani pomiaru rzeczywistych użytkowników.
8. Nie traktować listy adresów z HTML jako pełnej listy zasobów strony. JavaScript może dodawać kolejne zależności; CSS również wprowadza dodatkowe odwołania. Raport musi wskazywać zbadany podzbiór. [S7]

## Jak podejmować decyzję o Lighthouse

Proponowany status gotowości jest niezależny od listy usterek:

- **Gotowe** — potwierdzono właściwy dokument i scenariusz; można przejść do pomiaru.
- **Gotowe z uwagami** — potwierdzono scenariusz, ale znaleziono np. brak kompresji, ciężkie pliki lub nieefektywny cache. Zachować te ustalenia i wykonać pomiar bazowy.
- **Wstrzymane** — oczekiwany dokument jest niedostępny albo zastąpiony inną treścią, np. stroną logowania w scenariuszu anonimowym. Zapisać konkretną przeszkodę i warunek wznowienia.
- **Nieustalone** — zebrany materiał nie pozwala potwierdzić tożsamości strony lub warunków. Wymaga dodatkowego dowodu.

Nie każdy brak zasobu musi zatrzymywać badanie. Trzeba określić jego znaczenie dla badanego scenariusza. Awaria krytycznego skryptu i brak dekoracyjnego obrazka mogą mieć różne skutki. Są to reguły projektowanego workflow, nie oficjalne statusy Lighthouse.

Wykrycie błędów nie jest zgodą na automatyczne zmiany serwera. Domyślnym wynikiem audytu powinny być dowody i zalecenia.

## Co zostawić pomiarowi w przeglądarce

Z odpowiedzi HTTP i statycznej analizy nie należy wyprowadzać wyniku Performance ani deklarować wartości LCP, CLS czy TBT. Nie da się też w ten sposób wiarygodnie potwierdzić faktycznie niewykorzystanego kodu lub zachowania po interakcji.

Statyczna kontrola może wskazać podejrzany `loading="lazy"` na głównym obrazie. Dopiero pomiar potwierdzi, który element jest LCP w wybranym widoku. Google odradza opóźnione ładowanie faktycznego obrazu LCP. [S11]

Konfiguracja Lighthouse w odczytanej gałęzi `main` zawiera już kontrole dotyczące cache, opóźnienia dokumentu, obrazów, HTTP i blokowania renderowania. Etap wstępny powinien odsyłać do odpowiednich ustaleń Lighthouse zamiast liczyć je jako niezależne problemy dwa razy. [S12]

## Kontrakt raportu Markdown

Rekomendowana zawartość przyszłego raportu:

1. **Zakres:** URL wejściowy i końcowy, data, scenariusz, środowisko, pobrana próbka i ograniczenia.
2. **Gotowość:** jeden z proponowanych statusów wraz z uzasadnieniem.
3. **Ustalenia:** dla każdego adres zasobu, obserwacja, dowód, znaczenie, zalecenie oraz sposób potwierdzenia poprawki.
4. **Priorytety:** przeszkody w pomiarze osobno od kolejności optymalizacji. Priorytet oparty na skutkach i dowodach.
5. **Lighthouse:** jeżeli wykonany — wersje narzędzi, profil urządzenia, ustawienia, liczba uruchomień i odnośniki do danych. Jeżeli pominięty — przyczyna, bez wymyślonego wyniku 0/100.
6. **Niepewności:** czego nie zbadano i jakiego dowodu brakuje.

Przykład formy ustalenia, z danymi wyłącznie ilustracyjnymi:

> **Brak kompresji głównego skryptu — przykład hipotetyczny.** Dla GET `/assets/app.js` z zadeklarowaną obsługą gzip i Brotli otrzymano odpowiedź bez `Content-Encoding`; próbka zawiera 420 KiB kodu. Oznacza to możliwość ograniczenia transferu. Zalecenie: sprawdzić kompresję na publicznej ścieżce dostarczania pliku. Weryfikacja: ponownie pobrać zasób, potwierdzić poprawną dekompresję i porównać rozmiary. Wpływ na metryki wymaga pomiaru.

Lighthouse CLI udostępnia formaty JSON, HTML i CSV; Markdown trzeba przygotować jako dodatkową warstwę raportowania. Warto zachować źródłowy JSON i powiązać opisane ustalenia z jego danymi. [S13]

Przy porównaniach zapisywać warunki i wykonywać powtórzenia. Dokumentacja projektu opisuje zmienność wyników i zaleca agregację wielu uruchomień oraz unikanie równoległych pomiarów na tej samej maszynie. Wybór np. mediany z pięciu prób powinien być jawnym parametrem metody. [S14]

## Proponowany pierwszy zakres

Pierwszy etap przyszłego workflow: **audyt dostarczania strony** — GET dokumentu, tożsamość treści, przekierowania, próbka zasobów, typy odpowiedzi, kompresja, polityki cache, rozmiary i opis opóźnień. Wynik: `preflight.md` oraz materiał dowodowy.

Następny etap: **audyt Lighthouse** korzystający z ustalonego scenariusza. Wynik: źródłowy JSON i czytelny raport `.md` powiązany z kontrolą wstępną.

Na etapie implementacji można je umieścić w jednym skillu z dwoma fazami albo wydzielić dwa skille. Research nie wykazuje potrzeby rozdzielenia ich przed sprawdzeniem istniejącego skilla.

Do ustalenia przed implementacją: treść obecnego skilla, pierwszy reprezentatywny URL, publiczny lub uwierzytelniony scenariusz, dostępność repozytorium strony oraz docelowe środowisko pomiarowe. Nie są to przeszkody dla niniejszego researchu.

## Źródła i ograniczenia

Pierwotny research wykonano przez narzędzie dostępu do internetu, bez terminala i interfejsu przeglądarki. Wtedy nie sprawdzono lokalnego cache OpenSRC ani plików projektu. Po wyjaśnieniu intencji użytkownika sprawdzono cache, odczytano repozytorium i zweryfikowano helper. Przez OpenSRC odczytano źródła Lighthouse 13.5.0, curl 8.7.1 i CPython 3.14.8. Szczegóły oraz rzeczywiste wyniki testów zawiera [raport weryfikacji](verification.md).

Repozytorium nie przypina jeszcze wersji wykonawczej Lighthouse. Źródła `main` użyte w pierwotnym researchu są zmienne; wersja znaleziona w cache także nie stanowi przypięcia dla wdrożenia. Przed implementacją trzeba wybrać i zweryfikować wersję wykonawcy.

- [S1: Chrome DevTools — Lighthouse, pomiar bazowy i produkcyjny build](https://developer.chrome.com/docs/devtools/lighthouse/)
- [S2: Lighthouse — błędy ładowania dokumentu, kod](https://raw.githubusercontent.com/GoogleChrome/lighthouse/main/core/lib/lh-error.js)
- [S3: RFC 9110 — HTTP Semantics, sekcje 8.3, 8.4, 9.3.1, 9.3.2 i 12.5.5](https://www.rfc-editor.org/rfc/rfc9110.html)
- [S4: web.dev — General HTML performance considerations](https://web.dev/learn/performance/general-html-performance)
- [S5: RFC 9111 — HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111.html)
- [S6: Chrome — Document request latency](https://developer.chrome.com/docs/performance/insights/document-latency)
- [S7: web.dev — Optimize resource loading](https://web.dev/learn/performance/optimize-resource-loading)
- [S8: web.dev — Image performance](https://web.dev/learn/performance/image-performance)
- [S9: Chrome — Modern HTTP](https://developer.chrome.com/docs/performance/insights/modern-http)
- [S10: MDN — Content-Encoding](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Encoding)
- [S11: web.dev — Optimize Largest Contentful Paint](https://web.dev/articles/optimize-lcp)
- [S12: Lighthouse — konfiguracja domyślna, kod](https://raw.githubusercontent.com/GoogleChrome/lighthouse/main/core/config/default-config.js)
- [S13: Lighthouse — README, formaty raportów](https://github.com/GoogleChrome/lighthouse/blob/main/readme.md)
- [S14: Lighthouse — Score Variability](https://github.com/GoogleChrome/lighthouse/blob/main/docs/variability.md)
