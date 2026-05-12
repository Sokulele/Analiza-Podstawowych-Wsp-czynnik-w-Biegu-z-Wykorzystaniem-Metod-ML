# Ensemble soft voting + median filter — krok 5 planu

Wspólna przestrzeń klatek: zakres LSTM (half=7 z każdej strony filmu obcięty).
Single-model wyniki **na tej samej przestrzeni** dla fair comparison vs ensemble.

## Single models (baseline na wspólnej przestrzeni)

| Model | acc | F1 macro | +median k=3 | +median k=5 |
|---|---|---|---|---|
| RF v1 (raw) | 0.6354 | 0.6262 | 0.6305 (-0.48pp) | 0.6250 (-1.04pp) |
| RF v2 (engineered) | 0.6872 | 0.6880 | 0.6941 (+0.69pp) | 0.6816 (-0.55pp) |
| LSTM run 1 (h=128) | 0.6713 | 0.6628 | 0.6699 (-0.14pp) | 0.6506 (-2.07pp) |
| LSTM run 2 (primary) | 0.6526 | 0.6449 | 0.6512 (-0.14pp) | 0.6215 (-3.11pp) |

## Ensembles (soft voting probabilistyczny)

| Ensemble | acc | F1 macro | +median k=3 | +median k=5 |
|---|---|---|---|---|
| rf_v2 + lstm_r1 | 0.6837 | 0.6763 | 0.6837 (+0.00pp) | 0.6644 (-1.93pp) |
| rf_v2 + lstm_r2 | 0.6740 | 0.6687 | 0.6727 (-0.14pp) | 0.6533 (-2.07pp) |
| rf_v2 + lstm_r1 + lstm_r2 | 0.6768 | 0.6696 | 0.6754 (-0.14pp) | 0.6595 (-1.73pp) |
| rf_v1 + rf_v2 + lstm_r1 + lstm_r2 | 0.6816 | 0.6735 | 0.6782 (-0.35pp) | 0.6616 (-2.00pp) |

## Per-film (best ensemble + median)

**Best**: ensemble `rf_v2_lstm_r1` (median k=0) → acc 0.6837

| Film | n | accuracy | F1 macro |
|---|---|---|---|
| 02 - Running at 13km⧸h - Side View.csv | 286 | 0.5874 | 0.5652 |
| 20 - Running (0.8 to 3.5 m⧸s)__segment_1 | 856 | 0.6857 | 0.6792 |
| 22 - Running Analysis with Physiotherapi | 306 | 0.7680 | 0.7511 |

## Interpretacja

Soft voting uśrednia probability każdej klasy z N modeli, argmax = predykcja.
Spodziewana wartość: ensemble eksploatuje **różne typy błędów** modeli składowych.
Wymóg: modele składowe muszą mieć **różne** błędy (decorrelated). Jeśli się myli
ten sam zestaw klatek, ensemble nie pomaga.