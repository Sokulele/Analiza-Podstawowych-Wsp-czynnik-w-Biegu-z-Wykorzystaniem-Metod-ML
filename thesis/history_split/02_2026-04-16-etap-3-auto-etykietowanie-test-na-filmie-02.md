# 2026-04-16 — Etap 3: Auto-etykietowanie (test na filmie 02)

**Opis dla agenta:** Pierwszy test auto-etykietowania na filmie 02 i wybór algorytmu peak-based

**Słowa kluczowe:** auto_label, phase, peak-based, film 02, GCT, FLIGHT

---

## 2026-04-16 — Etap 3: Auto-etykietowanie (test na filmie 02)

### Zrobione

- **Skrypt**: `src/labeling/auto_label.py` — auto-etykietowanie faz biegu
- **Test**: uruchomiony na filmie 02 (Running at 13km/h, 30 FPS, 300 klatek, 10s)
- **Wyjście**: kolumny `phase_auto` (surowa) i `phase` (po filtrze) dopisane do istniejącego CSV w `data/keypoints/`

### Algorytm — ewolucja podejścia

Pierwotny plan (progowanie Y_heel vs ground_level) okazał się niewystarczający:

1. **Proste progowanie heel_y** — za dużo FLIGHT (71%), bo threshold 0.02 za ciasny
2. **max(heel_y, foot_index_y)** — lepszy sygnał kontaktu (cały cykl heel strike → toe-off)
3. **Adaptacyjny próg per stopa** — poprawił symetrię L/R, ale nadal bezpośrednie L→R bez FLIGHT
4. **Peak-based (finalne)** — detekcja foot strikes (`find_peaks`), wymuszona alternacja L-R, proporcjonalny podział STANCE/FLIGHT

### Finalne parametry

- Sygnał kontaktu: `max(heel_y, foot_index_y)` per stopa
- Peak detection: `scipy.signal.find_peaks(distance=12, prominence=0.03)`
- Alternacja L-R wymuszona (przy podwójnych peakach — zachowaj wyższą prominence)
- FLIGHT: w punkcie `min(max(L,R))` między peakami, `flight_fraction=0.4`
- Filtr medianowy: `kernel=3` (faktycznie zmienił 0 klatek — peak-based jest już czysty)

### Wyniki na filmie 02

| Metryka        | Wartość       | Oczekiwane (13 km/h) |
| -------------- | ------------- | -------------------- |
| Kadencja       | 162 spm       | 160–175 spm          |
| Kontakty L / R | 14 / 14       | symetryczne          |
| GCT left       | 285 ms        | ~250 ms              |
| GCT right      | 207 ms        | ~250 ms              |
| Flight         | 115 ms (n=27) | 80–130 ms            |
| Direct L↔R     | 0             | 0                    |
| DOUBLE_SUPPORT | 0             | 0                    |

### Kluczowe wnioski z eksperymentów

- **Proste progowanie Y nie działa** przy 30 FPS — flight trwa ~3 klatki, za mało do wykrycia progiem
- **Heel_y sam nie wystarczy** — prawa stopa ma dużo większą amplitudę niż lewa (artefakt kąta kamery w ujęciu z boku), trzeba max(heel, foot_index)
- **Filtr medianowy kernel=5 szkodzi** — kasuje krótkie (2-3 klatki) segmenty FLIGHT
- **Peak-based jest odporniejszy** niż progowanie — prominence jest relatywna, nie zależy od absolutnych wartości Y

### Asymetria L/R (285 vs 207 ms)

Lewa stopa jest bliżej kamery → jej ruch w pikselach jest mniejszy → peak jest szerszy → stance dłuższy. To artefakt monocular 2D — akceptowalne do trenowania klasyfikatora (model uczy się pozycji ciała, nie timingów).

### Ocena uniwersalności algorytmu

**Powinno działać bez zmian:** filmy OK (01, 02, 03, 08×2) + WARN (18) — peak detection opiera się na relatywnych zmianach (prominence), nie absolutnych wartościach
**Ryzyko:**

- **Film 09** (88.9% detekcji) — brakujące klatki mogą generować fałszywe peaki
- **Film 16** (13 FPS) — flight = 1-2 klatki, flight_fraction=0.4 może być za dużo

### Do zrobienia w następnej sesji

1. Uruchomić na pozostałych filmach, ocenić metryki (kadencja, direct_LR, liczba peaków)
2. Zdecydować co z filmami 09 i 16
3. Ręczna weryfikacja etykiet na kilku fragmentach (opcjonalnie — wizualizacja szkieletu z kolorami faz)

### Odkładane decyzje (bez zmian)

- Wersjonowanie `data/keypoints/` — teraz pliki mają dodatkowe kolumny, więc decyzja pilniejsza
- Wizualna weryfikacja etykiet

---
