# Briefing na następną sesję

> **Data ostatniej sesji**: 2026-05-14 (Sesja C: walidacja foot strike + research podobnych prac + wybór problemu badawczego)
> **Data tego briefu**: 2026-05-14 (koniec sesji)

---

## 🔹 Co Claude MUSI przeczytać na starcie (w tej kolejności)

1. **`CLAUDE.md`** — zasady projektu, pipeline, sekcja "Notatki do pracy magisterskiej (auto-zapis)" — **obowiązuje automatycznie**
2. **`History.md`** — log chronologiczny. Najnowsze wpisy: **2026-05-13 (Sesja A) + 2026-05-13 (Sesja B część 1) + 2026-05-14 (Sesja C)**
3. **`docs/thesis-notes/README.md`** — index notatek (16 notatek)
4. **`docs/thesis-notes/2026-05-14-temat-pracy-finalny.md`** — **FINALNY TYTUŁ + 3 pytania badawcze (biomechanics-centric) + 7 hipotez + struktura 8 rozdziałów (~60 stron). Aktualna wytyczna do pisania.**
5. **`docs/thesis-notes/2026-05-14-problem-badawczy-propozycja-a.md`** — wersja **historyczna** (ML-centric, przed finalizacją tytułu z promotorem). Zachowana dla kontekstu.
6. **`docs/thesis-notes/2026-05-14-research-podobnych-prac.md`** — 7 prac peer-reviewed z cytatami problemów badawczych, 4 wzorce sformułowań, identyfikacja 5 gap'ów w literaturze
7. **`docs/thesis-notes/2026-05-14-sesja-c-foot-strike-walidacja.md`** — walidacja foot strike + reformulacja limitation #9 (Case 1 dla P3)
8. **`docs/thesis-notes/2026-05-13-sesja-b-stride-combinatorical.md`** — Sesja B: stride length + combinatorical quality
9. **`docs/thesis-notes/2026-05-13-integracja-etap7-analyze.md`** — Sesja A: integracja Etapu 7 z `analyze.py`, refaktor A2
10. **`docs/thesis-notes/2026-05-09-iteracja1-test-set.md`** — Iteracja 1 (limitation #9 z dopisem "Po dalszej pracy" z Sesji C)
11. **`src/recommendations/rules.py`** — silnik reguł. Po Sesji C ma `foot_strike_low_confidence`.
12. **`src/coefficients/spatial_metrics.py`** — `compute_foot_strike_pattern` z flagą `low_confidence` (próg 45°).
13. **`src/coefficients/analyze.py`** — orchestrator E2E (bez zmian w Sesji C).

---

## 🔹 Co Claude MUSI wiedzieć o projekcie

### Czym jest projekt

Praca **magisterska** — system analizujący wideo biegu na bieżni i obliczający współczynniki biomechaniczne z rekomendacjami. **Praca > produkt**.

Pipeline: wideo → MediaPipe (33 keypointy) → klasyfikator faz (LSTM r1 + aspect fix, 70.9% test acc) → współczynniki → rekomendacje (13+ reguł z literatury).

### Stan na ten moment (2026-05-14, koniec Sesji C)

- Etapy 1-4 zrobione (środowisko, ekstrakcja, etykietowanie, dataset 16 filmów)
- **Etap 5 — klasyfikator** ✅✅✅ — LSTM r1 + aspect fix = 70.9% test acc, F1 0.709 (primary)
- **Etap 6** ✅ MVP + Iteracja 1 + Sesja B (stride length — wszystkie 5 współczynników temporalnych z CLAUDE.md)
- **Etap 7** ✅ silnik reguł z 13+ regułami:
  - Sesja A: integracja z `analyze.py` (jedno CLI = E2E + rekomendacje)
  - Sesja B (część 1): `check_stride_length` + `quality_combo_high_si_low_conf`
  - **Sesja C**: `foot_strike_low_confidence` (warning) — ostrzeżenie gdy `|mean_angle|>45°`

### Sesja C — wyniki walidacji wizualnej (3 biegaczy × 6 klatek = 18 PNG)

| Biegacz | mean L / R | Werdykt manualnej inspekcji | low_confidence | nowa reguła |
|---|---|---|---|---|
| **Janek** (ujęcie z boku, OK) | −4° / −3° | ✓ zgadza się (midfoot) | False / False | nie fire (poprawnie) |
| **Adam** (ujęcie lekko od dołu) | −33° / −12° | prawa OK, lewa przesadzona perspektywą | False / False | nie fire (mean L pod progiem) |
| **22** (pionowe wideo) | −97° / −99° | bzdura geometryczna (|kąt|>90°) | True / True | ✅ fire warning |

**Wniosek**: hipoteza "systematyczny błąd metody" (limitation #9 w notatce Iteracji 1)
**odwołana**. Foot strike pattern jest wiarygodny **wyłącznie przy standardowym ujęciu
z boku**. System ostrzega `foot_strike_low_confidence` gdy warunki są nietypowe.

### Architektura modułu rekomendacji (po Sesjach A+B+C)

```
src/recommendations/
├── __init__.py        (eksport API)
├── rules.py           (~700 linii: 13+ reguł check_*, render_markdown, dataclass)
└── recommend.py       (105 linii: czyste CLI, import z rules.py)

src/coefficients/
├── analyze.py         (orchestrator: 6 kroków + krok 7 rekomendacje, --treadmill-speed-ms)
├── temporal_metrics.py (+compute_stride_length + parametr w compute_temporal_metrics)
├── spatial_metrics.py  (+low_confidence flag w compute_foot_strike_pattern, próg 45°)
└── ...

src/visualization/
├── render_frames.py                  (renderer ogólny z kolorami faz)
└── render_foot_strike_entries.py     (NOWY w Sesji C — walidacja foot strike)
```

**Pełna analiza E2E**:
```bash
.venv/Scripts/python.exe src/coefficients/analyze.py \
    --video "data/videos/22 - Running Analysis with Physiotherapist.mp4" \
    --skip-inference \
    --treadmill-speed-ms 3.0   # opcjonalny — jeśli znamy prędkość bieżni
# → 8 artefaktów (CSV, 4 JSON-y, 2 raporty MD, recommendations.json)
# foot_strike_low_confidence ostrzeże gdy |mean_angle|>45°
```

### Lista 13+ reguł (po Sesjach A+B+C)

- `check_cadence` (Heiderscheit 2011) — 5 progów
- `check_gct` (Souza 2016, Heiderscheit 2011) — + `overstriding_combo` (cad<160 + GCT>270)
- `check_flight` (Novacheck 1998)
- `check_duty_factor` (Souza 2016)
- `check_stride_length` (Novacheck 1998, Heiderscheit 2011) — 5 progów + `overstride_long_stride_combo` (stride>2.2m + cad<160)
- `check_torso_lean` (Novacheck 1998)
- `check_knee_at_contact` (Heiderscheit 2011, Novacheck 1998)
- `check_vertical_oscillation` (Diaz 2019)
- `check_symmetry` (Robinson 1987)
- `check_foot_strike` (Daoud 2012, Souza 2016) — **+ NOWA, Sesja C**: `foot_strike_low_confidence` (warning, walidacja wizualna)
- `check_data_quality` — 3 pojedyncze proxy + `quality_combo_high_si_low_conf` (Sesja B)

### Co JESZCZE nie zrobione (z planów poprzednich sesji)

Wszystkie pozycje **warunkowe** — Sesja C zamknęła ostatnią nierozwiązaną kwestię metody.
Lista odłożonych do decyzji użytkownika:

1. **Stable segment detection** dla mixed-tempo (film 20) — kosmetyka, odłożone w Sesji B
2. **Generator PDF** z wykresami matplotlib — kosmetyka, odłożone w Sesji B
3. **Walidacja Etapu 7 na własnym filmie biegowym** użytkownika — gdy będzie własne nagranie
4. **Asymetria perspektywy (case Adama)**: drugi próg `|mean_L − mean_R| > 20°` jako "watch" — wymaga walidacji na więcej filmach
5. **Pisanie pracy magisterskiej** — rozdziały 6 i 7 mają komplet materiału po A+B+C

---

## 🔹 Plan kolejnych sesji

### Sesja **D (priorytet)** — Pisanie pracy magisterskiej

**Po sesji 2026-05-14 (research podobnych prac + wybór Propozycji A) wszystkie
6 hipotez ma materiał empiryczny zebrany.** Praca może być pisana **bez dodatkowych
eksperymentów**. Notatki bazowe:
- `docs/thesis-notes/2026-05-14-research-podobnych-prac.md` (7 prac, 4 wzorce, gap analysis)
- `docs/thesis-notes/2026-05-14-problem-badawczy-propozycja-a.md` (tytuł roboczy,
  3 pytania badawcze, 6 hipotez, struktura 10 rozdziałów, lista cytatów do State of the Art)

**Tytuł roboczy**:
> *"Klasyfikacja faz biegu z monocular 2D wideo: porównanie podejść uczenia maszynowego
> i analiza wrażliwości metryk biomechanicznych na warunki akwizycji"*

**3 pytania badawcze (P1/P2/P3)**:
- **P1**: czy LSTM > RF na małym datasecie + jaki feature engineering zbliża RF do LSTM?
- **P2**: czy aspect ratio fix poprawia generalizację dla heterogenicznych orientacji?
- **P3**: które metryki są wrażliwe na warunki akwizycji (orientacja/perspektywa/FPS)
  i jak detekować artefakt automatycznie?

**Status hipotez**: wszystkie 6 (H1-H6) **potwierdzone** istniejącymi danymi.

**Materiał na P3 (bez nowych eksperymentów)**:
- Case 1: foot strike vs perspektywa kamery (Sesja C, 18 PNG)
- Case 2: aspect ratio fix dla film 22 (75.8% → 85.9%)
- Case 3: FPS dla film 16 (13 FPS = 15% błąd kwantyzacji)

**Rozdziały gotowe do pisania od razu** (mają komplet materiału):
- Rozdz. 4 — Eksperyment 1 (porównanie 4 klasyfikatorów)
- Rozdz. 5 — Eksperyment 2 (aspect ratio fix ablation)
- Rozdz. 6 — Współczynniki biomechaniczne (12 metryk)
- Rozdz. 7 — System rekomendacji (13+ reguł z citation)
- Rozdz. 8 — Eksperyment 3 (wrażliwość metryk, tabela "metryka × warunek")

**Co wymaga decyzji formalnej** (z promotorem):
- Dokładny tytuł
- Zakres (czy uwzględnić rekomendacje, czy tylko klasyfikację)
- Pozycjonowanie pracy (sport / injury prevention / rehabilitation / konsumencka app)
- Liczba stron, deadline

### Sesja **E** (warunkowa) — Stable segment detection / PDF generator / własny film

Trzy pozycje **odłożone** za zgodą użytkownika (kosmetyka, nie blokuje pracy):
1. **Stable segment detection** dla mixed-tempo (film 20)
2. **PDF generator** z wykresami matplotlib
3. **Walidacja Etapu 7 na własnym filmie biegowym** użytkownika (gdy nagra)

---

## 🔹 Znane pułapki — czego NIE zrobić

### Nie dotykać (krytyczne)

- **`data/splits.json`** — fair comparison wymaga identycznego splitu
- **`models/lstm_run1_overfit/`** — to **primary model** (LSTM r1 + aspect fix)
- **`models/*_pre_aspect_fix/`** i **`models/*_pre_extension/`** — backupy do rozdziału 5
- **Notatki thesis już napisane** — bez zgody usera. Aktualizuj jako sekcja "po dalszej pracy"
- **CLAUDE.md** — bez zgody usera
- **Progi w `src/recommendations/rules.py`** — kalibrowane vs `docs/reference-values.md` + literatura. Zmiana progu = zmiana citation
- **Próg 45° w `check_foot_strike` i `compute_foot_strike_pattern`** — kalibrowany na podstawie walidacji wizualnej Sesji C (Janek ≤12°, Adam 33°, 22 ≥82°). Zmiana = ryzyko false positives na Adamie lub false negatives na innych pionowych wideo
- **Logika combinatorical (`max_SI>50% AND conf<0.90`)** — kalibrowana dla edge case'u Janka
- **Konwencja `low_confidence` w spatial.json** — fallback w `check_foot_strike` (`abs(mean)>45°`) obsługuje legacy spatial.json sprzed Sesji C, nie usuwać

### Reguły rekomendacji — używaj świadomie

- **Severity ordering**: critical → warning → watch → info. Reguły quality_predykcji idą na początek
- **Citation jest częścią rekomendacji** (Sesja C dodała "Walidacja wizualna 2026-05-14")
- **Reguły deterministyczne, nie ML**
- **Stride length** wymaga `--treadmill-speed-ms` od użytkownika (graceful skip bez niego)
- **`foot_strike_low_confidence`** gdy fire → **blokuje** reguły semantyczne (`consistent`/`inconsistent`), bo bazują na klasyfikacji która jest artefaktem perspektywy

### Tu są open issues z poprzednich sesji

1. **Bug `postprocess_median.predict_lstm`** — pokazuje LSTM r1 = 66.4%, ale metrics.json mówi 70.9%. Niezmieniony.
2. ~~**Foot strike kąty −33°/−58°**~~ — **rozwiązane w Sesji C** (limitation #9 reformulowana, mitygant w kodzie)
3. **Torso lean 2.3°** Adam — niskie, ale stabilne (możliwy szum keypointów lub running tall)
4. **Slug strategy** — `24-adam` vs `24-adam-bieg__segment_1`. Funkcja `_slugify` powinna normalizować typowe sufiksy. Drobne, ale warto naprawić przed publikacją.
5. **Re-inferencja MediaPipe** produkuje minimalnie inne wyniki spatial (XNNPACK, multi-threading). Do omówienia w Limitations.
6. **Asymetria perspektywy (Adam)** — lewa noga 3× bardziej ujemna niż prawa, ale obie pod progiem 45°. Future work: drugi próg `|mean_L - mean_R| > 20°`.

### Nie robić bez wyraźnego sygnału

- **Hyperparameter sweep LSTM** — sufit ~71% jest niezależny od architektury
- **Augmentacja flip** — wymaga przerobienia auto_label
- **Velocity features**, **Ensemble** — nie pomagają
- **3D motion capture** — poza scope, ale ważny argument w Limitations
- **Dodawanie reguł bez citation** — każda reguła w `rules.py` ma źródło (literatura lub walidacja wewnętrzna)
- **Stable segment detection / PDF generator** — odłożone z Sesji B za zgodą usera, nie wracać bez prośby
- **Asymetria perspektywy jako reguła** — wymagałaby walidacji na więcej filmów

---

## 🔹 Szybka pigułka — jeden akapit

Sesja **C** (2026-05-14, część 1) zamknęła rewizję **limitation #9** z notatki Iteracji 1.
**Część 2 tej samej sesji** (po pytaniu strategicznym usera o problem badawczy): research
7 podobnych prac naukowych (WebSearch + WebFetch — uprawnienia odblokowane w trakcie sesji,
WebFetch dla domen open-access: PMC, PLOS, Frontiers, MDPI; Nature i Springer wymagają auth)
zidentyfikował **5 gap'ów w literaturze** które ta praca wypełnia, oraz **4 typowe szablony
sformułowania problemu badawczego** w obszarze. Wybrana **Propozycja A** (notatka
`2026-05-14-problem-badawczy-propozycja-a.md`): tytuł roboczy *"Klasyfikacja faz biegu
z monocular 2D wideo: porównanie podejść uczenia maszynowego i analiza wrażliwości metryk
biomechanicznych na warunki akwizycji"*, 3 pytania badawcze (P1: porównanie 4 klasyfikatorów,
P2: aspect ratio fix ablation, P3: wrażliwość metryk na orientację/perspektywę/FPS), 6 hipotez
(wszystkie potwierdzone istniejącymi danymi — bez nowych eksperymentów). P3 oparte
na 3 case studies: foot strike (Sesja C, 18 PNG), aspect ratio fix dla film 22
(75.8% → 85.9% +10.1pp), FPS dla film 16 (13 FPS = 15% błąd kwantyzacji). Pełna struktura
10 rozdziałów + lista 7 cytatów do State of the Art. **Praca może być pisana od razu,
bez dodatkowych eksperymentów. Następna sesja D = pisanie pracy.**

---

## 🔹 (poprzednia pigułka, dla kontekstu) Szybka pigułka — Sesja C część 1

Sesja **C część 1** (2026-05-14) zamknęła rewizję **limitation #9** z notatki Iteracji 1.
Nowy skrypt `src/visualization/render_foot_strike_entries.py` wybiera klatki
entry-into-STANCE z phases.csv, liczy kąt foot strike per noga, renderuje PNG ze
szkieletem + paskiem info. 18 PNG (3 biegaczy × 2 nogi × 3 klatki) zwalidowane wizualnie
przez użytkownika: Janek (ujęcie z boku) → kąty −12° do +5° **zgadzają się** z midfoot
strike ✓; Adam (ujęcie lekko od dołu) → prawa OK (−12°), lewa przesadzona perspektywą
(−33° do −56°) = **artefakt kamery**; **22** (pionowe wideo) → kąty −82° do −160° =
**bzdura geometryczna**. Hipoteza "systematyczny błąd metody" **odwołana**. Mitygant
w kodzie: `compute_foot_strike_pattern` dorzuca `low_confidence: True` gdy
`|mean|>45°`; `check_foot_strike` ma nową regułę `foot_strike_low_confidence` (warning,
citation "Walidacja wizualna 2026-05-14"). Smoke test na 3 biegaczach: 22
`foot_strike_consistent` (info) → `foot_strike_low_confidence` (warning, total 10 bez
regresji); Adam 8 reguł bez zmian; Janek 11 reguł bez zmian. Nowa reguła **nie produkuje
false positives** na poprawnym ujęciu. Limitation #9 w notatce Iteracji 1 dopisana sekcją
"Po dalszej pracy" (konwencja CLAUDE.md). Nowa notatka thesis
`2026-05-14-sesja-c-foot-strike-walidacja.md` (metodyka, predykcja referencyjna,
walidacja per biegacz, reformulacja, implementacja, weryfikacja, future work).
**Po Sesji C metoda jest zamknięta** — następna sesja warunkowa: Sesja D (stable
segment lub PDF, kosmetyka), Sesja E (walidacja na własnym filmie usera, gdy będzie),
albo **Sesja F (pisanie pracy magisterskiej)** — rozdziały 6 i 7 mają komplet materiału.
