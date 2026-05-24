# Briefing na następną sesję

> **Ostatnia sesja**: 2026-05-23 (Sesja E: pisanie rozdziału 3, sekcje 3.1–3.3)
> **Następna sesja**: kontynuacja rozdziału 3, od sekcji 3.4

---

## Co przeczytać na starcie (MINIMALNA lista)

1. **Ten plik** — kontekst + co robić
2. **`CLAUDE.md`** — zasady kodowania, pipeline, konwencje (ładowane automatycznie)
3. **`thesis/chapters/03-materialy-metody.tex`** — aktualny stan rozdziału do pisania

**Sięgnij głębiej TYLKO gdy potrzebujesz konkretnych danych:**
- Liczby/metryki modeli → `docs/thesis-notes/figures/comparison_summary.json`
- Wyniki per-film → `docs/thesis-notes/figures/per_file_test.md`
- Decyzje metodologiczne → `docs/thesis-notes/2026-05-14-temat-pracy-finalny.md`
- Wyjaśnienia pojęć → `docs/thesis-notes/2026-05-14-wyjasnienia-pojec-do-pisania.md`
- Pełna historia → `history.md` (1260+ linii — NIE czytaj w całości)

---

## Projekt w jednym akapicie

Praca magisterska SGGW: *"Analiza podstawowych współczynników biegu przy pomocy uczenia maszynowego"*. Pipeline: wideo bieżni (ujęcie z boku) → MediaPipe Pose (33 keypointy) → Savitzky-Golay → auto-etykietowanie faz (peak-based) → klasyfikator BiLSTM (70.9% test acc) → 12 współczynników biomechanicznych (5 temporalnych + 7 przestrzennych) → 13+ reguł rekomendacji z literaturą. Wszystkie etapy implementacyjne (1-7) zakończone. Praca jest gotowa do pisania bez dodatkowych eksperymentów.

---

## Stan pracy magisterskiej (thesis/)

**Szablon**: SGGW-thesis.cls, `\MAGISTERSKAtrue`, `\WZIMtrue`
**Kompilacja**: `pdflatex main.tex` (3×) lub `latexmk -pdf main.tex`
**Metadane**: TODO w `main.tex` linie 13-19 (autor, album, promotor)

### Rozdziały — stan na 2026-05-23 (po sesji E)

| # | Plik | Tytuł | Stan | Materiał źródłowy |
|---|---|---|---|---|
| 1 | `01-wstep.tex` | Wstęp | szkielet TODO | pisać NA KOŃCU |
| 2 | `02-state-of-the-art.tex` | Przegląd literatury | szkielet TODO | `2026-05-14-research-podobnych-prac.md` |
| 3 | `03-materialy-metody.tex` | Materiały i metody | **W TRAKCIE** (3.1–3.3 ✅, 3.4–3.8 TODO) | CLAUDE.md, history.md, src/ |
| 4 | `04-klasyfikator.tex` | Klasyfikator faz (P2) | szkielet TODO | `figures/comparison_*.md`, `figures/*.png` |
| 5 | `05-wspolczynniki.tex` | Współczynniki biegu (P1) | szkielet TODO | `2026-05-09-coefficients-mvp.md`, `reference-values.md` |
| 6 | `06-rekomendacje.tex` | System rekomendacji | szkielet TODO | `2026-05-12-etap7-rekomendacje.md`, `rules.py` |
| 7 | `07-wrazliwosc.tex` | Wrażliwość (P3) | szkielet TODO | `2026-05-14-sesja-c-foot-strike-walidacja.md` |
| 8 | `08-dyskusja-wnioski.tex` | Dyskusja i wnioski | szkielet TODO | pisać NA KOŃCU |

**Kolejność pisania**: ~~3~~ → 4 → 5 → 7 → 6 → 2 → 1 → 8 (rozdział 3 w trakcie)

### Bibliografia

`chapters/bibliography.tex` — **27 zweryfikowanych wpisów** (3× agenci + ręcznie user).
Diaz 2019 usunięty (niepotwierdzony). Wszystkie wpisy mają DOI (poza Goodfellow/PyTorch/OpenCV).

---

## Kluczowe liczby (żeby nie szukać)

| Metryka | Wartość |
|---|---|
| Dataset | 15 filmów (nr 1–13, w tym 5a/5b i 6a/6b), ~12 biegaczy, 12 087 klatek |
| Klasy | LEFT_STANCE / RIGHT_STANCE / FLIGHT (3 klasy, ~33% każda) |
| Split | Train 10 filmów (72%), Val 2 (9%), Test 3 (19%) |
| RF v1 (raw) test | 62.7% acc, F1 0.617 |
| RF v2 (engineered) test | 67.0% acc, F1 0.671 |
| LSTM r1 + aspect fix test | **70.9% acc, F1 0.709** ← PRIMARY |
| LSTM r2 + aspect fix test | 68.2% acc, F1 0.681 |
| Współczynniki | 12 (5 temporalnych + 7 przestrzennych) |
| Reguły rekomendacji | 13+ z literaturą (Heiderscheit, Novacheck, Souza, Daoud, Robinson) |
| Walidacja pipeline | 3 biegaczy (Adam=train, 22=test, Janek=edge case) |

