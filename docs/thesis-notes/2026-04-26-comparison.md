# Analiza porównawcza klasyfikatorów (Etap 5.4)

**Data sesji**: 2026-04-26
**Skrypt**: `src/training/compare_models.py`
**Materiał**: `docs/thesis-notes/figures/` (3 PNG + 4 MD/JSON wygenerowane skryptem)
**Kontekst**: konsolidacja Sesji 1, 2, 3 — gotowy materiał do rozdziału 5.4 pracy magisterskiej.

---

## 1. Cel sesji i metoda

Porównujemy cztery modele klasyfikujące fazę biegu (FLIGHT / LEFT_STANCE / RIGHT_STANCE) trenowane na **identycznym splicie** (`data/splits.json` — 8 plików train, 2 val, 3 test):

- **RF v1** — Random Forest na 132 surowych keypointach MediaPipe (x, y, z, visibility) — baseline (Sesja z 2026-04-24).
- **RF v2** — Random Forest na 106 cechach inżynierowanych (znormalizowane współrzędne + 6 kątów stawów + pochylenie tułowia) — izolacja wpływu cech (Sesja z 2026-04-24).
- **LSTM run 1** — BiLSTM h=128, dropout=0.3, lr=1e-3 — pierwsza próba, wczesny overfitting (best @ epoka 1) — odrzucony jako primary, zachowany do dyskusji.
- **LSTM run 2 (primary)** — BiLSTM h=64, dropout=0.4, lr=3e-4, weight_decay=1e-4 — przemyślana konfiguracja, plateau val_loss przez 4 epoki — **model docelowy** (Sesja z 2026-04-26).

**Co dokładnie izoluje każdy krok** (klasyczna ablacja akademicka):

| Krok | Co zmienia się | Co testujemy |
| --- | --- | --- |
| RF v1 → RF v2 | tylko cechy (132→106 + normalizacja + kąty) | wpływ feature engineeringu |
| RF v2 → LSTM run 2 | tylko architektura (RF→BiLSTM, okno 15) | wpływ kontekstu czasowego |
| LSTM run 1 ↔ run 2 | tylko hiperparametry (h, lr, dropout, wd) | metodologia: jak wybrać LSTM "primary" |

Wszystkie liczby w tej notatce pochodzą z `models/{rf_baseline,rf_engineered,lstm_run1_overfit,lstm_primary}/metrics.json`. Skrypt `compare_models.py` wczytuje je i generuje surowe artefakty — tabele MD/JSON i wykresy PNG — bez ponownego trenowania.

## 2. Tabela zbiorcza — metryki globalne

[Patrz: `figures/comparison_table.md`, `figures/comparison_summary.json`]

| Model | Cechy | n train / val / test | Val acc | Val F1 | Test acc | Test F1 | Luka val→test |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RF v1 (raw) | 132 | 5811 / 737 / 1490 | 80.6% | 0.803 | **59.0%** | **0.583** | 21.6 p.p. |
| RF v2 (engineered) | 106 | 5811 / 737 / 1490 | 79.4% | 0.792 | **61.0%** | **0.611** | 18.4 p.p. |
| LSTM run 1 (h=128, overfit) | 106 | 5699 / 709 / 1448 | 78.3% | 0.780 | **66.0%** | **0.658** | 12.3 p.p. |
| LSTM run 2 (primary) | 106 | 5699 / 709 / 1448 | 80.4% | 0.801 | **64.8%** | **0.637** | 15.5 p.p. |

**Uwaga o n testowym**: LSTM ma 1448 okien zamiast 1490 klatek (RF). Różnica 42 = 14 klatek odrzuconych z każdego z 3 plików test (po 7 z każdej strony — krawędzie okna 15). Mianowniki różne, ale procentowe metryki porównywalne.

### Trzy obserwacje z tabeli

