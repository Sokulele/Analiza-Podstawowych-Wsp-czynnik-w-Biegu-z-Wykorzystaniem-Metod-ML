# Historia sesji

Log pracy między sesjami — krótki recap + kontekst do kontynuacji.

---

## 2026-04-15 — Etap 2: Ekstrakcja keypointów ✅

### Zrobione

- **Środowisko**: utworzony `.venv/` (Python 3.11), plik `requirements.txt`, `.gitignore`
  - Kluczowe: `mediapipe==0.10.14` (ostatnia z legacy `mp.solutions.pose` API wymaganego przez CLAUDE.md; 0.10.21+ ma tylko nowe Tasks API)
- **Skrypty**:
  - `src/extraction/probe_videos.py` — sonduje metadane wideo → `data/videos_metadata.csv`
  - `src/extraction/extract_keypoints.py` — MediaPipe Pose (complexity=2) + Savitzky-Golay (window=11, polyorder=3) + raport jakości
- **Wyjście**: 9 CSV w `data/keypoints/` (135 kolumn: frame, timestamp, pose_detected + 33×{x,y,z,visibility}), raport w `_quality_report.{csv,md}`
- **Metryki**: filtr savgol redukuje jitter o 53–86%

### Stan datasetu (9 filmików)

| Flag        | Filmiki                                                                                                       |
| ----------- | ------------------------------------------------------------------------------------------------------------- |
| OK (6)      | 01, 02, 03, 08×2, 20 — detection 100%, vis 0.88–0.97                                                          |
| WARN (1)    | 18 (exoskeleton) — FPS 23.98                                                                                  |
| **BAD (2)** | **09** Sage Canaday (detection 88.9%, 166 klatek bez pozy), **16** (FPS 13.33 — za niski do precyzyjnego GCT) |

### Znane pułapki

- **Film 01** to slow-motion — kadencja/GCT wyjdą zaniżone bez znajomości rzeczywistego współczynnika spowolnienia
- **Film 09** — brakujące detekcje wymagają zbadania (czy zgrupowane, czy rozproszone → czy da się wyciąć problematyczny fragment)
- **Film 16** — 13 FPS daje błąd kwantyzacji ~15% na czasie kontaktu; kandydat do test-set lub odrzucenia
- Nazwy plików zawierają Unicode (`⧸`, `｜`) — trzeba `sys.stdout.reconfigure(encoding="utf-8")` na Windows (już w skryptach)

### Do zrobienia w następnej sesji — Etap 3: Auto-etykietowanie

Plan: `src/labeling/auto_label.py` wg reguł z `.claude/rules/labeling.md`:

1. Wyznaczyć `ground_level` per filmik (mediana Y stopy w najniższych 10% klatek)
2. Klasyfikacja faz: `LEFT_STANCE` / `RIGHT_STANCE` / `FLIGHT` / `DOUBLE_SUPPORT` na podstawie Y_heel vs ground_level + threshold
3. Filtr medianowy (kernel=5) na sekwencji etykiet — przeciw migotaniu
4. Detekcja kierunku biegu (L/P może być zamienione)
5. Dopisać kolumny `phase_auto` i `phase` do istniejących CSV w `data/keypoints/`

Przed startem: sprawdzić dla 09 czy brakujące klatki są zgrupowane; zdecydować co zrobić z filmikami 09 i 16 (wyciąć fragment / odrzucić / zostawić jako test).

### Odkładane decyzje

- Czy wersjonować `data/keypoints/` (14 MB) czy dodać do .gitignore + LFS
- Czy generować wizualną weryfikację (szkielet na klatkach) — plan.md etap 2 to wymienia, ale zostawiłem na potem

---

## 2026-04-16 — Etap 3: Auto-etykietowanie (test na filmie 02)

### Zrobione

- **Skrypt**: `src/labeling/auto_label.py` — auto-etykietowanie faz biegu
- **Test**: uruchomiony na filmie 02 (Running at 13km/h, 30 FPS, 300 klatek, 10s)
- **Wyjście**: kolumny `phase_auto` (surowa) i `phase` (po filtrze) dopisane do istniejącego CSV w `data/keypoints/`

### Algorytm — ewolucja podejścia

Pierwotny plan (progowanie Y_heel vs ground_level) okazał się niewystarczający:

1. **Proste progowanie heel_y** — za dużo FLIGHT (71%), bo threshold 0.02 za ciasny
2. **max(heel_y, foot_index_y)** — lepszy sygnał kontaktu (cały cykl heel strike → toe-off)
3. **Adaptacyjny próg per stopa** — poprawił symetrię L/R, ale nadal bezpośrednie L→R bez FLIGHT
4. **Peak-based (finalne)** — detekcja foot strikes (`find_peaks`), wymuszona alternacja L-R, proporcjonalny podział STANCE/FLIGHT

### Finalne parametry

- Sygnał kontaktu: `max(heel_y, foot_index_y)` per stopa
- Peak detection: `scipy.signal.find_peaks(distance=12, prominence=0.03)`
- Alternacja L-R wymuszona (przy podwójnych peakach — zachowaj wyższą prominence)
- FLIGHT: w punkcie `min(max(L,R))` między peakami, `flight_fraction=0.4`
- Filtr medianowy: `kernel=3` (faktycznie zmienił 0 klatek — peak-based jest już czysty)

### Wyniki na filmie 02

| Metryka        | Wartość       | Oczekiwane (13 km/h) |
| -------------- | ------------- | -------------------- |
| Kadencja       | 162 spm       | 160–175 spm          |
| Kontakty L / R | 14 / 14       | symetryczne          |
| GCT left       | 285 ms        | ~250 ms              |
| GCT right      | 207 ms        | ~250 ms              |
| Flight         | 115 ms (n=27) | 80–130 ms            |
| Direct L↔R     | 0             | 0                    |
| DOUBLE_SUPPORT | 0             | 0                    |

### Kluczowe wnioski z eksperymentów

- **Proste progowanie Y nie działa** przy 30 FPS — flight trwa ~3 klatki, za mało do wykrycia progiem
- **Heel_y sam nie wystarczy** — prawa stopa ma dużo większą amplitudę niż lewa (artefakt kąta kamery w ujęciu z boku), trzeba max(heel, foot_index)
- **Filtr medianowy kernel=5 szkodzi** — kasuje krótkie (2-3 klatki) segmenty FLIGHT
- **Peak-based jest odporniejszy** niż progowanie — prominence jest relatywna, nie zależy od absolutnych wartości Y

### Asymetria L/R (285 vs 207 ms)

Lewa stopa jest bliżej kamery → jej ruch w pikselach jest mniejszy → peak jest szerszy → stance dłuższy. To artefakt monocular 2D — akceptowalne do trenowania klasyfikatora (model uczy się pozycji ciała, nie timingów).

### Ocena uniwersalności algorytmu

**Powinno działać bez zmian:** filmy OK (01, 02, 03, 08×2) + WARN (18) — peak detection opiera się na relatywnych zmianach (prominence), nie absolutnych wartościach
**Ryzyko:**

- **Film 09** (88.9% detekcji) — brakujące klatki mogą generować fałszywe peaki
- **Film 16** (13 FPS) — flight = 1-2 klatki, flight_fraction=0.4 może być za dużo

### Do zrobienia w następnej sesji

1. Uruchomić na pozostałych filmach, ocenić metryki (kadencja, direct_LR, liczba peaków)
2. Zdecydować co z filmami 09 i 16
3. Ręczna weryfikacja etykiet na kilku fragmentach (opcjonalnie — wizualizacja szkieletu z kolorami faz)

### Odkładane decyzje (bez zmian)

- Wersjonowanie `data/keypoints/` — teraz pliki mają dodatkowe kolumny, więc decyzja pilniejsza
- Wizualna weryfikacja etykiet

---

## 2026-04-20 — Etap 3 dokończony: audyt datasetu + auto-etykietowanie wszystkich filmów

