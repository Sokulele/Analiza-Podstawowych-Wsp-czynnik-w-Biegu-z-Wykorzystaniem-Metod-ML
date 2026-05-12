# Porównanie modeli — accuracy per filmik testowy

| Film | n RF / LSTM | RF v1 | RF v2 | LSTM run 1 | LSTM run 2 |
| --- | --- | --- | --- | --- | --- |
| **02** — Running at 13 km/h — boczne ujęcie| 300 / 286| 47.0%| 63.7%| 56.3%| 64.0% |
| **20** — Walk → run, 0.8–3.5 m/s| 870 / 856| 60.9%| 61.1%| 67.8%| 65.1% |
| **22** — Physiotherapist demo — pionowe wideo| 320 / 306| 65.0%| 58.1%| 70.3%| 65.0% |

## F1 macro per-film

| Film | RF v1 | RF v2 | LSTM run 1 | LSTM run 2 |
| --- | --- | --- | --- | --- |
| **02** — Running at 13 km/h — boczne ujęcie| 0.352| 0.609| 0.558| 0.623 |
| **20** — Walk → run, 0.8–3.5 m/s| 0.605| 0.614| 0.670| 0.640 |
| **22** — Physiotherapist demo — pionowe wideo| 0.605| 0.571| 0.575| 0.549 |
