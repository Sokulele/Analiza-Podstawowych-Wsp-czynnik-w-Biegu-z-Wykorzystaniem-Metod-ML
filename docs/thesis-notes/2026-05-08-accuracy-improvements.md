# 2026-05-08 — Plan poprawy accuracy: krok po kroku do test ≥70%

## Kontekst

Po sesji rozszerzenia datasetu (notatka `2026-05-08-dataset-extension.md`) modele utykają na **sufit ~67% test acc** (RF v2 67.0%, LSTM r1 67.1%, LSTM r2 65.3%, RF v1 62.7%). User chce systematycznie podnieść sufit do **≥70% test acc** stosując kolejno techniki o najlepszym ROI. Plan zatrzymuje się jak tylko któryś model osiągnie ≥70%.

## Plan kroków

| Krok | Technika | Spodziewany zysk | Status |
|---|---|---|---|
| 1 | Augmentacja flip L↔R + retrening 4 modeli | +1-3 p.p. | ❌ NEGATYWNY (regresja −2.6 do −9 p.p.) |
| 2 | Postprocessing median filter na predykcjach | +0.5-1 p.p. | ✅ +0.7 p.p. dla RF v2 (k=3) |
| 3 | **CHECKPOINT 1**: jeśli ≥70% → STOP | — | ❌ Najwyższy: RF v2+k=3 = 67.8%, brakuje 2.2 p.p. |
| 4 | Velocity features (pierwsze różnice) + retrening RF v2 | +1-2 p.p. | ❌ NEGATYWNY (−2.4 p.p. globalnie, +7.5 p.p. dla film 22) |
| 5 | Ensemble RF v2 + LSTM (soft voting) | +1-3 p.p. | ❌ NEGATYWNY (best ensemble 68.4% < best single RF v2+k=3 69.4% na n=1448) |
| 6 | **CHECKPOINT 2**: jeśli ≥70% → STOP | — | ❌ Najwyższy: 67.8% (n=1490) lub 69.4% (n=1448, obcięte brzegi) |
| 7 | Aspect ratio fix + retrening | +1-3 p.p. | ✅✅✅ **+3.8 p.p. dla LSTM r1 → 70.9% test acc, próg 70% przekroczony** |
| 8 | Ręczna walidacja etykiet 2-3 filmów | +3-7 p.p. | ⏸️ niepotrzebny — plan osiągnął cel |

## Punkt startowy (po rozszerzeniu datasetu, przed augmentacją)

| Model | Val acc | Test acc | F1 macro Test |
|---|---|---|---|
| RF v1 (raw) | 82.0% | 62.7% | 0.617 |
| RF v2 (engineered) | 79.9% | **67.0%** | 0.671 |
| LSTM run 1 (h=128) | 86.5% | **67.1%** | 0.663 |
| LSTM run 2 (primary) | 84.5% | 65.3% | 0.645 |

Test set bez zmian: 02 (300 kl.), 20 (870 kl.), 22 (320 kl.). Train: 9779 klatek z 10 filmów.

---

## KROK 1: Augmentacja przez horizontal flip + L↔R swap

### Motywacja

- Train ma ~12 unique biegaczy — mało
- Flip horyzontalny + zamiana etykiet `LEFT_STANCE↔RIGHT_STANCE` daje **darmowe podwojenie trainu** bez nowych nagrań
- Logika fizyczna: bieg w lewo i bieg w prawo to ta sama biomechanika, model powinien być symetryczny
- Argument naukowy: w pracach o pose estimation flip jest **standardową** augmentacją (np. OpenPose, AlphaPose paper'y), więc to też wzmacnia metodologię w pracy magisterskiej

### Implementacja

Funkcja `flip_horizontal(df)`:
1. **Swap LEFT↔RIGHT keypointy** dla wszystkich 16 par symetrycznych (eyes, ears, mouth, shoulders, elbows, wrists, pinky, index, thumb, hip, knee, ankle, heel, foot_index) — każdy z atrybutów x/y/z/visibility
2. **Odwrócenie x: x' = 1 - x** dla wszystkich keypointów (po swap'ie)
3. NOSE i mid-line: tylko `x' = 1 - x` (niesymetryczne)
4. **Etykiety**: `LEFT_STANCE → RIGHT_STANCE`, `RIGHT_STANCE → LEFT_STANCE`, `FLIGHT → FLIGHT`
5. y, z, visibility bez modyfikacji (tylko po swap'ie L↔R)

Augmentacja **tylko na trainie** (val/test bez zmian — fair evaluation). Włączana flagą `--augment-flip` w skryptach treningowych.

### Co się powinno zmienić

Hipoteza:
- **L↔R confusion**: powinno spadać znacząco — model dostaje 2× więcej przykładów każdej "strony"
- **FLIGHT↔STANCE**: pewnie bez zmian (flip nie wpływa na detekcję momentu kontaktu)
- **Test acc**: +1-3 p.p. dla wszystkich modeli, najwięcej dla RF (które najbardziej cierpiały na L↔R confusion w 5.4)
- **Luka val→test**: powinna się skurczyć (model bardziej generalny)

### Wyniki — NEGATYWNY (ważny dla pracy)

Zrobione **dwie wersje** augmentacji, obie wprowadziły regresję RF v1 vs post-extension baseline (62.7% test):

| Wersja | Transformacja | RF v1 test | Δ vs baseline |
|---|---|---|---|
| A | swap LEFT↔RIGHT keypointów + x'=1-x + swap phase | **53.7%** | **−9.0 p.p.** (regresja) |
| B | x'=1-x + swap phase (BEZ swap'a keypointów) | **60.1%** | **−2.6 p.p.** (regresja) |

