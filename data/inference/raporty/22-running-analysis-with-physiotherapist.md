# Raport analizy biegu — 22 - Running Analysis with Physiotherapist

- **Wideo**: `22 - Running Analysis with Physiotherapist.mp4`
- **FPS**: 29.97
- **Klatki**: 320
- **Czas trwania**: 10.68 s
- **Rozdzielczość**: 608×1080
- **Model klasyfikatora**: `models\lstm_run1_overfit` (test acc 0.709)
- **Średnia confidence predykcji**: 0.89
- **Wygenerowano**: 2026-05-09 09:45:57

## Temporal — wskaźniki czasowe

| Współczynnik | Wartość | Klasyfikacja | Ostrzeżenia | Komentarz |
|---|---|---|---|---|
| Kadencja [spm] | 163.0 | ✅ rekreacyjny | — | n_steps=29, L/R=15/14 |
| GCT lewa [ms] | 285 ± 58 | ✅ jogging (wolny) | — | n=15 |
| GCT prawa [ms] | 226 ± 29 | ✅ rekreacyjny | — | n=14 |
| Flight time [ms] | 116 ± 19 | ✅ typowy bieg | — | n=28 |
| Cycle time [ms] | 729 ± 37 | — — | — | L=734, R=724 |
| Duty factor lewa | 0.388 | ✅ rekreacyjny | — |  |
| Duty factor prawa | 0.313 | 🟡 out_of_typical | — |  |

_Rekomendacja kadencji_: celuj w 170-180 spm (zmniejsza obciążenie stawów)

## Spatial — wskaźniki kinematyczne

| Współczynnik | Wartość | Klasyfikacja | Ostrzeżenia | Komentarz |
|---|---|---|---|---|
| Kąt kolana @ initial contact LEWA [°] | 98.2 ± 20.8 | 🟡 out_of_typical | 'siedzący' bieg (kolano zbyt ugięte), strata energii | n=15 |
| Kąt kolana @ initial contact PRAWA [°] | 137.4 ± 6.2 | 🟡 out_of_typical | 'siedzący' bieg (kolano zbyt ugięte), strata energii | n=14 |
| Pochylenie tułowia [°] | 9.9 ± 2.0 | ✅ prawidłowy | — | n=320 |
| Vertical oscillation (per torso) | 0.100 ± 0.020 | 🟡 out_of_typical | Bardzo niska oscylacja (< 0.12 torso): możliwy szum keypointów | n_cycles=14 |
| Foot strike LEWA | forefoot strike | ✅ forefoot strike | — | H/M/F = 0/0/15 (0%/0%/100%), kąt -97.0° |
| Foot strike PRAWA | forefoot strike | ✅ forefoot strike | — | H/M/F = 0/0/14 (0%/0%/100%), kąt -98.8° |

_Vertical oscillation_: Wartość znormalizowana długością tułowia (bezwymiarowa). Dla typowego tułowia ~50 cm: 0.12-0.16 = ~6-8 cm = dobry biegacz, 0.16-0.24 = ~8-12 cm = rekreacyjny, >0.24 = >12 cm = marnowanie energii.

_Foot strike_: Rearfoot ~75%, midfoot ~20%, forefoot ~5% biegaczy rekreacyjnych. Brak rekomendacji 'najlepszego' — ważniejsze jest overstriding.

## Symetria L/P

| Wskaźnik | L | R | Δ | SI [%] | Klasyfikacja |
|---|---|---|---|---|---|
| GCT [ms] | 285 | 226 | -58.3 | 22.81 | 🔴 potencjalny problem |
| Cycle time [ms] | 734 | 724 | -10.3 | 1.41 | ✅ norma |
| Duty factor | 0.388 | 0.313 | -0.075 | 21.4 | 🔴 potencjalny problem |
| Kąt kolana @ stance [°] | 92.1 | 131.3 | +39.15 | 35.05 | 🔴 potencjalny problem |
| Kąt kostki @ stance [°] | 113.7 | 122.2 | +8.54 | 7.24 | 🟡 wymaga uwagi |

**Foot strike consistency**: ✅ tak (L=forefoot strike 100.0% forefoot, R=forefoot strike 100.0% forefoot)

**Ogólna symetria**: max SI = 35.05%, mean SI = 17.58%

## Wnioski i ostrzeżenia

**Wykryte odchylenia od wartości referencyjnych:**

- ⚠️ Największa asymetria 35.05% > 10% — kandydat do uwagi specjalisty
- Knee@contact LEWA: 'siedzący' bieg (kolano zbyt ugięte), strata energii
- Knee@contact PRAWA: 'siedzący' bieg (kolano zbyt ugięte), strata energii
- Vertical osc: Bardzo niska oscylacja (< 0.12 torso): możliwy szum keypointów
- GCT [ms]: asymetria potencjalny problem (SI=22.81%)
- Duty factor: asymetria potencjalny problem (SI=21.4%)
- Kąt kolana @ stance [°]: asymetria potencjalny problem (SI=35.05%)
- Kąt kostki @ stance [°]: asymetria wymaga uwagi (SI=7.24%)

_Powyższe odchylenia warto przedyskutować z trenerem / fizjoterapeutą. Wartości referencyjne pochodzą z literatury (Novacheck 1998, Heiderscheit 2011, Souza 2016, Diaz 2019) i mają charakter ogólny — indywidualna sytuacja biegacza może wymagać innych progów._

---

_Raport wygenerowany automatycznie. Nie zastępuje konsultacji ze specjalistą biomechaniki sportu / fizjoterapeutą._

_Wartości referencyjne: zob. `docs/reference-values.md`._