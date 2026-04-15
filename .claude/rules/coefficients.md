---
globs: src/coefficients/**
---

# Obliczanie współczynników biegu

## Współczynniki z faz
- Kadencja: (liczba_kroków / czas_trwania_s) * 60 [kroki/min]
- Czas kontaktu (GCT): klatki_w_stance * (1/FPS) [s] — oblicz osobno dla L i R
- Czas lotu: klatki_w_flight * (1/FPS) [s]
- Stride length: prędkość_bieżni_m_s * czas_cyklu_s [m] — wymaga inputu od użytkownika
- Duty factor: GCT / czas_cyklu — wartość 0-1

## Współczynniki z keypointów
- Kąty stawów: użyj np.arctan2() na wektorach między keypointami, wynik w stopniach
  - Kolano: biodro → kolano → kostka
  - Biodro: ramię → biodro → kolano
  - Kostka: kolano → kostka → palce stopy
- Pochylenie tułowia: kąt linii (mid_hip → mid_shoulder) względem pionu
- Vertical oscillation: max(Y_hip) - min(Y_hip) w obrębie jednego cyklu, przelicz na cm (wymaga kalibracji)
- Overstriding: odległość X między ankle a hip w momencie initial contact
- Foot strike: kąt stopy (heel vs foot_index) w momencie kontaktu

## Kalibracja piksel→metr
- Jeśli znamy wzrost biegacza — stosunek pikseli do metrów z odległości hip-ankle
- Jeśli nie — podajemy wartości w jednostkach znormalizowanych i zaznaczamy to

## Ważne
- ZAWSZE obliczaj na WYGŁADZONYCH keypointach
- Podawaj mean ± std dla każdego współczynnika (nie tylko jedną wartość)
- Obliczaj osobno dla lewej i prawej nogi (symetria)