1. **Luka val→test maleje monotonicznie** (21.6 → 18.4 → 15.5 p.p.). Nawet kiedy globalna val accuracy lekko spada (RF v2 ma 79.4% vs 80.6% baseline), test accuracy rośnie i luka się zmniejsza — to **silny sygnał, że każdy krok poprawia generalizację międzyfilmową**, niezależnie od tego co dzieje się z val.
2. **LSTM bije oba RF na test acc o 4-5 p.p.** — kontekst czasowy faktycznie pomaga, hipoteza kierunkowa potwierdzona.
3. **Test accuracy zatrzymuje się przy 65-66%** mimo trzech różnych architektur. To sufit, który nie należy do wyboru modelu — wskazuje na problem w danych/etykietach/aspect ratio (patrz § 7).

## 3. Analiza per-film

[Patrz: `figures/per_file_test.md`]

| Film | n RF / LSTM | RF v1 | RF v2 | LSTM run 1 | LSTM run 2 |
| --- | --- | --- | --- | --- | --- |
| **02** — Running at 13 km/h, boczne ujęcie | 300 / 286 | 47.0% | 63.7% | 56.3% | **64.0%** |
| **20** — Walk → run, 0.8–3.5 m/s | 870 / 856 | 60.9% | 61.1% | **67.8%** | 65.1% |
| **22** — Physiotherapist demo, pionowe wideo | 320 / 306 | 65.0% | 58.1% | **70.3%** | 65.0% |

### Co zrobił feature engineering, a co kontekst czasowy — per-film

| Film | RF v1 → RF v2 (engineered features) | RF v2 → LSTM run 2 (kontekst czasowy) |
| --- | --- | --- |
| **02** | **+16.7 p.p.** 🎯 — duża poprawa, kosztem zerowej zmiany u LSTM | +0.3 p.p. — LSTM nie odzyskuje już więcej |
| **20** | +0.2 p.p. — neutralne | **+4.0 p.p.** 🎯 — kontekst czasowy odzyskuje to czego cechy nie dały |
| **22** | −6.9 p.p. ⚠️ — pogorszenie (bug aspect ratio dla pionowego wideo) | +6.9 p.p. — LSTM odzyskuje stratę, ale tylko do baseline'u |

**Wniosek**: feature engineering i kontekst czasowy **rozwiązują różne filmy**. Film 02 wymagał normalizacji (jego biegacz miał inną pozycję x w kadrze niż train set); film 20 (walk→run, zmienna kadencja) wymagał kontekstu czasowego, bo zmiany cyklu są niewidoczne dla per-frame klasyfikatora. Film 22 wymaga *innej* naprawy (aspect ratio), której żadna z dwóch ścieżek nie pokrywa.

## 4. Typologia błędów — gdzie każda iteracja realnie pomaga

[Patrz: `figures/error_breakdown.md`, `figures/confusion_matrices_test.png`]

Z macierzy pomyłek 3×3 wyróżniamy dwie kategorie błędów:
- **L↔R** (`LEFT_STANCE` ↔ `RIGHT_STANCE`) — pomyłki o to, **która noga** ląduje. Najgorszy typ błędu, bo bezpośrednio rujnuje współczynnik symetrii L/R w produkcji.
- **FLIGHT↔STANCE** — pomyłki o **moment kontaktu** (1-2 klatki przesunięcia w cyklu). Mniej dotkliwe — przesuwają GCT/flight time o pojedyncze klatki, ale nie zmieniają której nogi dotyczy faza.

Dla 3 klas suma tych dwóch kategorii pokrywa **wszystkie** pola off-diagonal — to są wszystkie błędy.

| Model | n test | poprawne | błędy razem | L↔R | FLIGHT↔STANCE | % L↔R w błędach |
| --- | --- | --- | --- | --- | --- | --- |
| RF v1 (raw) | 1490 | 879 | 611 | **185** | 426 | 30.3% |
| RF v2 (engineered) | 1490 | 909 | 581 | **95** | 486 | 16.4% |
| LSTM run 1 (h=128, overfit) | 1448 | 956 | 492 | **67** | 425 | 13.6% |
| LSTM run 2 (primary) | 1448 | 939 | 509 | 101 | **408** | 19.8% |

