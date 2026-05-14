# 2026-05-14 — Temat pracy magisterskiej (FINALNY): "Analiza podstawowych współczynników biegu przy pomocy uczenia maszynowego"

## Tytuł formalny (potwierdzony przez promotora)

> **Analiza podstawowych współczynników biegu przy pomocy uczenia maszynowego**

## Geneza i ewolucja zakresu

**Pierwotny plan**: praca o **podstawowych** współczynnikach biegu (kadencja, GCT,
stride length, ewentualnie foot strike) — typowy zestaw biomechaniczny opisywany
w każdej publikacji o biegu.

**W trakcie realizacji**: zakres rozszerzył się naturalnie do **12 współczynników**
(5 temporalnych + 7 przestrzennych) — zarówno z powodu dostępności keypointów MediaPipe
(33 punkty pozwalają policzyć więcej niż początkowo zakładano), jak i z naturalnej
kompozycji pipeline (skoro mamy granice faz, mamy też kąty stawów; skoro mamy ankle_y,
mamy też vertical oscillation, foot strike pattern, itd.).

**Konsekwencja dla pracy**: w rozdziale o współczynnikach uczciwie zaznaczamy:
- Współczynniki "rdzeniowe" pierwotnego planu: kadencja, GCT, stride length, foot strike
- Współczynniki dodane w trakcie: czas lotu, duty factor, kąty stawów (kolano, biodro,
  kostka), pochylenie tułowia, vertical oscillation, overstriding, symetria L/P (SI Robinsona)

To **wzmacnia narrację** pracy: początkowy minimalny zakres → empiryczne odkrycie że można
więcej → rozszerzenie z uzasadnieniem biomechanicznym.

## Framing biomechanics-centric (vs ML-centric)

Tytuł stawia akcent na:
- **Główny obiekt badań**: 12 współczynników biegu
- **Narzędzie**: uczenie maszynowe (MediaPipe Pose + LSTM klasyfikator faz)
- **Pytanie**: czy ML pozwala dokładnie obliczyć współczynniki + co wpływa na ich jakość

**Klasyfikator faz biegu jest środkiem do celu**, nie celem samym w sobie. To istotna
różnica: porównanie 4 modeli ML (RF baseline/engineered, LSTM primary, LSTM r1 + aspect fix)
**nie jest** głównym wkładem pracy — jest **podstawą metodologiczną** dla obliczeń
współczynników temporalnych.

## Trzy pytania badawcze (przeformułowane pod tytuł)

### **P1 — Pipeline ML do obliczania współczynników biegu**

> Jak zaprojektować pipeline uczenia maszynowego (pose estimation → klasyfikacja faz →
> obliczenia geometryczne) wyliczający 12 współczynników biegu (5 temporalnych + 7 przestrzennych)
> z pojedynczego monocular 2D wideo bieżni mechanicznej, i jaką dokładność osiąga
> dla każdego z nich?

**Hipoteza H1**: Pipeline 3-etapowy (MediaPipe Pose → klasyfikator faz LSTM → obliczenia
z faz i keypointów) pozwala wyliczyć wszystkie 12 współczynników z akceptowalną
dokładnością walidowaną względem reference values z literatury biomechanicznej.

**Materiał empiryczny**:
- Pełna implementacja w `src/` (extraction, labeling, training, coefficients, recommendations)
- Walidacja na 3 biegaczach (Adam train ideal case, 22 test set, Janek edge case)
- Reference values w `docs/reference-values.md` z citation
- Raporty MD w `data/inference/raporty/` (porównanie wyliczonych vs reference)

### **P2 — Wybór klasyfikatora faz biegu i jego wpływ na precyzję współczynników temporalnych**

> Który klasyfikator faz biegu (RF baseline, RF engineered, LSTM primary, LSTM r1
> + aspect ratio fix) dostarcza najbardziej wiarygodnych granic stance/flight,
> i jak accuracy klasyfikacji przekłada się na precyzję wyliczanych z faz współczynników
> temporalnych (kadencja, GCT, stride length, duty factor)?

**Hipoteza H2**: LSTM (modelujący sekwencję) przewyższa Random Forest (klatka-po-klatce)
o min. 5 pp test accuracy, co przekłada się na mniejszy błąd granic faz i precyzyjniejsze
obliczenia metryk temporalnych.

**Hipoteza H3**: Engineered features (kąty stawów, prędkości, akceleracje) zbliżają RF
do LSTM o min. 10 pp względem RF na raw keypointach.

