# 2026-04-26 — Etap 5.4: analiza porównawcza 4 modeli

**Opis dla agenta:** Analiza porównawcza 4 modeli i artefakty do rozdziału 5.4

**Słowa kluczowe:** compare_models, rozdział 5.4, macierze pomyłek, feature importances, learning curves

---

## 2026-04-26 — Etap 5.4: analiza porównawcza 4 modeli

### Decyzja sesji

Wybrana **Opcja 1** z briefu — konsolidacja istniejących wyników (RF v1, RF v2, LSTM run 1, LSTM run 2) bez naprawy aspect ratio. Film 22 zostaje jako limitation w pracy. Cel: gotowy materiał do rozdziału 5.4.

### Zrobione

- **`src/training/compare_models.py`** — standalone skrypt wczytujący 4 metrics.json, generujący tabele MD/JSON i wykresy PNG. Reentrant (po retreningu modelu generuje nowe artefakty automatycznie).
- **Notatka thesis**: `docs/thesis-notes/2026-04-26-comparison.md` — pełna analiza 11 sekcji z odwołaniami do figur i tabel.
- **Artefakty w `docs/thesis-notes/figures/`**:
  - `comparison_table.md`, `comparison_summary.json` — metryki globalne
  - `per_file_test.md` — accuracy per filmik × model
  - `error_breakdown.md` — typologia błędów L↔R vs FLIGHT↔STANCE
  - `confusion_matrices_test.png` — 4 macierze pomyłek (heatmapy znormalizowane recall)
  - `learning_curves_lstm.png` — train/val loss + val_acc dla obu runów LSTM
  - `feature_importances_rf.png` — TOP-15 cech dla RF v1 i RF v2 (kolorowanie semantyczne)

### Kluczowe nowe obserwacje (z konsolidacji)

1. **Luka val→test maleje monotonicznie** (21.6 → 18.4 → 15.5 p.p.) — każdy krok poprawia generalizację międzyfilmową, niezależnie od tego co dzieje się z val accuracy. To jest mocniejsza obserwacja niż samo "test acc rośnie".
2. **Każda iteracja redukuje **inny typ** błędu**:
   - RF v1 → RF v2: −49% L↔R (185 → 95) — feature engineering (normalizacja antropometryczna)
   - RF v2 → LSTM run 2: −16% FLIGHT↔STANCE (486 → 408) — kontekst czasowy
   - To pokazuje że dwa kierunki poprawy są **komplementarne**, nie alternatywne.
3. **Per-film: feature engineering i kontekst czasowy ratują różne filmy**:
   - Film 02 (47 → 64% RF v2) — beneficjent normalizacji (inna pozycja w kadrze niż train)
   - Film 20 (61 → 65% LSTM r2) — beneficjent kontekstu (walk→run, zmienna kadencja)
   - Film 22 — żaden z dwóch kierunków nie pomaga (bug aspect ratio)
4. **Total errors: 611 → 581 → 509** (poprawa 17%) — narracja kumulatywna potwierdzona w danych.

### Drobne kosmetyczne poprawki w skrypcie

- Confusion matrix layout: tytuły jednoliniowe + `subplots_adjust(hspace=0.45)` + osobny colorbar (axes lista 2D nie działa z `fig.colorbar`)
- Per-file table: lepszy parser nazw plików (kropka w "0.8 to 3.5" rozbijała etykietę 20)
- Error breakdown: usunięta myląca kolumna "inne" (dla 3 klas L↔R + FLIGHT↔STANCE pokrywa wszystkie pola off-diagonal)

### Materiał do pracy magisterskiej

- Rozdział 5.4 ma teraz pełną tabelę zbiorczą + 3 wykresy + 3 tabele pomocnicze
- Run 1 vs run 2 jako case study procesu badawczego ("wyższy test acc nie znaczy lepszy model gdy dochodzi to przez overfit")
- Sufit ~65% test mimo trzech architektur — jako uzasadnienie sekcji "Limitations"
- TOP cechy RF v2 = kąty stawów — jako biomechaniczna walidacja modelu

### Do zrobienia w następnej sesji

**Etap 6 — obliczanie współczynników biomechanicznych** (lub naprawa aspect ratio jako warunek wstępny):

1. Decyzja: czy najpierw aspect ratio (Opcja 2 z briefu poprzedniego — oczekiwany zysk +3-7 p.p. test), czy od razu Etap 6 z aktualnym LSTM?
2. Etap 6: nowy pipeline `src/coefficients/` — kadencja, GCT, flight time, stride length, kąty stawów, vertical oscillation, foot strike pattern, symetria L/R. KRYTYCZNE: tu FPS i prędkość bieżni mają znaczenie (vs trenowanie).

### Odkładane decyzje (bez zmian)

- Wersjonowanie `models/`
- Ręczna walidacja etykiet (low priority — sufit szumu etykiet)
- Hyperparameter sweep LSTM (low priority — sufit nie jest tam)

---