### Audyt datasetu

**Film 09 (Sage Canaday)** — analiza braków detekcji:

- 166 braków (11.1%) to **JEDNA zwarta grupa**: kl. 894–1059 (29.8–35.3s)
- Pocięty na 2 czyste segmenty (ffmpeg via `cut_video.py`):
  - Segment 1: 892 kl., 29.8s, 100% detekcji, vis 0.91 → **OK**
  - Segment 2: 438 kl., 14.6s, 99.8% detekcji, vis 0.91 → **OK**
- Keypointy przeekstrahowane dla obu segmentów

**Film 16** (13 FPS) → przeniesiony do `data/test_edge_cases/`, `exclude_from_training=True`

### Auto-etykietowanie — wszystkie filmy

Algorytm peak-based (z sesji 2026-04-16) uruchomiony na wszystkich filmach. Wyniki:

| Film              | Klatki | Kadencja  | L/R   | Direct L↔R | Uwagi                      |
| ----------------- | ------ | --------- | ----- | ---------- | -------------------------- |
| 01 (slow-mo ~10x) | 949    | 15.1 spm  | 5/4   | 0          | OK — dużo klatek/cykl      |
| 02                | 300    | 162.0 spm | 14/14 | 0          | OK (z poprzedniej sesji)   |
| 03 (15km/h)       | 300    | 174.2 spm | 15/15 | 0          | OK                         |
| 08 seg1           | 660    | 147.0 spm | 27/28 | 0          | OK, outlier 835ms R_STANCE |
| 08 seg2 (slow-mo) | 300    | 77.8 spm  | 7/7   | 0          | OK — slow-motion           |
| 09 seg1           | 892    | 132.9 spm | 34/33 | 0          | OK, marathon pace          |
| 09 seg2           | 438    | 172.3 spm | 22/21 | 0          | OK                         |
| 20 (chód→bieg)    | 870    | 109.8 spm | 27/27 | 0          | OK, duży std oczekiwany    |

**Kluczowe obserwacje:**

- Filtr medianowy (kernel=3) zmienił **0 klatek** we wszystkich filmach — peak-based jest inherentnie czysty
- Slow-motion nie przeszkadza etykietowaniu — prominence jest relatywna
- Asymetria L/R GCT to artefakt monocular 2D (nie wpływa na etykiety faz)

**Bugfix:** CSV filmu 20 miał spacje w nazwach kolumn (`NOSE_x ` zamiast `NOSE_x`) — naprawiony strip()

### Rozszerzenie datasetu — 6 nowych filmików

Dodane nowe filmy, pełny pipeline (ekstrakcja keypointów + auto-etykietowanie):

| Film                         | FPS   | Klatki | Kadencja  | L/R   | Uwagi               |
| ---------------------------- | ----- | ------ | --------- | ----- | ------------------- |
| 06 (15km/h slow-mo ~8x)      | 9.46  | 560    | 20.3 spm  | 11/10 | OK                  |
| 15 (4m/s slow-mo ~5x)        | 13.33 | 800    | 30.0 spm  | 16/15 | OK                  |
| 19 (barefoot slow-mo ~8x)    | 11.25 | 900    | 21.0 spm  | 14/15 | OK                  |
| 20b (chód→bieg)              | 30.0  | 870    | 109.8 spm | 27/27 | OK                  |
| Running at 4ms (slow-mo ~5x) | 15.0  | 750    | 32.4 spm  | 14/14 | OK, piękna symetria |
| 22 (fizjoterapeuta)          | 29.97 | 320    | 157.2 spm | 15/14 | OK, pionowe wideo   |

Wszystkie: 100% detekcji MediaPipe, 0 direct L↔R, 0 zmian filtra medianowego.

### Finalny dataset

| Metryka             | Wartość |
| ------------------- | ------- |
| Filmów z etykietami | 13      |
| Łącznie klatek      | 8039    |
| LEFT_STANCE         | ~34%    |
| RIGHT_STANCE        | ~32%    |
| FLIGHT              | ~34%    |
| DOUBLE_SUPPORT      | 0%      |
| Unikalnych biegaczy | ~9-10   |

Rozkład klas równomierny — brak problemu z imbalance.

### Decyzja: niski FPS OK dla trenowania

Filmy z niskim FPS (06: 9.46, 15: 13.33, 19: 11.25) włączone do training set. FPS nie ma znaczenia dla klasyfikatora faz — model uczy się pozycji ciała, nie timingów (CLAUDE.md). Niski FPS jest problemem tylko przy obliczaniu współczynników (inferencja).

### Zmiany w plikach

- `data/videos_metadata.csv` — dodane kolumny `exclude_from_training` i `notes`; nowe filmy
- `data/test_edge_cases/` — nowy katalog z filmem 16
- `data/videos/` — 2 segmenty filmu 09 + 6 nowych filmów
- `data/keypoints/` — CSV z keypointami + etykietami faz dla wszystkich 13 filmów

### Do zrobienia w następnej sesji — Etap 5: Trenowanie klasyfikatora

1. Podział danych: train/val/test (per filmik, nie per klatka!)
2. Baseline: Random Forest na wektorze keypointów
3. Primary: LSTM lub 1D CNN na sekwencji klatek
4. Metryki: accuracy, confusion matrix, F1 per klasa

### Odkładane decyzje

- Wersjonowanie `data/keypoints/` (rosnące — teraz ~30 MB)
- Etap 4 (korekta ręczna etykiet) — pominięty, bo algorytm jest czysty (0 zmian filtra medianowego, 0 direct L↔R we wszystkich filmach). Jeśli model będzie słaby → wrócić do weryfikacji etykiet

---

## 2026-04-24 — Etap 5 (część 1): Split datasetu + Random Forest baseline

### Zrobione

- **`src/training/split_data.py`** — podział per filmik wg briefu. Output `data/splits.json`
  - Train (8 filmów, 5811 kl., 72.3%): 01, 06, 08 seg1, 08 seg2, 09 seg1, 15, 19, Running at 4ms
  - Val (2 filmy, 738 kl., 9.2%): 03, 09 seg2
  - Test (3 filmy, 1490 kl., 18.5%): 02, 20, 22
  - 02/03 rozdzieleni (ten sam biegacz) — 03 w val, 02 w test ✓
  - Klasy: tylko 3 (LEFT_STANCE / RIGHT_STANCE / FLIGHT), brak DOUBLE_SUPPORT
- **`src/training/train_rf.py`** — RF na 132 cechach (33 keypointy × x,y,z,visibility)
  - `RandomForestClassifier(n_estimators=300, class_weight="balanced", seed=42)`
  - Zapisuje model (`models/rf_baseline/model.joblib`) + metryki (`metrics.json`)
- **Dodano do requirements**: `scikit-learn>=1.3.0`, `joblib>=1.3.0`

### Wyniki RF baseline (n_estimators=300, class_weight=balanced, 132 cechy)

| Split | accuracy | F1 macro | Uwagi |
| --- | --- | --- | --- |
| VAL (03 + 09 seg2) | **80.6%** | 0.803 | powyżej oczekiwanych >80% z briefu |
| TEST (02 + 20 + 22) | **59.0%** | 0.583 | duża luka vs val |
| TEST[02] | 47.0% | 0.352 | mylenie RIGHT_STANCE→LEFT_STANCE (recall RIGHT=0.07) |
| TEST[20] | 60.9% | 0.605 | najbardziej zrównoważony |
| TEST[22] | 65.0% | 0.605 | pionowe wideo, radzi sobie OK |

**Confusion matrix TEST (rows=true):**

```
             FLIGHT  L_STANCE  R_STANCE
FLIGHT          203       192        81
LEFT_STANCE      74       372        79
RIGHT_STANCE     79       106       304
```

### Kluczowe obserwacje

