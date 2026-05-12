"""Etap 6: obliczanie współczynników biomechanicznych biegu.

Pipeline: wideo → MediaPipe → keypointy → klasyfikator faz (LSTM r1 + aspect fix)
→ współczynniki temporalne (kadencja, GCT, flight, duty factor) i przestrzenne
(kąty stawów, pochylenie tułowia, vertical oscillation, foot strike) + symetria L/P.

Stride length jest **świadomie pomijane** w MVP — wymaga inputu użytkownika
(prędkość bieżni). Pozostałe współczynniki nie wymagają tej informacji.
"""
