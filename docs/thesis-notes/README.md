# Notatki do pracy magisterskiej

**Tytuł pracy (FINALNY)**: *Analiza podstawowych współczynników biegu przy pomocy uczenia maszynowego*

**Aktualna wytyczna do pisania**: [2026-05-14 — Temat pracy (FINALNY) + struktura 8 rozdziałów (~60 stron)](2026-05-14-temat-pracy-finalny.md)

Folder na myśli, obserwacje i surowe fragmenty, które będą materiałem źródłowym do pisania pracy.

**Konwencja**: jeden plik = jedno zagadnienie / jedna sesja eksperymentów. Nazwa: `YYYY-MM-DD-temat.md`.

## Spis notatek

- [2026-04-24 — Random Forest baseline (Etap 5, część 1)](2026-04-24-rf-baseline.md)
- [2026-04-24 — Decyzja: Opcja B (engineered RF → LSTM)](2026-04-24-decision-option-b.md)
- [2026-04-24 — Random Forest v2 (engineered features)](2026-04-24-rf-engineered.md)
- [2026-04-26 — BiLSTM primary (Etap 5, część 3) — model docelowy + dwa runy](2026-04-26-lstm-primary.md)
- [2026-04-26 — Analiza porównawcza 4 modeli (Etap 5.4) — materiał do rozdziału 5.4 pracy](2026-04-26-comparison.md)
- [2026-05-08 — Rozszerzenie datasetu o 2 nowych biegaczy (23 Pawel, 24 Adam) + retrening 4 modeli](2026-05-08-dataset-extension.md)
- [2026-05-08 — Plan poprawy accuracy: krok po kroku do test ≥70%](2026-05-08-accuracy-improvements.md)
- [2026-05-09 — Etap 6 MVP: pipeline obliczania współczynników biegu](2026-05-09-coefficients-mvp.md)
- [2026-05-09 — Iteracja 1: pipeline na test set + raporty z porównaniem do referencji](2026-05-09-iteracja1-test-set.md)
- [2026-05-12 — Etap 7: moduł rekomendacji biegowych (reguły z literatury)](2026-05-12-etap7-rekomendacje.md)
- [2026-05-13 — Integracja Etapu 7 z `analyze.py` (Sesja A — pipeline E2E)](2026-05-13-integracja-etap7-analyze.md)
- [2026-05-13 — Sesja B (część 1): stride length + combinatorical low-quality detection](2026-05-13-sesja-b-stride-combinatorical.md)
- [2026-05-14 — Sesja C: walidacja foot strike pattern (rewizja limitation #9)](2026-05-14-sesja-c-foot-strike-walidacja.md)
- [2026-05-14 — Research podobnych prac naukowych: jak formułują problem badawczy](2026-05-14-research-podobnych-prac.md)
- [2026-05-14 — Problem badawczy pracy magisterskiej (Propozycja A — historyczna, ML-centric)](2026-05-14-problem-badawczy-propozycja-a.md)
- [2026-05-14 — **Temat pracy (FINALNY)** + struktura 8 rozdziałów (~60 stron)](2026-05-14-temat-pracy-finalny.md)
- [2026-05-14 — Wyjaśnienia pojęć i decyzji projektowych do pisania pracy (rosnący dokument)](2026-05-14-wyjasnienia-pojec-do-pisania.md)
- [2026-05-14 — Setup LaTeX dla pracy + 7 technik optymalizacji kosztów Claude](2026-05-14-setup-latex-i-koszty.md)

## Folder `figures/`

Wykresy i tabele wygenerowane skryptem `src/training/compare_models.py` —
materiał do bezpośredniego wstawienia w pracę. Po rozszerzeniu datasetu (2026-05-08)
artefakty wygenerowane od nowa, stara wersja zachowana w `figures_pre_extension/`:
- `comparison_table.md`, `comparison_summary.json` — metryki globalne 4 modeli
- `per_file_test.md` — accuracy per filmik testowy
- `error_breakdown.md` — typologia błędów (L↔R vs FLIGHT↔STANCE)
- `confusion_matrices_test.png` — macierze pomyłek (heatmapy)
- `learning_curves_lstm.png` — krzywe uczenia run 1 vs run 2
- `feature_importances_rf.png` — TOP-15 cech RF v1 i RF v2

## Folder `figures_pre_extension/`

Backup artefaktów z rozdziału 5.4 (2026-04-26) — przed dodaniem Pawła i Adama do trainu.
Materiał porównawczy "przed/po" do podrozdziału 5.5 pracy.
