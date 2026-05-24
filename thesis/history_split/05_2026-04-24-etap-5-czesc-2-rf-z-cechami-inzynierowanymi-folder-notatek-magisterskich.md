# 2026-04-24 — Etap 5, część 2: RF z cechami inżynierowanymi + folder notatek magisterskich

**Opis dla agenta:** RF v2 z cechami inżynierowanymi, normalizacja względem biegacza, wnioski do pracy

**Słowa kluczowe:** engineered features, normalizacja, kąty stawów, RF v2, aspect ratio

---

## 2026-04-24 — Etap 5, część 2: RF z cechami inżynierowanymi + folder notatek magisterskich

### Zrobione

- **`docs/thesis-notes/`** — nowy folder na materiał do pracy magisterskiej + reguła auto-zapisu w CLAUDE.md (decyzje, dewagacje, wyniki, ograniczenia są zapisywane proaktywnie)
- **Notatka decyzyjna**: `2026-04-24-decision-option-b.md` — wybór Opcji B (engineered RF → LSTM) vs alternatyw A i C, z uzasadnieniem
- **`src/training/features.py`** — reużywalny moduł: normalizacja (mid_hip + torso length), kąty stawów (6: kolana/biodra/kostki L+R), pochylenie tułowia
- **`src/training/train_rf_v2.py`** — RF na 106 engineered features, te same hiperparametry co baseline
- **Model**: `models/rf_engineered/` (model.joblib + metrics.json)

### Wyniki RF v2 vs baseline

| Metryka | Baseline | RF v2 | Zmiana |
| --- | --- | --- | --- |
| Val accuracy | 80.6% | 79.4% | −1.2 p.p. |
| Test accuracy | **59.0%** | **61.0%** | +2.0 p.p. |
| Test F1 macro | 0.583 | 0.611 | +0.028 |
| Luka val↔test | 21.6 p.p. | 18.4 p.p. | −3.2 p.p. |

Per-film test:
- **Film 02: 47% → 64%** (+17 p.p.) — hipoteza potwierdzona: normalizacja naprawia mylenie L↔R (RIGHT_STANCE recall 7% → 70%)
- Film 20: 61% → 61% (bez zmian)
- **Film 22: 65% → 58%** (−7 p.p.) — nieoczekiwane pogorszenie, przypuszczalnie bug z aspect ratio (pionowe wideo)

### Najważniejsze obserwacje

1. **TOP-3 feature importances to kąty stawów** (right_ankle_angle, left_knee_angle, right_knee_angle) — biomechaniczna walidacja. W baseline top features to były surowe `_y` stóp + visibility ust/kciuków (artefakty). W v2 model patrzy na "co robi noga" przed "gdzie ta noga jest"
2. **Mylenie L↔R spadło o ~50%** (z 185 do 95 klatek off-diagonal L/R). Dla produktu (współczynniki symetrii) to kluczowa metryka
3. **Ale** mylenie FLIGHT↔STANCE wzrosło o ~14%. Model "wymienił" jeden typ błędu na drugi — jakościowo lepszy, bo mniej szkodliwy dla użytkownika końcowego
4. **Hipoteza test 70–78% niespełniona** (61% faktycznie) — normalizacja to nie magic bullet. Reszta luki wynika prawdopodobnie z: brak kontekstu czasowego (wymaga LSTM), szum etykiet peak-based, monocular 2D, bug aspect ratio dla pionowych filmów

### Zidentyfikowane bugi / kierunki naprawcze (do rozważenia po LSTM)

- **Aspect ratio correction**: MediaPipe normalizuje x, y osobno per oś (0-1), więc torso_length w pionowym wideo (film 22) jest zawyżona. Naprawa: wymnożenie współrzędnych przez (width, height) z `videos_metadata.csv` przed normalizacją
- **Z-axis noise**: w monocular side view z jest głównie szumem. Wariant 2D (x, y) może działać lepiej
- **Pierwsze różnice współrzędnych** jako tani kontekst czasowy (bez LSTM)

### Do zrobienia w następnej sesji — Sesja 2: LSTM

- `src/training/train_lstm.py` na tych samych engineered features co RF v2 (okno N=15 klatek, środkowa klatka jako target)
- PyTorch
- Early stopping na val loss
- Porównanie z oboma wariantami RF (naive 59% / engineered 61% / LSTM ?)

### Plan na pracę magisterską (aktualizacja struktury)

Rozdział eksperymentalny ma teraz 3 potwierdzone pozycje:
- 5.1 Baseline (RF naive) — 59% test
- 5.2 RF z cechami inżynierowanymi — 61% test + jakościowa poprawa (L↔R)
- 5.3 LSTM (do zrobienia) — hipoteza 82-90% test dzięki kontekstowi czasowemu
- 5.4 Analiza porównawcza

---