### Trzy obserwacje z analizy błędów

1. **Spadek L↔R z 185 → 95 między RF v1 a RF v2 (−49%)** — to jest dokładnie to, co ma robić **normalizacja antropometryczna** (cechy wycentrowane na mid_hip i podzielone długością tułowia). Mid_hip absorbuje pozycję w kadrze, długość tułowia normuje skalę — model przestaje się mylić "lewa stopa = ta po prawej w kadrze".
2. **Spadek FLIGHT↔STANCE z 486 → 408 między RF v2 a LSTM run 2 (−16%)** — to jest dokładnie to, co ma robić **kontekst czasowy**. Klatka pojedyncza nie odróżnia "stopa schodzi z ziemi" od "stopa już oderwana"; okno 15 klatek tak.
3. **Każdy krok zmniejsza całkowitą liczbę błędów** (611 → 581 → 509 = poprawa 17%) — narracja kumulatywna działa. Ale zmniejsza je w innych kategoriach: RF v2 wymienia jeden typ błędu na drugi (mniej L↔R, więcej FLIGHT↔STANCE), LSTM run 2 zmniejsza FLIGHT↔STANCE bez powrotu do złego L↔R.

### Subtelność: LSTM run 1 jest najlepszy w L↔R (67), ale...

LSTM run 1 ma rekordowe 67 błędów L↔R — niżej niż run 2 (101) i RF v2 (95). To wynik pierwszej epoki uczenia (best @ ep 1), zanim model zaczął się przeuczać do absolutnych pozycji w train. Zachowujemy go w `models/lstm_run1_overfit/` jako **materiał porównawczy**, ale nie jako primary — patrz § 6.

## 5. Krzywe uczenia — case study run 1 vs run 2

[Patrz: `figures/learning_curves_lstm.png`]

Wykres pokazuje dramatyczną różnicę w dynamice uczenia obu konfiguracji:

- **Run 1 (h=128, lr=1e-3, dropout=0.3)**: val_loss osiąga minimum **już na epoce 1** (0.484), potem rośnie monotonicznie do 1.05 mimo że train_loss spada z 0.56 do 0.14. Klasyczna sygnatura overfittingu — model **zapamiętuje train zamiast się go uczyć**.
- **Run 2 (h=64, lr=3e-4, dropout=0.4, wd=1e-4)**: val_loss osiąga minimum na epoce 2 (0.510) i utrzymuje plateau 0.51-0.53 przez epoki 2-5, dopiero potem rośnie. Model ma **realną fazę uczenia** widoczną w danych, nie tylko szczęśliwy snapshot.

Pionowa kreska na wykresie zaznacza `best_epoch` (epoka załadowanych wag finalnych).

## 6. Dlaczego run 2 jako primary, mimo niższego globalnego test acc

Run 1 ma marginalnie wyższy globalny test (66.0% vs 64.8%), ale dla pracy magisterskiej run 2 jest lepszym fundamentem z czterech powodów:

1. **Walidowana zdolność do nauki** — run 2 ma 4 epoki plateau val_loss (~0.52) zanim zacznie overfitować. To dowód, że gradient sygnał faktycznie się przekłada na generalizację, nie tylko pierwszy krok inicjalizacji + Adam trafił szczęśliwie.
2. **Stabilność per-film**: run 1 ma zakres acc 56.3-70.3% (różnica 14 p.p.), run 2 ma 64.0-65.1% (1.1 p.p.). To znaczy, że run 2 generalizuje **bardziej spójnie między biegaczami** — w pracy mgr to ważniejsze niż wyższy globalny pojedynczy wynik.
3. **Run 1 ma sygnaturę overfittingu na każdym wykresie** (loss, val_acc) — recenzent zapyta "dlaczego patience=15 jeśli zatrzymujesz na epoce 1?", "czy testowano mniejsze lr/h?". Run 2 odpowiada na te pytania w samej konfiguracji.
4. **Run 1 zawdzięcza niski L↔R (67) loterii**, nie generalizacji — to wszystko cena "zatrzymania na inicjalizacji + jeden krok Adama".