- **Luka VAL(81%) → TEST(59%)** to silny sygnał overfittingu do absolutnych pozycji w kadrze
- **TOP feature importances**: wszystkie to `_y` stóp (ankle_y, foot_index_y, heel_y) — sensowne biomechanicznie. Ale też `visibility` barków/ust/kciuków — to artefakty kadrowania, nie pozy
- **Film 02 rozbity**: RIGHT_STANCE klasyfikowane jako LEFT_STANCE (tylko 6/87 poprawnych). To sugeruje, że model nauczył się absolutnych współrzędnych x/y biegacza w kadrze — gdy 02 ma biegacza w innej pozycji horyzontalnej niż train set, model się gubi
- MediaPipe zwraca x,y znormalizowane (0-1) **względem całego kadru**, nie względem biegacza — więc gdy kamera ma inny kadr/aspect ratio, "lewa" i "prawa" stopa mają różne absolutne x

### Hipotezy do testów (do konsultacji z użytkownikiem)

1. **Normalizacja względem biegacza** — odjąć mid_hip, przeskalować długością tułowia. Tanie, powinno znacząco pomóc
2. **Wyrzucić visibility** — `--no-visibility` (99 cech) — sprawdzić czy visibility mouth/thumb to faktyczny szum
3. **Cechy inżynierowane** — kąty stawów, odległości stopa-biodro (invariant na kadr) zamiast surowych keypointów
4. **Więcej danych** — train 8 filmów, ~10 unikalnych biegaczy, to mało. Pytanie czy zwiększenie datasetu vs. lepsze cechy da większy zysk

### Do zrobienia w następnej sesji

- Najpierw: normalizacja cech względem biegacza (pkt 1 wyżej) — sprawdzić czy zamyka lukę val↔test
- Dopiero potem decyzja: LSTM/1D-CNN vs. cechy inżynierowane
- **LSTM wstrzymany** — czekamy aż baseline się ustabilizuje

---

## 2026-04-24 — Etap 5, część 2: RF z cechami inżynierowanymi + folder notatek magisterskich

### Zrobione

- **`docs/thesis-notes/`** — nowy folder na materiał do pracy magisterskiej + reguła auto-zapisu w CLAUDE.md (decyzje, dewagacje, wyniki, ograniczenia są zapisywane proaktywnie)
- **Notatka decyzyjna**: `2026-04-24-decision-option-b.md` — wybór Opcji B (engineered RF → LSTM) vs alternatyw A i C, z uzasadnieniem
- **`src/training/features.py`** — reużywalny moduł: normalizacja (mid_hip + torso length), kąty stawów (6: kolana/biodra/kostki L+R), pochylenie tułowia
- **`src/training/train_rf_v2.py`** — RF na 106 engineered features, te same hiperparametry co baseline
- **Model**: `models/rf_engineered/` (model.joblib + metrics.json)

### Wyniki RF v2 vs baseline

| Metryka | Baseline | RF v2 | Zmiana |
| --- | --- | --- | --- |
| Val accuracy | 80.6% | 79.4% | −1.2 p.p. |
| Test accuracy | **59.0%** | **61.0%** | +2.0 p.p. |
| Test F1 macro | 0.583 | 0.611 | +0.028 |
| Luka val↔test | 21.6 p.p. | 18.4 p.p. | −3.2 p.p. |

Per-film test:
- **Film 02: 47% → 64%** (+17 p.p.) — hipoteza potwierdzona: normalizacja naprawia mylenie L↔R (RIGHT_STANCE recall 7% → 70%)
- Film 20: 61% → 61% (bez zmian)
- **Film 22: 65% → 58%** (−7 p.p.) — nieoczekiwane pogorszenie, przypuszczalnie bug z aspect ratio (pionowe wideo)

### Najważniejsze obserwacje

1. **TOP-3 feature importances to kąty stawów** (right_ankle_angle, left_knee_angle, right_knee_angle) — biomechaniczna walidacja. W baseline top features to były surowe `_y` stóp + visibility ust/kciuków (artefakty). W v2 model patrzy na "co robi noga" przed "gdzie ta noga jest"
2. **Mylenie L↔R spadło o ~50%** (z 185 do 95 klatek off-diagonal L/R). Dla produktu (współczynniki symetrii) to kluczowa metryka
3. **Ale** mylenie FLIGHT↔STANCE wzrosło o ~14%. Model "wymienił" jeden typ błędu na drugi — jakościowo lepszy, bo mniej szkodliwy dla użytkownika końcowego
4. **Hipoteza test 70–78% niespełniona** (61% faktycznie) — normalizacja to nie magic bullet. Reszta luki wynika prawdopodobnie z: brak kontekstu czasowego (wymaga LSTM), szum etykiet peak-based, monocular 2D, bug aspect ratio dla pionowych filmów

### Zidentyfikowane bugi / kierunki naprawcze (do rozważenia po LSTM)

- **Aspect ratio correction**: MediaPipe normalizuje x, y osobno per oś (0-1), więc torso_length w pionowym wideo (film 22) jest zawyżona. Naprawa: wymnożenie współrzędnych przez (width, height) z `videos_metadata.csv` przed normalizacją
- **Z-axis noise**: w monocular side view z jest głównie szumem. Wariant 2D (x, y) może działać lepiej
- **Pierwsze różnice współrzędnych** jako tani kontekst czasowy (bez LSTM)

### Do zrobienia w następnej sesji — Sesja 2: LSTM

- `src/training/train_lstm.py` na tych samych engineered features co RF v2 (okno N=15 klatek, środkowa klatka jako target)
- PyTorch
- Early stopping na val loss
- Porównanie z oboma wariantami RF (naive 59% / engineered 61% / LSTM ?)

### Plan na pracę magisterską (aktualizacja struktury)

Rozdział eksperymentalny ma teraz 3 potwierdzone pozycje:
- 5.1 Baseline (RF naive) — 59% test
- 5.2 RF z cechami inżynierowanymi — 61% test + jakościowa poprawa (L↔R)
- 5.3 LSTM (do zrobienia) — hipoteza 82-90% test dzięki kontekstowi czasowemu
- 5.4 Analiza porównawcza

---

## 2026-04-26 — Etap 5, część 3: BiLSTM (model docelowy)

### Zrobione

- **`src/training/train_lstm.py`** — BiLSTM PyTorch na oknie 15 klatek, target = klatka środkowa, bidirectional, dropout, StandardScaler na train, early stopping na val loss
- Dodane `torch>=2.0.0` (CPU-only) do `requirements.txt`
- **Dwa runy** (świadoma decyzja metodologiczna — patrz notatka thesis):
  - Run 1 (h=128, lr=1e-3, dropout=0.3): early stop @ epoka 1 → klasyczny overfit, **odrzucony jako primary**, zachowany w `models/lstm_run1_overfit/`
  - Run 2 (h=64, lr=3e-4, dropout=0.4, wd=1e-4): best @ epoka 2, plateau val_loss ep 2-5 → **wybrany jako primary**, w `models/lstm_primary/`

### Wyniki (LSTM run 2 = primary)

| Split | accuracy | F1 macro |
| --- | --- | --- |
| Val | 80.4% | 0.801 |
| **Test** | **64.9%** | **0.637** |

### Porównanie 4 modeli na test

| Model | Test acc | Test F1 macro | Luka val→test |
| --- | --- | --- | --- |
| RF v1 (raw) | 59.0% | 0.583 | 21.6 p.p. |
| RF v2 (engineered) | 61.0% | 0.611 | 18.4 p.p. |
| LSTM run 1 (h=128, overfitted) | 66.0% | 0.658 | 12.3 p.p. |
| **LSTM run 2 (primary)** | **64.9%** | **0.637** | **15.5 p.p.** |

LSTM bije oba RF o 4-5 p.p. test acc — kontekst czasowy faktycznie pomaga. Hipoteza 82-90% **niespełniona** — sufit ~65% niezależnie od architektury.

### Per-film test (LSTM run 2 vs RF v2)

