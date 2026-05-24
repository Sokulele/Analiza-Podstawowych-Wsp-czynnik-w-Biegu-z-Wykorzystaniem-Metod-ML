# 2026-05-08 — Rozszerzenie datasetu o 2 biegaczy (23, 24) + retrening 4 modeli

**Opis dla agenta:** Rozszerzenie datasetu o Pawła i Adama, retrening modeli, wpływ większego train setu

**Słowa kluczowe:** Pawel, Adam, dataset extension, retraining, 5.5

---

## 2026-05-08 — Rozszerzenie datasetu o 2 biegaczy (23, 24) + retrening 4 modeli

### Decyzja sesji

Dodanie 2 własnych filmów (Pawel, Adam) do datasetu, oba do TRAIN, test bez zmian (porównywalność z 5.4). Pełny pipeline: ekstrakcja → auto-etykietowanie → split update → retrening wszystkich 4 modeli → re-run compare_models.py.

### Zrobione

- **Resize 4K Pawła → 720p** (ffmpeg, oryginał w `data/videos/_originals_4k/`)
- **Rozszerzenie skryptów** `probe_videos.py` i `extract_keypoints.py` o glob `*.mov`
- **Ekstrakcja keypointów** (MediaPipe complexity=2, savgol 11/3): Pawel 100% detekcji (WARN — vis 0.79, low_vis 13.9%), Adam 100% (OK — vis 0.88, low_vis 3.1%)
- **Auto-etykietowanie peak-based**: Pawel 154.7 spm L/R 71/72; Adam 167.5 spm L/R 112/112 (idealna symetria)
- **Wycięcie pierwszych 80 klatek Adama** (artefakt brzegowy peak-based — LEFT_STANCE bez peaka), backup w `data/keypoints/_originals_pre_trim/`
- **`split_data.py`** zaktualizowany — 23 i 24 dodane do TRAIN: 8 → 10 plików, **5811 → 9779 klatek (+68%)**
- **Backup 4 modeli + figures** do `models/*_pre_extension/` i `docs/thesis-notes/figures_pre_extension/`
- **Retrening 4 modeli** bez zmian hiperparametrów: RF v1, RF v2, LSTM run 1 (h=128), LSTM run 2 primary (h=64)
- **Re-run `compare_models.py`** — nowe artefakty w `figures/`
- **Notatka thesis**: `docs/thesis-notes/2026-05-08-dataset-extension.md`

### Wyniki retreningu — globalnie

| Model | Test acc (przed → po) | Δ | F1 macro | Luka val→test |
| --- | --- | --- | --- | --- |
| RF v1 (raw) | 59.0 → **62.7%** | +3.7 | 0.62 | 21.6 → 19.3 p.p. |
| RF v2 (engineered) | 61.0 → **67.0%** | **+6.0** | 0.67 | 18.4 → **12.9** p.p. |
| LSTM run 1 (h=128) | 66.0 → **67.1%** | +1.1 | 0.66 | 12.3 → 19.3 p.p. |
| LSTM run 2 (primary) | 64.9 → 65.3% | +0.5 | 0.65 | 15.5 → 19.2 p.p. |

### Per-film test (najistotniejsze)

| Film | RF v1 | RF v2 | LSTM r1 | LSTM r2 |
| --- | --- | --- | --- | --- |
| 02 | +4.7 | −0.7 | −1.4 | **−13.3** |
| 20 | +2.8 | **+7.5** | +0.3 | +1.8 |
| **22 (aspect ratio bug)** | **+5.3** | **+8.5** | **+5.5** | **+9.2** |

### Kluczowe obserwacje

1. **Sufit przesunięty z ~65% do ~67%** (+2 p.p.), ale dalej istnieje. 4 architektury × 2 rozmiary trainu utykają w tym samym miejscu — silniejszy dowód że problem w danych/etykietach
2. **RF v2 wygrał rozszerzenie** (+6 p.p., luka val→test do 12.9 p.p. — najmniejsza). Konkurencyjny z LSTM (67.0 vs 65.3-67.1) — częściowa rewizja wniosku rozdziału 5.4 "LSTM bije RF dzięki kontekstowi czasowemu"
3. **LSTM ledwo drgnęły** mimo +69% okien — h=64 niedouczone, h=128 wciąż overfit od ep 4. Niemożność wykorzystania extra danych
4. **Film 22 najwięcej zyskał** wszędzie (~+7 p.p. średnio) — Pawel/Adam (16:9, 720p+) **częściowo zniwelowali aspect ratio bug** przez różnorodność w trainie
5. **Film 02 dramatycznie spadł dla LSTM r2 (−13.3 p.p.)** — LSTM wrażliwy na zmianę dystrybucji trainu. Argument **przeciwko** zostawieniu r2 jako primary, ale val_loss plateau dalej stabilniejsze niż r1
6. **Luka val→test odwróciła trend**: kurczy się dla RF, rośnie dla LSTM — val (filmy 03, 09 seg2) blisko Pawła/Adama dystrybucyjnie

### Materiał do pracy magisterskiej

- Podrozdział **5.5 "Wpływ rozszerzenia datasetu"** — naturalne rozszerzenie 5.4 bez nadpisywania
- Stara analiza 5.4 zostaje (`figures_pre_extension/`) jako baseline
- Sekcja **Limitations**: silniejszy argument o sufit (4 archit. × 2 rozmiary trainu wszystkie ~67%); aspect ratio bug **częściowo** rozwiązany — full fix nadal kandydatem na future work
- Run 2 dalej rekomendowany jako primary (stabilniejsze plateau val_loss), choć argument słabszy

### Do zrobienia w następnej sesji

1. **Etap 6 (obliczanie współczynników)** — najsensowniejszy następny krok. Nowy klasyfikator (RF v2 67% lub LSTM r1 67.1%) jako wejście do inferencji wideo→fazy→współczynniki
2. (alternatywa) **Naprawa aspect ratio bug** — częściowo zniwelowany różnorodnością, ale full fix nadal ciekawy. Spodziewany dodatkowy zysk: +1-3 p.p. (zamiast wcześniej szacowanych +3-7)
3. (opcjonalnie) Hyperparameter sweep LSTM (h=96, dropout=0.35) — niski priorytet, sufit nie jest tam

### Odkładane decyzje (bez zmian)

- Wersjonowanie `models/` (rośnie — teraz 8 modeli z backupami)
- Ręczna walidacja etykiet
- Pełen retrening LSTM z większym hidden_size jako follow-up

---
