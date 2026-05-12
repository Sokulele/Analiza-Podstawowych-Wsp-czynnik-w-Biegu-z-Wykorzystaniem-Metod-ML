# 2026-05-09 — Etap 6 MVP: pipeline obliczania współczynników biegu

## Kontekst

Po sesji 2026-05-08 (przekroczony próg 70% test acc dzięki aspect ratio fix), klasyfikator faz jest gotowy do produkcyjnego użycia. Etap 6: pierwsza implementacja **inferencji E2E** wideo → fazy → współczynniki biomechaniczne. **Cel sesji**: MVP z testem na filmie Adama (24).

## Decyzje sesji

### 1. Primary model: LSTM r1 + aspect fix

Formalnie zmieniono primary z LSTM r2 (h=64) na **LSTM r1 + aspect fix** (h=128, dropout=0.3, lr=1e-3, wd=1e-5). Argumenty + szczegóły w `2026-05-08-accuracy-improvements.md` (sekcja "Decyzja: zmiana primary modelu"). **70.9% test acc, F1 0.709**.

### 2. Stride length pominięta w MVP

Stride length wymaga inputu użytkownika (prędkość bieżni). W MVP **pomijamy** — pozostałe współczynniki nie wymagają tej informacji. Implementacja stride length odłożona do iteracji po MVP (gdy będzie UI z polem "prędkość bieżni").

### 3. Test pipeline na Adamie (24)

Świadomy wybór: Adam jest w **train** (nie test), więc inferencja na nim **nie** jest fair miarą jakości klasyfikatora. Cel testu: weryfikacja że pipeline E2E działa. Adam ma 80s normalnej prędkości, idealne side-view, 100% MediaPipe detection.

## Architektura

```
src/coefficients/
├── __init__.py
├── run_inference.py     — wideo → MediaPipe → savgol → aspect fix → LSTM → fazy
├── temporal_metrics.py  — kadencja, GCT, flight, cycle, duty factor
├── spatial_metrics.py   — kąty stawów per faza, torso lean, vertical osc, foot strike
└── symmetry.py          — Symmetry Index L/P (Robinson 1987)
```

Każdy moduł CLI-runable standalone + reużywalny jako library (`compute_temporal_metrics`, `compute_spatial_metrics`, `compute_symmetry`).

### Pipeline danych

1. **`run_inference.py`** wczytuje wideo, MediaPipe Pose (complexity=2) per klatka, savgol smoothing (window=11, polyorder=3), pose_detected flag
2. Auto-detect `aspect_fix=True` z `model_dir/config.json` → `apply_aspect_ratio_correction(df, width, height)` (z `videos_metadata.csv`, ale tu height/width z `cv2.VideoCapture`)
3. `compute_engineered_features` → 106 cech (znormalizowane keypointy + 6 kątów stawów + torso lean)
4. `scaler.transform` (StandardScaler z trainu) → input dla LSTM
5. Sliding window N=15 klatek, target = klatka środkowa, `softmax(logits)` → predykcja + confidence
6. **Klatki krawędzi (pierwsze/ostatnie 7 = half)** dostają fazę pierwszej/ostatniej predykcji extend, confidence=0 (oznaczenie "niepewne")
7. Output CSV: `frame, timestamp, pose_detected, phase_predicted, confidence` + opcjonalnie wszystkie keypointy

### Decyzja klatek krawędzi: extend vs drop

- Drop (jak w eval) → klatki początkowe/końcowe nie mają predykcji
- Extend (zaimplementowane) → wszystkie klatki mają predykcję, ale pierwsze 7 i ostatnie 7 mają zerową confidence

Wybrane **extend** dla MVP — w produkcyjnej inferencji użytkownik chce widzieć fazy dla całego wideo, choć klatki brzegowe mają niepewną etykietę. Adekwatnie oznaczone (confidence=0).

## Wyniki na Adamie (24)

### Temporal metrics