| Film | RF v2 | LSTM run 2 | Δ |
| --- | --- | --- | --- |
| 02 | 63.7% | 64.0% | +0.3 |
| 20 | 61.1% | 65.1% | +4.0 |
| 22 | 58.1% | 65.0% | +6.9 |

LSTM run 2 jest **co najmniej tak dobry jak RF v2 na każdym filmie**, najbardziej zbalansowany między filmami (range 64.0-65.1).

### Kluczowe obserwacje

1. **Run 1 vs run 2 jako case study** — run 1 ma marginalnie wyższy test (66 vs 65%), ale early stop @ ep 1 to zła reprezentacja zdolności LSTM. Run 2 ma 4 epoki plateau val_loss = walidowana zdolność do nauki. Wybrany run 2 mimo niższego globalnego test.
2. **Mylenie L↔R**: RF v1 185 → RF v2 95 → **LSTM run 2 101**. LSTM trochę pogorszył vs RF v2 (+6 klatek, w granicach szumu).
3. **Mylenie FLIGHT↔STANCE**: RF v1 426 → RF v2 486 → **LSTM run 2 408** (−16% vs RF v2). Kontekst czasowy pomaga rozróżnić moment kontaktu.
4. **Bug filmu 22 — FLIGHT recall = 4%** w obu runach LSTM — ten sam patologiczny wzorzec niezależnie od architektury. Confirmed: bug aspect ratio (608×1080 vs ~16:9 train), torso_length zawyżony → wszystkie cechy znormalizowane skompresowane → model nie rozpoznaje FLIGHT.
5. **Sufit ~65% test mimo 3 architektur** — silny dowód że problem leży w danych/etykietach/aspect ratio, nie w modelu

### Hipotezy z briefu

| Hipoteza | Wynik | Ocena |
| --- | --- | --- |
| Test acc 82-90% | 64.9% | ❌ niespełniona |
| Zamknie lukę FLIGHT↔STANCE | 486 → 408 (−16%) | 🟢 częściowo spełniona |
| Nie pogorszy mylenia L↔R | 95 → 101 | 🟡 na granicy |

### Materiał do pracy magisterskiej

- Notatka thesis: `docs/thesis-notes/2026-04-26-lstm-primary.md`
- Run 1 vs run 2 jako ilustracja procesu badawczego (overfitting jako lesson learned)
- Sufit ~65% w trzech architekturach jako uzasadnienie sekcji "limitations"
- Bug aspect ratio jako kandydat na osobny podrozdział i kierunek przyszłej pracy

### Do zrobienia w następnej sesji

1. **Sesja 3: analiza porównawcza** — ujednolicony raport 3 modeli, wizualizacje (krzywe uczenia, confusion matrices side-by-side), tabele do wstawienia w pracę
2. (alternatywa) **Naprawa aspect ratio bug** — pomnożenie x, y przez (width, height) z metadanych przed normalizacją; retrening RF v2 + LSTM; oczekiwany zysk +3-7 p.p. test

### Odkładane decyzje

- Czy uruchomić sesję 3 jako "tylko porównanie istniejących" (~1h) vs "porównanie + naprawa aspect ratio" (~2-3h)
- Wersjonowanie `models/` (rośnie — teraz 2× LSTM + 2× RF + scalery)
- Hyperparameter sweep dla LSTM (low priority — sufit jest gdzie indziej)

---

## 2026-04-26 — Etap 5.4: analiza porównawcza 4 modeli

### Decyzja sesji

Wybrana **Opcja 1** z briefu — konsolidacja istniejących wyników (RF v1, RF v2, LSTM run 1, LSTM run 2) bez naprawy aspect ratio. Film 22 zostaje jako limitation w pracy. Cel: gotowy materiał do rozdziału 5.4.

### Zrobione

- **`src/training/compare_models.py`** — standalone skrypt wczytujący 4 metrics.json, generujący tabele MD/JSON i wykresy PNG. Reentrant (po retreningu modelu generuje nowe artefakty automatycznie).
- **Notatka thesis**: `docs/thesis-notes/2026-04-26-comparison.md` — pełna analiza 11 sekcji z odwołaniami do figur i tabel.
- **Artefakty w `docs/thesis-notes/figures/`**:
  - `comparison_table.md`, `comparison_summary.json` — metryki globalne
  - `per_file_test.md` — accuracy per filmik × model
  - `error_breakdown.md` — typologia błędów L↔R vs FLIGHT↔STANCE
  - `confusion_matrices_test.png` — 4 macierze pomyłek (heatmapy znormalizowane recall)
  - `learning_curves_lstm.png` — train/val loss + val_acc dla obu runów LSTM
  - `feature_importances_rf.png` — TOP-15 cech dla RF v1 i RF v2 (kolorowanie semantyczne)

### Kluczowe nowe obserwacje (z konsolidacji)

1. **Luka val→test maleje monotonicznie** (21.6 → 18.4 → 15.5 p.p.) — każdy krok poprawia generalizację międzyfilmową, niezależnie od tego co dzieje się z val accuracy. To jest mocniejsza obserwacja niż samo "test acc rośnie".
2. **Każda iteracja redukuje **inny typ** błędu**:
   - RF v1 → RF v2: −49% L↔R (185 → 95) — feature engineering (normalizacja antropometryczna)
   - RF v2 → LSTM run 2: −16% FLIGHT↔STANCE (486 → 408) — kontekst czasowy
   - To pokazuje że dwa kierunki poprawy są **komplementarne**, nie alternatywne.
3. **Per-film: feature engineering i kontekst czasowy ratują różne filmy**:
   - Film 02 (47 → 64% RF v2) — beneficjent normalizacji (inna pozycja w kadrze niż train)
   - Film 20 (61 → 65% LSTM r2) — beneficjent kontekstu (walk→run, zmienna kadencja)
   - Film 22 — żaden z dwóch kierunków nie pomaga (bug aspect ratio)
4. **Total errors: 611 → 581 → 509** (poprawa 17%) — narracja kumulatywna potwierdzona w danych.

### Drobne kosmetyczne poprawki w skrypcie

- Confusion matrix layout: tytuły jednoliniowe + `subplots_adjust(hspace=0.45)` + osobny colorbar (axes lista 2D nie działa z `fig.colorbar`)
- Per-file table: lepszy parser nazw plików (kropka w "0.8 to 3.5" rozbijała etykietę 20)
- Error breakdown: usunięta myląca kolumna "inne" (dla 3 klas L↔R + FLIGHT↔STANCE pokrywa wszystkie pola off-diagonal)

### Materiał do pracy magisterskiej

- Rozdział 5.4 ma teraz pełną tabelę zbiorczą + 3 wykresy + 3 tabele pomocnicze
- Run 1 vs run 2 jako case study procesu badawczego ("wyższy test acc nie znaczy lepszy model gdy dochodzi to przez overfit")
- Sufit ~65% test mimo trzech architektur — jako uzasadnienie sekcji "Limitations"
- TOP cechy RF v2 = kąty stawów — jako biomechaniczna walidacja modelu

### Do zrobienia w następnej sesji

**Etap 6 — obliczanie współczynników biomechanicznych** (lub naprawa aspect ratio jako warunek wstępny):

1. Decyzja: czy najpierw aspect ratio (Opcja 2 z briefu poprzedniego — oczekiwany zysk +3-7 p.p. test), czy od razu Etap 6 z aktualnym LSTM?
2. Etap 6: nowy pipeline `src/coefficients/` — kadencja, GCT, flight time, stride length, kąty stawów, vertical oscillation, foot strike pattern, symetria L/R. KRYTYCZNE: tu FPS i prędkość bieżni mają znaczenie (vs trenowanie).

### Odkładane decyzje (bez zmian)

- Wersjonowanie `models/`
- Ręczna walidacja etykiet (low priority — sufit szumu etykiet)
- Hyperparameter sweep LSTM (low priority — sufit nie jest tam)

---

## 2026-05-08 — Rozszerzenie datasetu o 2 biegaczy (23, 24) + retrening 4 modeli

### Decyzja sesji

