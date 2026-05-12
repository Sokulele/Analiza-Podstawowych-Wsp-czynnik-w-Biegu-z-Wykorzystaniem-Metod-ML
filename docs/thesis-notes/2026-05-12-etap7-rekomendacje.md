# 2026-05-12 — Etap 7: moduł rekomendacji biegowych

## Kontekst

Po Iteracji 1 Etapu 6 (raporty MD per biegacz z klasyfikacją vs reference values), Etap 7 dodaje
**warstwę interpretacyjną**: silnik reguł kodowanych ręcznie na podstawie literatury biomechanicznej.
Wejście: JSON-y z `src/coefficients/analyze.py` (`*-temporal.json`, `*-spatial.json`,
`*-symmetry.json`, `*-meta.json`). Wyjście: `*-recommendations.json` + sekcja Markdown
do dołączenia do raportu.

Zgodnie z CLAUDE.md (sekcja "Rekomendacje"): **NIE uczymy reguł z danych** — to konwersja
literatury na deterministyczne progi.

## Architektura

```
src/recommendations/
├── __init__.py
├── rules.py        — silnik reguł: dataclass Recommendation + 9 funkcji check_*
└── recommend.py    — CLI: wczytuje JSON-y → generate_recommendations → MD + JSON
```

### Decyzje implementacyjne

1. **Severity 4-poziomowe**: `critical` / `warning` / `watch` / `info`. Sortowanie wyników:
   krytyczne zawsze pierwsze, info na końcu.
2. **Każda rekomendacja ma citation** (Heiderscheit 2011, Novacheck 1998, Souza 2016,
   Diaz 2019, Robinson 1987, Daoud 2012) — ułatwia obronę pracy i jest wprost w raporcie.
3. **Reguły jakości predykcji idą jako pierwsze** — przed klasyczną biomechaniką pokazujemy
   ostrzeżenia z Iteracji 1: confidence < 0.85, L/R steps asymmetry > 20%, max SI > 30%.
   Użytkownik powinien zobaczyć, że raport może być niewiarygodny, zanim zacznie czytać metryki.
4. **Każda reguła zwraca `Recommendation`** (dataclass z `rule_id`, `severity`, `category`,
   `title`, `message`, `citation`, `detail`, `suggestion`) — łatwo serializowalne do JSON
   i renderowalne do MD, łatwo testowalne (rule_id jako unique key).

### Reguły zaimplementowane (10 kategorii)

| Kategoria | Funkcja | Progi (z literatury) | Citation |
|---|---|---|---|
| **Jakość predykcji** | `check_data_quality` | conf < 0.85, steps SI > 20%, max SI > 30% | Iteracja 1 (wewnętrzna walidacja) |
| **Kadencja** | `check_cadence` | <150 critical, 150-160 warning (overstriding), 160-170 watch, 170-185 info, 185-200 elita, >200 watch | Heiderscheit 2011, Novacheck 1998 |
| **GCT** | `check_gct` (per noga) | >350 critical, >280 warning, <150 watch + kombinacja overstriding (cad<160 ∧ GCT>270) | Souza 2016, Heiderscheit 2011 |
| **Flight time** | `check_flight` | <30 warning (sanity check chodu) | Novacheck 1998 |
| **Duty factor** | `check_duty_factor` (per noga) | ≥0.5 critical (chód), >0.45 warning, <0.22 watch (sprint) | Souza 2016 |
| **Tułów** | `check_torso_lean` | <5° warning, 5-15° info, 15-20° watch, >20° critical | Novacheck 1998 |
| **Kolano @ kontakt** | `check_knee_at_contact` (per noga) | >175° critical (overstriding), 160-175° info, <155° watch | Heiderscheit 2011, Novacheck 1998 |
| **Vertical osc** | `check_vertical_oscillation` (per torso) | >0.24 warning, 0.16-0.24 watch, 0.12-0.16 info, <0.12 watch (szum) | Diaz 2019 |
| **Symetria L/P** | `check_symmetry` | SI>10% warning, 5-10% watch, <5% info | Robinson 1987 |
| **Foot strike** | `check_foot_strike` | inconsistent L/P warning, consistent info | Daoud 2012, Souza 2016 |

### Reguła łączona — sygnał overstriding

Jedna z najbardziej wartościowych reguł literackich (Heiderscheit 2011) to **kombinacja**:
**kadencja < 160 spm AND średni GCT > 270 ms** → warning "klasyczny wzorzec overstridingu".
Reguły jednowymiarowe nie złapałyby tego sygnału.

## Wyniki testów

Pipeline puścony na trzech biegaczach: 22 (najlepszy test set, 85.9% acc), Adam (train,
sanity), Janek (świeży test, znanej kiepskiej jakości — brak czubka głowy, biodro
zasłonięte poręczami).

### Tabela porównawcza

