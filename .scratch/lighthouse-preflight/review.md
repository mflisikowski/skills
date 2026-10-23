# Przegląd wdrożenia lighthouse-check

Data: 2026-10-23. Punkt odniesienia: `85ea1c7eb057633c843c363b97f7850f5ed7e434`.

Przegląd wykonano zgodnie z lokalnym `code-review`: niezależnie oceniono standardy repozytorium i zgodność ze specyfikacją. Zakres obejmował zmiany robocze oraz nowe pliki, następnie poprawki usterek. Nie obejmował zmian badanej aplikacji.

## Standards

Brak naruszeń udokumentowanych zasad repozytorium i istotnych problemów wymagających refaktoryzacji. Pakiet pozostaje samowystarczalny; zasoby, katalog i bundlowana licencja zachowują kontrakt.

W tej osi znaleziono dwie konkretne usterki poprawności:

1. Fragment URL był usuwany również przed nawigacją w przeglądarce. Poprawka zachowuje fragment dla pomiaru i usuwa go tylko dla HTTP. Rzeczywisty test strony z trasą `#/target` przeszedł.
2. Import raportów do niepustego katalogu mógł nadpisać jeszcze nieodczytane źródło. Polecenie wymaga teraz pustego katalogu wyjściowego przed rozpoczęciem pracy. Test odwróconej kolejności źródeł potwierdza zachowanie ich bajtów.

Ponowny przegląd potwierdził obie poprawki; brak nowych usterek w tych zmianach.

## Spec

W tej osi znaleziono dwa braki względem obiecanego zachowania:

1. Utrata fragmentu URL mogła prowadzić do pomiaru innej podstrony SPA i fałszywego potwierdzenia scenariusza. Poprawiono jak wyżej, z rzeczywistym testem przeglądarkowym.
2. `runWarnings: null` i jednostka metryki będąca listą mogły przerwać renderowanie bez pliku Markdown. Walidacja odrzuca te pola przed przyjęciem przebiegu; testy potwierdzają raport `INCOMPLETE` zamiast tracebacka bez raportu.

Nie stwierdzono istotnego rozszerzenia zakresu. Ponowny przegląd potwierdził poprawki. Audyt wskazanej strony został następnie wykonany, a jego raport uzupełniono o analizę i dodatkowe dowody HTTP.

Stan końcowy: Standards — 0 nierozwiązanych uwag; Spec — 0 nierozwiązanych uwag. Początkowe ustalenia obu osi obejmowały trzy odrębne usterki, wszystkie usunięte.
