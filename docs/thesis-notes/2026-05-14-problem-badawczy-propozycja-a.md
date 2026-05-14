# 2026-05-14 — Problem badawczy pracy magisterskiej (Propozycja A — wybrana, **historyczna**)

> **Po dalszej pracy (2026-05-14, ta sama sesja)**: po dyskusji z użytkownikiem
> okazało się, że formalny tytuł pracy uzgodniony z promotorem to:
> *"Analiza podstawowych współczynników biegu przy pomocy uczenia maszynowego"* —
> **biomechanics-centric**, nie ML-centric. Główny obiekt badań to **współczynniki biegu**,
> a uczenie maszynowe jest **narzędziem**. Aktualną wytyczną do pisania pracy jest
> **`2026-05-14-temat-pracy-finalny.md`**. Niniejsza notatka pozostaje jako **historyczna**
> — zachowuje 3 pytania badawcze i 6 hipotez, które finalna notatka **przeformułowuje**
> w nowym framingu (akcent na współczynniki, klasyfikator jako narzędzie).

## Tytuł roboczy

> **Klasyfikacja faz biegu z monocular 2D wideo: porównanie podejść uczenia maszynowego
> i analiza wrażliwości metryk biomechanicznych na warunki akwizycji**

(*alt*: "System analizy biomechanicznej biegu z wideo monocular 2D — porównanie
klasyfikatorów ML i wrażliwość metryk na warunki akwizycji")

## Geneza wyboru

Wybór po analizie 7 podobnych prac (notatka `2026-05-14-research-podobnych-prac.md`).
Propozycja A łączy 3 wzorce sformułowań z literatury (szablony A "lack of validation",
C "gap in conditions/methodology", B "cost/accessibility gap") i wypełnia **5 gap'ów
w literaturze** zidentyfikowanych w researchu:

1. Running-specific (vs chód kliniczny)
2. Systematyczne porównanie 4 klasyfikatorów na małym datasecie
3. Aspect ratio fix jako pre-processing
4. System rekomendacji rule-based z citation
5. Auto-detekcja niskiej wiarygodności predykcji

## Trzy pytania badawcze

### **P1 — Porównanie klasyfikatorów**

> Czy LSTM przewyższa klasyczne uczenie maszynowe (Random Forest) w klasyfikacji
> czterech faz biegu (LEFT_STANCE, RIGHT_STANCE, FLIGHT, DOUBLE_SUPPORT) z keypointów
> MediaPipe Pose na małym heterogenicznym datasecie (~16 filmów, ~10 biegaczy)?
> Jaki feature engineering zbliża Random Forest do wyników LSTM?

**Hipoteza H1**: LSTM (z modelowaniem temporalnym) istotnie przewyższa RF (klatka-po-klatce)
o min. 5 pp test accuracy.

**Hipoteza H2**: Engineered features (kąty stawów, prędkości, akceleracje) zbliżają
RF do LSTM o min. 10 pp względem RF na raw keypoints.

**Materiał empiryczny (gotowy)**:
- 4 wytrenowane modele: `models/rf_baseline/`, `models/rf_engineered/`,
  `models/lstm_primary/`, `models/lstm_run1_overfit/`
- Backupy `models/*_pre_extension/` (przed rozszerzeniem datasetu) — pozwalają omówić
  efekt rozmiaru próbki.
- Artefakty: `docs/thesis-notes/figures/comparison_table.md`, `comparison_summary.json`,
  `confusion_matrices_test.png`, `learning_curves_lstm.png`,
  `feature_importances_rf.png`, `per_file_test.md`, `error_breakdown.md`.
- Tabela wyników (z briefu Sesji C):

| Model | Test accuracy | F1 (macro) |
|---|---|---|
| Random Forest (raw keypointy) | 51.3% | 0.495 |
| Random Forest (engineered features) | 65.5% | 0.638 |
| LSTM primary (większa regularyzacja) | 68.4% | 0.683 |
| **LSTM r1 + aspect fix (primary)** | **70.9%** | **0.709** |

**Oczekiwany wkład do literatury**: systematyczne porównanie 4 podejść ML na biegu
sportowym (nie chodzie) — pierwsza taka publikacja w literaturze, którą udało się
znaleźć w researchu 2026-05-14.

---

### **P2 — Aspect ratio fix jako pre-processing**

> Czy normalizacja keypointów względem aspect ratio kadru wideo poprawia generalizację
> klasyfikatora LSTM między filmami o różnej orientacji (landscape vs portrait, różne
> proporcje)?

**Hipoteza H3**: Aspect ratio fix daje istotny wzrost accuracy o ~5 pp dla LSTM,
ze szczególnie dużym efektem dla wideo pionowego (film 22, portrait).

**Materiał empiryczny (gotowy)**:
- Backup `models/lstm_run1_overfit_pre_aspect_fix/` — model przed fix.
- Aktualny `models/lstm_run1_overfit/` — model po fix.
- Per-film accuracy breakdown (`per_file_test.md`) — pokazuje że film 22 (pionowy)
  miał 75.8% przed fix, 85.9% po fix (+10.1 pp na konkretnym edge case).
- Ablation study **już zrobione** — wystarczy je formalnie spisać w pracy.

**Argument w literaturze**: Ripic et al. 2023 (Front Rehab Sci) identyfikują problem
*"errors in motions perpendicular to the video's plane"*, ale **nikt nie publikuje
ablation aspect ratio fix dla gait/running pose classifier**. To jest konkretna luka.

**Oczekiwany wkład**: zaproponowanie pre-processingu wraz z walidacją na heterogenicznym
datasecie (filmy landscape + portrait + slow-motion + różne FPS).

---

### **P3 — Wrażliwość metryk biomechanicznych na warunki akwizycji**

> Które z 12 wyliczanych metryk biomechanicznych (kadencja, GCT, czas lotu, stride length,
> duty factor, kąty stawów, vertical oscillation, foot strike pattern, symetria L/P)
> są wrażliwe na warunki akwizycji wideo (orientacja kadru, perspektywa kamery, FPS),
> i jak detekować ten artefakt automatycznie?

**Hipoteza H4**: Niektóre metryki (foot strike pattern, vertical oscillation) są
**istotnie wrażliwe** na perspektywę kamery — wymagają standardowego ujęcia z boku,
inaczej generują artefakty geometryczne.

**Hipoteza H5**: Inne metryki (kadencja, GCT) są **wrażliwe na FPS** — niski FPS
(<15) daje błąd kwantyzacji rzędu 15-20%.

**Hipoteza H6**: Auto-detekcja niskiej wiarygodności jest możliwa **bez ground truth**
przez analizę wartości metryki vs fizjologiczny zakres (np. `|foot_strike_angle| > 45°`
jako sygnał artefaktu perspektywy).

**Materiał empiryczny — 3 case studies (gotowy, bez nowych eksperymentów)**:

#### Case 1 — Foot strike pattern wrażliwy na perspektywę kamery (Sesja C, 2026-05-14)

18 PNG entry-into-STANCE × 3 biegaczy zwalidowane wizualnie:

| Biegacz | Ujęcie | Mean L / R | Wzorzec wizualnie | Werdykt |
|---|---|---|---|---|
| Janek | landscape, prostopadle do bieżni | −4° / −3° | midfoot | **predykcja zgadza się** ✓ |
| Adam | landscape, kamera lekko od dołu | −33° / −12° | forefoot (prawa), perspective artifact (lewa) | predykcja częściowo prawdziwa, asymetria z perspektywy |
| 22 | **portrait (pionowe)** | −97° / −99° | nieinterpretowalne (|kąt|>90°) | **predykcja bezwartościowa** ✗ |

Mitygant w kodzie: `compute_foot_strike_pattern` → flaga `low_confidence: True` gdy
`|mean| > 45°`. Reguła `foot_strike_low_confidence` (warning) w `rules.py` ostrzega
użytkownika.

#### Case 2 — Aspect ratio fix dla klasyfikatora LSTM (film 22)

Per-film accuracy LSTM **przed** i **po** aspect ratio fix:
- Film 22 (portrait, 320 klatek): 75.8% → **85.9%** (+10.1 pp)
- Inne filmy (landscape): zmiana w granicach ±2 pp

Wniosek: aspect ratio normalization jest **kluczowa dla wideo o nietypowej orientacji**,
ale jest również **kosztem zaniedbywalnym** dla wideo standardowych — pre-processing
"safe to enable always".

#### Case 3 — FPS jako warunek precyzji metryk temporalnych (film 16)

Film 16 (Treadmill Running, 13.33 FPS) został **wykluczony z trainingu**
(`exclude_from_training=True` w `data/videos_metadata.csv`) i przeniesiony do
`data/test_edge_cases/`.

Uzasadnienie z History.md (2026-04-15):

> *"Film 16 — 13 FPS daje błąd kwantyzacji ~15% na czasie kontaktu; kandydat do
> test-set lub odrzucenia"*

Matematyka: GCT typowy ~250 ms = 8 klatek przy 30 FPS, 3.3 klatki przy 13.33 FPS.
Błąd ±1 klatka = ±30% przy 13.33 FPS vs ±12.5% przy 30 FPS. Stride length proporcjonalnie
do GCT.

Wniosek: **niski FPS dyskwalifikuje wideo do precyzyjnych metryk temporalnych**, choć
NIE dyskwalifikuje go do trenowania klasyfikatora (model uczy się pozycji, nie czasu).

#### Synteza P3

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
| Symetria L/P | tak (asymetria perspektywy) | nie | częściowo (Symmetry Index >50% jako proxy) |

**Oczekiwany wkład**: tabela "metryka × warunek × wpływ" + reguły auto-detekcji.
To wypełnia gap zidentyfikowany przez Frontiers Phys 2025 review
(*"PE accuracy depends on video quality, frame rates, and environmental conditions"*).

---

## Struktura rozdziałów pracy (propozycja)

```
1. Wstęp
   1.1 Motywacja (biomechanika biegu, prewencja injury)
   1.2 Problem badawczy (P1, P2, P3)
   1.3 Cel i zakres pracy
   1.4 Struktura pracy

2. State of the Art
   2.1 Pose estimation z monocular 2D wideo (OpenPose, MediaPipe, AlphaPose)
   2.2 Analiza biomechaniczna biegu (cytaty: Heiderscheit, Souza, Novacheck, Diaz)
   2.3 Klasyfikatory faz biegu/chodu (przegląd metod)
   2.4 Walidacja 2D pose vs 3D MoCap (Stenum 2021, Ripic 2023, HGcnMLP 2023)
   2.5 Identyfikacja luki w literaturze (5 gap'ów z researchu 2026-05-14)

3. Materiały i metody
   3.1 Dataset (16 filmów, ~10 biegaczy, FPS heterogeniczne 9.46–30)
   3.2 Pipeline (MediaPipe → Savgol → auto_label → klasyfikator)
   3.3 Architektury klasyfikatorów (RF baseline, RF engineered, LSTM primary, LSTM r1 + aspect fix)
   3.4 Obliczanie współczynników biomechanicznych
   3.5 Silnik reguł rekomendacji
   3.6 Splity, evaluation, metryki

4. Eksperyment 1 — porównanie klasyfikatorów (P1)
   4.1 Konfiguracja
   4.2 Wyniki (tabela 4 modeli, per-film accuracy, confusion matrices)
   4.3 Analiza błędów (L↔R vs FLIGHT↔STANCE confusion)
   4.4 Feature importance dla RF
   4.5 Dyskusja H1 i H2

5. Eksperyment 2 — aspect ratio fix (P2)
   5.1 Motywacja (problem normalizacji keypointów dla różnych orientacji)
   5.2 Definicja aspect ratio fix
   5.3 Ablation study (przed/po fix, per-film breakdown)
   5.4 Wynik dla film 22 (portrait) jako case study
   5.5 Dyskusja H3

6. Współczynniki biomechaniczne — pipeline obliczania
   6.1 Współczynniki temporalne (5 metryk)
   6.2 Współczynniki przestrzenne (7 metryk)
   6.3 Symetria L/P (Symmetry Index Robinson)
   6.4 Walidacja przez sanity check vs literatura

7. System rekomendacji — reguły deterministyczne z citation
   7.1 Argument za rule-based vs ML (interpretability, mały dataset, citation requirement)
   7.2 Architektura (rules.py + render_markdown)
   7.3 13+ reguł z citation (tabela)
   7.4 Reguły łączone (combinatorical: overstriding, stride, quality)
   7.5 Walidacja na 3 biegaczach (Adam, 22, Janek)

8. Eksperyment 3 — wrażliwość metryk na warunki akwizycji (P3)
   8.1 Hipotezy H4, H5, H6
   8.2 Case 1 — foot strike vs perspektywa kamery (Sesja C, 18 PNG)
   8.3 Case 2 — aspect ratio dla film 22
   8.4 Case 3 — FPS dla film 16
   8.5 Tabela syntetyczna "metryka × warunek × auto-detekcja"
   8.6 Dyskusja H4, H5, H6

9. Dyskusja
   9.1 Wkład pracy (5 gap'ów z literatury)
   9.2 Ograniczenia (small dataset, monocular 2D, non-determinizm MediaPipe)
   9.3 Implikacje dla praktyki (kiedy używać tej metody, kiedy nie)
   9.4 Praca przyszła (3D motion capture validation, większy dataset, walidacja klinicznych grup)

10. Wnioski
   Krótkie podsumowanie odpowiedzi na P1, P2, P3.
```

## Lista hipotez (do uzupełnienia w trakcie pisania)

| Hipoteza | Pytanie | Status | Materiał |
|---|---|---|---|
| H1: LSTM > RF o min. 5 pp | P1 | **potwierdzona** (71% vs 65%) | comparison_table.md |
| H2: engineered ≥ raw RF + 10 pp | P1 | **potwierdzona** (65% vs 51%) | comparison_table.md |
| H3: aspect fix +5 pp | P2 | **potwierdzona** (71% vs 66%) | per_file_test.md, pre_aspect_fix backups |
| H4: foot strike wrażliwy na perspektywę | P3 | **potwierdzona** (Sesja C) | 18 PNG, low_confidence flag |
| H5: FPS<15 daje błąd kwantyzacji >15% | P3 | **potwierdzona** (film 16, matematycznie) | History.md 2026-04-15 |
| H6: auto-detekcja low_confidence bez ground truth | P3 | **potwierdzona** (próg 45° dla foot strike) | rules.py foot_strike_low_confidence |

**Wszystkie 6 hipotez ma materiał empiryczny już zebrany.** Praca może być pisana
bez dodatkowych eksperymentów.

## Co dopisać do State of the Art (na bazie researchu z 2026-05-14)

7 prac do cytowania jako baseline literatury:

1. **Stenum et al. 2021** — klasyk walidacji OpenPose vs 3D MoCap (cytować w 2.4 i jako
   źródło limitation #9 reformułowanego w Sesji C: "step length sensitive to field of view").
2. **Ripic et al. 2023** — bezpośrednie porównanie OpenPose+MediaPipe vs Vicon vs Kinovea
   (cytować jako uzasadnienie wyboru aspect ratio fix; cytat: *"errors in motions
   perpendicular to the video's plane"*).
3. **Ali et al. 2024** (DMD MediaPipe+LSTM-CNN) — najbliższa metodologicznie do tej pracy
   (cytować w 2.3 i 4 jako "podobna architektura LSTM-CNN dla gait classification, ale
   na innym task'u").
4. **HGcnMLP 2023** (smartphone single-view) — uzasadnienie monocular 2D + cytat
   o jednej orientacji kamery (90°) jako limitation tej rodziny prac.
5. **Frontiers Phys 2025 mini review** — ogólny obraz state-of-the-art markerless
   motion analysis w sporcie (cytować w 2.1).
6. **Bouchabou 2024 narrative review** — przegląd 9 modeli HPE (cytować w 2.1 jako
   uzasadnienie wyboru MediaPipe Pose vs alternatives).
7. **Hannigan 2024 foot strike self-report** — argument za automatyzacją (cytować w 1.1
   jako motywację: ludzie nie rozpoznają własnego foot strike w 57% przypadków).

## Co dopisać do Limitations (rozdział 9.2)

Bezpośrednio na bazie literatury + tej pracy:

1. **Small dataset** (16 filmów) — podobne do HGcnMLP 2023 (27 osób), Ripic 2023 (17 osób).
   Walidacja na większej próbce to **standard future work** w tej dziedzinie.
2. **Brak ground truth z 3D MoCap** — w odróżnieniu od Stenum 2021 i Ripic 2023.
   Cena: nie można podać MAE w metrach/sekundach jak w cytowanych pracach. Zysk:
   metoda działa stand-alone, bez kosztu kalibracji.
3. **Monocular 2D limitations** dziedziczone z literatury (out-of-plane, perspective,
   environmental dependence) — uczciwe omówienie, z mityganami które praca dostarcza
   (aspect ratio fix, low_confidence flag, combinatorical quality detection).
4. **Non-determinizm MediaPipe** (XNNPACK delegate) — minimal differences między
   uruchomieniami. Wpływ na liczbę reguł `info` w rekomendacjach. Do udokumentowania.

## Dalsze kroki

1. **Pisanie pracy** — rozdziały 4 (Eksperyment 1), 5 (Eksperyment 2), 7 (Rekomendacje),
   8 (Eksperyment 3) mają **komplet materiału**. Mogą być pisane natychmiast.
2. **State of the Art (rozdz. 2)** — wstępna lista 7 cytatów z researchu, można rozszerzyć
   do 25-30 cytatów (Heiderscheit, Souza, Novacheck, Diaz, Daoud, Robinson dla biomechaniki
   + 7 z researchu dla ML/pose + 5-10 dla pose estimation methodology).
3. **Sekcja Wstęp / Motywacja (rozdz. 1.1)** — wymaga **decyzji o pozycjonowaniu pracy**:
   sport ↔ injury prevention ↔ rehabilitation ↔ konsumencka aplikacja. Każde
   pozycjonowanie inaczej formułuje motivation.
4. **Decyzje formalne** — z promotorem: dokładny tytuł, zakres "scope" (np. czy
   uwzględniać rekomendacje, czy zostawić tylko klasyfikację), liczba stron, deadline.
