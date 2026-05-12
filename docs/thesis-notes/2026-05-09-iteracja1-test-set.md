# 2026-05-09 — Iteracja 1: pipeline na test set + raporty z porównaniem do referencji

## Kontekst

Po MVP Etapu 6 (sesja `2026-05-09-coefficients-mvp.md`), iteracja 1 dodała:
1. **Wartości referencyjne** z literatury (`reference_values.py`) — synced z `docs/reference-values.md`
2. **Klasyfikator wartości** + emoji (✅/🟡/🔴) per współczynnik
3. **Kąt kolana w initial contact** w `spatial_metrics` — nowa metryka do porównania z literaturą
4. **`report_generator.py`** — pełen raport MD per biegacz z porównaniem do referencji
5. **`analyze.py`** — orchestration: 1 CLI uruchamia E2E (wideo → temporal/spatial/symmetry/raport)
6. **Test pipeline na 02, 20, 22** (test set — unseen biegacze)

## Architektura raportu MD

Raport per biegacz (np. `data/inference/raporty/02-running-at-13km-h-side-view.md`) zawiera:

1. **Header** — meta wideo (FPS, klatki, rozdzielczość, model + test acc, średnia confidence)
2. **Temporal** — tabela: kadencja, GCT L/R, flight, cycle, duty factor + klasyfikacja vs referencje
3. **Spatial** — tabela: kąty kolana @ initial contact, torso lean, vertical oscillation, foot strike
4. **Symmetry** — tabela L/R wszystkich par + Symmetry Index + klasyfikacja (norma <5%, uwaga 5-10%, problem >10%)
5. **Wnioski i ostrzeżenia** — zebrane warningi posortowane priorytetem (⚠️ na początek)
6. **Footer** — disclaimer + odniesienie do `docs/reference-values.md`

## Wyniki — porównanie 4 filmów (3 test + Adam jako reference z train)

### Tabela zbiorcza temporal

