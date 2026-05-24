# 2026-05-13 — Sesja B (część 1): Stride length + combinatorical low quality ✅

**Opis dla agenta:** Stride length, combinatorial low quality detection i parametry prędkości bieżni

**Słowa kluczowe:** stride length, treadmill speed, low quality, stable segments

---

## 2026-05-13 — Sesja B (część 1): Stride length + combinatorical low quality ✅

### Zrobione

**Stride length** (`--treadmill-speed-ms` jako wymagany input użytkownika):
- `temporal_metrics.py` — nowa funkcja `compute_stride_length(cycle_time, treadmill_speed_ms)`
  zwraca `mean_m / std_m / n` per noga + combined. Wzór: `stride = speed × cycle_time`.
- Parametr `treadmill_speed_ms: float | None = None` w `compute_temporal_metrics()`. Gdy `None`,
  klucz `stride_length` w wyniku nie istnieje (graceful skip).
- CLI flag `--treadmill-speed-ms` w `analyze.py` i w standalone `temporal_metrics.py`.
- W meta.json zapisywany `treadmill_speed_ms` (do reprodukowalności).
- `print_temporal_report()` dologuje stride length gdy jest.

**Reguła `check_stride_length`** w `rules.py` (Heiderscheit 2011 + Novacheck 1998):
- < 1.2 m → warning (bardzo krótki, weryfikuj prędkość)
- 1.2–1.5 m → watch (powolny jogging)
- 1.5–2.4 m → info (typowy rekreacyjny)
- 2.4–3.0 m → watch (długi — szybki bieg)
- > 3.0 m → watch (sprint / błąd predykcji cycle)
- **Reguła łączona `overstride_long_stride_combo`** (warning): stride > 2.2 m AND cadence < 160
  — silniejszy sygnał overstridingu niż samo `overstriding_combo` z `check_gct` (które patrzy na GCT).
  Dwa łączące się sygnały overstridingu z różnych metryk = wzmocnienie konkluzji.

**Combinatorical low quality detection** w `check_data_quality`:
- Nowa reguła `quality_combo_high_si_low_conf` (critical): `max_SI > 50% AND avg_conf < 0.90`
- Dokładnie odzwierciedla edge case Janka z poprzedniej sesji — pojedyncze proxy
  (`conf<0.85`, `steps_SI>20%`, `max_SI>30%`) były niewystarczające: Janek miał
  conf 0.882 (>0.85), steps 98/99 zbalansowane, ale max SI 60% = ewidentny błąd predykcji
  granic STANCE per noga. Combinatorical łapie ten "cichy" błąd.
- Detail pokazuje wszystkie 3 wartości (`max SI`, `avg_conf`, `steps_SI`) dla pełnej diagnostyki.

### Weryfikacja

| Test | Wynik oczekiwany | Wynik faktyczny |
|---|---|---|
| **02 (problem case) z speed 13 km/h** | stride długi + combinatorical (steps_SI ~57%) | ✅ stride 2.83 m → stride_long + overstride_combo (warning); combinatorical fire (critical) |
| **22 (test set, dobry materiał)** | bez regresji, 0 critical | ✅ 0/3/5/2 = 10 reguł, identyczne jak przed dodaniem nowych reguł (max_SI 35%, conf 0.89 → combinatorical NIE fire) |
| **25 Janek (edge case)** | combinatorical fire jako critical #1 | ✅ 3 critical (poprzednio 2), combinatorical pojawił się pierwszy w liście |

Stride length matematycznie zgadza się ręcznie (3.611 m/s × 0.783 s = 2.826 m, mean_combined wyszło 2.826 m).

### Stan kodu po sesji

```
src/coefficients/temporal_metrics.py  (278 → 320 linii)
  + compute_stride_length()
  + parametr treadmill_speed_ms w compute_temporal_metrics
  + CLI flag --treadmill-speed-ms

src/coefficients/analyze.py
  + parametr treadmill_speed_ms w analyze_video()
  + zapis do meta dict + meta_json
  + CLI flag --treadmill-speed-ms

src/recommendations/rules.py  (~540 → ~660 linii)
  + check_stride_length() (5 progów + reguła łączona)
  + wpięcie do orchestratora
  + rozszerzenie check_data_quality o combinatorical (max_SI>50 AND conf<0.90)
```

### Co JESZCZE w Sesji B (z briefu)

Stable segment detection + PDF generator. Według ustaleń z dzisiejszej sesji obie pozycje
**odłożone** — są kosmetyczne, nie blokują pracy magisterskiej. Wracamy do nich tylko
jeśli pojawi się potrzeba.

### Do zrobienia w następnej sesji

**Sesja C** — walidacja foot strike (rewizja limitation #9): wybranie 3-5 klatek entry-into-STANCE
per film (Adam/22/Janek), render PNG, manualna inspekcja, porównanie z `compute_foot_strike_pattern`.

---
