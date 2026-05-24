# 2026-05-09 — Iteracja 1: pipeline na test set + raporty z porównaniem do referencji

**Opis dla agenta:** Iteracja 1: test pipeline na test set, raporty Markdown, jakość downstream metryk

**Słowa kluczowe:** raporty, reference_values, analyze.py, low quality, test set

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