| Metryka | Wartość | Typowe (literatura) |
|---|---|---|
| Kadencja | **173.5 spm** | 160-180 spm dla biegu |
| n_steps | 231 (L 115 / R 116) | symetryczne |
| GCT lewa | 203 ± 31 ms | 200-250 ms |
| GCT prawa | 245 ± 67 ms | 200-250 ms |
| Flight time | 122 ± 25 ms | 80-150 ms |
| Cycle time L | 684 ± 50 ms | dla 173 spm: 1/(173/120) = 693 ms ✓ |
| Cycle time R | 685 ± 30 ms | 693 ms ✓ |
| Duty factor L | 0.296 | 0.30-0.40 |
| Duty factor R | 0.357 | 0.30-0.40 |

**Walidacja**: kadencja 173 spm + cycle time 685 ms są spójne (60/0.685 ≈ 88 cykli/min × 2 nogi = 175 spm — różnica 1.5 spm to szum klatkowania).

### Spatial metrics

**Kąty stawów [stopnie] (mean ± std per faza):**

| Staw | overall | L_STANCE | R_STANCE | FLIGHT |
|---|---|---|---|---|
| LEFT_KNEE | 150.5 ± 16.6 | **163.7 ± 4.7** | 133.5 ± 14.7 | 156.8 ± 8.1 |
| RIGHT_KNEE | 139.5 ± 27.4 | 105.4 ± 23.5 | **157.2 ± 6.9** | 149.8 ± 15.8 |
| LEFT_HIP | 156.9 ± 10.4 | 145.8 ± 9.3 | 161.3 ± 6.7 | 161.6 ± 7.1 |
| RIGHT_HIP | 161.8 ± 5.2 | 161.5 ± 4.8 | 162.2 ± 5.3 | 161.8 ± 5.3 |
| LEFT_ANKLE | 138.3 ± 10.8 | 135.4 ± 6.6 | 134.6 ± 12.2 | 144.6 ± 9.2 |
| RIGHT_ANKLE | 129.6 ± 13.1 | 121.5 ± 14.2 | 128.0 ± 10.7 | 137.9 ± 8.8 |

**Walidacja biomechaniczna**:
- LEFT_KNEE jest **wyprostowane** (164°) w fazie L_STANCE → noga oporowa, znormalizowane wsparcie ✓
- LEFT_KNEE **zgięte** (133°) w R_STANCE → faza wahadła, ruch w przód ✓
- Symetrycznie dla RIGHT_KNEE (105° w L_STANCE = wahadło, 157° w R_STANCE = oparcie) ✓
- Biodra mniej zmienne — typowe dla biegu (mała amplituda ruchu względem korpusu)

**Pochylenie tułowia: 2.3° ± 1.1°** — niskie. Literatura: 5-10° dla typowego biegu. Możliwe wyjaśnienia:
- Adam biega "running tall" (wyprostowana sylwetka)
- Szum w komponencie z keypointów (MediaPipe z w monocular 2D jest niepewny)
- Konwencja MediaPipe: kąt liczony w płaszczyźnie obrazu (x, y bez z) — może niedoceniony

**Vertical oscillation**: 0.0300 raw, **0.140 per torso** (n_cycles=114). Typowe 6-10 cm; dla typowego tułowia ~50 cm to 0.12-0.20 — w zakresie.

**Foot strike pattern**:
- LEWA: forefoot strike (heel/mid/fore = 0/5/110 z 115 kontaktów = 95.7% forefoot, kąt −33° ± 19°)
- PRAWA: forefoot strike (2/27/87 z 116 = 75% forefoot, kąt −12° ± 9°)
- **Consistent**: oba forefoot (zgodny pattern)