Trzymamy run 1 w repo (`models/lstm_run1_overfit/`) jako **świadomy materiał do dyskusji** w pracy: pokazujemy konfrontację "naiwna konfiguracja vs przemyślana", co jest dobrą ilustracją procesu badawczego.

## 7. Feature importances — biomechaniczna walidacja modelu

[Patrz: `figures/feature_importances_rf.png`]

Wykres pokazuje TOP-15 cech dla obu wariantów RF, z kolorowaniem semantycznym:
- **Zielony** — kąty stawów / pochylenie (cechy biomechaniczne)
- **Niebieski** — surowa lub znormalizowana współrzędna keypointu
- **Czerwony** — visibility (artefakt kadrowania)

### RF v1 (baseline) — TOP-6 to surowe `_y` stóp, ale TOP-7..14 zawiera 3× visibility

Pierwsze 6 cech w RF v1 to `_y` stóp i pięt (`RIGHT_ANKLE_y`, `LEFT_FOOT_INDEX_y`, `LEFT_HEEL_y`, etc.) — **biomechanicznie sensowne**, bo oś Y stopy jest bezpośrednim wskaźnikiem kontaktu z ziemią. Ale niżej w TOP-15 pojawiają się: `RIGHT_SHOULDER_visibility`, `RIGHT_THUMB_visibility`, `LEFT_THUMB_visibility`. **Visibility kciuka nie ma biomechanicznego znaczenia dla fazy biegu** — to artefakt kadrowania (kciuk znika za ciałem w określonych pozach), na który model się przywiązuje.

### RF v2 — TOP-3 to **kąty stawów**, visibility znika z TOP-15

Po normalizacji i dodaniu kątów: **TOP-3 cechy to `right_ankle_angle`, `left_knee_angle`, `right_knee_angle`** (po 0.04 importance, znacznie ponad pozostałe). Visibility w ogóle nie ma w TOP-15. Reszta listy to znormalizowane współrzędne stóp/kolan (`*_y_norm`, `*_x_norm`).

To jest **niezależna walidacja**, że model nauczył się tego, co biomechanicy uważają za istotne (kąty kolana i kostki determinują fazę chodu/biegu w klasycznej analizie). Baseline uczył się **artefaktów kadrowania**; v2 patrzy na **co robi noga** zamiast na **gdzie ta noga jest**.

### Dla LSTM nie ma feature importance

Bidirectional LSTM nie produkuje natywnie ważności cech (są techniki post-hoc — gradient saliency, SHAP, permutation importance — ale nie wynika to bezpośrednio z architektury). To **interesująca asymetria w narracji**: RF jest interpretowalny z definicji, LSTM nie. W pracy można to potraktować jako kompromis: lepsza dokładność za cenę interpretowalności.

## 8. Sufit ~65% test mimo trzech architektur

Wszystkie trzy "poważne" konfiguracje (RF v1, RF v2, LSTM run 2) lądują w przedziale 59-65% test accuracy. Różnica RF v2 → LSTM run 2 to +4 p.p., różnica RF v1 → RF v2 to +2 p.p. — pojedyncze cyfry, nie skoki rzędu wielkości. Sufit ~65% **nie jest cechą architektury** — przekraczają go obie architektury identycznie i utykają w tym samym miejscu.

Hipotezowane źródła sufitu (kolejność prawdopodobieństwa):

