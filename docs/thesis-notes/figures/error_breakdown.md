# Analiza typów błędów na test

Z macierzy pomyłek 3×3 (FLIGHT / LEFT_STANCE / RIGHT_STANCE) wyróżniamy dwie kategorie błędów:

- **L↔R**: pomyłki między LEFT_STANCE a RIGHT_STANCE — najgorszy typ błędu, bo bezpośrednio rujnuje współczynnik symetrii L/R w produkcji
- **FLIGHT↔STANCE**: pomyłki o moment kontaktu z ziemią — przesunięcie GCT/flight time o 1-2 klatki, znacznie mniej dotkliwe

| Model | n test | poprawne | błędy razem | L↔R | FLIGHT↔STANCE | % L↔R w błędach |
| --- | --- | --- | --- | --- | --- | --- |
| RF v1 (raw) | 1490 | 934 | 556 | 153 | 403 | 27.5% |
| RF v2 (engineered) | 1490 | 999 | 491 | 88 | 403 | 17.9% |
| LSTM run 1 (h=128, overfit) | 1448 | 972 | 476 | 79 | 397 | 16.6% |
| LSTM run 2 (primary) | 1448 | 945 | 503 | 79 | 424 | 15.7% |

Dla 3 klas (FLIGHT/L_STANCE/R_STANCE) suma `L↔R` + `FLIGHT↔STANCE` pokrywa wszystkie 6 pól off-diagonal — czyli sumę błędów.