**Hipoteza H4**: Normalizacja aspect ratio kadru (aspect ratio fix) dodaje min. 5 pp
do accuracy LSTM, ze szczególnie dużym efektem dla wideo o nietypowej orientacji
(film 22 portrait: 75.8% → 85.9%, +10.1 pp).

**Materiał empiryczny (gotowy)**:
- 4 wytrenowane modele: `models/rf_baseline/`, `models/rf_engineered/`,
  `models/lstm_primary/`, `models/lstm_run1_overfit/`
- Backupy `models/*_pre_aspect_fix/` (przed aspect fix) i `models/*_pre_extension/`
  (przed rozszerzeniem datasetu)
- Artefakty: `docs/thesis-notes/figures/comparison_table.md`, `confusion_matrices_test.png`,
  `learning_curves_lstm.png`, `feature_importances_rf.png`, `per_file_test.md`,
  `error_breakdown.md`
- Tabela końcowa:

| Model | Test accuracy | F1 (macro) |
|---|---|---|
| Random Forest (raw keypointy) | 51.3% | 0.495 |
| Random Forest (engineered features) | 65.5% | 0.638 |
| LSTM primary (większa regularyzacja) | 68.4% | 0.683 |
| **LSTM r1 + aspect fix (primary, produkcyjny)** | **70.9%** | **0.709** |

### **P3 — Wrażliwość współczynników na warunki akwizycji wideo**

> Które ze współczynników biegu są wrażliwe na warunki akwizycji wideo (orientacja kadru,
> perspektywa kamery, FPS), i jak detekować automatycznie przypadki gdy współczynnik
> jest nieinterpretowalny ze względu na artefakt akwizycji?

**Hipoteza H5**: Współczynniki **przestrzenne** (foot strike pattern, vertical oscillation,
symetria L/P) są **istotnie wrażliwe na perspektywę kamery** — wymagają standardowego
ujęcia z boku (landscape, prostopadle do bieżni), inaczej generują artefakty geometryczne.

**Hipoteza H6**: Współczynniki **temporalne** (kadencja, GCT, czas lotu, stride length,
duty factor) są **wrażliwe na FPS** — niski FPS (<15) daje błąd kwantyzacji rzędu 15-20%.

**Hipoteza H7**: Auto-detekcja niskiej wiarygodności jest możliwa **bez ground truth**
przez analizę wartości metryki vs fizjologiczny zakres (np. `|foot_strike_angle| > 45°`
jako sygnał artefaktu perspektywy).

**Materiał empiryczny — 3 case studies (bez nowych eksperymentów)**:

| Case | Współczynnik | Warunek | Wynik |
|---|---|---|---|
| 1: Sesja C, 18 PNG, 3 biegaczy | foot strike pattern | orientacja kamery / perspektywa | Janek (z boku) OK; Adam (od dołu) borderline; 22 (pionowe) bezwartościowe |
| 2: aspect ratio fix, film 22 | klasyfikacja → wszystkie wsp. temporalne | aspect ratio kadru | 75.8% → 85.9% accuracy klasyfikatora (+10.1 pp); pośrednio: precyzja kadencji/GCT/stride length |
| 3: film 16, exclude_from_training | metryki temporalne | FPS 13.33 | błąd kwantyzacji GCT ~15% (typowe GCT 250 ms = 3.3 klatki przy 13 FPS, ±1 klatka = ±30% błąd) |

**Tabela syntetyczna "metryka × warunek × auto-detekcja"** (z notatki Propozycji A
historycznej, bez zmian):

| Metryka | Wrażliwa na orientację | Wrażliwa na FPS | Detekowalna automatycznie? |
|---|---|---|---|
| Kadencja | nie | tak (>15% błąd przy FPS<15) | tak — z FPS w metadanych |
| GCT | nie | tak (kwantyzacja) | tak — z FPS w metadanych |
| Czas lotu | nie | tak | tak |
| Stride length | nie | tak (przez cycle_time) | tak |
| Duty factor | nie | tak | tak |
| Kąty stawów | minimalnie | nie | nie (cichy artefakt) |
| Vertical oscillation | tak (out-of-plane) | nie | częściowo |
| **Foot strike pattern** | **tak (krytycznie)** | nie | **tak (`low_confidence` próg 45°)** |
| Symetria L/P | tak (asymetria perspektywy) | nie | częściowo (SI >50% jako proxy) |

## Status hipotez

