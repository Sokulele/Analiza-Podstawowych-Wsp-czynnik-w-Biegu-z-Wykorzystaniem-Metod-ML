# Raport analizy biegu — 25 - janek__segment_1

- **Wideo**: `25 - janek__segment_1.mov`
- **FPS**: 30.0
- **Klatki**: 2400
- **Czas trwania**: 80.0 s
- **Rozdzielczość**: 1080×1920
- **Model klasyfikatora**: `models\lstm_run1_overfit` (test acc 0.709)
- **Średnia confidence predykcji**: 0.882
- **Wygenerowano**: 2026-05-12 22:26:57

## Temporal — wskaźniki czasowe

| Współczynnik | Wartość | Klasyfikacja | Ostrzeżenia | Komentarz |
|---|---|---|---|---|
| Kadencja [spm] | 147.8 | 🔴 out_of_typical | Kadencja < 150 spm: bardzo niska, może oznaczać overstriding / chód | n_steps=197, L/R=98/99 |
| GCT lewa [ms] | 192 ± 38 | ✅ elita | — | n=98 |
| GCT prawa [ms] | 357 ± 35 | 🔴 out_of_typical | GCT > 350 ms: sugeruje wolny jogging lub chód | n=99 |
| Flight time [ms] | 130 ± 30 | ✅ typowy bieg | — | n=198 |
| Cycle time [ms] | 807 ± 32 | — — | — | L=807, R=808 |
| Duty factor lewa | 0.238 | ✅ sprint | — |  |
| Duty factor prawa | 0.442 | ✅ rekreacyjny | — |  |

_Rekomendacja kadencji_: celuj w 170-180 spm (zmniejsza obciążenie stawów)

## Spatial — wskaźniki kinematyczne

| Współczynnik | Wartość | Klasyfikacja | Ostrzeżenia | Komentarz |
|---|---|---|---|---|
| Kąt kolana @ initial contact LEWA [°] | 138.0 ± 8.9 | 🟡 out_of_typical | 'siedzący' bieg (kolano zbyt ugięte), strata energii | n=98 |
| Kąt kolana @ initial contact PRAWA [°] | 148.5 ± 5.7 | 🟡 out_of_typical | 'siedzący' bieg (kolano zbyt ugięte), strata energii | n=99 |
| Pochylenie tułowia [°] | 9.9 ± 2.4 | ✅ prawidłowy | — | n=2400 |
| Vertical oscillation (per torso) | 0.110 ± 0.020 | 🟡 out_of_typical | Bardzo niska oscylacja (< 0.12 torso): możliwy szum keypointów | n_cycles=97 |
| Foot strike LEWA | midfoot strike | ✅ midfoot strike | — | H/M/F = 0/60/38 (0%/61%/39%), kąt -4.2° |
| Foot strike PRAWA | midfoot strike | ✅ midfoot strike | — | H/M/F = 3/72/24 (3%/73%/24%), kąt -2.8° |

_Vertical oscillation_: Wartość znormalizowana długością tułowia (bezwymiarowa). Dla typowego tułowia ~50 cm: 0.12-0.16 = ~6-8 cm = dobry biegacz, 0.16-0.24 = ~8-12 cm = rekreacyjny, >0.24 = >12 cm = marnowanie energii.

_Foot strike_: Rearfoot ~75%, midfoot ~20%, forefoot ~5% biegaczy rekreacyjnych. Brak rekomendacji 'najlepszego' — ważniejsze jest overstriding.

## Symetria L/P

| Wskaźnik | L | R | Δ | SI [%] | Klasyfikacja |
|---|---|---|---|---|---|
| GCT [ms] | 192 | 357 | +164.4 | 59.85 | 🔴 potencjalny problem |
| Cycle time [ms] | 807 | 808 | +0.3 | 0.04 | ✅ norma |
| Duty factor | 0.238 | 0.442 | +0.204 | 60.0 | 🔴 potencjalny problem |
| Kąt kolana @ stance [°] | 129.9 | 128.6 | -1.35 | 1.04 | ✅ norma |
| Kąt kostki @ stance [°] | 92.8 | 95.0 | +2.24 | 2.39 | ✅ norma |

**Foot strike consistency**: ✅ tak (L=midfoot strike 38.8% forefoot, R=midfoot strike 24.2% forefoot)

**Ogólna symetria**: max SI = 60.0%, mean SI = 24.66%

## Wnioski i ostrzeżenia

**Wykryte odchylenia od wartości referencyjnych:**

- ⚠️ Największa asymetria 60.0% > 10% — kandydat do uwagi specjalisty
- Kadencja < 150 spm: bardzo niska, może oznaczać overstriding / chód
- GCT prawa: GCT > 350 ms: sugeruje wolny jogging lub chód
- Knee@contact LEWA: 'siedzący' bieg (kolano zbyt ugięte), strata energii
- Knee@contact PRAWA: 'siedzący' bieg (kolano zbyt ugięte), strata energii
- Vertical osc: Bardzo niska oscylacja (< 0.12 torso): możliwy szum keypointów
- GCT [ms]: asymetria potencjalny problem (SI=59.85%)
- Duty factor: asymetria potencjalny problem (SI=60.0%)

_Powyższe odchylenia warto przedyskutować z trenerem / fizjoterapeutą. Wartości referencyjne pochodzą z literatury (Novacheck 1998, Heiderscheit 2011, Souza 2016, Diaz 2019) i mają charakter ogólny — indywidualna sytuacja biegacza może wymagać innych progów._

---

_Raport wygenerowany automatycznie. Nie zastępuje konsultacji ze specjalistą biomechaniki sportu / fizjoterapeutą._

_Wartości referencyjne: zob. `docs/reference-values.md`._