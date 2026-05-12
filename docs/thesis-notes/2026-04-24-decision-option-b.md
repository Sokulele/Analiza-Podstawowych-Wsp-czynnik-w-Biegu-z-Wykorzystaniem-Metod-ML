# Decyzja: dalsza ścieżka po RF baseline — Opcja B (feature engineering → LSTM)

**Data**: 2026-04-24
**Kontekst**: zaraz po wytrenowaniu RF baseline (Val 81%, Test 59% — patrz [`2026-04-24-rf-baseline.md`](2026-04-24-rf-baseline.md))
**Charakter**: decyzja metodologiczna o strukturze rozdziału eksperymentalnego

---

## Pytanie do rozstrzygnięcia

Mamy wytrenowany baseline RF z czytelną diagnozą błędów (luka val↔test, mylenie L↔R, absolutne współrzędne jako słabe cechy). Co dalej?

1. Strojć dalej RF? *(odrzucone natychmiast — nic nowego nie wnosi)*
2. Przejść od razu do LSTM?
3. Najpierw poprawić cechy, potem LSTM?
4. Najpierw zweryfikować etykiety, potem LSTM?

## Rozważane opcje

### Opcja A: od razu LSTM

**Idea**: pominąć dalszą pracę z RF, przejść do modelu sekwencyjnego — bo to on jest "primary" w briefie.

**Plusy**:
- Najszybciej do pipeline'u end-to-end
- Pracujemy z modelem, który faktycznie trafi do pracy jako główny

**Minusy**:
- **Zmieniamy dwie zmienne naraz** (reprezentacja cech + architektura modelu). Jeśli LSTM da 70%, nie wiadomo: to model sekwencyjny źle działa, czy cechy są za słabe?
- Ubogi materiał porównawczy w pracy — tylko dwa punkty ("RF naiwny" vs "LSTM"). Pracy magisterskiej zwykle zarzuca się "za mało eksperymentów"
- Luka val↔test w RF była silnym sygnałem, że problem jest w cechach. Ignorowanie tego sygnału wygląda nieuczciwie

### Opcja B: engineered RF → LSTM *(wybrana)*

**Idea**: zrobić drugi wariant RF na **lepszych cechach** (znormalizowanych, z kątami stawów), dopiero potem LSTM.

**Plusy**:
- **Dezamplifikacja zmiennych eksperymentalnych** — RF engineered vs RF naive izoluje wpływ cech; LSTM vs RF engineered izoluje wpływ sekwencji. Każdy krok dowodzi czegoś **odrębnego**
- **Trzy punkty porównania** w rozdziale eksperymentalnym — klasyczna akademicka narracja "naive → engineered → temporal"
- Jeśli engineered RF skoczy do np. 75%, to **samodzielny wynik naukowy** (pokazuje wartość feature engineeringu, niezależnie od architektury)
- Jeśli engineered RF nie zamknie luki val↔test, to też jest silny sygnał — że problem jest głębiej (dataset, etykiety, monocular 2D) i trzeba to uczciwie omówić w pracy
- Koszt: jedna dodatkowa sesja ~1-2h

**Minusy**:
- Dodatkowa iteracja zanim zobaczymy LSTM
- Cechy inżynierowane wymagają decyzji (które kąty? jak normalizować?), ryzyko drobnych bugów

### Opcja C: najpierw ręczna weryfikacja etykiet, potem LSTM

**Idea**: zanim trenujemy cokolwiek nowego, sprawdzić ~200 klatek z 2-3 filmów, czy peak-based auto-etykietowanie jest zgodne z okiem człowieka.

**Plusy**:
- Gwarancja, że wszystkie dalsze metryki są wiarygodne
- Standard w literaturze biomechanicznej (gold-standard labeling)

**Minusy**:
- Czasochłonne (ręczne oglądanie klatek)
- **Przedwczesne** — nie mamy konkretnej przesłanki, że etykiety są złe. Wskaźniki jakości z sesji 2026-04-20 są dobre (0 zmian filtra medianowego, 0 direct L↔R)
- Może okazać się, że etykiety są OK, i stracimy czas

## Decyzja: Opcja B

### Uzasadnienie

1. **Naukowa czystość** — każdy krok eksperymentalny zmienia jedną rzecz. W pracy recenzent oczekuje ablacji, a Opcja B daje naturalną ablację: cechy vs. model
2. **Nadanie wartości obserwacji z baseline'u** — diagnoza luki val↔test i artefaktów `visibility` prowadzi prosto do engineered RF. Byłoby niespójne: zauważyć problem z cechami i od razu go pominąć
3. **Asymetryczny koszt** — 1-2h pracy vs. znaczny zysk narracyjny w pracy. Proporcja korzystna
4. **Opcja C w odwodzie** — weryfikację etykiet można odpalić **warunkowo**, jeśli LSTM utknie w okolicy 70-75% (wtedy etykiety stają się sensownym podejrzanym). Bez tego sygnału — szkoda czasu

### Plan na następne sesje

**Sesja 1 (kolejna)**: `src/training/train_rf_v2.py` z cechami inżynierowanymi:

- Normalizacja: wszystkie keypointy względem mid_hip (odjąć środek bioder od każdego)
- Skalowanie: dzielone przez długość tułowia (dystans mid_hip → mid_shoulder) — daje cechy w jednostkach antropometrycznych, niezależnych od kadru i wzrostu
- Cechy dodatkowe: kąty stawów (kolano, biodro, kostka), pochylenie tułowia — zgodnie z [`.claude/rules/coefficients.md`](../../.claude/rules/coefficients.md)
- Porównanie side-by-side: RF naive vs RF engineered na tym samym splicie

**Sesja 2**: `src/training/train_lstm.py` na engineered features — okno N=15 klatek, środkowa klatka jako target.

### Oczekiwane wyniki (hipotezy do sprawdzenia)

| Model | Hipoteza o test accuracy | Uzasadnienie hipotezy |
| --- | --- | --- |
| RF naive (jest) | 59% | zmierzone |
| RF engineered | 70–78% | normalizacja powinna zamknąć większość luki val↔test, bo zabije korelację z kadrem |
| LSTM engineered | 82–90% | temporal context pozwala odróżnić przejście STANCE→FLIGHT od chwilowego szumu keypointów |

Jeśli wyniki odbiegną od tych oczekiwań — każde odchylenie samo w sobie jest obserwacją do omówienia w pracy.

### Co to znaczy dla struktury pracy magisterskiej

Rozdział eksperymentalny:

- **5.1 Baseline — RF na surowych keypointach** (mamy)
- **5.2 RF z cechami inżynierowanymi** (wynik Sesji 1) — osobny wynik, pokazuje wartość normalizacji i cech antropometrycznych
- **5.3 Model sekwencyjny (LSTM)** (wynik Sesji 2) — model docelowy pipeline'u
- **5.4 Analiza porównawcza** — tabela trzech modeli, dyskusja co dodaje każdy krok, omówienie pozostałych ograniczeń

To jest struktura którą recenzent magisterki rozpoznaje jako dojrzałą.
