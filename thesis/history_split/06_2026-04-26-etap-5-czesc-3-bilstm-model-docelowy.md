# 2026-04-26 — Etap 5, część 3: BiLSTM (model docelowy)

**Opis dla agenta:** BiLSTM, dwa runy, wybór LSTM run 2 jako primary przed późniejszymi zmianami

**Słowa kluczowe:** BiLSTM, LSTM, run 1, run 2, primary, PyTorch

---

## 2026-04-26 — Etap 5, część 3: BiLSTM (model docelowy)

### Zrobione

- **`src/training/train_lstm.py`** — BiLSTM PyTorch na oknie 15 klatek, target = klatka środkowa, bidirectional, dropout, StandardScaler na train, early stopping na val loss
- Dodane `torch>=2.0.0` (CPU-only) do `requirements.txt`
- **Dwa runy** (świadoma decyzja metodologiczna — patrz notatka thesis):
  - Run 1 (h=128, lr=1e-3, dropout=0.3): early stop @ epoka 1 → klasyczny overfit, **odrzucony jako primary**, zachowany w `models/lstm_run1_overfit/`
  - Run 2 (h=64, lr=3e-4, dropout=0.4, wd=1e-4): best @ epoka 2, plateau val_loss ep 2-5 → **wybrany jako primary**, w `models/lstm_primary/`

### Wyniki (LSTM run 2 = primary)

| Split | accuracy | F1 macro |
| --- | --- | --- |
| Val | 80.4% | 0.801 |
| **Test** | **64.9%** | **0.637** |

### Porównanie 4 modeli na test

| Model | Test acc | Test F1 macro | Luka val→test |
| --- | --- | --- | --- |
| RF v1 (raw) | 59.0% | 0.583 | 21.6 p.p. |
| RF v2 (engineered) | 61.0% | 0.611 | 18.4 p.p. |
| LSTM run 1 (h=128, overfitted) | 66.0% | 0.658 | 12.3 p.p. |
| **LSTM run 2 (primary)** | **64.9%** | **0.637** | **15.5 p.p.** |

LSTM bije oba RF o 4-5 p.p. test acc — kontekst czasowy faktycznie pomaga. Hipoteza 82-90% **niespełniona** — sufit ~65% niezależnie od architektury.

### Per-film test (LSTM run 2 vs RF v2)

| Film | RF v2 | LSTM run 2 | Δ |
| --- | --- | --- | --- |
| 02 | 63.7% | 64.0% | +0.3 |
| 20 | 61.1% | 65.1% | +4.0 |
| 22 | 58.1% | 65.0% | +6.9 |

LSTM run 2 jest **co najmniej tak dobry jak RF v2 na każdym filmie**, najbardziej zbalansowany między filmami (range 64.0-65.1).

### Kluczowe obserwacje

1. **Run 1 vs run 2 jako case study** — run 1 ma marginalnie wyższy test (66 vs 65%), ale early stop @ ep 1 to zła reprezentacja zdolności LSTM. Run 2 ma 4 epoki plateau val_loss = walidowana zdolność do nauki. Wybrany run 2 mimo niższego globalnego test.
2. **Mylenie L↔R**: RF v1 185 → RF v2 95 → **LSTM run 2 101**. LSTM trochę pogorszył vs RF v2 (+6 klatek, w granicach szumu).
3. **Mylenie FLIGHT↔STANCE**: RF v1 426 → RF v2 486 → **LSTM run 2 408** (−16% vs RF v2). Kontekst czasowy pomaga rozróżnić moment kontaktu.
4. **Bug filmu 22 — FLIGHT recall = 4%** w obu runach LSTM — ten sam patologiczny wzorzec niezależnie od architektury. Confirmed: bug aspect ratio (608×1080 vs ~16:9 train), torso_length zawyżony → wszystkie cechy znormalizowane skompresowane → model nie rozpoznaje FLIGHT.
5. **Sufit ~65% test mimo 3 architektur** — silny dowód że problem leży w danych/etykietach/aspect ratio, nie w modelu

### Hipotezy z briefu

| Hipoteza | Wynik | Ocena |
| --- | --- | --- |
| Test acc 82-90% | 64.9% | ❌ niespełniona |
| Zamknie lukę FLIGHT↔STANCE | 486 → 408 (−16%) | 🟢 częściowo spełniona |
| Nie pogorszy mylenia L↔R | 95 → 101 | 🟡 na granicy |

### Materiał do pracy magisterskiej

- Notatka thesis: `docs/thesis-notes/2026-04-26-lstm-primary.md`
- Run 1 vs run 2 jako ilustracja procesu badawczego (overfitting jako lesson learned)
- Sufit ~65% w trzech architekturach jako uzasadnienie sekcji "limitations"
- Bug aspect ratio jako kandydat na osobny podrozdział i kierunek przyszłej pracy

### Do zrobienia w następnej sesji

1. **Sesja 3: analiza porównawcza** — ujednolicony raport 3 modeli, wizualizacje (krzywe uczenia, confusion matrices side-by-side), tabele do wstawienia w pracę
2. (alternatywa) **Naprawa aspect ratio bug** — pomnożenie x, y przez (width, height) z metadanych przed normalizacją; retrening RF v2 + LSTM; oczekiwany zysk +3-7 p.p. test

### Odkładane decyzje

- Czy uruchomić sesję 3 jako "tylko porównanie istniejących" (~1h) vs "porównanie + naprawa aspect ratio" (~2-3h)
- Wersjonowanie `models/` (rośnie — teraz 2× LSTM + 2× RF + scalery)
- Hyperparameter sweep dla LSTM (low priority — sufit jest gdzie indziej)

---
