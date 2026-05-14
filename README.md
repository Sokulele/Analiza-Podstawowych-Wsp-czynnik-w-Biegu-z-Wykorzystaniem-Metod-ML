# Running Analysis — biomechaniczna analiza biegu z wideo

System analizujący wideo biegu na bieżni i obliczający współczynniki biomechaniczne
z rekomendacjami poprawy formy. Praca magisterska.

**Pipeline**: wideo → MediaPipe Pose (33 keypointy) → klasyfikator faz biegu (LSTM) →
współczynniki temporalne i przestrzenne → rekomendacje z literatury biomechanicznej.

## Status projektu

Etapy 1–7 ukończone:

- **Etap 1–4**: środowisko, ekstrakcja keypointów, auto-etykietowanie, budowa datasetu
  (16 filmów, ~9–10 unikalnych biegaczy)
- **Etap 5**: klasyfikator faz biegu — **LSTM r1 + aspect fix, 70.9% test accuracy**,
  F1 0.709 (primary model)
- **Etap 6**: obliczanie współczynników — 5 współczynników temporalnych + 7 przestrzennych
- **Etap 7**: silnik rekomendacji — 13+ reguł z literatury biomechanicznej

Pełny pipeline E2E uruchamia się z jednego CLI (`src/coefficients/analyze.py`).

## Co system wylicza

### Współczynniki temporalne (z sekwencji faz + FPS)

| Współczynnik | Jednostka | Wymagane wejście |
|---|---|---|
| Kadencja | kroki/min | FPS |
| Czas kontaktu (GCT) — L i P | ms | FPS |
| Czas lotu | ms | FPS |
| Czas cyklu | ms | FPS |
| Duty factor | 0–1 | FPS |
| **Stride length** | m | FPS + prędkość bieżni |

### Współczynniki przestrzenne (z geometrii keypointów)

- Kąty stawów per faza (kolano, biodro, kostka — L i P)
- Pochylenie tułowia
- Vertical oscillation (raw + znormalizowane długością tułowia)
- Overstriding (dystans X między kostką a biodrem w klatce kontaktu)
- Foot strike pattern (heel / midfoot / forefoot, z flagą `low_confidence`
  gdy `|kąt| > 45°` — wskaźnik artefaktu perspektywy kamery)
- Kąt kolana w momencie kontaktu

### Symetria L/P

Symmetry Index (Robinson 1987) dla GCT, kadencji per noga, kątów stawów, foot strike.

### Rekomendacje (13+ reguł z citation)

Każda reguła ma severity (critical / warning / watch / info), uzasadnienie i citation
z literatury (Heiderscheit 2011, Novacheck 1998, Souza 2016, Diaz 2019, Robinson 1987,
Daoud 2012). Reguły łączone (`overstriding_combo`, `overstride_long_stride_combo`,
`quality_combo_high_si_low_conf`) wzmacniają sygnał gdy kilka metryk wskazuje
ten sam problem.

## Szybki start

### Instalacja

```bash
python -m venv .venv
.venv/Scripts/activate          # Windows
# albo: source .venv/bin/activate    (Linux/macOS)

pip install -r requirements.txt
# torch: instaluj z indexu CPU jeśli nie masz GPU:
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

Kluczowe zależności: `mediapipe==0.10.14` (legacy `mp.solutions.pose` API),
`opencv-python`, `pandas`, `numpy`, `scipy`, `scikit-learn`, `torch`, `matplotlib`.

### Pełna analiza wideo (E2E)

```bash
.venv/Scripts/python.exe src/coefficients/analyze.py \
    --video "data/videos/22 - Running Analysis with Physiotherapist.mp4" \
    --treadmill-speed-ms 3.0
```

Generuje 8 artefaktów w `data/inference/`:

- `{slug}-phases.csv` — keypointy z predykcją fazy per klatka
- `{slug}-temporal.json` — współczynniki temporalne
- `{slug}-spatial.json` — współczynniki przestrzenne (z flagą `low_confidence` foot strike)
- `{slug}-symmetry.json` — Symmetry Index L/P
- `{slug}-meta.json` — metadane (FPS, model, avg_confidence, treadmill_speed_ms)
- `raporty/{slug}.md` — raport MD z porównaniem do reference values
- `{slug}-recommendations.json` — lista rekomendacji
- `raporty/{slug}-rekomendacje.md` — sekcja MD z rekomendacjami

### Re-run na istniejących phases.csv (bez MediaPipe)

```bash
.venv/Scripts/python.exe src/coefficients/analyze.py \
    --video "data/videos/22 - Running Analysis with Physiotherapist.mp4" \
    --skip-inference