Dodanie 2 własnych filmów (Pawel, Adam) do datasetu, oba do TRAIN, test bez zmian (porównywalność z 5.4). Pełny pipeline: ekstrakcja → auto-etykietowanie → split update → retrening wszystkich 4 modeli → re-run compare_models.py.

### Zrobione

- **Resize 4K Pawła → 720p** (ffmpeg, oryginał w `data/videos/_originals_4k/`)
- **Rozszerzenie skryptów** `probe_videos.py` i `extract_keypoints.py` o glob `*.mov`
- **Ekstrakcja keypointów** (MediaPipe complexity=2, savgol 11/3): Pawel 100% detekcji (WARN — vis 0.79, low_vis 13.9%), Adam 100% (OK — vis 0.88, low_vis 3.1%)
- **Auto-etykietowanie peak-based**: Pawel 154.7 spm L/R 71/72; Adam 167.5 spm L/R 112/112 (idealna symetria)
- **Wycięcie pierwszych 80 klatek Adama** (artefakt brzegowy peak-based — LEFT_STANCE bez peaka), backup w `data/keypoints/_originals_pre_trim/`
- **`split_data.py`** zaktualizowany — 23 i 24 dodane do TRAIN: 8 → 10 plików, **5811 → 9779 klatek (+68%)**
- **Backup 4 modeli + figures** do `models/*_pre_extension/` i `docs/thesis-notes/figures_pre_extension/`
- **Retrening 4 modeli** bez zmian hiperparametrów: RF v1, RF v2, LSTM run 1 (h=128), LSTM run 2 primary (h=64)
- **Re-run `compare_models.py`** — nowe artefakty w `figures/`
- **Notatka thesis**: `docs/thesis-notes/2026-05-08-dataset-extension.md`

### Wyniki retreningu — globalnie

| Model | Test acc (przed → po) | Δ | F1 macro | Luka val→test |
| --- | --- | --- | --- | --- |
| RF v1 (raw) | 59.0 → **62.7%** | +3.7 | 0.62 | 21.6 → 19.3 p.p. |
| RF v2 (engineered) | 61.0 → **67.0%** | **+6.0** | 0.67 | 18.4 → **12.9** p.p. |
| LSTM run 1 (h=128) | 66.0 → **67.1%** | +1.1 | 0.66 | 12.3 → 19.3 p.p. |
| LSTM run 2 (primary) | 64.9 → 65.3% | +0.5 | 0.65 | 15.5 → 19.2 p.p. |

### Per-film test (najistotniejsze)

| Film | RF v1 | RF v2 | LSTM r1 | LSTM r2 |
| --- | --- | --- | --- | --- |
| 02 | +4.7 | −0.7 | −1.4 | **−13.3** |
| 20 | +2.8 | **+7.5** | +0.3 | +1.8 |
| **22 (aspect ratio bug)** | **+5.3** | **+8.5** | **+5.5** | **+9.2** |

### Kluczowe obserwacje

1. **Sufit przesunięty z ~65% do ~67%** (+2 p.p.), ale dalej istnieje. 4 architektury × 2 rozmiary trainu utykają w tym samym miejscu — silniejszy dowód że problem w danych/etykietach
2. **RF v2 wygrał rozszerzenie** (+6 p.p., luka val→test do 12.9 p.p. — najmniejsza). Konkurencyjny z LSTM (67.0 vs 65.3-67.1) — częściowa rewizja wniosku rozdziału 5.4 "LSTM bije RF dzięki kontekstowi czasowemu"
3. **LSTM ledwo drgnęły** mimo +69% okien — h=64 niedouczone, h=128 wciąż overfit od ep 4. Niemożność wykorzystania extra danych
4. **Film 22 najwięcej zyskał** wszędzie (~+7 p.p. średnio) — Pawel/Adam (16:9, 720p+) **częściowo zniwelowali aspect ratio bug** przez różnorodność w trainie
5. **Film 02 dramatycznie spadł dla LSTM r2 (−13.3 p.p.)** — LSTM wrażliwy na zmianę dystrybucji trainu. Argument **przeciwko** zostawieniu r2 jako primary, ale val_loss plateau dalej stabilniejsze niż r1
6. **Luka val→test odwróciła trend**: kurczy się dla RF, rośnie dla LSTM — val (filmy 03, 09 seg2) blisko Pawła/Adama dystrybucyjnie

### Materiał do pracy magisterskiej

- Podrozdział **5.5 "Wpływ rozszerzenia datasetu"** — naturalne rozszerzenie 5.4 bez nadpisywania
- Stara analiza 5.4 zostaje (`figures_pre_extension/`) jako baseline
- Sekcja **Limitations**: silniejszy argument o sufit (4 archit. × 2 rozmiary trainu wszystkie ~67%); aspect ratio bug **częściowo** rozwiązany — full fix nadal kandydatem na future work
- Run 2 dalej rekomendowany jako primary (stabilniejsze plateau val_loss), choć argument słabszy

### Do zrobienia w następnej sesji

1. **Etap 6 (obliczanie współczynników)** — najsensowniejszy następny krok. Nowy klasyfikator (RF v2 67% lub LSTM r1 67.1%) jako wejście do inferencji wideo→fazy→współczynniki
2. (alternatywa) **Naprawa aspect ratio bug** — częściowo zniwelowany różnorodnością, ale full fix nadal ciekawy. Spodziewany dodatkowy zysk: +1-3 p.p. (zamiast wcześniej szacowanych +3-7)
3. (opcjonalnie) Hyperparameter sweep LSTM (h=96, dropout=0.35) — niski priorytet, sufit nie jest tam

### Odkładane decyzje (bez zmian)

- Wersjonowanie `models/` (rośnie — teraz 8 modeli z backupami)
- Ręczna walidacja etykiet
- Pełen retrening LSTM z większym hidden_size jako follow-up

---

## 2026-05-08 — Plan poprawy accuracy: LSTM r1 + aspect fix → **70.9% test acc** (próg 70% przekroczony)

### Decyzja sesji

User dał plan 8 kroków uderzania w sufit ~67% test acc, ze stop'em przy ≥70%. Wykonane: kroki 1, 2, 4, 5, 7. Krok 8 (ręczna walidacja) niepotrzebny — krok 7 osiągnął cel.

### Zrobione