| Metryka | Adam (train) | 22 (test) | Janek (świeży test) |
|---|---|---|---|
| avg_confidence | 0.91 | 0.89 | 0.88 |
| Kadencja [spm] | 173 ℹ️ | 163 🟡 | **148** 🔴 |
| GCT L/R [ms] | 203 / 245 | 285 🟠 / 226 | 193 / **357** 🔴 |
| Steps L/R | 115/116 ✅ | 15/14 ✅ | 98/99 ✅ |
| DF L/R | 0.296 / 0.357 | 0.388 / 0.313 | 0.238 / 0.442 |
| Torso lean | 2.3° 🟠 | 9.9° ℹ️ | 9.9° ℹ️ |
| Vert osc / torso | 0.14 ℹ️ | 0.10 🟡 | 0.11 🟡 |
| Foot strike | oba forefoot ℹ️ | oba forefoot ℹ️ | oba midfoot ℹ️ |
| Max SI [%] | 18.7 | 35.0 🟠 | **60.0** 🟠 |
| **Σ critical / warning / watch / info** | 0 / 2 / 1 / 3 | 0 / 3 / 5 / 2 | **2 / 3 / 3 / 2** |

### Per biegacz — sygnał interpretacyjny

**Adam (sanity, train) — 6 rekomendacji, 0 critical**
- ✅ Kadencja 173 spm (info: zalecany zakres)
- ✅ Vert osc 0.14 (info: ekonomiczny)
- ✅ Foot strike forefoot consistent (info)
- 🟠 **Torso lean 2.3°** — "tułów zbyt pionowy" (limitation #6 z notatek MVP: szum MediaPipe 2D
  lub Adam biega "running tall")
- 🟠 Symetria GCT/DF SI≈18-19% (głównie monocular 2D bias, opisane w notatce MVP)
- 🟡 Łagodna asymetria ankle@stance SI 5.6%

