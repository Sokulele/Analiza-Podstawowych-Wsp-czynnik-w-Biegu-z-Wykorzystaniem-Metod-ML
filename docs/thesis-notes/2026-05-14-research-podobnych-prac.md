# 2026-05-14 — Research podobnych prac naukowych: jak formułują problem badawczy

## Kontekst

Po zakończeniu Sesji A+B+C (system funkcjonalnie kompletny) pojawiło się pytanie
strategiczne: **jaki problem badawczy rozwiązuje ta praca magisterska**? Inżynierka
pokazuje JAK zbudować system, magisterka musi odpowiedzieć na pytanie naukowe
(hipoteza → eksperyment → wniosek).

Cel tego researchu: zobaczyć jak podobne prace (2018-2025) formułują problem badawczy
w obszarze analizy biegu/chodu z monocular 2D wideo i pose estimation. Zidentyfikować
**typowe szablony sformułowań** i **gap w literaturze** który ta praca może wypełnić.

Research wykonany 2026-05-14 przez WebSearch + WebFetch (Google Scholar, PMC, Frontiers,
PLOS Comp Biology, ScienceDirect). 7 peer-reviewed prac z weryfikowalnymi linkami.

## Tabela syntetyczna — 7 prac z cytatami problemu badawczego

| # | Autorzy, rok, journal | Domena | Problem badawczy (cytat z abstraktu) |
|---|---|---|---|
| 1 | **Stenum et al. 2021**, PLOS Comp Bio | OpenPose vs 3D MoCap, walking | *"Recent advances in video-based pose estimation suggest potential for gait analysis using two-dimensional video collected from readily accessible devices."* |
| 2 | **Ali et al. 2024**, BioMed Inform Insights | DMD classification, MediaPipe+LSTM-CNN | *"Traditional manual analysis of motion data is labor-intensive and heavily reliant on the expertise and judgment of the therapist."* |
| 3 | **Frontiers Phys 2025 mini review** | markerless sport motion analysis | *"Traditional motion capture systems provide high accuracy but are expensive and complex for the public."* |
| 4 | **Hannigan 2024**, Front Sport Active Living | foot strike self-report accuracy | *"The ability to modify foot strike pattern depends on awareness of foot strike pattern before being able to attempt change the pattern."* |
| 5 | **Ripic 2023**, Front Rehab Sci | OpenPose+MediaPipe vs Vicon vs Kinovea | *"Pose estimation algorithms suffer from errors in motions perpendicular to the video's plane, as well as the fact that the dataset they were trained with, may not have been prepared by experts."* |
| 6 | **Bouchabou 2024 narrative review**, Heliyon | 9 modeli ML pose estimation | *"The accurate measurement and analysis of human movement are essential in fields ranging from rehabilitation and neuroscience to sports science and ergonomics."* |
| 7 | **HGcnMLP 2023**, Front Bioeng Biotech | smartphone single-view monocular | *"3D human pose estimation is mainly based on multi-view technology, while the more promising single-view technology has defects such as low accuracy and reliability."* |

## Szczegóły 7 prac

### [1] Stenum et al. 2021 — PLOS Computational Biology

**"Two-dimensional video-based analysis of human gait using pose estimation"**
DOI: 10.1371/journal.pcbi.1008935
Link: [journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1008935](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1008935)