```

Pomija inferencję MediaPipe + LSTM (najdroższy krok, ~3 min na film). Wymaga
istniejącego `{slug}-phases.csv`. Przyśpiesza iterację reguł rekomendacji.

### Pojedyncze etapy pipeline'u

```bash
# Ekstrakcja keypointów (cała folder data/videos/ lub jeden film)
.venv/Scripts/python.exe src/extraction/extract_keypoints.py --videos-dir data/videos

# Auto-etykietowanie faz (peak-based, scipy.signal.find_peaks)
.venv/Scripts/python.exe src/labeling/auto_label.py --keypoints-csv data/keypoints/02.csv

# Trening LSTM (z aspect ratio fix)
.venv/Scripts/python.exe src/training/train_lstm.py \
    --output-dir models/lstm_run1_overfit --aspect-fix --epochs 200

# Inferencja samego klasyfikatora (bez współczynników)
.venv/Scripts/python.exe src/coefficients/run_inference.py \
    --video "data/videos/22 - Running Analysis with Physiotherapist.mp4" \
    --model-dir models/lstm_run1_overfit

# Standalone CLI rekomendacji (z gotowych JSON-ów)
.venv/Scripts/python.exe src/recommendations/recommend.py --slug 22-running-analysis-with-physiotherapist

# Wizualizacja faz biegu (PNG ze szkieletem MediaPipe + kolor wg fazy)
.venv/Scripts/python.exe src/visualization/render_frames.py \
    --video "data/videos/02 - Running at 13km h - side view.mp4" \
    --keypoints data/keypoints/02.csv

# Walidacja foot strike (PNG entry-into-STANCE z obliczonym kątem)
.venv/Scripts/python.exe src/visualization/render_foot_strike_entries.py \
    --video "data/videos/25 - janek__segment_1.mov" \
    --phases-csv data/inference/25-janek__segment_1-phases.csv \
    --output-dir data/visualizations/foot_strike_validation/25-janek
```

## Struktura katalogów

```
running-analysis/
├── CLAUDE.md                    — zasady projektu (czyta agent Claude Code)
├── History.md                   — log chronologiczny sesji prac
├── requirements.txt
├── data/
│   ├── videos/                  — surowe filmiki (.mp4/.mov)
│   ├── keypoints/               — CSV z keypointami + fazami po auto-etykietowaniu
│   ├── inference/               — wyniki pipeline'u E2E per biegacz
│   │   └── raporty/             — raporty MD (per biegacz) + rekomendacje MD
│   ├── visualizations/          — PNG ze szkieletem (faza biegu / foot strike)
│   ├── splits.json              — train/val/test split datasetu (NIE modyfikować)
│   ├── videos_metadata.csv      — FPS, długość, exclude_from_training
│   └── test_edge_cases/         — filmy odrzucone z trainu (np. 13 FPS)
├── src/
│   ├── extraction/              — MediaPipe Pose + Savitzky-Golay
│   ├── labeling/                — auto-etykietowanie faz (peak-based)
│   ├── training/                — RF baseline / RF engineered / LSTM
│   ├── coefficients/            — temporal_metrics, spatial_metrics, symmetry,
│   │                             analyze (orchestrator E2E), report_generator
│   ├── recommendations/         — rules.py (silnik + render_markdown),
│   │                             recommend.py (CLI)
│   └── visualization/           — render_frames (fazy), render_foot_strike_entries
│                                  (walidacja foot strike)
├── models/
│   ├── lstm_run1_overfit/       — PRIMARY MODEL (70.9% test acc)
│   ├── lstm_primary/            — wariant z większą regularyzacją
│   ├── rf_baseline/, rf_engineered/ — modele porównawcze (RF)
│   └── *_pre_aspect_fix/, *_pre_extension/ — backupy do rozdziału 5 pracy
└── docs/
    ├── plan.md                  — plan etapów projektu
    ├── przewodnik-projekt.md    — przewodnik metodologiczny
    ├── reference-values.md      — wartości referencyjne z literatury
    ├── mediapipe-keypoints.md   — definicje 33 keypointów
    ├── next-session-brief.md    — briefing dla następnej sesji pracy
    └── thesis-notes/            — notatki do pracy magisterskiej
