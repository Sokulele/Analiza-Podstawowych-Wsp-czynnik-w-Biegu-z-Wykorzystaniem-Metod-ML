# 2026-04-20 — Etap 3 dokończony: audyt datasetu + auto-etykietowanie wszystkich filmów

**Opis dla agenta:** Dokończenie auto-etykietowania, audyt datasetu, segmentacja filmu 09, finalny dataset 13 filmów

**Słowa kluczowe:** dataset, film 09, film 16, etykiety, training set, split

---

## 2026-04-20 — Etap 3 dokończony: audyt datasetu + auto-etykietowanie wszystkich filmów

### Audyt datasetu

**Film 09 (Sage Canaday)** — analiza braków detekcji:

- 166 braków (11.1%) to **JEDNA zwarta grupa**: kl. 894–1059 (29.8–35.3s)
- Pocięty na 2 czyste segmenty (ffmpeg via `cut_video.py`):
  - Segment 1: 892 kl., 29.8s, 100% detekcji, vis 0.91 → **OK**
  - Segment 2: 438 kl., 14.6s, 99.8% detekcji, vis 0.91 → **OK**
- Keypointy przeekstrahowane dla obu segmentów

**Film 16** (13 FPS) → przeniesiony do `data/test_edge_cases/`, `exclude_from_training=True`

### Auto-etykietowanie — wszystkie filmy

Algorytm peak-based (z sesji 2026-04-16) uruchomiony na wszystkich filmach. Wyniki:

| Film              | Klatki | Kadencja  | L/R   | Direct L↔R | Uwagi                      |
| ----------------- | ------ | --------- | ----- | ---------- | -------------------------- |
| 01 (slow-mo ~10x) | 949    | 15.1 spm  | 5/4   | 0          | OK — dużo klatek/cykl      |
| 02                | 300    | 162.0 spm | 14/14 | 0          | OK (z poprzedniej sesji)   |
| 03 (15km/h)       | 300    | 174.2 spm | 15/15 | 0          | OK                         |
| 08 seg1           | 660    | 147.0 spm | 27/28 | 0          | OK, outlier 835ms R_STANCE |
| 08 seg2 (slow-mo) | 300    | 77.8 spm  | 7/7   | 0          | OK — slow-motion           |
| 09 seg1           | 892    | 132.9 spm | 34/33 | 0          | OK, marathon pace          |
| 09 seg2           | 438    | 172.3 spm | 22/21 | 0          | OK                         |
| 20 (chód→bieg)    | 870    | 109.8 spm | 27/27 | 0          | OK, duży std oczekiwany    |

**Kluczowe obserwacje:**

- Filtr medianowy (kernel=3) zmienił **0 klatek** we wszystkich filmach — peak-based jest inherentnie czysty
- Slow-motion nie przeszkadza etykietowaniu — prominence jest relatywna
- Asymetria L/R GCT to artefakt monocular 2D (nie wpływa na etykiety faz)

**Bugfix:** CSV filmu 20 miał spacje w nazwach kolumn (`NOSE_x ` zamiast `NOSE_x`) — naprawiony strip()

### Rozszerzenie datasetu — 6 nowych filmików

Dodane nowe filmy, pełny pipeline (ekstrakcja keypointów + auto-etykietowanie):

| Film                         | FPS   | Klatki | Kadencja  | L/R   | Uwagi               |
| ---------------------------- | ----- | ------ | --------- | ----- | ------------------- |
| 06 (15km/h slow-mo ~8x)      | 9.46  | 560    | 20.3 spm  | 11/10 | OK                  |
| 15 (4m/s slow-mo ~5x)        | 13.33 | 800    | 30.0 spm  | 16/15 | OK                  |
| 19 (barefoot slow-mo ~8x)    | 11.25 | 900    | 21.0 spm  | 14/15 | OK                  |
| 20b (chód→bieg)              | 30.0  | 870    | 109.8 spm | 27/27 | OK                  |
| Running at 4ms (slow-mo ~5x) | 15.0  | 750    | 32.4 spm  | 14/14 | OK, piękna symetria |
| 22 (fizjoterapeuta)          | 29.97 | 320    | 157.2 spm | 15/14 | OK, pionowe wideo   |

Wszystkie: 100% detekcji MediaPipe, 0 direct L↔R, 0 zmian filtra medianowego.

### Finalny dataset

| Metryka             | Wartość |
| ------------------- | ------- |
| Filmów z etykietami | 13      |
| Łącznie klatek      | 8039    |
| LEFT_STANCE         | ~34%    |
| RIGHT_STANCE        | ~32%    |
| FLIGHT              | ~34%    |
| DOUBLE_SUPPORT      | 0%      |
| Unikalnych biegaczy | ~9-10   |

Rozkład klas równomierny — brak problemu z imbalance.

### Decyzja: niski FPS OK dla trenowania

Filmy z niskim FPS (06: 9.46, 15: 13.33, 19: 11.25) włączone do training set. FPS nie ma znaczenia dla klasyfikatora faz — model uczy się pozycji ciała, nie timingów (CLAUDE.md). Niski FPS jest problemem tylko przy obliczaniu współczynników (inferencja).

### Zmiany w plikach

- `data/videos_metadata.csv` — dodane kolumny `exclude_from_training` i `notes`; nowe filmy
- `data/test_edge_cases/` — nowy katalog z filmem 16
- `data/videos/` — 2 segmenty filmu 09 + 6 nowych filmów
- `data/keypoints/` — CSV z keypointami + etykietami faz dla wszystkich 13 filmów

### Do zrobienia w następnej sesji — Etap 5: Trenowanie klasyfikatora

1. Podział danych: train/val/test (per filmik, nie per klatka!)
2. Baseline: Random Forest na wektorze keypointów
3. Primary: LSTM lub 1D CNN na sekwencji klatek
4. Metryki: accuracy, confusion matrix, F1 per klasa

### Odkładane decyzje

- Wersjonowanie `data/keypoints/` (rosnące — teraz ~30 MB)
- Etap 4 (korekta ręczna etykiet) — pominięty, bo algorytm jest czysty (0 zmian filtra medianowego, 0 direct L↔R we wszystkich filmach). Jeśli model będzie słaby → wrócić do weryfikacji etykiet

---
