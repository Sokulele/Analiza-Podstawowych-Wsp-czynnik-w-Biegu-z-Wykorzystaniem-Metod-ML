# Postprocessing median filter — krok 2 planu accuracy improvements

Generated: 2026-05-08 (krok 2)

## Globalne accuracy / F1 macro vs kernel size

| Model | baseline | k=3 | k=5 | k=7 | k=9 | best |
|---|---|---|---|---|---|---|
| RF v1 (raw) | acc=0.627 F1=0.617 | acc=0.623 F1=0.612 (-0.40pp) | acc=0.618 F1=0.606 (-0.87pp) | acc=0.589 F1=0.567 (-3.76pp) | acc=0.536 F1=0.475 (-9.06pp) | baseline |
| RF v2 (engineered) | acc=0.670 F1=0.671 | acc=0.678 F1=0.678 (+0.74pp) | acc=0.666 F1=0.666 (-0.40pp) | acc=0.630 F1=0.625 (-4.09pp) | acc=0.565 F1=0.546 (-10.54pp) | k=3 (0.678, +0.74pp) |
| LSTM run 1 (h=128) | acc=0.671 F1=0.663 | acc=0.670 F1=0.661 (-0.14pp) | acc=0.651 F1=0.636 (-2.07pp) | acc=0.566 F1=0.504 (-10.57pp) | acc=0.552 F1=0.472 (-11.88pp) | baseline |
| LSTM run 2 (primary) | acc=0.653 F1=0.645 | acc=0.651 F1=0.643 (-0.14pp) | acc=0.622 F1=0.607 (-3.11pp) | acc=0.565 F1=0.513 (-8.77pp) | acc=0.554 F1=0.462 (-9.88pp) | baseline |

## Per-film accuracy (best kernel each model)

| Model | best k | film 02 | film 20 | film 22 |
|---|---|---|---|---|
| RF v1 (raw) | baseline | 0.517 (+0.00pp) | 0.637 (+0.00pp) | 0.703 (+0.00pp) |
| RF v2 (engineered) | k=3 | 0.630 (+0.00pp) | 0.689 (+0.23pp) | 0.694 (+2.81pp) |
| LSTM run 1 (h=128) | baseline | 0.549 (+0.00pp) | 0.681 (+0.00pp) | 0.758 (+0.00pp) |
| LSTM run 2 (primary) | baseline | 0.507 (+0.00pp) | 0.669 (+0.00pp) | 0.742 (+0.00pp) |

## Interpretacja

Median filter wymusza lokalną spójność etykiet w czasie. Pojedyncze migotania
(1-2 klatki anomalii) są usuwane, ale długie segmenty zachowane. Filtr działa
PER FILMIK (granice filmów respektowane — nie crossuje plików).

Spodziewany efekt:
- Zmniejszenie L↔R direct transitions (typowy artefakt 1-2 klatkowy)
- Marginalny wpływ na FLIGHT↔STANCE (te błędy często są dłuższymi segmentami)
- Większe kernele (k≥7) mogą zacząć usuwać krótkie poprawne segmenty FLIGHT (~3-4 klatki przy 30 FPS)