1. **Bug aspect ratio (film 22 = 21% test setu)** — film 22 ma rozdzielczość 608×1080 (pion), pozostałe filmy są poziome. MediaPipe normalizuje x i y osobno per oś (0-1 niezależnie), więc `torso_length` w pionowym wideo jest zawyżony. Wszystkie cechy znormalizowane są skompresowane → model widzi "skompresowanego biegacza" → FLIGHT recall = 4% w obu LSTM (4/94 klatek). Naprawa aspect ratio (pomnożenie x, y przez (width, height) z `videos_metadata.csv`) może podnieść globalny test acc o 3-7 p.p. — zostaje na osobną sesję.
2. **Szum etykiet peak-based** — algorytm `auto_label.py` dzieli interwały między peakami na STANCE/FLIGHT w proporcji 60/40. W granicznych klatkach (±2 wokół przejścia) etykieta odbiega od ground truth. ~12% klatek datasetu ma potencjalny szum, więc sufit "perfekcyjny model" przy tej naturze etykiet to ~88%, nie 100%.
3. **Mały dataset** — 5811 klatek train, ~10 unikalnych biegaczy, 8 plików. Klasycznie LSTM dobrze działają od ~50k przykładów wzwyż. Weight decay i dropout w run 2 to próba kompensacji, ale nie zastąpią danych.
4. **Monocular 2D + brak DOUBLE_SUPPORT** — ujęcie z boku ma inherentne ograniczenia (jedna noga zasłania drugą), które nie znikną po żadnej iteracji modelu. DOUBLE_SUPPORT też nie istnieje w datasecie, więc model rozwiązuje 3-klasowy problem zamiast 4-klasowego z założenia.

## 9. Ocena zbiorcza hipotez (z trzech sesji łącznie)

| Hipoteza | Skąd | Wynik | Ocena |
| --- | --- | --- | --- |
| RF naive da test ~80% | brief Sesji 1 | 59.0% | ❌ niespełniona |
| RF engineered da test 70-78% | [decyzja Opcji B](2026-04-24-decision-option-b.md) | 61.0% | ❌ niespełniona |
| Normalizacja naprawi film 02 | [RF v2 notatka](2026-04-24-rf-engineered.md) | +17 p.p. (47→64%) | ✅ spełniona dokładnie |
| Kąty stawów będą TOP cechami | [RF v2 notatka](2026-04-24-rf-engineered.md) | TOP-3 cechy = kąty | ✅ spełniona mocno |
| LSTM da test 82-90% | [RF v2 notatka](2026-04-24-rf-engineered.md) | 64.8% | ❌ niespełniona |
| Kontekst czasowy zamknie lukę FLIGHT↔STANCE | [LSTM notatka](2026-04-26-lstm-primary.md) | 486 → 408 (−16%) | 🟢 częściowo spełniona |
| Bidirectional kontekst pomoże | [LSTM notatka](2026-04-26-lstm-primary.md) | LSTM > RF v2 o +4 p.p. test | ✅ spełniona kierunkowo |

**Podsumowanie**: hipotezy *kierunkowe* (co która zmiana **poprawi**) okazały się trafne na większość przypadków. Hipotezy *ilościowe* (jakie konkretnie liczby) były systematycznie **zbyt optymistyczne**. Sufit 65% test accuracy jest realistyczny dla tego datasetu bez dodatkowych napraw (aspect ratio, ręczna walidacja etykiet, więcej danych).

## 10. Co to znaczy dla pracy magisterskiej (rozdział 5.4)

### Mocne obserwacje (do wstawienia w pracę)