| Film | Test acc LSTM | Avg conf | Kadencja | n_steps L/R | GCT L/R [ms] | Flight [ms] | Cycle [ms] | DF L/R | Max SI |
|---|---|---|---|---|---|---|---|---|---|
| **02** (13 km/h sideview) | 54.5% | 0.795 | **144** spm | 14/10 | 247/**130** | 200 | 783 | 0.378/**0.132** | **96.5%** |
| **20** (walk→run) | 70.9% | 0.901 | 139 spm | 33/34 | 204/368 | 143 | 841 | 0.247/0.429 | 57.3% |
| **22** (physiotherapist) | 85.9% | 0.890 | 163 spm | 15/14 | 285/226 | 116 | 729 | 0.388/0.313 | 35.0% |
| **24 Adam** (train, ref) | — (train) | 0.909 | 174 spm | 115/116 | 203/245 | 122 | 685 | 0.296/0.357 | 18.7% |

### Korelacja Test Acc ↔ Jakość metryk — najważniejsza obserwacja

| Test acc | Confidence | Symetria L/R steps | Max SI | Wnioski |
|---|---|---|---|---|
| 54.5% (02) | 0.795 | **14/10** ❌ | 96.5% | Model myli L/R, brakuje 4 R-kontaktów, GCT R 130 ms nierealistyczne |
| 70.9% (20) | 0.901 | 33/34 ✅ | 57.3% | Mix walk+run zaburza średnie; symetria steps OK |
| 85.9% (22) | 0.890 | 15/14 ✅ | 35.0% | Najlepszy z testu — sensowne metryki, ale aspect ratio dalej daje asymetrie |
| Adam (sanity) | 0.909 | 115/116 ✅ | 18.7% | Najlepszy ogólnie — Adam w train, więc znany modelowi |

**Wniosek**: jakość współczynników biegu **silnie koreluje** z test acc LSTM dla danego filmu. Model z 54.5% acc daje **bezużyteczne** współczynniki (max SI 96.5% to po prostu szum predykcji). Model z 85%+ acc daje **akceptowalne** współczynniki z drobnymi artefaktami.

### Per-film analiza

#### Film 02 (13 km/h sideview, 360×450, 30 FPS, 10s) — **predykcje fundamentalnie zaszumione**

- LSTM r1 + aspect fix: **54.5% test acc** (najgorszy z test set)
- Avg confidence: 0.795 (najniższa)
- **L/R steps: 14/10** — model nie wykrył 4 prawych kontaktów. To **ścisła konsekwencja** L↔R confusion w tym filmie (znana z confusion matrix 5.4)
- GCT R = 130 ms vs L = 247 ms — różnica 117 ms (SI 62%). Realistyczne GCT dla biegu 13 km/h to ~220-260 ms (oba). Prawe GCT 130 ms to **artefakt** krótkich, fragmentarycznych segmentów RIGHT_STANCE
- Cycle time L 652 vs R 985 ms — patologiczna asymetria (SI 41%). Realne cycle time dla tego tempa to ~700 ms
- Duty factor L 0.38 vs R **0.13** — DF 0.13 wskazuje "bieg sprintera elity" (nieprawda dla 13 km/h)
- Foot strike: L midfoot, R forefoot (kąt −46°) — niespójne, prawdopodobnie artefakty

**Diagnoza**: dla filmu 02 system **NIE jest gotowy do produkcji**. Raport powinien w UI mieć ostrzeżenie "uwaga: niska jakość predykcji" gdy avg confidence < 0.85 lub L/R step asymmetry > 20%.

#### Film 20 (walk→run, 0.8-3.5 m/s, 640×360, 30s) — **mix faz zaburza średnie**

- LSTM r1: 70.9% test acc
- Avg confidence 0.901, L/R steps 33/34 (zbalansowane)
- Kadencja **139 spm** — niska, ale uzasadniona: film zawiera **fazę chodu** (0.8 m/s) na początku. Średnia globalna jest meaningless
- GCT L 204 / R 368 ms — duża asymetria, ale tu częściowo **prawdziwa**: faza chodu ma długie GCT, faza biegu krótkie. Średnia miesza
- DF L 0.247 / R 0.429 — DF L pokazuje sprint, DF R pokazuje rekreacyjny → mix walk+run

**Diagnoza**: film 20 wymaga **detekcji fazy "tempo"** przed obliczaniem statystyk per cykl. Future work: tylko klatki gdzie cycle time jest stabilny (filtrowanie outlier'ów cycle > 1.5×median lub < 0.5×median).

#### Film 22 (physiotherapist, 608×1080 pionowe, 11s) — **najbardziej akceptowalne**

- LSTM r1 + aspect fix: **85.9% test acc** (najlepszy z testu; aspect fix dramatycznie pomógł)
- Avg confidence 0.890, L/R steps 15/14 (zbalansowane)
- Kadencja 163 spm — w typowym zakresie rekreacyjnym
- GCT L 285 / R 226 ms — asymetria 23% (klasyfikacja "potencjalny problem"), ale to wciąż mniej dramatyczne niż film 02
- Flight 116 ms — typowy zakres (80-150 ms)
- Cycle 729 ms — spójny z kadencją 163 spm
- Foot strike: oba forefoot (consistent), kąt L −58° (ekstremalny — prawdopodobnie artefakt aspect ratio + foot pose nie idealnie wykryta)
- Pochylenie tułowia: **9.9°** — w zakresie typowym (5-15°) ✅

**Diagnoza**: dla filmu 22 system daje **użyteczne** wyniki, choć z ograniczeniami (asymetria może być artefaktem aspect ratio bug, foot strike kąty ekstremalne). To jest największy sukces aspect ratio fix — film 22 z 75.8% (przed fix) → 85.9% (po fix), współczynniki teraz zgrubnie akceptowalne.

#### Film 24 Adam (train, sanity check) — **najlepsze wyniki, jak oczekiwano**

- W train, więc model widział te dane (nie fair miara generalizacji)
- Najwyższa confidence 0.909, kadencja 174 spm, idealna symetria cycle time (684 vs 685 ms)
- GCT asymetria 18.7% — artefakt monocular 2D (lewa strona bliżej kamery)
- Wszystkie spatial metrics biomechanicznie poprawne

## Kluczowe obserwacje (wartość dla pracy)

1. **Confidence jako proxy jakości**: avg confidence < 0.85 silnie koreluje z bezsensownymi współczynnikami. **Sugestia dla UI**: pokaż ostrzeżenie "niska pewność predykcji" + zachęta do nagrania kolejnego filmu

2. **L/R steps asymmetry jako sanity check**: różnica > 20% (np. 14/10 dla 02) sygnalizuje że model myli L↔R. Łatwy do detekcji, można eskalować jako "krytyczny problem predykcji" niezależnie od pozostałych metryk

3. **Filmy z mieszanymi tempami (20)** wymagają specjalnej obsługi — średnie statystyki są meaningless. Future work: detekcja "stabilnych segmentów" + statystyki tylko z nich

4. **Korelacja test acc ↔ jakość downstream**: nasze 70.9% test acc LSTM r1 nie gwarantuje 70.9% jakości raportów. Per-film to spektrum 54-86%, więc raporty per-film są **różnej jakości**. Kluczowe dla pracy: udokumentować że "test acc 70.9%" to średnia, nie gwarancja per video

5. **Aspect ratio fix dramatycznie pomaga film 22** (75.8 → 85.9% acc, max SI z ~50% → 35%). Walidacja hipotezy z `2026-05-08-accuracy-improvements.md` na poziomie współczynników, nie tylko klasyfikacji

6. **Bug raport_generator emoji**: pierwotna wersja klasyfikowała "potencjalny problem" w SI jako ✅. Naprawione — heurystyka label + warnings + critical_terms (`ryzyko`, `problem`, `chód`, `marnowanie`, `obciążenie`)

## Implikacje dla pracy magisterskiej

### Sekcja Methodology — Pipeline E2E

Architektura `analyze.py` jako orchestration:
```
wideo → MediaPipe Pose (complexity=2) → savgol smoothing (savgol_window=11)
     → aspect ratio fix (auto-detect z config.json)
     → engineered features (106 cech)
     → StandardScaler (z trainu)
     → BiLSTM (sliding window 15)
     → predykcje fazy + confidence
     → temporal/spatial/symmetry metrics (per cykl)
     → klasyfikacja vs reference values (literatura)
     → raport MD
```

### Sekcja Wyniki — Tabela 4 filmów

Tabela "Wyniki na test set" (3 filmy) + Adam jako reference. Ważne pokazać:
- Test acc per film (54.5 / 70.9 / 85.9%) — silnie zmienne
- Jakość metryk koreluje z test acc
- Adam jako "ideal case" (model wie biegacza)

### Sekcja Walidacja

Korelacja test acc ↔ jakość raportów to **nowa walidacja** modelu na poziomie aplikacyjnym (nie tylko classification accuracy). Pokazuje że metryka "test acc 70.9%" nie jest pełną odpowiedzią — niektóre filmy mają 54%, niektóre 86%.

### Sekcja Limitations (rozszerzona)

Z poprzedniej notatki (6 punktów) + nowe z iteracji 1:
7. **Film 02 specyficzny** — model myli L↔R (54.5% acc), współczynniki niesensowne. Wymagana detekcja "low quality predictions" przed pokazaniem raportu użytkownikowi
8. **Filmy mixed-tempo (20)** wymagają detekcji stabilnych segmentów. Globalna średnia jest meaningless dla walk→run
9. **Foot strike kąty ekstremalne** (−46° dla 02 PRAWA, −58° dla 22 LEWA) — wzorzec się powtarza, prawdopodobnie systematyczny błąd metody (klatka entry-into-stance vs faktyczny moment kontaktu)
10. **Reference values mają charakter ogólny** (literatura na biegaczy zdrowych) — indywidualne progi mogą się różnić

### Sekcja Future Work

1. **Auto-detect "low quality predictions"** — flagi: avg_confidence < 0.85, L/R asymmetry > 20%, max SI > 30%
2. **Stable segment detection** dla filmów mixed-tempo — odsiewanie outlier'ów przed średnimi
3. **Walidacja foot strike** wizualną inspekcją wybranych klatek
4. **Stride length** (Iteracja 2) — input prędkości bieżni
5. **Generator raportu PDF** z wykresami (sygnały Y_hip per cykl, kadencja w czasie)

## Artefakty

```
src/coefficients/
├── reference_values.py       — synced z docs/reference-values.md
├── report_generator.py       — generator MD raportu
├── analyze.py                — orchestration CLI
└── (poprzednie 4 moduły)
```

```
data/inference/
├── 02-running-at-13km-h-side-view-{phases.csv, temporal/spatial/symmetry/meta.json}
├── 20-running-0.8-to-3.5-m-s-__segment_1-{...}
├── 22-running-analysis-with-physiotherapist-{...}
├── 24-adam-{...}  (z poprzedniej sesji)
└── raporty/
    ├── 02-running-at-13km-h-side-view.md         ← raport per biegacz
    ├── 20-running-0.8-to-3.5-m-s-__segment_1.md
    └── 22-running-analysis-with-physiotherapist.md
```

## Co dalej

### Iteracja 2 (rekomendowana następna)

1. **Stride length** z input użytkownika (`--treadmill-speed-ms`)
2. **Auto-detect low quality predictions** (warning w raporcie gdy confidence/symetria zła)
3. **Stable segment detection** dla filmów mixed-tempo
4. **Generator PDF** z wykresami (matplotlib)

### Etap 7 (rekomendacje)

Po Iteracji 2 — reguły rekomendacji z literatury jako rozdział 7 pracy.

### Drobne TODO (niski priorytet)

1. **Bug `postprocess_median.predict_lstm`** — różnica 4.5 p.p. vs metrics.json (z poprzednich sesji)
2. **Foot strike kąty ekstremalne** — wymaga walidacji wizualnej (kilka klatek per film)
3. **Adam meta.json** — uruchom analyze.py --skip-inference dla Adama żeby wygenerować meta.json (nie był utworzony przy run_inference.py)