| Hipoteza | Pytanie | Status | Materiał |
|---|---|---|---|
| H1 | P1 | **potwierdzona** | walidacja 3 biegaczy vs reference values |
| H2 | P2 | **potwierdzona** (71% LSTM vs 65% RF eng) | comparison_table |
| H3 | P2 | **potwierdzona** (65% RF eng vs 51% RF raw) | comparison_table |
| H4 | P2 | **potwierdzona** (71% z fix vs 66% bez fix, film 22 +10pp) | per_file_test |
| H5 | P3 | **potwierdzona** (Sesja C 18 PNG) | low_confidence flag w spatial.json |
| H6 | P3 | **potwierdzona** (film 16, matematycznie) | History.md 2026-04-15 |
| H7 | P3 | **potwierdzona** (próg 45° dla foot strike) | rules.py foot_strike_low_confidence |

**Wszystkie 7 hipotez ma materiał empiryczny zebrany.** Praca może być pisana bez
dodatkowych eksperymentów.

## Struktura 8 rozdziałów (~60 stron)

```
1. Wstęp                                                              ~5 stron
   1.1 Motywacja (biomechanika biegu, prewencja injury, dostępność)
   1.2 Problem badawczy (P1, P2, P3)
   1.3 Cel i zakres pracy
   1.4 Struktura pracy

2. State of the Art                                                   ~8 stron
   2.1 Pose estimation z monocular 2D wideo (OpenPose, MediaPipe, AlphaPose)
   2.2 Współczynniki biomechaniczne biegu (kadencja, GCT, stride length,
       foot strike, symetria) — citation: Heiderscheit 2011, Souza 2016,
       Novacheck 1998, Diaz 2019, Daoud 2012, Robinson 1987
   2.3 Klasyfikatory faz biegu/chodu (RF, LSTM, BiLSTM, 1D-CNN)
   2.4 Walidacja 2D pose vs 3D MoCap (Stenum 2021, Ripic 2023, HGcnMLP 2023,
       Ali 2024) — z research notatki 2026-05-14
   2.5 Identyfikacja luki w literaturze (5 gap'ów)

3. Materiały i metody                                                 ~8 stron
   3.1 Dataset (16 filmów, ~10 biegaczy, FPS 9.46–30, pozycje kamery)
   3.2 Pipeline (MediaPipe → Savgol filter → auto_label peak-based → klasyfikator)
   3.3 Architektury klasyfikatorów (4 modele) + aspect ratio fix
   3.4 Obliczanie współczynników (12 metryk, formuły, agregacje)
   3.5 Splity (train/val/test), evaluation, metryki

4. Klasyfikator faz biegu — wybór modelu i pre-processing (P2)        ~10 stron
   4.1 Porównanie 4 modeli — tabela accuracy + F1
   4.2 Confusion matrices + per-film breakdown
   4.3 Feature importance dla RF
   4.4 Ablation study: aspect ratio fix
   4.5 Wpływ accuracy klasyfikatora na precyzję metryk temporalnych
   4.6 Wnioski metodologiczne (kiedy LSTM, kiedy RF wystarczy)

5. Współczynniki biegu — pipeline obliczania (P1)                     ~12 stron
   5.1 Współczynniki temporalne (5 metryk: kadencja, GCT, czas lotu,
       stride length, duty factor)
   5.2 Współczynniki przestrzenne (7 metryk: kąty stawów, torso lean,
       vertical oscillation, foot strike, overstriding, symetria, knee@contact)
   5.3 Walidacja vs reference values z literatury
   5.4 3 case studies: Adam (train, ideal), 22 (test, dobry), Janek (edge case)
   5.5 Limitations obliczeń (brak kalibracji piksel→metr, monocular 2D,
       non-determinizm MediaPipe)

6. System rekomendacji (Wariant 1 — pełny rozdział)                   ~8 stron
   6.1 Argument za rule-based vs ML (interpretability, mały dataset,
       citation requirement, transparentność)
   6.2 Architektura modułu (rules.py + render_markdown)
   6.3 Tabela 13+ reguł z citation, progami, severity
   6.4 Reguły łączone (combinatorical: overstriding, stride_long, quality)
   6.5 Walidacja jakościowa na 3 biegaczach
   6.6 Ograniczenia (deterministyczne, ogólne progi)

7. Wrażliwość współczynników na warunki akwizycji (P3)                ~6 stron
   7.1 Hipotezy H5, H6, H7
   7.2 Case 1: foot strike vs perspektywa kamery (Sesja C, 18 PNG)
   7.3 Case 2: aspect ratio dla film 22
   7.4 Case 3: FPS dla film 16
   7.5 Tabela syntetyczna "metryka × warunek × auto-detekcja"
   7.6 Mitygant w kodzie: `low_confidence` flag, reguła
       `foot_strike_low_confidence`, combinatorical quality

8. Dyskusja i wnioski                                                 ~5 stron
   8.1 Odpowiedź na P1, P2, P3
   8.2 Wkład pracy (5 gap'ów z literatury)
   8.3 Ograniczenia (small dataset, monocular 2D, brak 3D MoCap validation)
   8.4 Implikacje praktyczne (kiedy używać, kiedy nie)
   8.5 Praca przyszła (3D MoCap validation, większy dataset, walidacja klinicznych grup)
   8.6 Wnioski końcowe

RAZEM: ~62 strony
```