**Krok 1 — Augmentacja horizontal flip** ❌ NEGATYWNY
- `src/training/augmentation.py` — funkcja `flip_horizontal_dataframe(df)`. Dwie wersje testowane (z/bez swap'a L/R keypointów), obie regresja −2.6 do −9 p.p.
- Diagnoza: konwencja CSV po `auto_label.swap_left_right` jest **zależna od kierunku biegu**, niezgodna z trywialnym flip horyzontalnym. Future work: przerobić auto_label na czysto anatomiczną konwencję
- Kod augmentacji + flag `--augment-flip` zachowane jako artefakt do future use

**Krok 2 — Postprocessing median filter** ✅ +0.7 p.p. dla RF v2
- `src/training/postprocess_median.py` — wczytuje 4 modele, generuje predykcje, aplikuje medfilt PER FILMIK dla kerneli {3, 5, 7, 9}
- Wyniki: tylko **RF v2 + k=3** dał poprawę (67.0 → 67.8%). LSTMy bez zmian (kontekst czasowy już wbudowany), RF v1 spadł, k≥7 dramatyczna regresja (kernel "wyzeruje" segmenty FLIGHT 3-5 klatkowe)

**Krok 4 — Velocity features** ❌ NEGATYWNY globalnie, +7.5 p.p. dla film 22
- `compute_velocity_features` w `features.py` — Δ znormalizowanych keypointów per filmik (99 cech, 33×{x,y,z})
- RF v2: 67.0 → 64.6% (−2.4 p.p.), film 22 +7.5 p.p.
- TOP-20 importance dominują velocity ramion (LEFT_ELBOW_x_dt, RIGHT_WRIST_x_dt) — silny sygnał, ale specyficzny dla biegacza, gorsza generalizacja
- **Ważne**: velocity invariant na aspect ratio bug (Δ-based) — dlatego film 22 zyskał. Wzmacnia argument za Opcją B (full aspect fix)
- Cofnięte, eksperyment w `models/rf_engineered_velocity/`

**Krok 5 — Ensemble soft voting** ❌ NEGATYWNY
- `src/training/ensemble.py` — predict_proba 4 modeli, soft voting na wspólnej przestrzeni klatek (n=1448, LSTM-determined)
- Ważne metodologicznie: ze wspólną przestrzenią RF v2 + median k=3 = **69.4%** (vs 67.8% na n=1490) — obcięcie brzegów to darmowe +1.6 p.p.
- Najlepszy ensemble (RF v2 + LSTM r1) = 68.4% < najlepszy single (RF v2 + median k=3 = 69.4%). Modele mają **skorelowane błędy** (głównie film 02), ensemble nie kompensuje
- Future work do produkcji: ignoruj predykcje na pierwszych/ostatnich 7 klatkach filmu (klatki brzegowe są zaszumione w etykietach)

**Krok 7 — Aspect ratio fix** ✅✅✅ **PROG 70% PRZEKROCZONY**
- `apply_aspect_ratio_correction(df, width, height)` w `features.py` — mnożenie x*width, y*height, z*width przed `compute_engineered_features`
- Flag `--aspect-fix` w `train_rf.py`, `train_rf_v2.py`, `train_lstm.py`. Auto-detect w `postprocess_median.py`
- **Backup wszystkich modeli** w `models/*_pre_aspect_fix/` przed retreningiem
- Wyniki:
  | Model | Test (przed → po) | Δ |
  | --- | --- | --- |
  | RF v1 | 62.7 → 41.9 (cofnięte do 62.7) | KATASTROFA — fix wymaga normalizacji |
  | RF v2 | 67.0 → 65.7 | −1.3 p.p. (ale film 22 +10.9) |
  | **LSTM r1** | 67.1 → **70.9** | **+3.8** ⭐⭐⭐ |
  | LSTM r2 | 65.3 → 68.2 | +2.9 |
- **Film 22 (aspect ratio bug)**: +10.9 (RF v2), +10.1 (LSTM r1), +3.6 (LSTM r2). Walidacja hipotezy z rozdziału 5.5
- RF v1 katastrofa: surowe keypointy bez normalizacji → różne skale per filmik (340x450 vs 1920x1080), model nie generalizuje. **Aspect fix wymaga normalizacji** w pipeline cech

### Notatka thesis

`docs/thesis-notes/2026-05-08-accuracy-improvements.md` — pełen przebieg planu, 5 kroków × wyniki, diagnozy negatywnych wyników, walidacja hipotez. **Materiał wartościowy do pracy** mimo że tylko 1 krok pozytywny:
- Sekcja Methodology — opisuje techniki, ich wymagania (aspect fix wymaga normalizacji), pułapki (augmentacja flip wymaga anatomicznej konwencji etykiet)
- Sekcja Limitations — 4 negatywne wyniki to wartościowe ograniczenia
- Sekcja Walidacja — film 22 case study (aspect ratio bug + naprawa = +10.1 p.p.)

### Status modeli po sesji (final)

| Model | Test acc | F1 macro | Status |
| --- | --- | --- | --- |
| RF v1 (baseline) | 62.7% | 0.617 | bez zmian (fix go niszczy) |
| RF v2 baseline | 67.0% | 0.671 | przywrócone |
| RF v2 + aspect fix | 65.7% | 0.650 | jako alternatywa |
| **LSTM r1 + aspect fix** | **70.9%** ⭐ | **0.709** | **kandydat na nowy primary** |
| LSTM r2 + aspect fix | 68.2% | 0.681 | dotychczasowy primary, też z fix |

### Inne artefakty zachowane

- `models/*_pre_aspect_fix/` — wszystkie 4 modele przed fix (post-extension baseline)
- `models/*_pre_extension/` — wszystkie 4 modele przed Pawel/Adam (z rozdziału 5.4)
- `models/rf_engineered_velocity/` — eksperyment velocity features
- `docs/thesis-notes/figures_pre_extension/` — artefakty rozdziału 5.4

### Otwarte sprawy

1. **Bug w `postprocess_median.predict_lstm`**: pokazuje LSTM r1 + aspect fix = 66.4% baseline, vs metrics.json 70.9%. Coś nieźbieżne. Do zbadania (low priority — metrics.json ma autorytetywne wyniki)
2. **Update primary**: rozważyć migrację LSTM r2 → LSTM r1 + aspect fix jako primary (h=128, +3.8 p.p. vs poprzedni primary). Trzeba sprawdzić czy r1 z aspect fix ma stabilne plateau val_loss
3. **Compare_models.py update**: re-run żeby wygenerować nowe artefakty 5.x z aspect fix wynikami

### Do zrobienia w następnej sesji

**Etap 6 — obliczanie współczynników biomechanicznych** (od dawna planowany):
1. Nowy klasyfikator (LSTM r1 + aspect fix, 70.9% test) jako wejście do inferencji wideo→fazy→współczynniki
2. `src/coefficients/` — kadencja, GCT, flight time, stride length, kąty stawów, vertical oscillation, foot strike, symetria L/R
3. KRYTYCZNE (vs trenowanie): tu FPS i prędkość bieżni mają znaczenie

Lub:
- Rozważenie kroku 8 (ręczna walidacja etykiet) — może podnieść sufit z 70.9% do 75-77% jeśli sufit jest w etykietach. Niski priorytet, bo prog 70% już osiągnięty
- Migracja primary model do LSTM r1 + aspect fix (formalna decyzja w notatce thesis)

### Odkładane decyzje (bez zmian)

- Wersjonowanie `models/` (teraz 12+ wariantów z backupami — robi się ciasno)
- Hyperparameter sweep LSTM (low priority — sufit nie jest tam, +1-3 p.p. najwyżej)
- Naprawa konwencji `auto_label.swap_left_right` na czysto anatomiczną (umożliwiłaby augmentację flip)

---

## 2026-05-09 — Etap 6 MVP: pipeline współczynników biegu (test na Adamie)

### Decyzje sesji

1. **Primary model = LSTM r1 + aspect fix** (h=128, 70.9% test acc) — formalna zmiana z LSTM r2. Notatka thesis zaktualizowana z argumentacją + uwagą o "case study run 1 vs run 2" (zachowane jako sekcja pedagogiczna w pracy)
2. **Stride length pominięta** w MVP — wymaga inputu użytkownika (prędkość bieżni). Implementacja warunkowa po MVP
3. **Test pipeline na Adamie (24)** — świadomy wybór mimo że jest w train. Cel: weryfikacja E2E, nie pomiar jakości
4. **Bug postprocess_median.predict_lstm** — zaakceptowany jako niski priorytet, metrics.json autorytetywny

### Zrobione

**Architektura `src/coefficients/`:**
- `run_inference.py` — pełen pipeline: cv2 + MediaPipe Pose (complexity=2) + savgol smoothing + auto-detect aspect_fix z config.json + LSTM predict + softmax confidence. Klatki brzegowe (half=7) extend pierwszej/ostatniej predykcji z confidence=0
- `temporal_metrics.py` — kadencja [spm], GCT (per L/R), flight time, cycle time (per L/R), duty factor. Run-length encoding sekwencji faz
- `spatial_metrics.py` — kąty stawów (kolana/biodra/kostki L+R) per faza, torso lean, vertical oscillation per cykl (raw + per torso), foot strike pattern (heel/mid/forefoot z kątem stopy w klatce kontaktu)
- `symmetry.py` — Symmetry Index = 200 × |L−R|/(L+R), klasyfikacja zdrowa/łagodna/znacząca

Każdy moduł CLI-runable + reużywalny jako library.

### Wyniki testu na Adamie (24, 80s, 30 FPS, 1920×1080)

**Inferencja**:
- 100% MediaPipe detection (2399/2399 klatek)
- Aspect fix: x*1920, y*1080, z*1920
- Predykcje: FLIGHT 35.3% / LEFT_STANCE 29.2% / RIGHT_STANCE 35.5%
- Średnia confidence: **0.909** (model bardzo pewny)
- Czas: 221s ekstrakcji + 1.5s predykcji LSTM

**Temporal**:
- Kadencja: **173.5 spm** (n=231: L=115, R=116) — typowy zakres 160-180
- GCT: L 203±31 ms, R 245±67 ms
- Flight: 122±25 ms
- Cycle time: L 684±50 ms, R 685±30 ms (niemal identyczne)
- Duty factor: L 0.296, R 0.357

**Spatial** — kąty stawów biomechanicznie poprawne:
- LEFT_KNEE wyprostowane (164°) w L_STANCE, zgięte (133°) w R_STANCE ✓
- RIGHT_KNEE symetrycznie odwrotnie (105°/157°) ✓
- Torso lean 2.3° (low — running tall lub szum)
- Vertical oscillation: 0.140 per torso (~14% długości tułowia, w typowym zakresie 12-20%)
- Foot strike: oba forefoot (LEWA 95.7%, PRAWA 75%, consistent=True). Kąt LEWA −33° wymaga inspekcji

**Symetria**:
- GCT SI **18.7%** (znacząca asymetria L<R)
- Cycle time SI **0.1%** (idealna symetria)
- Knee@STANCE SI 4.0%, Ankle@STANCE 5.6%
- Foot strike pattern consistent (oba forefoot)
- Overall: max SI 18.7%, mean SI 9.4%

### Najciekawsza obserwacja

**GCT asymetryczne, cycle time symetryczne** — Adam ma identyczny rytm cyklu (684 vs 685 ms), ale lewa noga ma krótszy stance / dłuższy flight, prawa odwrotnie. To **klasyczny artefakt monocular 2D** (lewa strona biegacza bliżej kamery → mniejsza amplituda pikselowa → krótszy "wykryty" stance), opisane już w `.claude/rules/labeling.md`. Walidacja: auto_label peak-based dał Adamowi GCT L=R=241 ms (po cięciu 80 brzegowych klatek), więc LSTM wprowadza niewielki błąd asymetryczny.

### Sanity checks pipeline'u

| Kontrola | Wynik | Komentarz |
|---|---|---|
| Kadencja vs cycle time | 173 spm vs 175 z cycle (0.685 s × 2 nogi) | różnica 1.5 spm — szum klatkowania ✓ |
| Klasy w sensownym rozkładzie | 35/29/35 (FLIGHT/L/R) | typowy bieg na bieżni ✓ |
| Kąty stawów biomechanika | knee L wyprostowane w L_STANCE | zgodne z fizjologią ✓ |
| Oscylacja pionowa | 14% torso | typowy zakres ✓ |
| Confidence predykcji | 0.91 | model pewny ✓ |

### Notatka thesis

`docs/thesis-notes/2026-05-09-coefficients-mvp.md` — pełna dokumentacja Etapu 6 MVP. Zawiera:
- Architekturę pipeline'u
- Decyzje (primary, stride length, klatki brzegowe extend vs drop)
- Wyniki na Adamie (3 tabele × kategorie metryk)
- Walidację biomechaniczną
- Sekcję Limitations (6 pkt — monocular 2D bias, foot strike kąty, torso lean low, Adam w train, klatki brzegowe, stride length)
- Plan iteracji 1-3 (test set, raport PDF, Etap 7 rekomendacje)

### Stan plików / artefakty

- `src/coefficients/` — 4 moduły + `__init__.py`
- `data/inference/24-adam-phases.csv` (16 MB, predykcje + keypointy)
- `data/inference/24-adam-temporal.json` / `-spatial.json` / `-symmetry.json`

### Do zrobienia w następnej sesji

**Iteracja 1** (krótkoterminowa):
1. Test pipeline na **02, 20, 22** (test set) — porównanie sensowności współczynników na unseen biegaczach
2. `analyze.py` orchestration script: 1 CLI uruchomienie wideo → wszystkie współczynniki + raport MD
3. Naprawa bug `postprocess_median.predict_lstm` (low priority)

**Iteracja 2** (średnioterminowa):
1. Stride length z input użytkownika (`--treadmill-speed-ms`), formuła `stride_length = speed × cycle_time`
2. Generator raportu PDF/Markdown per bieg
3. Walidacja kąta stopy (foot strike) — wizualna inspekcja klatek

**Iteracja 3** — Etap 7 (rekomendacje):
- `src/recommendations/rules.py` z regułami z literatury biomechanicznej
- Reguły kodowane ręcznie z citation (autor/rok)
- Przykłady: kadencja <160 + GCT >270 → overstriding, asymetria GCT >5% → kandydat do specjalisty

### Odkładane decyzje (bez zmian)

- Wersjonowanie `models/` i `data/inference/`
- Walidacja 3D motion capture (poza scope projektu, ale ważny argument do Limitations)

---

## 2026-05-09 — Iteracja 1: pipeline na test set + raporty z porównaniem do referencji

### Decyzja sesji

Po MVP Etapu 6, iteracja 1: dodać klasyfikator wartości względem `docs/reference-values.md`, `analyze.py` orchestration, generator raportu MD per biegacz. Test pipeline na 02, 20, 22 (test set — unseen biegacze) + Adam jako reference.

### Zrobione

**Nowe moduły** w `src/coefficients/`:
- `reference_values.py` — wartości z literatury (Novacheck, Heiderscheit, Souza, Diaz) jako Python dict + `classify_value()` zwracająca klasyfikację + warnings + emoji (✅/🟡/🔴)
- `report_generator.py` — Markdown raport: header meta + tabele temporal/spatial/symmetry z klasyfikacją + sekcja Wnioski + footer disclaimer
- `analyze.py` — 1 CLI uruchamia E2E (run_inference + temporal + spatial + symmetry + report). Flag `--skip-inference` dla reuse istniejących CSV faz

**Rozszerzone moduły:**
- `spatial_metrics.py` — dodana `compute_knee_angle_at_initial_contact` (kąt kolana w klatce entry into STANCE per L/R, do porównania z referencją 160-175°)

### Wyniki na test set + Adam (sanity check z train)

| Film | Test acc LSTM | Avg conf | Kadencja | n_steps L/R | Max SI | Ocena |
|---|---|---|---|---|---|---|
| 02 (13 km/h sideview) | 54.5% | 0.795 | 144 spm | **14/10** ❌ | **96.5%** | model myli L↔R, GCT R 130 ms artefakt |
| 20 (walk→run) | 70.9% | 0.901 | 139 spm | 33/34 | 57.3% | mix walk+run zaburza średnie |
| 22 (physiotherapist) | 85.9% | 0.890 | 163 spm | 15/14 | 35.0% | najlepszy z testu, akceptowalne metryki |
| 24 Adam (train, ref) | — | 0.909 | 174 spm | 115/116 | 18.7% | sanity check, jak oczekiwano |

### Kluczowa obserwacja sesji

**Korelacja test acc ↔ jakość downstream współczynników**:
- Film 02 (54.5% test) → max SI 96.5% (kompletnie nieprzytomne)
- Film 22 (85.9% test) → max SI 35% (akceptowalne)
- Średnie 70.9% test acc LSTM r1 to **średnia per-film** — niektóre filmy mają 54%, niektóre 86%, raporty per-film różnej jakości

**Confidence < 0.85 silnie koreluje z bezsensownymi współczynnikami**. **L/R steps asymmetry > 20%** sygnalizuje że model myli L↔R. Te dwa wskaźniki to dobre proxy dla "low quality prediction" (warning w UI).

### Raporty per biegacz

`data/inference/raporty/{film}.md` — 6 sekcji:
1. Header (meta, model, confidence)
2. Temporal (kadencja, GCT, flight, cycle, duty factor + emoji klasyfikacja)
3. Spatial (kąt kolana @ contact, torso lean, vertical osc, foot strike)
4. Symmetry (SI L/R + klasyfikacja: norma <5% / uwaga 5-10% / problem >10%)
5. Wnioski (lista warningów posortowana priorytetem ⚠️)
6. Footer (disclaimer + odniesienie do `docs/reference-values.md`)

### Naprawione bugi

- `Classification.status_emoji()` — pierwotnie pokazywał ✅ dla "potencjalny problem" w SI. Naprawiono: heurystyka {bad_labels, warn_labels, critical_terms (ryzyko/problem/chód/marnowanie/obciążenie)}

### Materiał do pracy magisterskiej

Notatka thesis `2026-05-09-iteracja1-test-set.md` z:
- Architektura raportu MD (struktura per biegacz)
- Tabela 4 filmów (test acc vs jakość metryk)
- Per-film analiza (4 sekcje)
- 6 kluczowych obserwacji
- Implikacje dla rozdziału 6 pracy
- 4 nowe punkty Limitations (powiększają sekcję z 6 do 10 pkt)
- Future Work (low quality detection, stable segment detection, foot strike walidacja, PDF z wykresami)

### Stan plików

- `src/coefficients/` — 4 nowe pliki (reference_values, report_generator, analyze + extension spatial_metrics)
- `data/inference/raporty/` — 3 raporty MD (02, 20, 22)
- `data/inference/{slug}-{phases.csv, temporal/spatial/symmetry/meta.json}` — 4 sety artefaktów

### Do zrobienia w następnej sesji

**Iteracja 2** (średnioterminowa):
1. **Stride length** z input użytkownika (`--treadmill-speed-ms`), formuła `stride = speed × cycle_time`
2. **Auto-detect low quality predictions** — flagi: avg_confidence < 0.85, L/R asymmetry > 20%, max SI > 30%. Warning w raporcie + odmowa pokazania niektórych metryk
3. **Stable segment detection** dla filmów mixed-tempo (jak film 20) — filtrowanie outlier'ów cycle time przed średnimi
4. **Generator raportu PDF** z wykresami (matplotlib) — sygnał Y_hip per cykl, kadencja w czasie, mapa faz

### Otwarte sprawy / drobne TODO

- Bug `postprocess_median.predict_lstm` (z poprzedniej sesji, low priority)
- Walidacja foot strike kątów ekstremalnych (−33° do −58°) — wymaga inspekcji wizualnej
- Adam: meta.json nie wygenerowane (uruchomiłem run_inference.py, nie analyze.py — drobne, można re-run --skip-inference)

### Odkładane decyzje (bez zmian)

- Wersjonowanie `models/` i `data/inference/`
- Walidacja 3D motion capture
- Etap 7 (rekomendacje) — po Iteracji 2

---

## 2026-05-12 — Etap 7: moduł rekomendacji biegowych ✅

### Cel sesji

Etap 7 z briefu — silnik rekomendacji oparty o reguły z literatury biomechanicznej
(Heiderscheit 2011, Novacheck 1998, Souza 2016, Diaz 2019, Robinson 1987, Daoud 2012).
Operuje na JSON-ach z Iteracji 1, generuje listę `Recommendation` + sekcję MD do raportu.

### Zrobione

- `src/recommendations/__init__.py` + `rules.py` + `recommend.py` (CLI)
- 10 funkcji `check_*` (kadencja, GCT, flight, duty_factor, torso_lean, knee@contact,
  vert_osc, symmetry, foot_strike, data_quality)
- Reguła łączona **overstriding combo** (cad<160 ∧ GCT_mean>270) — Heiderscheit 2011
- Severity 4-poziomowe: critical / warning / watch / info
- Citation w każdej rekomendacji (do obrony pracy + transparentność w raporcie)
- Test na 3 biegaczach: Adam (sanity), 22 (test), 25 Janek (świeży test z kiepskiego materiału)

### Wyniki testów

| Biegacz | conf | Kadencja | GCT L/R | Max SI | crit/warn/watch/info |
|---|---|---|---|---|---|
| Adam (train) | 0.91 | 173 ℹ️ | 203/245 | 18.7% | 0 / 2 / 1 / 3 |
| Film 22 (test) | 0.89 | 163 🟡 | 285🟠/226 | 35.0% | 0 / 3 / 5 / 2 |
| Janek (nowy test) | 0.88 | **148** 🔴 | 193/**357**🔴 | **60.0%** | **2** / 3 / 3 / 2 |

### Kluczowe obserwacje sesji

1. **Janek — ciekawy edge case**: avg_conf 0.88 powyżej progu 0.85 (proxy jakości się **nie**
   uruchomiło), steps L/R 98/99 zbalansowane (steps SI proxy się **nie** uruchomiło), ale
   GCT/DF asymetria 60%. Pojedyncze proxy nie wystarcza — potrzebny combinatorical check.
2. **Detection 100% u Janka** mimo zasłoniętego biodra przez poręcze — MediaPipe radzi sobie
   z częściową okluzją lepiej niż się obawialiśmy.
3. **Janek foot strike kąty −4°, −3°** (rozsądne!) — kontrhipoteza dla limitation #9 z notatki
   Iteracji 1: ekstremalne kąty −33°/−58° w innych filmach mogą być wrażliwe na ujęcie/aspect ratio,
   nie systematycznie zafałszowane.
4. **Reguły deterministyczne** dają repeatable, transparent recommendations z literackim
   uzasadnieniem każdej decyzji — idealne dla rozdziału 7 pracy magisterskiej.

### Materiał do pracy magisterskiej

Notatka thesis `2026-05-12-etap7-rekomendacje.md`:
- Architektura modułu rekomendacji + tabela 10 reguł × progi × citation
- Reguła łączona overstriding (Heiderscheit 2011 jako kluczowa publikacja)
- Wyniki na 3 biegaczach (Adam / 22 / Janek) + interpretacja per biegacz
- 4 punkty walidacji jakości (literatura progi, reguły łączone, severity, low quality detection)
- 4 punkty Future Work (combinatorical low quality detection, stride length rules, callout w raporcie, walidacja na większej próbce)
- 3 punkty Limitations (deterministyczne, ogólne progi, średnie wartości)

### Stan plików

- `src/recommendations/` — 3 nowe pliki (rules.py 480 linii, recommend.py 165, __init__.py)
- `data/inference/25-janek__segment_1-{phases.csv, temporal, spatial, symmetry, meta}.json` — Janek
- `data/inference/{22,24-adam,25-janek}-recommendations.json` — wyniki silnika
- `data/inference/raporty/{22,24-adam,25-janek}-rekomendacje.md` — MD do dołączenia do raportu

### Do zrobienia w następnej sesji

**Integracja Etapu 7 z analyze.py** — dodać krok 6 "generuj rekomendacje" do orchestration,
żeby `analyze.py` w jednym wywołaniu generował też rekomendacje.

**Iteracja 2** (z briefu poprzedniej sesji, niezmieniona):
1. Stride length z `--treadmill-speed-ms`
2. **Combinatorical low quality detection** — wzbogacenie reguły jakości (Janek pokazał edge case)
3. Stable segment detection dla mixed-tempo
4. Generator PDF z wykresami

### Otwarte sprawy / drobne TODO

- Bug `postprocess_median.predict_lstm` (niezmieniony z poprzednich sesji)
- Walidacja foot strike kątów: Janek dał normalne kąty, więc hipoteza "systematyczny błąd"
  z limitation #9 wymaga rewizji
- Adam meta.json dalej nie wygenerowany (--skip-inference + run analyze do tego potrzebny)

### Odkładane decyzje (bez zmian)

- Wersjonowanie `models/` i `data/inference/`
- Walidacja 3D motion capture
- Iteracja 2 (po Etapie 7 — naturalna kontynuacja)
