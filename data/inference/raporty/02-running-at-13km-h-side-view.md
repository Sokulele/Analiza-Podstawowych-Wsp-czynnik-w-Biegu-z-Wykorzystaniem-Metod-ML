# Raport analizy biegu — 02 - Running at 13km⧸h - Side View

- **Wideo**: `02 - Running at 13km⧸h - Side View.mp4`
- **FPS**: 30.0
- **Klatki**: 300
- **Czas trwania**: 10.0 s
- **Rozdzielczość**: 360×450
- **Model klasyfikatora**: `models\lstm_run1_overfit` (test acc 0.709)
- **Średnia confidence predykcji**: 0.795
- **Wygenerowano**: 2026-05-09 09:43:41

## Temporal — wskaźniki czasowe

| Współczynnik | Wartość | Klasyfikacja | Ostrzeżenia | Komentarz |
|---|---|---|---|---|
| Kadencja [spm] | 144.0 | 🔴 out_of_typical | Kadencja < 150 spm: bardzo niska, może oznaczać overstriding / chód | n_steps=24, L/R=14/10 |
| GCT lewa [ms] | 247 ± 88 | ✅ rekreacyjny | — | n=15 |
| GCT prawa [ms] | 130 ± 50 | 🟡 out_of_typical | GCT < 150 ms: nietypowo krótki, sprawdź dokładność predykcji | n=10 |
| Flight time [ms] | 200 ± 103 | 🟡 out_of_typical | Flight time > 150 ms: bardzo długa faza lotu, zwykle sprint | n=25 |
| Cycle time [ms] | 783 ± 347 | — — | — | L=652, R=985 |
| Duty factor lewa | 0.378 | ✅ rekreacyjny | — |  |
| Duty factor prawa | 0.132 | 🟡 out_of_typical | — |  |

_Rekomendacja kadencji_: celuj w 170-180 spm (zmniejsza obciążenie stawów)

## Spatial — wskaźniki kinematyczne

| Współczynnik | Wartość | Klasyfikacja | Ostrzeżenia | Komentarz |
|---|---|---|---|---|
| Kąt kolana @ initial contact LEWA [°] | 149.8 ± 13.6 | 🟡 out_of_typical | 'siedzący' bieg (kolano zbyt ugięte), strata energii | n=15 |
| Kąt kolana @ initial contact PRAWA [°] | 100.7 ± 22.1 | 🟡 out_of_typical | 'siedzący' bieg (kolano zbyt ugięte), strata energii | n=10 |
| Pochylenie tułowia [°] | 5.7 ± 2.5 | ✅ prawidłowy | — | n=300 |
| Vertical oscillation (per torso) | 0.170 ± 0.060 | ✅ rekreacyjny | — | n_cycles=14 |
| Foot strike LEWA | midfoot strike | ✅ midfoot strike | — | H/M/F = 2/7/6 (13%/47%/40%), kąt -10.9° |
| Foot strike PRAWA | forefoot strike | ✅ forefoot strike | — | H/M/F = 0/1/9 (0%/10%/90%), kąt -46.1° |

_Vertical oscillation_: Wartość znormalizowana długością tułowia (bezwymiarowa). Dla typowego tułowia ~50 cm: 0.12-0.16 = ~6-8 cm = dobry biegacz, 0.16-0.24 = ~8-12 cm = rekreacyjny, >0.24 = >12 cm = marnowanie energii.

_Foot strike_: Rearfoot ~75%, midfoot ~20%, forefoot ~5% biegaczy rekreacyjnych. Brak rekomendacji 'najlepszego' — ważniejsze jest overstriding.

## Symetria L/P

| Wskaźnik | L | R | Δ | SI [%] | Klasyfikacja |
|---|---|---|---|---|---|
| GCT [ms] | 247 | 130 | -116.7 | 61.96 | 🔴 potencjalny problem |
| Cycle time [ms] | 652 | 985 | +332.8 | 40.64 | 🔴 potencjalny problem |
| Duty factor | 0.378 | 0.132 | -0.246 | 96.47 | 🔴 potencjalny problem |
| Kąt kolana @ stance [°] | 150.5 | 115.2 | -35.28 | 26.55 | 🔴 potencjalny problem |
| Kąt kostki @ stance [°] | 90.3 | 81.1 | -9.23 | 10.77 | 🔴 potencjalny problem |

**Foot strike consistency**: 🟡 nie (L=midfoot strike 40.0% forefoot, R=forefoot strike 90.0% forefoot)

**Ogólna symetria**: max SI = 96.47%, mean SI = 47.28%

## Wnioski i ostrzeżenia

**Wykryte odchylenia od wartości referencyjnych:**

- ⚠️ Największa asymetria 96.47% > 10% — kandydat do uwagi specjalisty
- Kadencja < 150 spm: bardzo niska, może oznaczać overstriding / chód
- GCT prawa: GCT < 150 ms: nietypowo krótki, sprawdź dokładność predykcji
- Flight: Flight time > 150 ms: bardzo długa faza lotu, zwykle sprint
- Knee@contact LEWA: 'siedzący' bieg (kolano zbyt ugięte), strata energii
- Knee@contact PRAWA: 'siedzący' bieg (kolano zbyt ugięte), strata energii
- GCT [ms]: asymetria potencjalny problem (SI=61.96%)
- Cycle time [ms]: asymetria potencjalny problem (SI=40.64%)
- Duty factor: asymetria potencjalny problem (SI=96.47%)
- Kąt kolana @ stance [°]: asymetria potencjalny problem (SI=26.55%)
- Kąt kostki @ stance [°]: asymetria potencjalny problem (SI=10.77%)
- Foot strike różny L/R: L=midfoot strike, R=forefoot strike

_Powyższe odchylenia warto przedyskutować z trenerem / fizjoterapeutą. Wartości referencyjne pochodzą z literatury (Novacheck 1998, Heiderscheit 2011, Souza 2016, Diaz 2019) i mają charakter ogólny — indywidualna sytuacja biegacza może wymagać innych progów._

---

_Raport wygenerowany automatycznie. Nie zastępuje konsultacji ze specjalistą biomechaniki sportu / fizjoterapeutą._

_Wartości referencyjne: zob. `docs/reference-values.md`._