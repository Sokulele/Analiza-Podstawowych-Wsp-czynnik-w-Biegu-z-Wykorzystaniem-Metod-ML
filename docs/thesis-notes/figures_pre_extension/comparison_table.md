# Porównanie modeli — metryki globalne

| Model | Cechy | n train / val / test | Val acc | Val F1 | Test acc | Test F1 | Luka val→test |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RF v1 (raw) | 132 | 5811 / 737 / 1490 | 80.6% | 0.803 | **59.0%** | **0.583** | 21.6 p.p. |
| RF v2 (engineered) | 106 | 5811 / 737 / 1490 | 79.4% | 0.792 | **61.0%** | **0.611** | 18.4 p.p. |
| LSTM run 1 (h=128, overfit) | 106 | 5699 / 709 / 1448 | 78.3% | 0.780 | **66.0%** | **0.658** | 12.3 p.p. |
| LSTM run 2 (primary) | 106 | 5699 / 709 / 1448 | 80.4% | 0.801 | **64.8%** | **0.637** | 15.5 p.p. |

Uwaga: LSTM ma mniej okien niż RF ma klatek (po 7 z każdej strony pliku odpada — krawędzie okna 15). Test RF n=1490 vs test LSTM n=1448 (Δ 42).