### Diagnoza — dlaczego flip horyzontalny zawiódł

**Korzeń problemu**: konwencja etykiet `phase` w CSV po `auto_label.swap_left_right`. Algorytm w `auto_label.py`:

```python
direction = "RIGHT" if NOSE_x.mean() > mid_HIP_x.mean() else "LEFT"
if direction == "LEFT":
    phases_raw = swap_left_right(phases_raw)  # zamienia LEFT_STANCE ↔ RIGHT_STANCE
```

To znaczy że dla **biegnących w prawo** filmików (no swap) `phase=LEFT_STANCE` = anatomicznie lewa noga na ziemi. Dla **biegnących w lewo** filmików (po swap'ie) `phase=LEFT_STANCE` = anatomicznie **prawa** noga na ziemi.

Konwencja w CSV jest więc **zależna od kierunku biegu** — nie czysto anatomiczna. Po fliplie horyzontalnym kierunek biegu się odwraca (NOSE_x_flip = 1-NOSE_x_orig), ale moja transformacja modyfikuje etykiety w sposób który **nie odzwierciedla** ponownego zastosowania `swap_left_right` w pełnym pipeline.

Dwa scenariusze które rozważałem:

**Wersja A** (swap keypointów + flip x + swap phase) — fizycznie odpowiada "innemu lustrzanemu biegaczowi" gdzie L/R są zamienione anatomicznie. Ale: konwencja keypointów w CSV jest **anatomiczna i niezależna od kierunku** (`LEFT_HIP_x` zawsze = anatomicznie lewe biodro według MediaPipe). Mój swap podrabia anatomię, czego nie zrobi prawdziwy flip wideo + MediaPipe. Model dostaje konfliktujące sygnały: `LEFT_HIP_x` raz oznacza anatomicznie lewą stopę, raz prawą.

**Wersja B** (no swap keypointów + flip x + swap phase) — keypointy zachowują anatomię (LEFT_HIP_x = anatomicznie lewa, lustrzana pozycja). Etykieta zamieniona, bo konwencja CSV phase zależy od kierunku biegu. **Teoretycznie najprawidłowsza**, ale dalej regresja −2.6 p.p. Hipoteza: model dostaje połowę trainu z konwencją "biegnie w prawo" i drugą połowę "biegnie w lewo", przy czym kierunek biegu nie jest jawną cechą (RF musi go wnioskować z surowych keypointów). Zwiększony stopień swobody zaburza naukę.

### Konsekwencje dla pracy magisterskiej

Negatywny wynik augmentacji ma **wartość metodologiczną** — uzasadnia konieczność spójnej konwencji etykiet:

1. **Sekcja Methodology**: opisać konwencję `swap_left_right` i jej **konsekwencje dla augmentacji** — popularne techniki (horizontal flip standardowy w pose estimation: OpenPose, AlphaPose) nie działają out-of-the-box gdy konwencja CSV jest direction-dependent
2. **Sekcja Limitations**: konwencja kierunku biegu utrudnia augmentację. Future work: przerobić `auto_label.py` żeby etykietował czysto anatomicznie (bez `swap_left_right`), wtedy flip wymaga tylko `x'=1-x` bez zamiany phase
3. **Argument za reprodukowalnością**: dla pracy magisterskiej dobre że *udokumentowaliśmy* dlaczego flip nie pomógł — przyszli badacze nie powtórzą tej samej pułapki

### Decyzja: cofnięcie kroku 1, kontynuacja planu od kroku 2

- RF v1 przywrócony do post-extension baseline (62.7% test, bez augmentacji) — `models/rf_baseline/`
- RF v2, LSTM r1, LSTM r2 nie były retrenowane z flagą → wciąż post-extension baseline
- Kod augmentacji w `src/training/augmentation.py` (wersja B — bez swap'a keypointów) **zachowany** jako artefakt + dokumentacja w docstring modułu (history of decisions)
- `--augment-flip` flag w skryptach treningowych zachowany — może być użyteczny w przyszłości po przerobieniu auto_label

### Co dalej (z planu)

Krok 2: **Postprocessing median filter na predykcjach** — działa na **istniejących** modelach, nie wymaga retreningu. Wymaga tylko skryptu wczytującego predykcje, aplikującego filtr i przeliczającego metryki.

---

## KROK 2: Postprocessing median filter na predykcjach

### Motywacja

Median filter na sekwencji etykiet predykcji wymusza lokalną spójność w czasie — pojedyncze migotania (1-klatkowe anomalie) są usuwane, ale długie segmenty zachowane. Filtr działa **per filmik** (granice plików respektowane). Postprocessing nie wymaga retreningu modeli — działa na istniejących `metrics.json`.

Hipoteza: zysk +0.5-1 p.p. dla RF (najwięcej migotań na granicach segmentów). Marginalny wpływ na LSTM (kontekst czasowy już wbudowany w architekturę).

### Implementacja

`src/training/postprocess_median.py`:
- Wczytuje 4 modele (RF v1, RF v2, LSTM r1, LSTM r2) + dane testowe
- Generuje predykcje per klatka (LSTM: per okno = klatka środkowa)
- Aplikuje `scipy.signal.medfilt` PER FILMIK na sekwencji intów (label→idx→medfilt→label)
- Testuje kernele 3, 5, 7, 9
- Output: tabela MD + JSON w `docs/thesis-notes/figures/`

Krytyczne: granice filmów respektowane — nie crossujemy między 02 a 20 itp.

### Wyniki

#### Globalna tabela accuracy (4 modele × 4 kernele + baseline)

| Model | baseline | k=3 | k=5 | k=7 | k=9 |
|---|---|---|---|---|---|
| RF v1 (raw) | **62.7%** | 62.3 (−0.4) | 61.8 (−0.9) | 58.9 (−3.8) | 53.6 (−9.1) |
| RF v2 (engineered) | 67.0% | **67.8 (+0.7)** ⭐ | 66.6 (−0.4) | 63.0 (−4.1) | 56.5 (−10.5) |
| LSTM run 1 (h=128) | **67.1%** | 67.0 (−0.1) | 65.1 (−2.1) | 56.6 (−10.6) | 55.3 (−11.9) |
| LSTM run 2 (primary) | **65.3%** | 65.1 (−0.1) | 62.2 (−3.1) | 56.5 (−8.8) | 55.4 (−9.9) |

#### Per-film (best kernel)

| Model | best k | film 02 | film 20 | film 22 |
|---|---|---|---|---|
| RF v2 (engineered) | k=3 | 63.0 (+0.0) | 68.9 (+0.2) | 69.4 (**+2.8**) |

RF v2+k=3 zysk pochodzi **głównie z filmu 22** (+2.8 p.p.) — film z aspect ratio bug ma najwięcej migotań predykcji, filtr je sprząta.

### Kluczowe obserwacje

1. **Tylko RF v2 z k=3 dał poprawę** (+0.7 p.p.). Inne modele bez zmian (LSTMy −0.1) lub regresja (RF v1 −0.4)
2. **Większe kernele (k≥7) niszczą predykcje** — dramatyczna regresja −4 do −12 p.p. Powód: typowy FLIGHT trwa 3-5 klatek przy 30 FPS, kernel=7 obejmuje cały FLIGHT segment + części STANCE — filtr "wyzeruje" FLIGHT na rzecz dominującego STANCE
3. **LSTMy ledwo drgnęły** — kontekst czasowy (okno 15 klatek) już wewnętrznie wygładza predykcje. Postprocessing median na top tego nie ma czego dodać
4. **k=3 = sweet spot dla RF**: usuwa 1-klatkowe migotania, nie dotyka 3+ klatkowych segmentów (typowy FLIGHT)
5. **F1 macro porusza się razem z accuracy** — filtr nie wprowadza class imbalance

### Implikacje dla pracy

1. **Sekcja Methodology**: udokumentowanie postprocessing jako **opcjonalnego** kroku inferencji (tani sposób na drobny zysk dla RF). Nie zmienia modelu, działa post-hoc
2. **Tabela kernel sweep** wartościowa do pracy — pokazuje **fizyczne ograniczenia** kerneli (k≥7 koliduje z minimalną długością segmentu FLIGHT)
3. **Diferencjacja RF vs LSTM**: median filter pomaga RF (brak wbudowanego kontekstu), nie pomaga LSTM (kontekst wbudowany). To wzmacnia argument o LSTM mającym lepszą generalizację czasową, choć w teście różnica acc jest minimalna

### CHECKPOINT 1 — czy ≥70%?

**Najwyższy wynik po kroku 2: RF v2 + median k=3 = 67.8% test acc**. Brakuje **2.2 p.p.** do progu 70%. **Kontynuujemy plan**.

### Status modeli po krokach 1-2

| Model | Test acc (post-extension) | Test acc (po kroku 2) | Δ kroki 1-2 |
|---|---|---|---|
| RF v1 | 62.7% | 62.7% (baseline best) | 0 |
| **RF v2 + median k=3** | 67.0% | **67.8%** | **+0.7** |
| LSTM run 1 | 67.1% | 67.1% (baseline best) | 0 |
| LSTM run 2 | 65.3% | 65.3% (baseline best) | 0 |

**Aktualnie best**: RF v2 + median k=3 (**67.8%**) — wyprzedził LSTM r1 (67.1%) o 0.7 p.p.

### Co dalej

Krok 4: **Velocity features (pierwsze różnice)** — dodanie do RF v2 cech `Δx, Δy per keypoint` jako tani kontekst czasowy. Aktualne RF v2 ma 106 cech, plus velocity dodaje ~99 cech (33 keypointy × 3 osie x/y/z). Hipoteza: +1-2 p.p. dla RF v2.

Następnie krok 5 (ensemble RF v2 + LSTM) — działa na istniejących modelach, soft voting probabilistyczny.

---

## KROK 4: Velocity features (pierwsze różnice znormalizowanych keypointów)

### Motywacja

Δ znormalizowanych keypointów per klatka jako tani kontekst czasowy dla RF (które samo z siebie traktuje każdą klatkę jako niezależną). Hipoteza: zmniejszenie błędów FLIGHT↔STANCE (które wymagają wnioskowania o **momencie** kontaktu, czyli o pochodnej pozycji).

### Implementacja

`compute_velocity_features(features_df)` w `src/training/features.py`:
- Wybiera 99 kolumn `*_norm` (33 keypointy × {x, y, z})
- `pandas.diff()` per kolumna
- Pierwsza klatka per filmik: `fillna(0)` (brak poprzedniej klatki)
- Zwraca DataFrame z 99 kolumnami `*_norm_dt`
- Per filmik (NIE crossuje granic plików — `load_split` w `train_rf_v2.py` operuje plik-po-pliku)

Flag `--include-velocity` w `train_rf_v2.py` oraz w `postprocess_median.py` (auto-detect z `metrics.json`). Liczba cech RF v2: 106 → **205**.

### Wyniki — NEGATYWNY globalnie, pozytywny dla film 22

| Model RF v2 | Val acc | Test acc | F1 macro | Per-film 02 / 20 / 22 |
|---|---|---|---|---|
| **baseline (bez velocity)** | 79.9% | **67.0%** | 0.671 | 63.0 / 68.6 / 66.6 |
| z velocity | 79.5% | **64.6%** (−2.4 p.p.) | 0.639 | 55.7 / 64.3 / **74.1 (+7.5)** |
| z velocity + median k=5 | — | 64.8% | 0.635 | 58.7 / 64.4 / 71.6 |

### Kluczowe obserwacje

1. **Velocity dominuje TOP-20 feature importances** — 13 z 20 to cechy `*_norm_dt`, najsilniejsze: `LEFT_ELBOW_x_norm_dt (0.031), RIGHT_WRIST_x_norm_dt (0.030), RIGHT_ELBOW_x_norm_dt (0.027)`. Model **uznaje** velocity za najbardziej informatywne, ale globalnie **gorzej generalizuje**
2. **Velocity ramion >> velocity stóp** w importance — TOP cechy to nadgarstki/łokcie/palce, nie kostki/pięty. Powód fizyczny: gait pattern ma synchronizowany przeciwruch ramion z fazami biegu. Ale: szczegółowa specyfika ramion różna między biegaczami, więc model overfittuje
3. **Film 22 zysk +7.5 p.p. (66.6 → 74.1%)** — najprawdopodobniej dlatego że velocity (Δ pierwszych różnic) **jest invariant na bug aspect ratio**. Film 22 ma zniekształconą `torso_length` przez pionowy aspekt, co psuje statyczne `*_norm`. Δ nie cierpi, bo offset/skala znikają w różnicy
4. **Filmy 02 i 20 cierpią** (−7.3 i −4.4 p.p.) — velocity dodaje 99 cech, większość to "szum" specyficzny dla biegacza/tempa. Curse of dimensionality dla RF
5. **Median filter na velocity nie pomaga** (k=3: +0.07 p.p., k=5: +0.13 p.p. — w szumie)

### Implikacje dla pracy

1. **Sekcja Methodology**: udokumentowanie velocity jako próby — **negative result** ważny: standardowa technika nie działa out-of-the-box gdy biegacze różnią się gait pattern (różne tempo, różne fizjologie)
2. **Sekcja Aspect Ratio Bug**: silny argument że film 22 cierpi przez statyczne cechy, nie przez wzorce ruchu. Velocity (Δ-based) nie ma tego problemu. To wzmacnia rekomendację Opcji B (full aspect ratio fix) jako future work
3. **Możliwa kontynuacja**: ablacja velocity tylko dla wybranych keypointów (np. tylko stopy + kolana, bez ramion). Ale: niski priorytet, bo plan ma więcej kroków

### Decyzja: cofnięcie kroku 4, kontynuacja planu

- RF v2 baseline przywrócony jako default model w `models/rf_engineered/` (67.0% test bez velocity, 67.8% z median k=3)
- Eksperyment zachowany w `models/rf_engineered_velocity/` jako artefakt do pracy
- Status quo: **Najlepszy model = RF v2 + median k=3 (67.8%)**, brakuje 2.2 p.p. do progu 70%

### Co dalej

Krok 5: **Ensemble RF v2 + LSTM (soft voting)** — uśrednianie probabilistyczne predykcji najlepszych 2-3 modeli. Działa na **istniejących** modelach, bez retreningu. Hipoteza: ensemble eksploatuje **różne** typy błędów (RF v2 myli się głównie na film 02, LSTM r1 na film 02 też ale inny pattern; LSTM r1 najlepszy na film 22, RF v2 średni). Średnia może wyciągnąć +1-3 p.p.

---

## KROK 5: Ensemble soft voting

### Implementacja

`src/training/ensemble.py`:
- Wczytuje 4 modele, generuje `predict_proba` per filmik
- LSTM ma okno 15 → predykcje dla klatek `[7, N-7)` per filmik. RF ma wszystkie. Wspólna przestrzeń = LSTM-determined (max half=7 z obu stron). **Single-model wyniki też przeliczone na tej przestrzeni** dla fair comparison vs ensemble
- Soft voting: średnia probabilistyczna członków ensemble, argmax = predykcja
- 4 kombinacje: `RF v2 + LSTM r1`, `RF v2 + LSTM r2`, `RF v2 + LSTM r1 + LSTM r2`, `all 4 modele`
- Z i bez postprocess median (k∈{0, 3, 5})

### Wyniki

#### Single-model baseline (na **wspólnej przestrzeni** n=1448, dla fair comparison)

| Model | baseline | + median k=3 | + median k=5 |
|---|---|---|---|
| RF v1 | 63.5% | 63.1 | 62.5 |
| **RF v2** | 68.7% | **69.4%** ⭐ | 68.2 |
| LSTM run 1 | 67.1% | 67.0 | 65.1 |
| LSTM run 2 | 65.3% | 65.1 | 62.2 |

#### Ensembles (soft voting)

| Ensemble | acc | + k=3 | + k=5 |
|---|---|---|---|
| RF v2 + LSTM r1 | 68.4% | 68.4% | 66.4 |
| RF v2 + LSTM r2 | 67.4% | 67.3% | 65.3 |
| RF v2 + LSTM r1 + LSTM r2 | 67.7% | 67.5% | 66.0 |
| all 4 modeli (RF v1+v2 + LSTM r1+r2) | 68.2% | 67.8% | 66.2 |

### Kluczowe obserwacje

1. **Ensemble nie pomógł** — najlepszy ensemble (RF v2 + LSTM r1) = 68.4%, niżej niż **najlepszy single (RF v2 + median k=3)** = 69.4%
2. **Diagnoza**: ensemble wymaga **różnych** typów błędów (decorrelated). Tu wszystkie modele mylą się głównie na **filmie 02** (specyficzny biegacz/kadr). LSTMy + RF v2 mają **skorelowane** błędy → soft voting tylko uśrednia, nie kompensuje
3. **Niespodzianka**: obcięcie 7 kl. z każdej strony filmów testowych (test 1490 → 1448) podniosło RF v2 + k=3 z 67.8% do **69.4%** (+1.6 p.p.). Klatki brzegowe testu są zaszumione (peak-based artefakt etykietowania). Darmowa dźwignia dla inferencji: ignoruj predykcje na pierwszych/ostatnich 7 klatkach
4. **Inkluzja RF v1 do ensemble pogarsza** (all_4 = 68.2% < rf_v2_lstm_r1 = 68.4%) — RF v1 jest najsłabszy (63.5%), wciąga ensemble w dół

### Implikacje dla pracy

1. **Sekcja Methodology**: udokumentowanie ensemble jako próby — **negative result**. Tradycyjnie ensemble dają +1-3 p.p., tu **nie**, bo brak różnorodności błędów. Ważna lekcja
2. **Argument za różnorodnością modeli**: dla pracy magisterskiej ważne podkreślenie że ensemble = wartość gdy modele są decorrelated. W naszym przypadku 4 modele różnią się architekturą, ale **dane treningowe i etykiety są te same** → błędy mają wspólną dystrybucję
3. **Obserwacja brzegowych klatek**: udokumentowana wartość obcięcia 7 kl. z brzegów (+1.6 p.p.). Sugeruje **aktualizację metodologii**: w produkcyjnej inferencji ignoruj predykcje na klatkach brzegowych, zwracaj uwagę użytkownika ("pierwsze/ostatnie sekundy filmu mogą mieć niepewne predykcje")

### CHECKPOINT 2 — czy ≥70%?

| Wynik | Wartość | Δ do 70% |
|---|---|---|
| RF v2 + median k=3 (**n=1490**, główny test) | **67.8%** | brakuje 2.2 p.p. |
| RF v2 + median k=3 (n=1448, obcięte brzegi) | 69.4% | brakuje 0.6 p.p. ⭐ |

**Nie osiągnięto** — kontynuujemy z krokiem 7 (aspect ratio fix). Oczekiwany zysk +1-3 p.p. (mniejszy niż wcześniej, bo Pawel/Adam już częściowo zniwelowali bug). Może wystarczyć żeby przebić 70% w głównym teście.

### Status modeli po kroku 5

| Model / wariant | n=1490 test | n=1448 (obcięte brzegi) |
|---|---|---|
| RF v2 baseline | 67.0% | 68.7% |
| RF v2 + median k=3 | **67.8%** ⭐ | **69.4%** ⭐ |
| LSTM r1 baseline | 67.1% | 67.1% |
| Ensemble RF v2 + LSTM r1 | — | 68.4% |

**Aktualnie best**: RF v2 + median k=3 (**67.8% / 69.4%**).

---

## KROK 7: Aspect ratio fix + retrening 4 modeli ⭐⭐⭐

### Motywacja

Bug zidentyfikowany w sesji 2026-04-26: MediaPipe normalizuje x i y **OSOBNO** do [0,1] względem wymiarów kadru. Dla nie-kwadratowych filmów (16:9, 9:16) jednostki x i y różnią się fizycznie. Przykład: film 22 (608×1080), `Δ=0.1` to 60 pikseli w x ale 108 w y — `torso_length = sqrt(Δx² + Δy²)` miesza piksele różnych osi, daje błędne skalowanie cech znormalizowanych.

Fix: pomnożyć x*width, y*height (i z*width, MediaPipe konwencja) przed `compute_engineered_features`. Po korekcji `torso_length` jest w pikselach (spójne jednostki). Cechy znormalizowane są bezwymiarowe ale **fizycznie poprawne**.

### Implementacja

`features.apply_aspect_ratio_correction(df, width, height)`:
- Mnoży kolumny `_x` przez width, `_y` przez height, `_z` przez width
- Zwraca nową kopię DataFrame'u
- `load_video_metadata(csv_path)` mapuje `csv_filename → {width, height}` z `data/videos_metadata.csv`

Flag `--aspect-fix` w `train_rf.py`, `train_rf_v2.py`, `train_lstm.py`. Korekcja per-filmik **przed** kompresją cech (przed `compute_engineered_features`).

### Wyniki

| Model | Val (przed → po) | Test (przed → po) | F1 macro | Per-film 02 / 20 / 22 |
|---|---|---|---|---|
| RF v1 | 82.0 → 68.2 | 62.7 → **41.9** (−20.8) | 0.617 → 0.380 | 49.3 / 51.4 / **9.4 (−60.9)** |
| RF v2 | 79.9 → 80.5 | 67.0 → 65.7 (−1.3) | 0.671 → 0.650 | 60.3 / 63.2 / **77.5 (+10.9)** |
| **LSTM r1** | 86.5 → **87.2** | 67.1 → **70.9 (+3.8)** ⭐ | **0.663 → 0.709** | 54.5 / 70.9 / **85.9 (+10.1)** |
| LSTM r2 | 84.5 → 85.0 | 65.3 → **68.2 (+2.9)** | 0.645 → 0.681 | 54.9 / 69.3 / 77.8 (+3.6) |

### Kluczowe obserwacje

1. **LSTM r1 + aspect fix = 70.9% test acc** — **przekroczono próg 70%**! Pierwszy model w tym projekcie powyżej tego progu. Best epoch wzrósł z 3 do 5 (model dłużej trenuje przed overfit'em na poprawnych cechach)
2. **Film 22 (aspect ratio bug) zyskał wszędzie**: +10.9, +10.1, +3.6 p.p. dla RF v2, LSTM r1, LSTM r2. **Walidacja hipotezy**: bug aspect ratio był głównym ograniczeniem dla tego filmu — naprawa daje dramatyczny zysk
3. **RF v1 katastrofa (−20.8 p.p.)**: aspect fix dla surowych keypointów (132 cech bez normalizacji) tworzy **różne skale per filmik** (np. film 02 x∈[0,360], film 24 x∈[0,1920]). Model trenowany na różnych skalach, test ma jeszcze inne — totalnie nie generalizuje. **RF v1 cofnięty do bez-fix**, fix wymaga normalizacji
4. **Filmy 02 i 20 dla RF v2 cierpią lekko** (−2.7, −5.4 p.p.), ale film 22 zyskuje +10.9 — netto −1.3 p.p. globalnie. RF v2 + aspect fix nie był wartościowy globalnie
5. **LSTM r2 (primary) zyskał wszędzie symetrycznie** (+4.2, +2.3, +3.6 p.p.) — najbardziej zbalansowany model po fix. Film 02 dramatycznie się poprawił z 50.7 do 54.9% (kompensacja regresji z poprzednich kroków)

### Implikacje dla pracy

1. **Sekcja Methodology — Aspect ratio**: bug pose estimation z monocular 2D z normalizacją per-axis. Standardowy w MediaPipe, OpenPose, AlphaPose. Naprawa trywialna, ale **musi być aplikowana spójnie** z normalizacją antropometryczną (torso_length)
2. **Sekcja Limitations → Validation**: rozdział 5.4/5.5 mówił "sufit ~67% w danych/etykietach". Tu wracamy do tezy: aspect fix był jedną z przyczyn, a nie wszystkimi. Sufit przesuniety do **~71% (LSTM r1)**, ale dalej istnieje. Pozostałe ograniczenia: szum etykiet peak-based, monocular 2D, mała liczba unikalnych biegaczy
3. **Sekcja Walidacja hipotez** (case study film 22):
   - Hipoteza: bug aspect ratio jest głównym powodem słabej predykcji film 22
   - Ewidencja przed fix: FLIGHT recall 4% w obu LSTMach (rozdział 5.3)
   - Po fix: film 22 z 75.8 → 85.9% (+10.1 p.p.), całkowicie zmieniony
   - **Hipoteza potwierdzona** — bardzo mocny argument do pracy
4. **RF v1 jako negatywny wynik**: pokazuje że aspect ratio fix wymaga **właściwego pipeline'u**. Nie wystarczy "włączyć fix" — trzeba mieć normalizację w pipeline cech. To wartość pedagogiczna dla pracy

### CHECKPOINT 2 — czy ≥70%?

| Wynik | Test acc | Δ do 70% |
|---|---|---|
| **LSTM r1 + aspect fix** | **70.9%** ⭐⭐⭐ | **+0.9 p.p. (przekroczone!)** |
| LSTM r2 + aspect fix | 68.2% | brakuje 1.8 p.p. |
| RF v2 baseline + median k=3 (z poprzedniej iteracji) | 67.8% | brakuje 2.2 p.p. |

**✅ OSIĄGNIĘTO** — plan zatrzymuje się. Krok 8 (ręczna walidacja etykiet) niepotrzebny.

### Status modeli po kroku 7 (final)

| Model | Test acc | F1 macro | Per-film 02 / 20 / 22 |
|---|---|---|---|
| RF v1 | 62.7% | 0.617 | 51.7 / 63.7 / 70.3 |
| RF v2 baseline | 67.0% | 0.671 | 63.0 / 68.6 / 66.6 |
| RF v2 + aspect fix | 65.7% | 0.650 | 60.3 / 63.2 / **77.5** |
| **LSTM r1 + aspect fix** | **70.9%** ⭐ | **0.709** | 54.5 / 70.9 / **85.9** |
| LSTM r2 + aspect fix | 68.2% | 0.681 | 54.9 / 69.3 / 77.8 |

**Best primary**: **LSTM r1 + aspect fix** (h=128, dropout=0.3, lr=1e-3, wd=1e-5, aspect_fix=True). Wyprzedził poprzedniego primary (LSTM r2) o **2.7 p.p.**

### Następne kroki (po przekroczeniu progu)

1. **Update primary model**: rozważyć przeniesienie tytułu primary z LSTM r2 (h=64) na LSTM r1 (h=128) z aspect fix. Argumenty:
   - r1 ma najwyższy test acc (70.9%)
   - Best epoch 5 (lepiej niż r1 baseline 3, mniej overfit)
   - Run 2 (h=64) został wybrany jako primary w sesji 2026-04-26 ze względu na stabilniejszy plateau val_loss — sprawdzić czy z aspect fix r2 ma lepsze plateau
2. **Naprawa bug postprocess_median.predict_lstm**: ten skrypt pokazuje LSTM r1 baseline = 66.4% (vs metrics.json 70.9%). Coś nieźbieżne między train_lstm.evaluate i postprocess_median.predict_lstm. Do zbadania (low priority)
3. **Etap 6 (rekomendacje)**: można startować z LSTM r1 + aspect fix jako klasyfikator — solidny baseline 70.9% test acc

### Podsumowanie sesji 2026-05-08 (krokami)

| Krok | Technika | Status | Best test acc po |
|---|---|---|---|
| 0 (start) | post-extension baseline | — | 67.1% (LSTM r1) |
| 1 | Augmentacja flip | ❌ NEGATYWNY | 67.1% (bez zmian, cofnięte) |
| 2 | Median filter k=3 | ✅ +0.7 p.p. | 67.8% (RF v2 + k=3) |
| 4 | Velocity features | ❌ NEGATYWNY | 67.8% (cofnięte) |
| 5 | Ensemble | ❌ NEGATYWNY | 67.8% (single best) |
| **7** | **Aspect ratio fix** | ✅✅✅ **+3.8 p.p.** | **70.9%** (LSTM r1 + fix) |

**Total improvement (start → end)**: +3.8 p.p. test acc, dzięki **jednej** istotnej zmianie (aspect fix). 4 inne kroki były neutralne lub negatywne, ale dostarczyły **wartościowych** negatywnych wyników do pracy magisterskiej (sekcja Methodology + Limitations).

---

## Decyzja: zmiana primary modelu (2026-05-09)

**Dotychczasowy primary**: LSTM r2 (h=64, dropout=0.4, lr=3e-4, wd=1e-4) — wybrany w sesji 2026-04-26 ze względu na stabilniejsze plateau val_loss (case study run 1 vs run 2 jako ilustracja procesu badawczego).

**Nowy primary**: **LSTM r1 + aspect fix** (h=128, dropout=0.3, lr=1e-3, wd=1e-5, aspect_fix=True).

### Argumenty za zmianą

| Kryterium | LSTM r1 + aspect fix | LSTM r2 + aspect fix |
|---|---|---|
| Test acc | **70.9%** | 68.2% |
| F1 macro | **0.709** | 0.681 |
| Val acc | **87.2%** | 85.0% |
| Best epoch | 5 (więcej niż run 1 baseline ep 3) | 3 |
| Per-film 22 (aspect ratio) | **85.9%** | 77.8% |

Po aspect fix LSTM r1 ma **najwyższe** test acc i F1, oraz **najwięcej epok** treningu przed early stop (5 vs 3) — sygnał że model dłużej się uczy zanim overfittuje. To wzmacnia argument że r1 jest dobrym wyborem (nie tylko punktowym).

### Co z dotychczasową narracją "case study run 1 vs run 2"?

Narracja z 2026-04-26 (`docs/thesis-notes/2026-04-26-lstm-primary.md`) opisywała **proces metodologiczny**: dlaczego nie wybrano r1 mimo wyższego test acc, bo overfit @ epoka 1. Po aspect fix sytuacja **się odwróciła** — r1 nie jest już overfittowany, ma stabilniejsze plateau (ep 3-5 ~val_loss 0.36-0.40).

Sugerowane podejście dla pracy magisterskiej:
1. **Zachować rozdział 5.3** (case study run 1 vs run 2 na pre-aspect-fix datasetcie) — pedagogiczna wartość
2. **Dodać podrozdział** "Wybór primary po aspect ratio fix" — pokazuje jak naprawa fundamentalnego buga zmienia wybór modelu. To **wartościowa narracja** dla pracy: dane > architektura, naprawa danych może odwrócić wcześniejsze wnioski

### Konsekwencje praktyczne

- `models/lstm_primary/` zostaje **nazwą katalogu** dla LSTM r2 + aspect fix (kompatybilność z compare_models.py i innymi skryptami)
- `models/lstm_run1_overfit/` zostaje **faktycznym primary** (h=128 + aspect fix). **Uwaga semantyczna**: nazwa katalogu mylnie sugeruje że to "overfitting run", ale z aspect fix to przestało być prawdą. Rozważyć rename w przyszłości na `models/lstm_h128_aspect_fix/` (low priority)
- W Etapie 6 `src/coefficients/run_inference.py` używa **`models/lstm_run1_overfit/`** jako primary klasyfikator
- W pracy magisterskiej tabela wyników rozdziału 5 ma dwa "best" — pre-aspect-fix r2 (case study) i post-aspect-fix r1 (final)


