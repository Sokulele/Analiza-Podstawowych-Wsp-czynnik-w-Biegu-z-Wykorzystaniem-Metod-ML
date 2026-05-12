# Raport analizy biegu — 20 -Running (0.8 to 3.5 m⧸s)__segment_1

- **Wideo**: `20 -Running (0.8 to 3.5 m⧸s)__segment_1.mp4`
- **FPS**: 30.0
- **Klatki**: 870
- **Czas trwania**: 29.0 s
- **Rozdzielczość**: 640×360
- **Model klasyfikatora**: `models\lstm_run1_overfit` (test acc 0.709)
- **Średnia confidence predykcji**: 0.901
- **Wygenerowano**: 2026-05-09 09:45:16

## Temporal — wskaźniki czasowe

| Współczynnik | Wartość | Klasyfikacja | Ostrzeżenia | Komentarz |
|---|---|---|---|---|
| Kadencja [spm] | 138.6 | 🔴 out_of_typical | Kadencja < 150 spm: bardzo niska, może oznaczać overstriding / chód | n_steps=67, L/R=33/34 |
| GCT lewa [ms] | 204 ± 24 | ✅ szybki bieg | — | n=34 |
| GCT prawa [ms] | 368 ± 51 | 🔴 out_of_typical | GCT > 350 ms: sugeruje wolny jogging lub chód | n=34 |
| Flight time [ms] | 143 ± 47 | ✅ typowy bieg | — | n=67 |
| Cycle time [ms] | 841 ± 101 | — — | — | L=825, R=858 |
| Duty factor lewa | 0.247 | ✅ sprint | — |  |
| Duty factor prawa | 0.429 | ✅ rekreacyjny | — |  |

_Rekomendacja kadencji_: celuj w 170-180 spm (zmniejsza obciążenie stawów)

## Spatial — wskaźniki kinematyczne

| Współczynnik | Wartość | Klasyfikacja | Ostrzeżenia | Komentarz |
|---|---|---|---|---|
| Kąt kolana @ initial contact LEWA [°] | 167.0 ± 5.3 | ✅ prawidłowy | — | n=34 |
| Kąt kolana @ initial contact PRAWA [°] | 170.0 ± 7.7 | ✅ prawidłowy | — | n=34 |
| Pochylenie tułowia [°] | 2.8 ± 1.1 | 🟡 out_of_typical | tułów zbyt pionowy, brak wykorzystania grawitacji | n=870 |
| Vertical oscillation (per torso) | 0.150 ± 0.010 | ✅ dobry biegacz | — | n_cycles=33 |
| Foot strike LEWA | heel strike | ✅ heel strike | — | H/M/F = 25/8/1 (74%/24%/3%), kąt 10.2° |
| Foot strike PRAWA | heel strike | ✅ heel strike | — | H/M/F = 31/1/2 (91%/3%/6%), kąt 15.0° |

_Vertical oscillation_: Wartość znormalizowana długością tułowia (bezwymiarowa). Dla typowego tułowia ~50 cm: 0.12-0.16 = ~6-8 cm = dobry biegacz, 0.16-0.24 = ~8-12 cm = rekreacyjny, >0.24 = >12 cm = marnowanie energii.

_Foot strike_: Rearfoot ~75%, midfoot ~20%, forefoot ~5% biegaczy rekreacyjnych. Brak rekomendacji 'najlepszego' — ważniejsze jest overstriding.

## Symetria L/P

| Wskaźnik | L | R | Δ | SI [%] | Klasyfikacja |
|---|---|---|---|---|---|
| GCT [ms] | 204 | 368 | +163.7 | 57.29 | 🔴 potencjalny problem |
| Cycle time [ms] | 825 | 858 | +32.3 | 3.84 | ✅ norma |
| Duty factor | 0.247 | 0.429 | +0.182 | 53.85 | 🔴 potencjalny problem |
| Kąt kolana @ stance [°] | 163.5 | 161.1 | -2.39 | 1.47 | ✅ norma |
| Kąt kostki @ stance [°] | 105.4 | 98.5 | -6.86 | 6.73 | 🟡 wymaga uwagi |

**Foot strike consistency**: ✅ tak (L=heel strike 2.9% forefoot, R=heel strike 5.9% forefoot)

**Ogólna symetria**: max SI = 57.29%, mean SI = 24.64%

## Wnioski i ostrzeżenia

**Wykryte odchylenia od wartości referencyjnych:**

- ⚠️ Największa asymetria 57.29% > 10% — kandydat do uwagi specjalisty
- Kadencja < 150 spm: bardzo niska, może oznaczać overstriding / chód
- GCT prawa: GCT > 350 ms: sugeruje wolny jogging lub chód
- Tułów: tułów zbyt pionowy, brak wykorzystania grawitacji
- GCT [ms]: asymetria potencjalny problem (SI=57.29%)
- Duty factor: asymetria potencjalny problem (SI=53.85%)
- Kąt kostki @ stance [°]: asymetria wymaga uwagi (SI=6.73%)

_Powyższe odchylenia warto przedyskutować z trenerem / fizjoterapeutą. Wartości referencyjne pochodzą z literatury (Novacheck 1998, Heiderscheit 2011, Souza 2016, Diaz 2019) i mają charakter ogólny — indywidualna sytuacja biegacza może wymagać innych progów._

---

_Raport wygenerowany automatycznie. Nie zastępuje konsultacji ze specjalistą biomechaniki sportu / fizjoterapeutą._

_Wartości referencyjne: zob. `docs/reference-values.md`._