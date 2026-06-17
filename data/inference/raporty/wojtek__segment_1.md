# Raport analizy biegu — Wojtek__segment_1

- **Wideo**: `Wojtek__segment_1.mov`
- **FPS**: 29.97
- **Klatki**: 1228
- **Czas trwania**: 40.97 s
- **Rozdzielczość**: 1920×1080
- **Model klasyfikatora**: `models\lstm_run1_overfit` (test acc 0.709)
- **Średnia confidence predykcji**: 0.855
- **Wygenerowano**: 2026-06-03 21:02:57

## Temporal — wskaźniki czasowe

| Współczynnik | Wartość | Klasyfikacja | Ostrzeżenia | Komentarz |
|---|---|---|---|---|
| Kadencja [spm] | 162.5 | ✅ rekreacyjny | — | n_steps=111, L/R=55/56 |
| GCT lewa [ms] | 255 ± 26 | ✅ rekreacyjny | — | n=55 |
| GCT prawa [ms] | 254 ± 35 | ✅ rekreacyjny | — | n=56 |
| Flight time [ms] | 116 ± 17 | ✅ typowy bieg | — | n=110 |
| Cycle time [ms] | 737 ± 27 | — — | — | L=735, R=739 |
| Duty factor lewa | 0.347 | 🟡 out_of_typical | — |  |
| Duty factor prawa | 0.343 | 🟡 out_of_typical | — |  |

_Rekomendacja kadencji_: celuj w 170-180 spm (zmniejsza obciążenie stawów)

## Spatial — wskaźniki kinematyczne

| Współczynnik | Wartość | Klasyfikacja | Ostrzeżenia | Komentarz |
|---|---|---|---|---|
| Kąt kolana @ initial contact LEWA [°] | 120.1 ± 13.5 | 🟡 out_of_typical | 'siedzący' bieg (kolano zbyt ugięte), strata energii | n=55 |
| Kąt kolana @ initial contact PRAWA [°] | 121.5 ± 10.0 | 🟡 out_of_typical | 'siedzący' bieg (kolano zbyt ugięte), strata energii | n=56 |
| Pochylenie tułowia [°] | 6.1 ± 1.2 | ✅ prawidłowy | — | n=1228 |
| Vertical oscillation (per torso) | 0.130 ± 0.020 | ✅ dobry biegacz | — | n_cycles=54 |
| Foot strike LEWA | forefoot strike | ✅ forefoot strike | — | H/M/F = 0/0/55 (0%/0%/100%), kąt -90.5° |
| Foot strike PRAWA | forefoot strike | ✅ forefoot strike | — | H/M/F = 0/0/56 (0%/0%/100%), kąt -98.4° |

_Vertical oscillation_: Wartość znormalizowana długością tułowia (bezwymiarowa). Dla typowego tułowia ~50 cm: 0.12-0.16 = ~6-8 cm = dobry biegacz, 0.16-0.24 = ~8-12 cm = rekreacyjny, >0.24 = >12 cm = marnowanie energii.

_Foot strike_: Rearfoot ~75%, midfoot ~20%, forefoot ~5% biegaczy rekreacyjnych. Brak rekomendacji 'najlepszego' — ważniejsze jest overstriding.

## Symetria L/P

| Wskaźnik | L | R | Δ | SI [%] | Klasyfikacja |
|---|---|---|---|---|---|
| GCT [ms] | 255 | 254 | -1.6 | 0.63 | ✅ norma |
| Cycle time [ms] | 735 | 739 | +3.6 | 0.49 | ✅ norma |
| Duty factor | 0.347 | 0.343 | -0.004 | 1.16 | ✅ norma |
| Kąt kolana @ stance [°] | 124.1 | 128.5 | +4.43 | 3.51 | ✅ norma |
| Kąt kostki @ stance [°] | 125.4 | 114.0 | -11.38 | 9.51 | 🟡 wymaga uwagi |

**Foot strike consistency**: ✅ tak (L=forefoot strike 100.0% forefoot, R=forefoot strike 100.0% forefoot)

**Ogólna symetria**: max SI = 9.51%, mean SI = 3.06%

## Wnioski i ostrzeżenia

**Wykryte odchylenia od wartości referencyjnych:**

- Knee@contact LEWA: 'siedzący' bieg (kolano zbyt ugięte), strata energii
- Knee@contact PRAWA: 'siedzący' bieg (kolano zbyt ugięte), strata energii
- Kąt kostki @ stance [°]: asymetria wymaga uwagi (SI=9.51%)

_Powyższe odchylenia warto przedyskutować z trenerem / fizjoterapeutą. Wartości referencyjne pochodzą z literatury (Novacheck 1998, Heiderscheit 2011, Souza 2016, Diaz 2019) i mają charakter ogólny — indywidualna sytuacja biegacza może wymagać innych progów._

---

_Raport wygenerowany automatycznie. Nie zastępuje konsultacji ze specjalistą biomechaniki sportu / fizjoterapeutą._

_Wartości referencyjne: zob. `docs/reference-values.md`._