# Raport analizy biegu — 24 - Adam bieg__segment_1

- **Wideo**: `24 - Adam bieg__segment_1.mov`
- **FPS**: 29.99
- **Klatki**: 2399
- **Czas trwania**: 80.0 s
- **Rozdzielczość**: 1920×1080
- **Model klasyfikatora**: `models\lstm_run1_overfit` (test acc 0.709)
- **Średnia confidence predykcji**: 0.909
- **Wygenerowano**: 2026-05-13 08:51:39

## Temporal — wskaźniki czasowe

| Współczynnik | Wartość | Klasyfikacja | Ostrzeżenia | Komentarz |
|---|---|---|---|---|
| Kadencja [spm] | 173.3 | ✅ zaawansowany | — | n_steps=231, L/R=115/116 |
| GCT lewa [ms] | 203 ± 31 | ✅ szybki bieg | — | n=115 |
| GCT prawa [ms] | 245 ± 67 | ✅ rekreacyjny | — | n=116 |
| Flight time [ms] | 122 ± 25 | ✅ typowy bieg | — | n=231 |
| Cycle time [ms] | 686 ± 42 | — — | — | L=685, R=686 |
| Duty factor lewa | 0.296 | ✅ sprint | — |  |
| Duty factor prawa | 0.357 | ✅ rekreacyjny | — |  |

_Rekomendacja kadencji_: celuj w 170-180 spm (zmniejsza obciążenie stawów)

## Spatial — wskaźniki kinematyczne

| Współczynnik | Wartość | Klasyfikacja | Ostrzeżenia | Komentarz |
|---|---|---|---|---|
| Kąt kolana @ initial contact LEWA [°] | 161.8 ± 6.1 | ✅ prawidłowy | — | n=115 |
| Kąt kolana @ initial contact PRAWA [°] | 162.0 ± 4.0 | ✅ prawidłowy | — | n=116 |
| Pochylenie tułowia [°] | 2.3 ± 1.1 | 🟡 out_of_typical | tułów zbyt pionowy, brak wykorzystania grawitacji | n=2399 |
| Vertical oscillation (per torso) | 0.140 ± 0.020 | ✅ dobry biegacz | — | n_cycles=114 |
| Foot strike LEWA | forefoot strike | ✅ forefoot strike | — | H/M/F = 0/5/110 (0%/4%/96%), kąt -32.9° |
| Foot strike PRAWA | forefoot strike | ✅ forefoot strike | — | H/M/F = 2/27/87 (2%/23%/75%), kąt -11.5° |

_Vertical oscillation_: Wartość znormalizowana długością tułowia (bezwymiarowa). Dla typowego tułowia ~50 cm: 0.12-0.16 = ~6-8 cm = dobry biegacz, 0.16-0.24 = ~8-12 cm = rekreacyjny, >0.24 = >12 cm = marnowanie energii.

_Foot strike_: Rearfoot ~75%, midfoot ~20%, forefoot ~5% biegaczy rekreacyjnych. Brak rekomendacji 'najlepszego' — ważniejsze jest overstriding.

## Symetria L/P

| Wskaźnik | L | R | Δ | SI [%] | Klasyfikacja |
|---|---|---|---|---|---|
| GCT [ms] | 203 | 245 | +41.9 | 18.71 | 🔴 potencjalny problem |
| Cycle time [ms] | 685 | 686 | +0.7 | 0.1 | ✅ norma |
| Duty factor | 0.296 | 0.357 | +0.061 | 18.68 | 🔴 potencjalny problem |
| Kąt kolana @ stance [°] | 163.7 | 157.2 | -6.48 | 4.04 | ✅ norma |
| Kąt kostki @ stance [°] | 135.4 | 128.0 | -7.38 | 5.6 | 🟡 wymaga uwagi |

**Foot strike consistency**: ✅ tak (L=forefoot strike 95.7% forefoot, R=forefoot strike 75.0% forefoot)

**Ogólna symetria**: max SI = 18.71%, mean SI = 9.43%

## Wnioski i ostrzeżenia

**Wykryte odchylenia od wartości referencyjnych:**

- ⚠️ Największa asymetria 18.71% > 10% — kandydat do uwagi specjalisty
- Tułów: tułów zbyt pionowy, brak wykorzystania grawitacji
- GCT [ms]: asymetria potencjalny problem (SI=18.71%)
- Duty factor: asymetria potencjalny problem (SI=18.68%)
- Kąt kostki @ stance [°]: asymetria wymaga uwagi (SI=5.6%)

_Powyższe odchylenia warto przedyskutować z trenerem / fizjoterapeutą. Wartości referencyjne pochodzą z literatury (Novacheck 1998, Heiderscheit 2011, Souza 2016, Diaz 2019) i mają charakter ogólny — indywidualna sytuacja biegacza może wymagać innych progów._

---

_Raport wygenerowany automatycznie. Nie zastępuje konsultacji ze specjalistą biomechaniki sportu / fizjoterapeutą._

_Wartości referencyjne: zob. `docs/reference-values.md`._