```

## Klasyfikator faz biegu

### Klasy

- `LEFT_STANCE` — lewa stopa na ziemi
- `RIGHT_STANCE` — prawa stopa na ziemi
- `FLIGHT` — obie stopy w powietrzu
- `DOUBLE_SUPPORT` — obie na ziemi (rzadkie przy biegu, w datasecie ~0%)

### Modele porównane (Etap 5)

| Model | Test accuracy | F1 (macro) | Komentarz |
|---|---|---|---|
| Random Forest (baseline, raw keypointy) | 51.3% | 0.495 | sprawdzenie czy zadanie jest "trywialne" |
| Random Forest (engineered features) | 65.5% | 0.638 | feature engineering: kąty, prędkości, akceleracje |
| LSTM primary (większa regularyzacja) | 68.4% | 0.683 | dwuwarstwowy BiLSTM hidden=128, dropout=0.3 |
| **LSTM r1 + aspect fix (overfit, primary)** | **70.9%** | **0.709** | mniejsza regularyzacja + normalizacja aspect ratio na FPS-niezależną |

Aspect fix to korekta wagi visibilty + normalizacja x przez aspect ratio kadru —
istotne dla filmu 22 (pionowe wideo) i pozwala modelowi działać niezależnie od proporcji.

### Klasyfikator vs współczynniki — uwaga metodologiczna

**Trenowanie modelu** i **obliczanie współczynników** to dwa osobne etapy:

- **Trenowanie**: model uczy się rozpoznawać pozycję ciała (faza biegu), nie czas.
  FPS, slow-motion, prędkość bieżni — **nie mają znaczenia**. Filmy slow-motion
  są pełnoprawnym materiałem treningowym.
- **Inferencja** (na nowym wideo użytkownika): FPS jest krytyczny dla precyzji obliczeń
  czasowych, prędkość bieżni potrzebna do stride length.

## Dataset

| Metryka | Wartość |
|---|---|
| Filmów w trainie/val/test | 16 (z 1 wykluczonym jako edge case: 13 FPS) |
| Łącznie klatek z fazami | ~8000+ |
| Unikalnych biegaczy | ~9–10 |
| LEFT_STANCE / RIGHT_STANCE / FLIGHT | ~34% / 32% / 34% (zbalansowane) |

Filmy z różnym FPS (9.46, 11.25, 13.33, 15, 23.98, 29.97, 30) i tempem (jogging,
sprint, slow-motion 5–10×). Edge cases (chód → bieg, exoskeleton, marathon pace)
zachowane w teście dla testu robustness.

## Znane ograniczenia

1. **MediaPipe nie jest deterministyczny** (XNNPACK delegate, multi-threading) —
   ponowna inferencja na tym samym filmie produkuje minimalnie inne metryki spatial.
   Wpływ widoczny np. w liczbie reguł `info` (różnica 2/8 reguł między uruchomieniami).
2. **Klasyfikator nie wykrywa DOUBLE_SUPPORT** — w datasecie ta klasa ma <1% klatek,
   model jej nie uczy. Bieg na bieżni rzadko wymaga tej klasy.
3. **Foot strike pattern** jest wiarygodny **wyłącznie przy standardowym ujęciu
   z boku** (landscape, kamera prostopadle do toru biegu). Przy pionowym lub ukośnym
   ujęciu kąt jest artefaktem perspektywy — system ostrzega regułą `foot_strike_low_confidence`.
4. **Stride length** wymaga znanej prędkości bieżni (input użytkownika) — nie da
   się jej wyliczyć z samego wideo monocular.
5. **Kalibracja piksel → metr** — bez znanego wzrostu biegacza vertical oscillation
   raportowany w jednostkach znormalizowanych (długość tułowia), nie cm.
6. **Reference values mają charakter ogólny** — kalibrowane na biegaczy zdrowych
   z literatury. Indywidualne progi mogą się różnić (rehabilitacja, sport wyczynowy).
7. **3D motion capture** to złoty standard biomechaniki — monocular 2D z MediaPipe
   produkuje asymetrię L/P jako artefakt kąta kamery (noga bliżej kamery ma większą
   amplitudę pikselową).

Pełna sekcja "Limitations" w notatkach pracy magisterskiej:
`docs/thesis-notes/2026-05-09-iteracja1-test-set.md`.

## Dokumentacja i notatki

- `docs/plan.md` — plan etapów projektu
- `docs/przewodnik-projekt.md` — przewodnik metodologiczny
- `docs/reference-values.md` — wartości referencyjne z literatury (kalibracja progów reguł)
- `docs/mediapipe-keypoints.md` — definicje 33 keypointów MediaPipe Pose
- `docs/thesis-notes/` — notatki źródłowe do pracy magisterskiej (decyzje,
  eksperymenty, wyniki, ograniczenia). Index w `docs/thesis-notes/README.md`.
- `History.md` — log chronologiczny sesji prac z opisem wprowadzanych zmian
- `CLAUDE.md` — zasady projektu (komentarze po polsku, nazwy po angielsku,
  rozdzielenie trenowania od inferencji, auto-zapis notatek thesis)

## Licencja

Projekt jest pracą magisterską. Kontakt: slawomir.sokolowski@pfro.pl.
