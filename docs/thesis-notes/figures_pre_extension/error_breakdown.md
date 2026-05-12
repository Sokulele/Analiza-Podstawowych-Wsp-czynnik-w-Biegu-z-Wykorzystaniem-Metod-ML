# Analiza typów błędów na test

Z macierzy pomyłek 3×3 (FLIGHT / LEFT_STANCE / RIGHT_STANCE) wyróżniamy dwie kategorie błędów:

- **L↔R**: pomyłki między LEFT_STANCE a RIGHT_STANCE — najgorszy typ błędu, bo bezpośrednio rujnuje współczynnik symetrii L/R w produkcji
- **FLIGHT↔STANCE**: pomyłki o moment kontaktu z ziemią — przesunięcie GCT/flight time o 1-2 klatki, znacznie mniej dotkliwe

| Model | n test | poprawne | błędy razem | L↔R | FLIGHT↔STANCE | % L↔R w błędach |
| --- | --- | --- | --- | --- | --- | --- |
| RF v1 (raw) | 1490 | 879 | 611 | 185 | 426 | 30.3% |
| RF v2 (engineered) | 1490 | 909 | 581 | 95 | 486 | 16.4% |
| LSTM run 1 (h=128, overfit) | 1448 | 956 | 492 | 67 | 425 | 13.6% |
| LSTM run 2 (primary) | 1448 | 939 | 509 | 101 | 408 | 19.8% |

Dla 3 klas (FLIGHT/L_STANCE/R_STANCE) suma `L↔R` + `FLIGHT↔STANCE` pokrywa wszystkie 6 pól off-diagonal — czyli sumę błędów.
