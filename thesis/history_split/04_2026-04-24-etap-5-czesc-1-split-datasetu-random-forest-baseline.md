# 2026-04-24 — Etap 5 (część 1): Split datasetu + Random Forest baseline

**Opis dla agenta:** Split train/val/test i pierwszy baseline Random Forest na surowych keypointach

**Słowa kluczowe:** Random Forest, RF baseline, split_data, metrics, confusion matrix

---

## 2026-04-24 — Etap 5 (część 1): Split datasetu + Random Forest baseline

### Zrobione

- **`src/training/split_data.py`** — podział per filmik wg briefu. Output `data/splits.json`
  - Train (8 filmów, 5811 kl., 72.3%): 01, 06, 08 seg1, 08 seg2, 09 seg1, 15, 19, Running at 4ms
  - Val (2 filmy, 738 kl., 9.2%): 03, 09 seg2
  - Test (3 filmy, 1490 kl., 18.5%): 02, 20, 22
  - 02/03 rozdzieleni (ten sam biegacz) — 03 w val, 02 w test ✓
  - Klasy: tylko 3 (LEFT_STANCE / RIGHT_STANCE / FLIGHT), brak DOUBLE_SUPPORT
- **`src/training/train_rf.py`** — RF na 132 cechach (33 keypointy × x,y,z,visibility)
  - `RandomForestClassifier(n_estimators=300, class_weight="balanced", seed=42)`
  - Zapisuje model (`models/rf_baseline/model.joblib`) + metryki (`metrics.json`)
- **Dodano do requirements**: `scikit-learn>=1.3.0`, `joblib>=1.3.0`

### Wyniki RF baseline (n_estimators=300, class_weight=balanced, 132 cechy)

| Split | accuracy | F1 macro | Uwagi |
| --- | --- | --- | --- |
| VAL (03 + 09 seg2) | **80.6%** | 0.803 | powyżej oczekiwanych >80% z briefu |
| TEST (02 + 20 + 22) | **59.0%** | 0.583 | duża luka vs val |
| TEST[02] | 47.0% | 0.352 | mylenie RIGHT_STANCE→LEFT_STANCE (recall RIGHT=0.07) |
| TEST[20] | 60.9% | 0.605 | najbardziej zrównoważony |
| TEST[22] | 65.0% | 0.605 | pionowe wideo, radzi sobie OK |

**Confusion matrix TEST (rows=true):**

```
             FLIGHT  L_STANCE  R_STANCE
FLIGHT          203       192        81
LEFT_STANCE      74       372        79
RIGHT_STANCE     79       106       304
```

### Kluczowe obserwacje

- **Luka VAL(81%) → TEST(59%)** to silny sygnał overfittingu do absolutnych pozycji w kadrze
- **TOP feature importances**: wszystkie to `_y` stóp (ankle_y, foot_index_y, heel_y) — sensowne biomechanicznie. Ale też `visibility` barków/ust/kciuków — to artefakty kadrowania, nie pozy
- **Film 02 rozbity**: RIGHT_STANCE klasyfikowane jako LEFT_STANCE (tylko 6/87 poprawnych). To sugeruje, że model nauczył się absolutnych współrzędnych x/y biegacza w kadrze — gdy 02 ma biegacza w innej pozycji horyzontalnej niż train set, model się gubi
- MediaPipe zwraca x,y znormalizowane (0-1) **względem całego kadru**, nie względem biegacza — więc gdy kamera ma inny kadr/aspect ratio, "lewa" i "prawa" stopa mają różne absolutne x

### Hipotezy do testów (do konsultacji z użytkownikiem)

1. **Normalizacja względem biegacza** — odjąć mid_hip, przeskalować długością tułowia. Tanie, powinno znacząco pomóc
2. **Wyrzucić visibility** — `--no-visibility` (99 cech) — sprawdzić czy visibility mouth/thumb to faktyczny szum
3. **Cechy inżynierowane** — kąty stawów, odległości stopa-biodro (invariant na kadr) zamiast surowych keypointów
4. **Więcej danych** — train 8 filmów, ~10 unikalnych biegaczy, to mało. Pytanie czy zwiększenie datasetu vs. lepsze cechy da większy zysk

### Do zrobienia w następnej sesji

- Najpierw: normalizacja cech względem biegacza (pkt 1 wyżej) — sprawdzić czy zamyka lukę val↔test
- Dopiero potem decyzja: LSTM/1D-CNN vs. cechy inżynierowane
- **LSTM wstrzymany** — czekamy aż baseline się ustabilizuje

---
