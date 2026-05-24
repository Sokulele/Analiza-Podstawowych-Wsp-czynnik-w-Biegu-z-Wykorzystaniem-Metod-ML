# 2026-05-09 — Etap 6 MVP: pipeline współczynników biegu (test na Adamie)

**Opis dla agenta:** Etap 6 MVP: pipeline współczynników biegu i test end-to-end na Adamie

**Słowa kluczowe:** coefficients, MVP, temporal_metrics, spatial_metrics, symmetry, Adam

---

## 2026-05-09 — Etap 6 MVP: pipeline współczynników biegu (test na Adamie)

### Decyzje sesji

1. **Primary model = LSTM r1 + aspect fix** (h=128, 70.9% test acc) — formalna zmiana z LSTM r2. Notatka thesis zaktualizowana z argumentacją + uwagą o "case study run 1 vs run 2" (zachowane jako sekcja pedagogiczna w pracy)
2. **Stride length pominięta** w MVP — wymaga inputu użytkownika (prędkość bieżni). Implementacja warunkowa po MVP
3. **Test pipeline na Adamie (24)** — świadomy wybór mimo że jest w train. Cel: weryfikacja E2E, nie pomiar jakości
4. **Bug postprocess_median.predict_lstm** — zaakceptowany jako niski priorytet, metrics.json autorytetywny

### Zrobione

**Architektura `src/coefficients/`:**
- `run_inference.py` — pełen pipeline: cv2 + MediaPipe Pose (complexity=2) + savgol smoothing + auto-detect aspect_fix z config.json + LSTM predict + softmax confidence. Klatki brzegowe (half=7) extend pierwszej/ostatniej predykcji z confidence=0
- `temporal_metrics.py` — kadencja [spm], GCT (per L/R), flight time, cycle time (per L/R), duty factor. Run-length encoding sekwencji faz
- `spatial_metrics.py` — kąty stawów (kolana/biodra/kostki L+R) per faza, torso lean, vertical oscillation per cykl (raw + per torso), foot strike pattern (heel/mid/forefoot z kątem stopy w klatce kontaktu)
- `symmetry.py` — Symmetry Index = 200 × |L−R|/(L+R), klasyfikacja zdrowa/łagodna/znacząca

Każdy moduł CLI-runable + reużywalny jako library.

### Wyniki testu na Adamie (24, 80s, 30 FPS, 1920×1080)

**Inferencja**:
- 100% MediaPipe detection (2399/2399 klatek)
- Aspect fix: x*1920, y*1080, z*1920
- Predykcje: FLIGHT 35.3% / LEFT_STANCE 29.2% / RIGHT_STANCE 35.5%
- Średnia confidence: **0.909** (model bardzo pewny)
- Czas: 221s ekstrakcji + 1.5s predykcji LSTM

**Temporal**:
- Kadencja: **173.5 spm** (n=231: L=115, R=116) — typowy zakres 160-180
- GCT: L 203±31 ms, R 245±67 ms
- Flight: 122±25 ms
- Cycle time: L 684±50 ms, R 685±30 ms (niemal identyczne)
- Duty factor: L 0.296, R 0.357

**Spatial** — kąty stawów biomechanicznie poprawne:
- LEFT_KNEE wyprostowane (164°) w L_STANCE, zgięte (133°) w R_STANCE ✓
- RIGHT_KNEE symetrycznie odwrotnie (105°/157°) ✓
- Torso lean 2.3° (low — running tall lub szum)
- Vertical oscillation: 0.140 per torso (~14% długości tułowia, w typowym zakresie 12-20%)
- Foot strike: oba forefoot (LEWA 95.7%, PRAWA 75%, consistent=True). Kąt LEWA −33° wymaga inspekcji

**Symetria**:
- GCT SI **18.7%** (znacząca asymetria L<R)
- Cycle time SI **0.1%** (idealna symetria)
- Knee@STANCE SI 4.0%, Ankle@STANCE 5.6%
- Foot strike pattern consistent (oba forefoot)
- Overall: max SI 18.7%, mean SI 9.4%

### Najciekawsza obserwacja

**GCT asymetryczne, cycle time symetryczne** — Adam ma identyczny rytm cyklu (684 vs 685 ms), ale lewa noga ma krótszy stance / dłuższy flight, prawa odwrotnie. To **klasyczny artefakt monocular 2D** (lewa strona biegacza bliżej kamery → mniejsza amplituda pikselowa → krótszy "wykryty" stance), opisane już w `.claude/rules/labeling.md`. Walidacja: auto_label peak-based dał Adamowi GCT L=R=241 ms (po cięciu 80 brzegowych klatek), więc LSTM wprowadza niewielki błąd asymetryczny.

### Sanity checks pipeline'u

| Kontrola | Wynik | Komentarz |
|---|---|---|
| Kadencja vs cycle time | 173 spm vs 175 z cycle (0.685 s × 2 nogi) | różnica 1.5 spm — szum klatkowania ✓ |
| Klasy w sensownym rozkładzie | 35/29/35 (FLIGHT/L/R) | typowy bieg na bieżni ✓ |
| Kąty stawów biomechanika | knee L wyprostowane w L_STANCE | zgodne z fizjologią ✓ |
| Oscylacja pionowa | 14% torso | typowy zakres ✓ |
| Confidence predykcji | 0.91 | model pewny ✓ |

### Notatka thesis

`docs/thesis-notes/2026-05-09-coefficients-mvp.md` — pełna dokumentacja Etapu 6 MVP. Zawiera:
- Architekturę pipeline'u
- Decyzje (primary, stride length, klatki brzegowe extend vs drop)
- Wyniki na Adamie (3 tabele × kategorie metryk)
- Walidację biomechaniczną
- Sekcję Limitations (6 pkt — monocular 2D bias, foot strike kąty, torso lean low, Adam w train, klatki brzegowe, stride length)
- Plan iteracji 1-3 (test set, raport PDF, Etap 7 rekomendacje)

### Stan plików / artefakty

- `src/coefficients/` — 4 moduły + `__init__.py`
- `data/inference/24-adam-phases.csv` (16 MB, predykcje + keypointy)
- `data/inference/24-adam-temporal.json` / `-spatial.json` / `-symmetry.json`

### Do zrobienia w następnej sesji

**Iteracja 1** (krótkoterminowa):
1. Test pipeline na **02, 20, 22** (test set) — porównanie sensowności współczynników na unseen biegaczach
2. `analyze.py` orchestration script: 1 CLI uruchomienie wideo → wszystkie współczynniki + raport MD
3. Naprawa bug `postprocess_median.predict_lstm` (low priority)

**Iteracja 2** (średnioterminowa):
1. Stride length z input użytkownika (`--treadmill-speed-ms`), formuła `stride_length = speed × cycle_time`
2. Generator raportu PDF/Markdown per bieg
3. Walidacja kąta stopy (foot strike) — wizualna inspekcja klatek

**Iteracja 3** — Etap 7 (rekomendacje):
- `src/recommendations/rules.py` z regułami z literatury biomechanicznej
- Reguły kodowane ręcznie z citation (autor/rok)
- Przykłady: kadencja <160 + GCT >270 → overstriding, asymetria GCT >5% → kandydat do specjalisty

### Odkładane decyzje (bez zmian)

- Wersjonowanie `models/` i `data/inference/`
- Walidacja 3D motion capture (poza scope projektu, ale ważny argument do Limitations)

---
