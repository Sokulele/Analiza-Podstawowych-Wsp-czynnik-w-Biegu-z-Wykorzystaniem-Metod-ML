# Porównanie modeli — metryki globalne

| Model | Cechy | n train / val / test | Val acc | Val F1 | Test acc | Test F1 | Luka val→test |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RF v1 (raw) | 132 | 9779 / 737 / 1490 | 82.0% | 0.816 | **62.7%** | **0.617** | 19.3 p.p. |
| RF v2 (engineered) | 106 | 9779 / 737 / 1490 | 79.9% | 0.796 | **67.0%** | **0.671** | 12.9 p.p. |
| LSTM run 1 (h=128, overfit) | 106 | 9639 / 709 / 1448 | 86.5% | 0.861 | **67.1%** | **0.663** | 19.3 p.p. |
| LSTM run 2 (primary) | 106 | 9639 / 709 / 1448 | 84.5% | 0.839 | **65.3%** | **0.645** | 19.2 p.p. |

Uwaga: LSTM ma mniej okien niż RF ma klatek (po 7 z każdej strony pliku odpada — krawędzie okna 15). Test RF n=1490 vs test LSTM n=1448 (Δ 42).