**Uwaga**: kąty −33° (LEWA) wydają się ekstremalne (typowy forefoot to −10 do −20°). Możliwe przyczyny:
1. **Klatka kontaktu** w predykcji LSTM może być przesunięta vs rzeczywisty initial contact (LSTM ma okno 15 klatek, może wykrywać entry into stance kilka klatek po faktycznym kontakcie)
2. Konwencja kąta (`atan2(-dy, dx)`) — przy bardzo małym dx (stopa pionowa) kąt skacze do ekstremów
3. Lewy bok bliżej kamery (artefakt monocular 2D) → większa amplituda ruchu lewej stopy w pikselach → większy kąt

To **limitation**, do dyskusji w sekcji Limitations pracy.

### Symetria L/P (Symmetry Index = 200 × |L−R| / (L+R))

| Wskaźnik | L | R | Δ | SI [%] | Klasyfikacja |
|---|---|---|---|---|---|
| **GCT** | 203 ms | 245 ms | +42 ms | **18.7** | asymetria znacząca |
| **Cycle time** | 684 ms | 685 ms | +0.7 ms | **0.1** | symetria zdrowa |
| **Duty factor** | 0.296 | 0.357 | +0.061 | **18.7** | asymetria znacząca |
| Knee @ STANCE | 163.7° | 157.2° | −6.5° | 4.0 | symetria zdrowa |
| Ankle @ STANCE | 135.4° | 128.0° | −7.4° | 5.6 | asymetria łagodna |
| Foot strike | 95.7% fore | 75.0% fore | — | — | consistent (oba fore) |
| **OGÓLNIE** | — | — | — | max **18.7** / mean **9.4** | mieszane |

### Najciekawsza obserwacja: **GCT asymetryczne, cycle time symetryczne**

Adam ma:
- **Cycle time L ≈ R** (684 vs 685 ms — 0.1% asymetria, idealna)
- **GCT L < R** (203 vs 245 ms — 18.7% asymetria)

To znaczy: lewa noga ma **krótszy** stance i **dłuższy** flight (po lewym stance), prawa noga ma **dłuższy** stance i **krótszy** flight. Ale rytm cyklu jest **identyczny**.

**Interpretacja biomechaniczna**:
- Hipoteza A — **artefakt monocular 2D**: lewa strona biegacza bliżej kamery, MediaPipe widzi większą amplitudę ruchu lewej nogi (większy zakres pikseli), peak detection LSTM może wcześniej "wyjść" z LEFT_STANCE. Opisane w `.claude/rules/labeling.md` jako znany artefakt
- Hipoteza B — **rzeczywista asymetria** Adama: krótszy stance lewej nogi może wskazywać na asymetrię siły/koordynacji. Wymaga walidacji w 3D motion capture (poza scope MVP)
- Hipoteza C — **szum predict LSTM**: model wytrenowany na danych z aspect fix może niedokładnie określać granice STANCE/FLIGHT, błąd skumulowany asymetrycznie

**Auto_label peak-based** dla Adama (z train) dał GCT L=R=241 ms, cycle 685 ms — symetryczne. LSTM różni się głównie w GCT (+42 ms na R, −38 ms na L). To wzmacnia hipotezę C (predict LSTM jest mniej idealny niż reguła peak-based dla tego typu pomiaru).

### Podsumowanie testu MVP

| Kryterium | Status |
|---|---|
| Pipeline E2E działa (wideo → współczynniki) | ✅ |
| Wszystkie współczynniki w sensownych zakresach | ✅ (z drobnymi zastrzeżeniami) |
| Kadencja zgadza się z cycle time (sanity check) | ✅ (173 spm vs 175 z cycle) |
| Kąty stawów biomechanicznie poprawne | ✅ (knee L wyprostowane w L_STANCE) |
| Symetria pokazuje sensowne wartości | ✅ (z hipotezą o artefaktach 2D) |
| Foot strike kąty | 🟡 LEWA −33° wymaga inspekcji |
| Pochylenie tułowia | 🟡 niskie (2.3°) — running tall lub szum |

## Ograniczenia (do sekcji Limitations pracy)