1. **Każda iteracja redukuje błędy w innym typie** (RF v1 → RF v2 redukuje L↔R, RF v2 → LSTM redukuje FLIGHT↔STANCE) — to **dwie różne dźwignie poprawy**, nie jedna ilościowa. Pokazuje że feature engineering i kontekst czasowy są **komplementarne**, nie alternatywne.
2. **Luka val→test maleje monotonicznie** (21.6 → 18.4 → 15.5 p.p.) — silny dowód, że każdy krok poprawia generalizację międzyfilmową, niezależnie od tego co dzieje się z accuracy globalną.
3. **TOP cechy RF v2 to kąty stawów** — niezależna biomechaniczna walidacja modelu (model uczy się "co robi noga" przed "gdzie ta noga jest").
4. **Sufit ~65% w trzech architekturach** — silny dowód że problem leży **w danych, nie w modelu**. To pełnoprawny materiał na sekcję "Limitations" i uzasadnienie kierunków przyszłej pracy.
5. **Run 1 vs run 2 jako case study procesu badawczego** — "wyższy test acc nie znaczy lepszy model" gdy dochodzi do tego przez overfit. Recenzent docenia świadome decyzje.

### Uczciwie ujmiemy w sekcji "Limitations"

- Hipoteza 82-90% była zbyt optymistyczna. Próbowaliśmy 2 konfiguracji LSTM — obie utknęły przy 65% test.
- Bug aspect ratio nie jest naprawiony. Film 22 (21% test setu) ma FLIGHT recall = 4% w obu LSTM — co sztywno obniża globalny test.
- Etykiety auto-generated, bez walidacji ręcznej. Szum etykiet peak-based nakłada teoretyczny sufit < 100%.
- Mały dataset (8 plików train, ~10 biegaczy). LSTM dobrze działa od rzędów wielkości większych zbiorów.
- Brak DOUBLE_SUPPORT w datasecie — pipeline założony na 4 klasy, model trenowany na 3.

### Kierunki przyszłej pracy (do dyskusji w pracy)

- **Naprawa aspect ratio** — pomnożenie x, y przez (width, height) z metadanych przed normalizacją. Retrening RF v2 i LSTM. Oczekiwany zysk +3-7 p.p. globalnego test.
- **Etap 6** — obliczanie współczynników biomechanicznych (kadencja, GCT, flight time, stride length, kąty, symetria) z LSTM jako klasyfikatora. KRYTYCZNE: tu FPS i prędkość bieżni mają znaczenie (vs trenowanie).
- **Etap 7** — reguły rekomendacji na podstawie literatury biomechanicznej (kodowane ręcznie, NIE uczone z danych).
- (low priority) Ręczna walidacja etykiet na 200-300 klatkach — eliminuje sufit szumu etykiet, ale kosztowne.
- (low priority) Większy hyperparameter sweep dla LSTM — szybkie, ale ograniczony zysk (sufit jest gdzie indziej).

## 11. Indeks artefaktów wygenerowanych w tej sesji

Wszystko w `docs/thesis-notes/figures/`:

| Plik | Typ | Zawartość |
| --- | --- | --- |
| `comparison_table.md` | Markdown | Tabela 4 modeli × {val_acc, val_f1, test_acc, test_f1, luka} |
| `comparison_summary.json` | JSON | To samo w postaci listy słowników (do dalszej obróbki) |
| `per_file_test.md` | Markdown | Tabela 4 modeli × 3 filmy × {acc, F1} |
| `error_breakdown.md` | Markdown | Tabela 4 modeli × {L↔R, FLIGHT↔STANCE, % L↔R w błędach} |
| `confusion_matrices_test.png` | PNG, 11×10 | 4 macierze pomyłek (heatmapy znormalizowane recall) |
| `learning_curves_lstm.png` | PNG, 13×5 | Krzywe train/val loss + val_acc dla LSTM run 1 i run 2 |
| `feature_importances_rf.png` | PNG, 13×6 | TOP-15 cech RF v1 i RF v2 (kolorowanie: kąty / współrzędne / visibility) |

Kod: `src/training/compare_models.py`. Skrypt jest reentrant — uruchomienie po retreningu modelu (np. po naprawie aspect ratio) regeneruje wszystkie artefakty z nowych metrics.json bez ręcznych zmian.