- **Problem**: brak rygorystycznej walidacji video-based pose estimation vs 3D MoCap dla quantitative gait analysis (stride-by-stride).
- **Metoda**: OpenPose vs 3D MoCap, healthy adults, overground walking.
- **Wynik**: MAE 0.02 s (temporal), 0.049 m (step length), 4.0°/5.6°/7.4° (hip/knee/ankle).
- **Kluczowy limitation**: *"individual step lengths are estimated most accurately when the person is in the center of the field of view of the camera"* — **systematyczny błąd perspektywy** identyczny z Twoją Sesją C (limitation #9).

### [2] Ali et al. 2024 — PMC, BioMed Inform Insights

**"Human Pose Estimation for Clinical Analysis of Gait Pathologies"**
Link: [pmc.ncbi.nlm.nih.gov/articles/PMC11097739](https://pmc.ncbi.nlm.nih.gov/articles/PMC11097739/)

- **Problem**: manualna analiza gait jest expert-dependent i czasochłonna.
- **Metoda**: 2D/3D HPE (OpenPose, MeTRAbs, MediaPipe) → spatiotemporal i sagittal joint angles → SVM + LSTM-CNN binary classifier (DMD vs healthy). Dataset z YouTube + publiczne datasety.
- **Wynik**: SVM 96.2%, deep learning 97% accuracy.
- **Limitation**: *"does not specifically differentiate between DMD patients and patients with other gait impairments"*.

### [3] Frontiers in Physiology 2025 — mini review

**"Commercial vision sensors and AI-based pose estimation frameworks for markerless motion analysis in sports and exercises"**
Link: [frontiersin.org/journals/physiology/articles/10.3389/fphys.2025.1649330](https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2025.1649330/full)

- **Problem**: traditional MoCap drogi i niedostępny dla szerokiej publiczności.
- **Wynik review**: *"2D systems offer economic and straightforward solutions, but they still face limitations in capturing out-of-plane movements"*.
- **Kluczowy gap**: *"PE accuracy depends on video quality, frame rates, and environmental conditions"* — review **identyfikuje** że systematyczna analiza wpływu warunków akwizycji jest niedostatecznie zbadana, ale sama jej nie dostarcza.

### [4] Hannigan et al. 2024 — Front Sport Active Living

**"Accuracy of self-reported foot strike pattern detection among endurance runners"**
Link: [frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2024.1491486](https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2024.1491486/full)

- **Problem**: foot strike pattern wpływa na running-related injury; modyfikacja wymaga awareness.
- **Hipoteza explicite**: *"The overall foot strike detection accuracy would be low, particularly among rearfoot striking runners who wear shoes with high heel height"*.
- **Metoda**: 710 biegaczy, self-report vs 3D MoCap, treadmill, retrospective cross-sectional.
- **Wynik**: tylko **42.7%** trafność self-reportu.
- **Argument w pracy**: konieczność automatycznej detekcji — argument dla każdego systemu auto-detekcji foot strike (m.in. dla mojej pracy).

### [5] Ripic et al. 2023 — Front Rehab Sci

**"Gait analysis comparison between manual marking, 2D pose estimation algorithms, and 3D marker-based system"**
Link: [frontiersin.org/journals/rehabilitation-sciences/articles/10.3389/fresc.2023.1238134](https://www.frontiersin.org/journals/rehabilitation-sciences/articles/10.3389/fresc.2023.1238134/full)

- **Problem**: czy 2D pose estimation algorithms dorównują 3D marker-based dla gait analysis u elderly?
- **Metoda**: 17 elderly, Vicon (10 IR cameras) vs OpenPose v1.7 vs MediaPipe v0.9.0.1 vs Kinovea (manual).
- **Wynik**: OpenPose 2 min 9 s vs Kinovea 38 h (1000× szybciej); **MediaPipe *"worst output... not recommended for gait analysis"*** (stan na 2023).
- **Kluczowy limitation**: *"errors in motions perpendicular to the video's plane"*, *"ankle keypoint misplacement"*.

### [6] Bouchabou et al. 2024 — PMC, Heliyon (narrative review)

**"A comprehensive analysis of the machine learning pose estimation models used in human movement and posture analyses"**
Link: [pmc.ncbi.nlm.nih.gov/articles/PMC11566680](https://pmc.ncbi.nlm.nih.gov/articles/PMC11566680/)

- **Problem**: gdzie aktualnie stoją ML pose estimation models dla human movement?
- **Metoda**: review 9 modeli HPE (OpenPose, PoseNet, AlphaPose, DeepLabCut, HRNet, MediaPipe, BlazePose, EfficientPose, MoveNet).
- **Wynik**: *"potential for non-invasive, cost-effective assessments"* w clinical gait/posture, sports performance, workplace ergonomics.
- **Limitation**: *"challenges in accuracy, data quality, and integration"*; accuracy zależy od *"training of the ML model, source quality, or video occlusions"*.

### [7] HGcnMLP 2023 — Front Bioeng Biotech

**"Effective evaluation of HGcnMLP method for markerless 3D pose estimation of musculoskeletal diseases patients based on smartphone monocular video"**
Link: [frontiersin.org/journals/bioengineering-and-biotechnology/articles/10.3389/fbioe.2023.1335251](https://www.frontiersin.org/journals/bioengineering-and-biotechnology/articles/10.3389/fbioe.2023.1335251/full)

- **Problem**: *"3D human pose estimation is mainly based on multi-view technology, while the more promising single-view technology has defects such as low accuracy and reliability"*.
- **Metoda**: 27 osób (12 patients, 15 healthy), iPhone 14, gait + TUG test, validation vs VICON.
- **Wynik**: ICC 0.839–0.982, Pearson r 0.808–0.978; step period error 0.02 s; knee ROM error 0.3°.
- **Kluczowy limitation**: *"Only performed data collection at 90°"* — **jedna orientacja kamery**, brak walidacji innych perspektyw. To dokładnie Twoja Sesja C (foot strike przy pionowym wideo zawodzi).

## Wzorce sformułowania problemu badawczego

Z 7 prac wyłaniają się **4 typowe szablony**:

### Szablon A: "Lack of validation"
> *"Despite recent advances in X, no rigorous evaluation compares X to gold-standard Y for task Z."*

Stosują: Stenum 2021, Ripic 2023, HGcnMLP 2023.

### Szablon B: "Cost / accessibility gap"
> *"Y is expensive, immobile, and expert-dependent. Can X be a cost-effective alternative for population/task Z?"*

Stosują: Ali 2024, Frontiers Phys 2025, Stenum 2021.

### Szablon C: "Specific gap in conditions / methodology"
> *"Existing methods work under conditions A, but performance under conditions B/C/D has not been systematically investigated."*

Stosują: Frontiers Phys 2025 (FPS/quality/environment), HGcnMLP 2023 (only 90°), Stenum 2021 (field of view position).

### Szablon D: "Detection accuracy problem motivating automation"
> *"Manual / self-reported detection of X has accuracy of only ~Y%, motivating automated systems."*

Stosują: Hannigan 2024 (foot strike 42.7%), Ali 2024 (manual gait analysis).

## Gap w literaturze, który ta praca może wypełnić

Z analizy 7 prac wynika, że **w żadnej** z nich nie znajduje się jednocześnie:

1. **Running-specific, nie chód** — wszystkie 7 prac dotyczy **chodu** (gait), nie biegu.
   Bieg sportowy na bieżni mechanicznej ma inne fazy (FLIGHT istnieje, DOUBLE_SUPPORT
   minimalny), inne progi kadencji/GCT, inne reference values — to faktycznie odrębna nisza.
2. **Systematyczne porównanie 4 modeli ML** (RF baseline → RF engineered → LSTM →
   LSTM + pre-processing fix) na **małym datasecie** (~16 filmów). Większość prac proponuje
   **jeden** model; mała próba jest rzadko traktowana jako wartościowy przedmiot badań.
3. **Aspect ratio fix jako pre-processing** dla heterogenicznych orientacji wideo — Ripic 2023
   identyfikuje *"errors in motions perpendicular to the video's plane"*, ale **nikt nie
   raportuje** ablation study aspect ratio fix dla LSTM gait classifier.
4. **System rekomendacji rule-based z citation z literatury biomechanicznej** — Heiderscheit
   2011, Souza 2016, Novacheck 1998, Robinson 1987, Daoud 2012 są cytowane jako źródła
   reference values, ale **żaden papier ich nie operacjonalizuje** w postaci 13+ wykonywalnych
   reguł z severity, citation, i reguł łączonych.
5. **Auto-detekcja niskiej wiarygodności** na podstawie wartości metryk (combinatorical
   quality detection, low_confidence flag dla foot strike) — Stenum 2021 i Ripic 2023
   **identyfikują** problem perspektywy/orientation, **żaden nie flaguje automatycznie**
   przypadków gdy metryka jest nieinterpretowalna.

## Wnioski dla pracy magisterskiej

1. **Naukowa wartość ≠ nowy algorytm.** Wartością może być: walidacja, systematyczna
   analiza, ablation study, identyfikacja gap'u + jego mitygacja. Wszystkie 7 prac
   pasuje do tego schematu.
2. **Small dataset to nie wada — to specyfikacja.** Wiele prac (Hannigan 710 biegaczy,
   Ripic 17 elderly, HGcnMLP 27 osób) operuje na małych próbkach z dobrze opisaną
   metodologią. Dataset 16 filmów + 10 biegaczy jest **akceptowalny** jeśli się go
   uczciwie opisze (homogeniczność/heterogeniczność, ograniczenia generalizacji).
3. **Limitations są materiałem.** Stenum 2021 limitation o field-of-view position to
   dokładnie Twoje limitation #9. **Identyfikacja, walidacja i mitygacja takich
   limitations** to wartość naukowa równa proponowaniu nowej metody.
4. **Citation pattern.** Praca powinna mieć State of the Art opartą na min. 30 cytatach
   — 7 prac z tego researchu to dobry punkt startowy dla rozdziału 2 (background).
5. **Nisza biegu vs chodu** to atut, nie wada — gait analysis (chód) jest "przeznaczone"
   dla klinicznej diagnostyki, running analysis dla sportu i prewencji injury. Inne progi,
   inne reference values, inne potrzeby użytkownika.