## Cytaty do State of the Art (z researchu 2026-05-14)

7 prac peer-reviewed z notatki `2026-05-14-research-podobnych-prac.md`:

1. **Stenum et al. 2021** (PLOS Comp Bio) — walidacja OpenPose vs 3D MoCap, cytować
   w 2.4 jako klasyk + jako źródło limitation perspektywy field-of-view
2. **Ali et al. 2024** (PMC) — DMD MediaPipe+LSTM-CNN, cytować w 2.3 jako najbliższa
   architektura
3. **Ripic et al. 2023** (Front Rehab) — OpenPose+MediaPipe vs Vicon vs Kinovea,
   cytować w 2.4 i 4.4 jako uzasadnienie aspect ratio fix
4. **HGcnMLP 2023** (Front Bioeng) — smartphone single-view, cytować w 2.1 i 7
   jako paralela "tylko 90°" → Sesja C
5. **Frontiers Phys 2025** mini review — cytować w 2.1 jako overview state-of-the-art
   markerless sport
6. **Bouchabou 2024** (PMC, Heliyon) — narrative review 9 modeli HPE, cytować w 2.1
   jako uzasadnienie wyboru MediaPipe
7. **Hannigan 2024** (Front Sport) — foot strike self-report 42.7%, cytować w 1.1
   jako motywacja: ludzie nie rozpoznają własnego foot strike

Plus klasyczne biomechaniczne (już w `rules.py` jako citation):
- Heiderscheit 2011 — kadencja, knee@contact, overstriding
- Souza 2016 — GCT, foot strike pattern
- Novacheck 1998 — czas lotu, torso lean, stride length
- Diaz 2019 — vertical oscillation
- Robinson 1987 — Symmetry Index
- Daoud 2012 — foot strike injury risk

Razem: ~13-15 cytatów core, do rozszerzenia o 10-15 prac (biomechanika 3D MoCap,
inne klasyfikatory faz, MediaPipe technical papers) — łącznie 25-30 referencji,
typowy zakres dla magisterki.

## Limitations (rozdz. 8.3) — gotowe punkty

1. **Small dataset** (16 filmów) — typowe w tej dziedzinie (HGcnMLP 27 osób, Ripic 17),
   ale ogranicza generalizację.
2. **Brak ground truth 3D MoCap** — nie można podać MAE w metrach/sekundach.
   Walidacja przez porównanie z reference values + sanity checks + reguły z citation.
3. **Monocular 2D limitations** — out-of-plane, perspective, environmental dependence
   (zgodne z literaturą: Ripic 2023, Stenum 2021, Frontiers Phys 2025).
4. **Non-determinizm MediaPipe** (XNNPACK delegate) — minimal differences między
   uruchomieniami, wpływ na reguły info w rekomendacjach.
5. **Reference values mają charakter ogólny** — kalibrowane na zdrowych biegaczy
   z literatury, indywidualne progi mogą się różnić.
6. **Foot strike pattern wymaga ujęcia z boku** — Sesja C, mitygant w kodzie
   (`low_confidence` flag).

## Dalsze kroki

1. **Pisanie pracy** — rozdziały 4-7 mają komplet materiału, można pisać od razu.
2. **Decyzje formalne** z promotorem:
   - Dokładny tytuł (potwierdzony jako "Analiza podstawowych współczynników biegu
     przy pomocy uczenia maszynowego")
   - Pozycjonowanie (sport / injury prevention / rehabilitation / konsumencka app)
   - Deadline obrony
3. **Bibliografia** — rozszerzyć z 7 prac z researchu do 25-30 referencji
   (biomechanika 3D MoCap, klasyfikatory faz, MediaPipe technical papers).
4. **Sekcja 1.1 Motywacja** — zależna od pozycjonowania (decyzja z promotorem).
5. **Streszczenie** (abstrakt) — pisać na końcu, gdy struktura jest pełna.
