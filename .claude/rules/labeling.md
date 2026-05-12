---
globs: src/labeling/**
---

# Auto-etykietowanie faz biegu

## Algorytm: peak-based (zaimplementowany w auto_label.py)

Progowanie Y_heel okazało się niewystarczające (faza lotu = 2–3 klatki przy 30 FPS, asymetria L/R z kąta kamery). Finalne podejście:

1. **Sygnał kontaktu**: max(heel_y, foot_index_y) per stopa — obejmuje cały cykl od heel strike do toe-off
2. **Detekcja foot strikes**: scipy.signal.find_peaks(distance=12, prominence=0.03) per stopa
3. **Wymuszenie alternacji L-R**: jeśli dwa peaki tej samej stopy z rzędu — zachowaj wyższą prominence
4. **Podział na fazy**: między peakami szukaj min(max(L,R)) = centrum FLIGHT. Reszta = STANCE.
   - flight_fraction=0.4 (40% interwału między peakami to FLIGHT)
5. **Filtr medianowy**: kernel=3 (w praktyce zmienia 0 klatek — peak-based jest już czysty)
6. **Kierunek biegu**: NOSE_x vs mid_HIP_x → jeśli biegacz biegnie w lewo, zamień LEFT/RIGHT

## Dawne podejście (odrzucone)
Proste progowanie Y_heel vs ground_level + threshold nie działało:
- Threshold 0.02 za ciasny → 70% FLIGHT
- Heel_y sam ma za dużą asymetrię L/R (artefakt kąta kamery)
- Filtr medianowy kernel=5 kasował krótkie segmenty FLIGHT

## Format wyjściowy
- Kolumna `phase_auto` (surowa etykieta) i `phase` (po filtrze medianowym) dopisane do CSV z keypointami