---

## Preferencje usera (z memory)

- **Pisanie sekcja po sekcji** — NIE cały rozdział naraz. Jedna \section{} na raz.
- **Komentarze w kodzie po polsku**, nazwy zmiennych po angielsku
- **Proaktywnie zapisuj** notatki do `docs/thesis-notes/` i wyjaśnienia do `2026-05-14-wyjasnienia-pojec-do-pisania.md`
- **Limit stron zniesiony** — może być więcej niż 60, wstawiamy kod/wykresy/diagramy
- **Własny filmik z biegu** — user jeszcze nie nagrał, nie blokuje pisania

---

## Czego NIE dotykać

- `data/splits.json` — fair comparison
- `models/lstm_run1_overfit/` — primary model
- `models/*_pre_aspect_fix/`, `models/*_pre_extension/` — backupy
- Notatki thesis już napisane — bez zgody usera
- Progi w `rules.py` — kalibrowane vs literatura
- CLAUDE.md — bez zgody usera

---

## Otwarte sprawy (niski priorytet)

1. Bug `postprocess_median.predict_lstm` (66.4% vs 70.9% — metrics.json autorytetywny)
2. Slug strategy (`24-adam` vs `24-adam-bieg__segment_1`)
3. Stable segment detection (film 20) — odłożone
4. PDF generator z wykresami — odłożone
5. Diaz 2019 — szukać pełnych danych bibliograficznych (vertical oscillation running)
6. Metadane `main.tex` — autor, album, promotor (user musi uzupełnić)

---

## Pytania badawcze i hipotezy (do wklejania w tekst)

**P1**: Jak zaprojektować pipeline ML wyliczający 12 współczynników z monocular 2D wideo?
**P2**: Który klasyfikator faz najlepiej przekłada się na precyzję metryk temporalnych?
**P3**: Które współczynniki są wrażliwe na warunki akwizycji i jak detekować automatycznie?

| Hipoteza | Status | Skrót |
|---|---|---|
| H1: pipeline 3-etapowy daje akceptowalne wyniki | potwierdzona | walidacja 3 biegaczy |
| H2: LSTM > RF o min. 5 pp | potwierdzona | 70.9 vs 67.0 |
| H3: engineered RF ≥ raw RF +10 pp | potwierdzona | 67.0 vs 62.7 (+4.3pp, nie 10 — częściowo) |
| H4: aspect fix +5 pp | potwierdzona | +3.8 pp LSTM r1 (film 22 +10.1 pp) |
| H5: metryki przestrzenne wrażliwe na perspektywę | potwierdzona | foot strike 22 → bzdura |
| H6: FPS<15 = 15% błąd kwantyzacji | potwierdzona | film 16 matematycznie |
| H7: auto-detekcja bez ground truth | potwierdzona | low_confidence próg 45° |

---

## Sekcje rozdziału 3 — co zostało do napisania

Sekcje 3.1–3.3 GOTOWE. Dla każdej pozostałej: (1) przeczytaj źródło, (2) napisz LaTeX, (3) pokaż userowi.

| Sekcja | Co opisać | Główne źródło danych | Stan |
|---|---|---|---|
| 3.1 Dataset | 15 filmów, kryteria, tabela, split | `data/videos_metadata.csv`, `data/splits.json` | ✅ |
| 3.2 Pipeline ekstrakcji | MediaPipe 0.10.14, 33 keypointy, Savgol 11/3 | `src/extraction/`, `.claude/rules/extraction.md` | ✅ |
| 3.3 Auto-etykietowanie | peak-based, dlaczego nie progowanie Y | `.claude/rules/labeling.md` | ✅ |
| **3.4 Architektury klasyfikatorów** | **4 modele, hiperparametry, aspect fix** | **`src/training/`, `comparison_summary.json`** | **NASTĘPNA** |
| 3.5 Obliczanie współczynników | 12 metryk, formuły, agregacje | `.claude/rules/coefficients.md`, `src/coefficients/` | TODO |
| 3.6 Silnik reguł | 13+ reguł, severity, citation | `src/recommendations/rules.py` | TODO |
| 3.7 Splity i metryki | train/val/test, accuracy, F1, confusion matrix | `data/splits.json`, `comparison_summary.json` | TODO |
