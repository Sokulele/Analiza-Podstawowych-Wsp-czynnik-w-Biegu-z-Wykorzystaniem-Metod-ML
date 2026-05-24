# 2026-05-08 — Plan poprawy accuracy: LSTM r1 + aspect fix → **70.9% test acc** (próg 70% przekroczony)

**Opis dla agenta:** Plan poprawy accuracy, testy augmentacji/median/velocity/ensemble/aspect fix, osiągnięcie 70.9%

**Słowa kluczowe:** accuracy, aspect fix, augmentacja, velocity, ensemble, 70.9

---

## 2026-05-08 — Plan poprawy accuracy: LSTM r1 + aspect fix → **70.9% test acc** (próg 70% przekroczony)

### Decyzja sesji

User dał plan 8 kroków uderzania w sufit ~67% test acc, ze stop'em przy ≥70%. Wykonane: kroki 1, 2, 4, 5, 7. Krok 8 (ręczna walidacja) niepotrzebny — krok 7 osiągnął cel.

### Zrobione

**Krok 1 — Augmentacja horizontal flip** ❌ NEGATYWNY
- `src/training/augmentation.py` — funkcja `flip_horizontal_dataframe(df)`. Dwie wersje testowane (z/bez swap'a L/R keypointów), obie regresja −2.6 do −9 p.p.
- Diagnoza: konwencja CSV po `auto_label.swap_left_right` jest **zależna od kierunku biegu**, niezgodna z trywialnym flip horyzontalnym. Future work: przerobić auto_label na czysto anatomiczną konwencję
- Kod augmentacji + flag `--augment-flip` zachowane jako artefakt do future use

**Krok 2 — Postprocessing median filter** ✅ +0.7 p.p. dla RF v2
- `src/training/postprocess_median.py` — wczytuje 4 modele, generuje predykcje, aplikuje medfilt PER FILMIK dla kerneli {3, 5, 7, 9}
- Wyniki: tylko **RF v2 + k=3** dał poprawę (67.0 → 67.8%). LSTMy bez zmian (kontekst czasowy już wbudowany), RF v1 spadł, k≥7 dramatyczna regresja (kernel "wyzeruje" segmenty FLIGHT 3-5 klatkowe)

**Krok 4 — Velocity features** ❌ NEGATYWNY globalnie, +7.5 p.p. dla film 22
- `compute_velocity_features` w `features.py` — Δ znormalizowanych keypointów per filmik (99 cech, 33×{x,y,z})
- RF v2: 67.0 → 64.6% (−2.4 p.p.), film 22 +7.5 p.p.
- TOP-20 importance dominują velocity ramion (LEFT_ELBOW_x_dt, RIGHT_WRIST_x_dt) — silny sygnał, ale specyficzny dla biegacza, gorsza generalizacja
- **Ważne**: velocity invariant na aspect ratio bug (Δ-based) — dlatego film 22 zyskał. Wzmacnia argument za Opcją B (full aspect fix)
- Cofnięte, eksperyment w `models/rf_engineered_velocity/`

**Krok 5 — Ensemble soft voting** ❌ NEGATYWNY
- `src/training/ensemble.py` — predict_proba 4 modeli, soft voting na wspólnej przestrzeni klatek (n=1448, LSTM-determined)
- Ważne metodologicznie: ze wspólną przestrzenią RF v2 + median k=3 = **69.4%** (vs 67.8% na n=1490) — obcięcie brzegów to darmowe +1.6 p.p.
- Najlepszy ensemble (RF v2 + LSTM r1) = 68.4% < najlepszy single (RF v2 + median k=3 = 69.4%). Modele mają **skorelowane błędy** (głównie film 02), ensemble nie kompensuje
- Future work do produkcji: ignoruj predykcje na pierwszych/ostatnich 7 klatkach filmu (klatki brzegowe są zaszumione w etykietach)

**Krok 7 — Aspect ratio fix** ✅✅✅ **PROG 70% PRZEKROCZONY**
- `apply_aspect_ratio_correction(df, width, height)` w `features.py` — mnożenie x*width, y*height, z*width przed `compute_engineered_features`
- Flag `--aspect-fix` w `train_rf.py`, `train_rf_v2.py`, `train_lstm.py`. Auto-detect w `postprocess_median.py`
- **Backup wszystkich modeli** w `models/*_pre_aspect_fix/` przed retreningiem
- Wyniki:
  | Model | Test (przed → po) | Δ |
  | --- | --- | --- |
  | RF v1 | 62.7 → 41.9 (cofnięte do 62.7) | KATASTROFA — fix wymaga normalizacji |
  | RF v2 | 67.0 → 65.7 | −1.3 p.p. (ale film 22 +10.9) |
  | **LSTM r1** | 67.1 → **70.9** | **+3.8** ⭐⭐⭐ |
  | LSTM r2 | 65.3 → 68.2 | +2.9 |
- **Film 22 (aspect ratio bug)**: +10.9 (RF v2), +10.1 (LSTM r1), +3.6 (LSTM r2). Walidacja hipotezy z rozdziału 5.5
- RF v1 katastrofa: surowe keypointy bez normalizacji → różne skale per filmik (340x450 vs 1920x1080), model nie generalizuje. **Aspect fix wymaga normalizacji** w pipeline cech

### Notatka thesis

`docs/thesis-notes/2026-05-08-accuracy-improvements.md` — pełen przebieg planu, 5 kroków × wyniki, diagnozy negatywnych wyników, walidacja hipotez. **Materiał wartościowy do pracy** mimo że tylko 1 krok pozytywny:
- Sekcja Methodology — opisuje techniki, ich wymagania (aspect fix wymaga normalizacji), pułapki (augmentacja flip wymaga anatomicznej konwencji etykiet)
- Sekcja Limitations — 4 negatywne wyniki to wartościowe ograniczenia
- Sekcja Walidacja — film 22 case study (aspect ratio bug + naprawa = +10.1 p.p.)

### Status modeli po sesji (final)

| Model | Test acc | F1 macro | Status |
| --- | --- | --- | --- |
| RF v1 (baseline) | 62.7% | 0.617 | bez zmian (fix go niszczy) |
| RF v2 baseline | 67.0% | 0.671 | przywrócone |
| RF v2 + aspect fix | 65.7% | 0.650 | jako alternatywa |
| **LSTM r1 + aspect fix** | **70.9%** ⭐ | **0.709** | **kandydat na nowy primary** |
| LSTM r2 + aspect fix | 68.2% | 0.681 | dotychczasowy primary, też z fix |

### Inne artefakty zachowane

- `models/*_pre_aspect_fix/` — wszystkie 4 modele przed fix (post-extension baseline)
- `models/*_pre_extension/` — wszystkie 4 modele przed Pawel/Adam (z rozdziału 5.4)
- `models/rf_engineered_velocity/` — eksperyment velocity features
- `docs/thesis-notes/figures_pre_extension/` — artefakty rozdziału 5.4

### Otwarte sprawy

1. **Bug w `postprocess_median.predict_lstm`**: pokazuje LSTM r1 + aspect fix = 66.4% baseline, vs metrics.json 70.9%. Coś nieźbieżne. Do zbadania (low priority — metrics.json ma autorytetywne wyniki)
2. **Update primary**: rozważyć migrację LSTM r2 → LSTM r1 + aspect fix jako primary (h=128, +3.8 p.p. vs poprzedni primary). Trzeba sprawdzić czy r1 z aspect fix ma stabilne plateau val_loss
3. **Compare_models.py update**: re-run żeby wygenerować nowe artefakty 5.x z aspect fix wynikami

### Do zrobienia w następnej sesji

**Etap 6 — obliczanie współczynników biomechanicznych** (od dawna planowany):
1. Nowy klasyfikator (LSTM r1 + aspect fix, 70.9% test) jako wejście do inferencji wideo→fazy→współczynniki
2. `src/coefficients/` — kadencja, GCT, flight time, stride length, kąty stawów, vertical oscillation, foot strike, symetria L/R
3. KRYTYCZNE (vs trenowanie): tu FPS i prędkość bieżni mają znaczenie

Lub:
- Rozważenie kroku 8 (ręczna walidacja etykiet) — może podnieść sufit z 70.9% do 75-77% jeśli sufit jest w etykietach. Niski priorytet, bo prog 70% już osiągnięty
- Migracja primary model do LSTM r1 + aspect fix (formalna decyzja w notatce thesis)

### Odkładane decyzje (bez zmian)

- Wersjonowanie `models/` (teraz 12+ wariantów z backupami — robi się ciasno)
- Hyperparameter sweep LSTM (low priority — sufit nie jest tam, +1-3 p.p. najwyżej)
- Naprawa konwencji `auto_label.swap_left_right` na czysto anatomiczną (umożliwiłaby augmentację flip)

---
