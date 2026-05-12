# Postprocessing median filter — krok 2 planu accuracy improvements

Generated: 2026-05-08 (krok 2)

## Globalne accuracy / F1 macro vs kernel size

| Model | baseline | k=3 | k=5 | best |
|---|---|---|---|---|
| RF v1 (raw) | acc=0.627 F1=0.617 | acc=0.623 F1=0.612 (-0.40pp) | acc=0.618 F1=0.606 (-0.87pp) | baseline |
| RF v2 (engineered) | acc=0.657 F1=0.650 | acc=0.652 F1=0.644 (-0.54pp) | acc=0.633 F1=0.621 (-2.42pp) | baseline |
| LSTM run 1 (h=128) | acc=0.664 F1=0.664 | acc=0.664 F1=0.663 (-0.07pp) | acc=0.657 F1=0.656 (-0.76pp) | baseline |
| LSTM run 2 (primary) | acc=0.660 F1=0.655 | acc=0.657 F1=0.652 (-0.28pp) | acc=0.637 F1=0.629 (-2.28pp) | baseline |

## Per-film accuracy (best kernel each model)

| Model | best k | film 02 | film 20 | film 22 |
|---|---|---|---|---|
| RF v1 (raw) | baseline | 0.517 (+0.00pp) | 0.637 (+0.00pp) | 0.703 (+0.00pp) |
| RF v2 (engineered) | baseline | 0.603 (+0.00pp) | 0.632 (+0.00pp) | 0.775 (+0.00pp) |
| LSTM run 1 (h=128) | baseline | 0.549 (+0.00pp) | 0.703 (+0.00pp) | 0.663 (+0.00pp) |
| LSTM run 2 (primary) | baseline | 0.549 (+0.00pp) | 0.683 (+0.00pp) | 0.699 (+0.00pp) |

## Interpretacja

Median filter wymusza lokalną spójność etykiet w czasie. Pojedyncze migotania
(1-2 klatki anomalii) są usuwane, ale długie segmenty zachowane. Filtr działa
PER FILMIK (granice filmów respektowane — nie crossuje plików).

Spodziewany efekt:
- Zmniejszenie L↔R direct transitions (typowy artefakt 1-2 klatkowy)
- Marginalny wpływ na FLIGHT↔STANCE (te błędy często są dłuższymi segmentami)
- Większe kernele (k≥7) mogą zacząć usuwać krótkie poprawne segmenty FLIGHT (~3-4 klatki przy 30 FPS)