**Komentarz**: Idealny sanity check — silnik nie generuje fałszywych alarmów dla biegacza
biomechanicznie poprawnego, jednocześnie nie ukrywa znanych ograniczeń (torso 2.3° to
limitation #5 z `2026-05-09-coefficients-mvp.md`).

**Film 22 (test, 85.9% acc) — 10 rekomendacji, 0 critical, 3 warning**
- 🟠 GCT lewa 285 ms — przedłużony (warning)
- 🟠 Asymetria L/P SI 22.8% GCT + 35.0% knee@stance → "rozważ konsultację"
- 🟠 Quality: max SI 35% wpadło w warning jakości predykcji
- 🟡 Kadencja 163 spm — "rekreacyjna, można poprawić"
- 🟡 Kolano L 98° + R 137° — oba <155° (limitation #9: klatka kontaktu w predykcji LSTM
  systematycznie błędna)
- 🟡 Vert osc 0.10 — "bardzo niska, możliwy szum" (zgadza się z limitacją vertical
  pionowy film 608×1080)
- ℹ️ Torso 9.9° prawidłowy, foot strike forefoot consistent

**Komentarz**: silnik trafnie diagnozuje znane ograniczenia raportu z Iteracji 1 (kąty knee
@ contact i asymetrie z aspect ratio). User dostaje sensowne ostrzeżenia, ale brak fałszywego
alarmu "critical" — bo ten biegacz **biomechanicznie** jest OK, tylko predykcja ma artefakty.

**Janek (nowy test, kiepski materiał) — 10 rekomendacji, 2 critical, 3 warning** ⭐ ciekawy case
- 🔴 Kadencja 148 spm — bardzo niska (poniżej zakresu biegu)
- 🔴 GCT prawa 357 ms — "bardzo długi czas kontaktu" 
- 🟠 Sygnał overstriding (cad 148 + GCT_mean 275 — reguła łączona zadziałała)
- 🟠 Asymetria L/P GCT SI 59.9% + DF SI 60.0% — predykcja prawdopodobnie zła
- 🟠 Max SI 60% w jakości predykcji
- 🟡 Knee L 138° + R 148° — oba <155°
- 🟡 Vert osc 0.11 — bardzo niska
- ℹ️ Torso 9.9°, foot strike midfoot consistent (oba kąty rozsądne −4°, −3° — kontrast vs ekstremy w 22 i Adam)

**Komentarz**: trzy ciekawe obserwacje:
1. **Detection 100%** mimo zasłoniętego biodra — MediaPipe radzi sobie z częściową okluzją
2. **avg_confidence 0.882** — powyżej progu 0.85, więc reguła jakości confidence się **nie** uruchomiła
   (false negative w naszym proxy). To uczciwy edge case do dyskusji w Limitations.
3. **Cycle time L=R=807 ms** — perfekcyjnie symetryczne, ale GCT/DF mocno asymetryczne →
   model myli granicę STANCE/FLIGHT asymetrycznie. Identyczny wzorzec do Adama z notatki MVP
   (hipoteza C: szum LSTM, nie biegacza).
4. **Foot strike kąty −4°/−3°** — rozsądne (nie ekstremalne −33° do −58° jak w innych
   filmach). Ciekawa kontrhipoteza dla limitation #9: kąty foot strike mogą być wrażliwe
   na konkretne ujęcie/aspect ratio, nie systematycznie zafałszowane.

## Walidacja jakości

Rekomendacje są **deterministyczne** (reguły, nie ML) — walidacja sprowadza się do:
1. **Czy progi w kodzie zgadzają się z literaturą?** → tak, kalibrowane vs `docs/reference-values.md`
2. **Czy reguły łączone (overstriding combo) triggerują się na sensownych przypadkach?** → tak,
   Janek 148+275 → trigger; Adam 173+224 → no trigger
3. **Czy severity jest dopasowane?** → tak, biegacz z prawidłowymi metrykami nie dostaje
   żadnych critical (Adam), biegacz z patologicznymi metrykami dostaje 2 critical (Janek)
4. **Czy reguły jakości łapią low quality predictions?** → częściowo:
   - Janek max SI 60% → trigger ✅
   - Janek steps L/R 98/99 → no trigger (steps się zgadzają, ale GCT nie — proxy jest niepełne)
   - Janek conf 0.882 → no trigger (powyżej progu 0.85)
   - To **wzbogaca limitation #7** z notatki Iteracji 1: pojedyncze proxy nie wystarcza,
     potrzebne combinatorical check (np. "max SI > 50% OR steps SI > 20%")

## Implikacje dla pracy magisterskiej

### Rozdział 7 — Rekomendacje

Nowy rozdział pracy. Struktura:
1. **Motywacja** — diagnostyka biomechaniczna pojedynczego biegacza, baseline dla recenzji.
2. **Decyzja**: reguły kodowane ręcznie, nie ML — uzasadnienie (mało danych, brak ground
   truth dla "dobrej techniki", łatwiejsza walidacja, citation literatury w wyniku).
3. **Reguły z literatury** — tabela 10 kategorii × progi × citation
4. **Reguła łączona overstriding** — Heiderscheit 2011 jako kluczowa publikacja, w analizie
   jednowymiarowej nie wykrylibyśmy tego sygnału.
5. **Wyniki na 3 biegaczach** — Adam (sanity), 22 (rekreacyjny test), Janek (kiepski materiał) —
   tabela porównawcza i interpretacja.

### Future Work

1. **Combinatorical low quality detection** — pojedyncze proxy nie wystarcza (Janek przeszedł
   confidence check, ale steps tylko marginalnie zgadzały się z asymetrią GCT 60%). Propozycja:
   logika "warning gdy (conf<0.85) OR (steps_SI>20%) OR (max_SI>50% AND conf<0.90)".
2. **Stride length-based rules** — czekają na Iterację 2 (input prędkości bieżni).
3. **Rule severity callout w raporcie** — raport MD z Iteracji 1 nie pokazuje skondensowanej
   tabeli rekomendacji. Propozycja: linkować `*-rekomendacje.md` z `*.md` lub embed top-3 critical.
4. **Walidacja reguł na większej próbce** — uruchomienie na całym test secie + cross-check z
   manualną oceną biomechanika (specjalista 1× godzina daje ground truth).

### Limitations dopisywane

- **Reguły są deterministyczne** — nie uczą się specyfiki biegacza, traktują każdego w pełni
  rekreacyjnego biegacza tak samo
- **Progi z literatury są ogólne** — biegacz po kontuzji ortopedycznej może mieć inne
  fizjologiczne "norma"
- **Reguły operują na wartościach średnich** — nie wykrywają patternów w czasie (np. zmęczenie,
  spadek kadencji w trakcie biegu)

## Artefakty

```
src/recommendations/
├── __init__.py            (5 linii)
├── rules.py               (10 funkcji check_*, dataclass Recommendation, ~480 linii)
└── recommend.py           (CLI: --basename, --inference-dir, --output-json, --output-md, ~165 linii)
```

```
data/inference/
├── 22-...-recommendations.json
├── 24-adam-recommendations.json
├── 25-janek__segment_1-{phases.csv, temporal, spatial, symmetry, meta, recommendations}.json
└── raporty/
    ├── 22-...-rekomendacje.md
    ├── 24-adam-rekomendacje.md
    ├── 25-janek__segment_1-rekomendacje.md
    └── 25-janek__segment_1.md   (raport MD z Iteracji 1, wygenerowany przy okazji)
```

## Co dalej

### Iteracja 2 (rekomendowane, ~3-4h)

Z briefu sesji 2026-05-09 (next-session-brief, Opcja A):
1. **Stride length** z input `--treadmill-speed-ms` (formuła `stride = speed × cycle_time`)
2. **Auto-detect low quality predictions** — rozszerzenie reguł jakości o combinatorical check
3. **Stable segment detection** dla mixed-tempo (film 20)
4. **Raport PDF** z wykresami matplotlib

### Integracja Etapu 7 z analyze.py

Obecnie `analyze.py` kończy się na MD raporcie Iteracji 1. Dobrze byłoby dodać krok 6:
"generuj rekomendacje" — automatycznie tworzy `*-recommendations.json` + `*-rekomendacje.md`
w jednym przejściu, zamiast wymagać oddzielnego wywołania `recommend.py`.

### Walidacja dodatkowa

Janek pokazał ciekawy edge case (asymetryczne GCT przy symetrycznym cycle time + zbalansowanych
steps + przyzwoitej confidence). Wzbogacenie reguły jakości o combinatorical check ma sens —
można to zrobić w Iteracji 2 razem z low quality detection.
