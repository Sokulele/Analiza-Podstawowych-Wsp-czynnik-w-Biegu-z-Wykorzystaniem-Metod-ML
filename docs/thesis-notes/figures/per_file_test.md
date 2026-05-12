# Porównanie modeli — accuracy per filmik testowy

| Film | n RF / LSTM | RF v1 | RF v2 | LSTM run 1 | LSTM run 2 |
| --- | --- | --- | --- | --- | --- |
| **02** — Running at 13 km/h — boczne ujęcie| 300 / 286| 51.7%| 63.0%| 54.9%| 50.7% |
| **20** — Walk → run, 0.8–3.5 m/s| 870 / 856| 63.7%| 68.6%| 68.1%| 66.9% |
| **22** — Physiotherapist demo — pionowe wideo| 320 / 306| 70.3%| 66.6%| 75.8%| 74.2% |

## F1 macro per-film

| Film | RF v1 | RF v2 | LSTM run 1 | LSTM run 2 |
| --- | --- | --- | --- | --- |
| **02** — Running at 13 km/h — boczne ujęcie| 0.422| 0.614| 0.521| 0.495 |
| **20** — Walk → run, 0.8–3.5 m/s| 0.634| 0.684| 0.673| 0.661 |
| **22** — Physiotherapist demo — pionowe wideo| 0.644| 0.669| 0.740| 0.725 |
