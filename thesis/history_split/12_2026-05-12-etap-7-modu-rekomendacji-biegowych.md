# 2026-05-12 — Etap 7: moduł rekomendacji biegowych ✅

**Opis dla agenta:** Etap 7: moduł rekomendacji biegowych oparty o reguły literaturowe

**Słowa kluczowe:** recommendations, rules.py, Heiderscheit, Novacheck, Daoud, Janek

---

## 2026-05-12 — Etap 7: moduł rekomendacji biegowych ✅

### Cel sesji

Etap 7 z briefu — silnik rekomendacji oparty o reguły z literatury biomechanicznej
(Heiderscheit 2011, Novacheck 1998, Souza 2016, Diaz 2019, Robinson 1987, Daoud 2012).
Operuje na JSON-ach z Iteracji 1, generuje listę `Recommendation` + sekcję MD do raportu.

### Zrobione

- `src/recommendations/__init__.py` + `rules.py` + `recommend.py` (CLI)
- 10 funkcji `check_*` (kadencja, GCT, flight, duty_factor, torso_lean, knee@contact,
  vert_osc, symmetry, foot_strike, data_quality)
- Reguła łączona **overstriding combo** (cad<160 ∧ GCT_mean>270) — Heiderscheit 2011
- Severity 4-poziomowe: critical / warning / watch / info
- Citation w każdej rekomendacji (do obrony pracy + transparentność w raporcie)
- Test na 3 biegaczach: Adam (sanity), 22 (test), 25 Janek (świeży test z kiepskiego materiału)

### Wyniki testów

| Biegacz | conf | Kadencja | GCT L/R | Max SI | crit/warn/watch/info |
|---|---|---|---|---|---|
| Adam (train) | 0.91 | 173 ℹ️ | 203/245 | 18.7% | 0 / 2 / 1 / 3 |
| Film 22 (test) | 0.89 | 163 🟡 | 285🟠/226 | 35.0% | 0 / 3 / 5 / 2 |
| Janek (nowy test) | 0.88 | **148** 🔴 | 193/**357**🔴 | **60.0%** | **2** / 3 / 3 / 2 |

### Kluczowe obserwacje sesji

1. **Janek — ciekawy edge case**: avg_conf 0.88 powyżej progu 0.85 (proxy jakości się **nie**
   uruchomiło), steps L/R 98/99 zbalansowane (steps SI proxy się **nie** uruchomiło), ale
   GCT/DF asymetria 60%. Pojedyncze proxy nie wystarcza — potrzebny combinatorical check.
2. **Detection 100% u Janka** mimo zasłoniętego biodra przez poręcze — MediaPipe radzi sobie
   z częściową okluzją lepiej niż się obawialiśmy.
3. **Janek foot strike kąty −4°, −3°** (rozsądne!) — kontrhipoteza dla limitation #9 z notatki
   Iteracji 1: ekstremalne kąty −33°/−58° w innych filmach mogą być wrażliwe na ujęcie/aspect ratio,
   nie systematycznie zafałszowane.
4. **Reguły deterministyczne** dają repeatable, transparent recommendations z literackim
   uzasadnieniem każdej decyzji — idealne dla rozdziału 7 pracy magisterskiej.

### Materiał do pracy magisterskiej

Notatka thesis `2026-05-12-etap7-rekomendacje.md`:
- Architektura modułu rekomendacji + tabela 10 reguł × progi × citation
- Reguła łączona overstriding (Heiderscheit 2011 jako kluczowa publikacja)
- Wyniki na 3 biegaczach (Adam / 22 / Janek) + interpretacja per biegacz
- 4 punkty walidacji jakości (literatura progi, reguły łączone, severity, low quality detection)
- 4 punkty Future Work (combinatorical low quality detection, stride length rules, callout w raporcie, walidacja na większej próbce)
- 3 punkty Limitations (deterministyczne, ogólne progi, średnie wartości)

### Stan plików

- `src/recommendations/` — 3 nowe pliki (rules.py 480 linii, recommend.py 165, __init__.py)
- `data/inference/25-janek__segment_1-{phases.csv, temporal, spatial, symmetry, meta}.json` — Janek
- `data/inference/{22,24-adam,25-janek}-recommendations.json` — wyniki silnika
- `data/inference/raporty/{22,24-adam,25-janek}-rekomendacje.md` — MD do dołączenia do raportu

### Do zrobienia w następnej sesji

**Integracja Etapu 7 z analyze.py** — dodać krok 6 "generuj rekomendacje" do orchestration,
żeby `analyze.py` w jednym wywołaniu generował też rekomendacje.

**Iteracja 2** (z briefu poprzedniej sesji, niezmieniona):
1. Stride length z `--treadmill-speed-ms`
2. **Combinatorical low quality detection** — wzbogacenie reguły jakości (Janek pokazał edge case)
3. Stable segment detection dla mixed-tempo
4. Generator PDF z wykresami

### Otwarte sprawy / drobne TODO

- Bug `postprocess_median.predict_lstm` (niezmieniony z poprzednich sesji)
- Walidacja foot strike kątów: Janek dał normalne kąty, więc hipoteza "systematyczny błąd"
  z limitation #9 wymaga rewizji
- Adam meta.json dalej nie wygenerowany (--skip-inference + run analyze do tego potrzebny)

### Odkładane decyzje (bez zmian)

- Wersjonowanie `models/` i `data/inference/`
- Walidacja 3D motion capture
- Iteracja 2 (po Etapie 7 — naturalna kontynuacja)

---