1. **Stride length pominięte** w MVP — wymaga inputu użytkownika (prędkość bieżni). Implementacja warunkowa w iteracji po MVP
2. **Klatki brzegowe (pierwsze/ostatnie 7)** mają predykcje extend, nie rzeczywiste — confidence=0 oznacza niepewność. W produkcji UI powinno informować użytkownika
3. **Monocular 2D bias**: GCT L vs R asymetria może być artefaktem (lewa bliżej kamery), nie rzeczywistą asymetrią biegacza. Walidacja 3D wymagałaby motion capture
4. **Foot strike kąty ekstremalne** (LEWA −33°) — możliwe przesunięcie klatki kontaktu w predykcji LSTM. Do zbadania
5. **Pochylenie tułowia 2.3°** — niskie, możliwy szum keypointów lub specyficzna postawa Adama
6. **Adam jest w train**: ten test nie jest fair miarą jakości — pipeline może działać gorzej na unseen biegaczy. Powinien być sprawdzony też na 02/20/22 (test set)

## Co dalej

### Iteracja 1 (krótkoterminowa, ~1h)

1. **Test pipeline na 02, 20, 22** (test set) — porównanie sensowności współczynników na nieznanych modelowi biegaczach
2. **Naprawa bug postprocess_median.predict_lstm** (z poprzedniej sesji, low priority — tu też w grze)
3. **Dodać `analyze.py`** orchestration script: jeden CLI uruchomienie pipeline'u E2E (wideo → temporal + spatial + symmetry JSON-y + raport MD)

### Iteracja 2 (średnioterminowa, ~2-3h)

1. **Stride length** — input użytkownika (CLI flag `--treadmill-speed-ms`), formuła: `stride_length = speed × cycle_time`
2. **Generator raportu PDF/Markdown** per bieg — czytelne podsumowanie dla użytkownika końcowego (nie programisty)
3. **Walidacja kąta stopy** (foot strike) — porównanie z wizualną inspekcją wybranych klatek

### Iteracja 3 (Etap 7 — rekomendacje)

Reguły z literatury biomechanicznej (kodowane ręcznie, NIE uczone z danych):
- "kadencja < 160 spm + przedłużony GCT (>270 ms) → ryzyko overstriding, sugeruj zwiększenie kadencji o 5%"
- "duty factor > 0.40 → biegacz w fazie kontaktu zbyt długo, sugeruj lżejszy krok / zwiększenie tempa"
- "vertical oscillation > 0.20 per torso → nadmiar ruchu pionowego, marnowanie energii"
- "asymetria GCT > 5% → kandydat do ortopedy / fizjoterapeuty"
- "heel strike + przedłużony GCT → sugeruj transition do midfoot przez progresywne ćwiczenia"

Implementacja: `src/recommendations/rules.py` — funkcje czytają wynikowe JSON-y z Etapu 6, generują listę rekomendacji z source citation (np. autor/rok publikacji medycznej).

## Artefakty zachowane

- `src/coefficients/` — 4 moduły + `__init__.py`
- `data/inference/24-adam-phases.csv` — predykcje fazy + keypointy (16 MB, do downstream)
- `data/inference/24-adam-temporal.json` — temporal metrics
- `data/inference/24-adam-spatial.json` — spatial metrics
- `data/inference/24-adam-symmetry.json` — symmetry

## Materiał do pracy magisterskiej

**Rozdział 6** ma teraz pierwsze pełne wyniki:
- Architektura pipeline'u E2E
- Tabela współczynników z ich biomechanicznymi zakresami
- Walidacja sanity (kadencja vs cycle time)
- Sekcja **Limitations** silnie podparta obserwacjami:
  - Monocular 2D bias na GCT
  - Klatki brzegowe (boundary problem)
  - Foot strike kąty ekstremalne (do zbadania)
- Materiał do **Future Work**: stride length, raport PDF, walidacja 3D motion capture

Negatywne obserwacje (foot strike, torso lean) są tak samo wartościowe jak pozytywne — pokazują **uczciwą analizę** ograniczeń systemu.
