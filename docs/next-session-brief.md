# Briefing na następną sesję

> **Data ostatniej sesji**: 2026-05-12 (Etap 7 — moduł rekomendacji biegowych)
> **Data tego briefu**: 2026-05-12 (koniec sesji)

---

## 🔹 Co Claude MUSI przeczytać na starcie (w tej kolejności)

1. **`CLAUDE.md`** — zasady projektu, pipeline, sekcja "Notatki do pracy magisterskiej (auto-zapis)" — **obowiązuje automatycznie**
2. **`History.md`** — log chronologiczny. Najnowsze wpisy: 2026-05-09 (Iteracja 1) + **2026-05-12 (Etap 7)**
3. **`docs/thesis-notes/README.md`** — index notatek (10 notatek)
4. **`docs/thesis-notes/2026-05-12-etap7-rekomendacje.md`** — **najnowsza, kluczowa**: silnik reguł, 10 funkcji `check_*`, wyniki na Adamie/22/Janku, edge case Janka
5. **`docs/thesis-notes/2026-05-09-iteracja1-test-set.md`** — kontekst Iteracji 1 (raporty per biegacz)
6. **`src/recommendations/rules.py`** — silnik reguł z citation (referencja do progów + reguły łączone)
7. **`src/coefficients/analyze.py`** — orchestration, do której Etap 7 nie jest jeszcze zintegrowany

---

## 🔹 Co Claude MUSI wiedzieć o projekcie

### Czym jest projekt

Praca **magisterska** — system analizujący wideo biegu na bieżni i obliczający współczynniki biomechaniczne z rekomendacjami. **Praca > produkt**.

Pipeline: wideo → MediaPipe (33 keypointy) → klasyfikator faz (LSTM r1 + aspect fix, 70.9% test acc) → współczynniki → **rekomendacje (Etap 7 ✅)**.

### Stan na ten moment (2026-05-12, koniec sesji — po Etapie 7)

- Etapy 1-4 zrobione (środowisko, ekstrakcja, etykietowanie, dataset 15 + Janek = 16 filmów)
- **Etap 5 — klasyfikator** ✅✅✅ — LSTM r1 + aspect fix = 70.9% test acc, F1 0.709 (primary)
- **Etap 6** ✅ MVP + Iteracja 1 (pipeline + raporty per biegacz). Iteracje 2-3 dalej do zrobienia
- **Etap 7 — rekomendacje** ✅ silnik reguł działa, 3 biegacze przetestowani

### Wyniki Etapu 7 (test na 3 biegaczach)

| Biegacz | conf | Kadencja | GCT L/R | Max SI | crit/warn/watch/info | Komentarz |
|---|---|---|---|---|---|---|
| Adam (train, sanity) | 0.91 | 173 ℹ️ | 203/245 | 18.7% | 0 / 2 / 1 / 3 | 0 critical = pipeline nie generuje fałszywych alarmów |
| 22 (test) | 0.89 | 163 🟡 | 285🟠/226 | 35.0% | 0 / 3 / 5 / 2 | sensowne ostrzeżenia o asymetrii + jakości predykcji |
| 25 Janek (nowy, kiepski materiał) | 0.88 | **148** 🔴 | 193/**357**🔴 | **60.0%** | **2** / 3 / 3 / 2 | edge case: combinatorical low quality detection potrzebny |

### Janek — kluczowy edge case do Iteracji 2

Janek przeszedł pojedyncze proxy "low quality":
- avg_confidence 0.882 > próg 0.85 ✅ (nie triggeruje)
- steps L/R 98/99 zbalansowane ✅ (nie triggeruje steps_SI > 20%)
- max SI 60% → triggeruje "max SI > 30%" ✅

…ale GCT/DF asymetria **60%** to ewidentny błąd predykcji granicy STANCE per noga. Pojedyncze proxy
nie wystarcza — należy zaimplementować **combinatorical check** (np. `conf<0.85 OR steps_SI>20% OR
(max_SI>50% AND conf<0.90)`).

Druga obserwacja Janka: **foot strike kąty −4°, −3°** (rozsądne!) — to kontrhipoteza dla
limitation #9 z notatki Iteracji 1 (ekstremalne −33°/−58° mogą być wrażliwe na konkretne ujęcie,
nie systematyczne).

### Architektura modułu rekomendacji (Etap 7)

```
src/recommendations/
├── __init__.py        (eksport API)
├── rules.py           (10 funkcji check_*, dataclass Recommendation, ~480 linii)
└── recommend.py       (CLI: --basename / --inference-dir / --output-json / --output-md, ~165 linii)
```

**Najprostsze użycie**:
```bash
.venv/Scripts/python.exe src/recommendations/recommend.py \
    --basename 22-running-analysis-with-physiotherapist
# → data/inference/22-...-recommendations.json
# → data/inference/raporty/22-...-rekomendacje.md
```

10 reguł z citation: Heiderscheit 2011 (kadencja, overstriding), Novacheck 1998 (tułów, kolano),
Souza 2016 (GCT, duty factor), Diaz 2019 (vert osc), Robinson 1987 (symetria), Daoud 2012 (foot strike).

**Reguła łączona overstriding** (Heiderscheit 2011) — najbardziej wartościowa: cad<160 AND GCT_mean>270.

### Co JESZCZE nie jest zintegrowane

`analyze.py` (Iteracja 1) generuje 4 JSON-y + raport MD, ale **nie wywołuje `recommend.py`**.
Trzeba osobno uruchomić CLI Etapu 7. Naturalna kontynuacja: dodać krok 6 "generuj rekomendacje"
do `analyze.py`.

---

## 🔹 Plan kolejnych sesji — ustalony 2026-05-12 przez użytkownika

Po Etapie 7 user ustalił **konkretną kolejność** sesji:

> **Sesja A → Sesja B → Sesja C**, jedna po drugiej.

### ⏭️ Sesja A (NASTĘPNA) — Integracja Etapu 7 z analyze.py (~30-60 min)

**Co zrobić**:

1. **Edytuj `src/coefficients/analyze.py`**:
   - Dodaj import `generate_recommendations` z `src/recommendations/rules.py`
     i `render_markdown` z `src/recommendations/recommend.py` (lub przenieś renderer do
     `rules.py`, jeśli to upraszcza importy — patrz sekcja "Decyzja importów" niżej)
   - Po kroku 5 (generate_report Iteracji 1) dodaj **krok 6**:
     - `result = generate_recommendations(meta, temporal, spatial, symmetry)`
     - Zapisz `{slug}-recommendations.json`
     - Zapisz `raporty/{slug}-rekomendacje.md`
   - Dodaj wpisy do `paths` dict zwracanego z `analyze_video`: `recommendations_json`, `recommendations_md`
   - Opcjonalny CLI flag `--no-recommendations` (domyślnie krok 6 ZAWSZE się wykonuje)

2. **Decyzja importów** — `recommend.py` (CLI) zawiera funkcję `render_markdown`, która
   jest potrzebna `analyze.py`. Dwie opcje:
   - **A1 (prostsza)**: importuj `render_markdown` z `src.recommendations.recommend` —
     potencjalnie wykona też side-effecty CLI (sys.stdout.reconfigure). Zweryfikuj że nie
     wykonuje argparse przy imporcie (powinien być chroniony `if __name__ == "__main__"`).
   - **A2 (czystsza)**: przenieś `render_markdown` z `recommend.py` do `rules.py` (logika
     prezentacji + dane). `recommend.py` zostaje CLI-only.

   Rekomendowane: **A2** (cleaner separation), zajmie ~5 min dodatkowo.

3. **Test E2E na 22 i Adamie**:
   ```bash
   .venv/Scripts/python.exe src/coefficients/analyze.py \
       --video "data/videos/22 - Running Analysis with Physiotherapist.mp4" \
       --skip-inference
   # Sprawdź: powstają 22-...-recommendations.json + raporty/22-...-rekomendacje.md

   .venv/Scripts/python.exe src/coefficients/analyze.py \
       --video "data/videos/24 - Adam bieg__segment_1.mov" \
       --skip-inference
   # Sprawdź: powstaje brakujący 24-adam-meta.json + 24-adam-recommendations.json + raport rekomendacji
   ```

4. **Verify**: `data/inference/22-*-recommendations.json` + `data/inference/raporty/22-*-rekomendacje.md`
   powinny istnieć i być identyczne z tym, co generuje `recommend.py` standalone.

5. **(opcjonalnie, jeśli czas)** Update `report_generator.py` — embed top-3 critical/warning
   rekomendacji w sekcji "Wnioski" raportu Iteracji 1 (callout w głównym raporcie zamiast
   linku do osobnego pliku).

**Cel**: 1 CLI = pełna analiza E2E + rekomendacje + raporty. Dopina pipeline produkcyjnie.

### ⏭️ Sesja B (PO A) — Iteracja 2: produkcyjne usprawnienia raportu (~3-4h)

1. **Stride length** z input `--treadmill-speed-ms`, formuła `stride = speed × cycle_time`
   - Nowa metryka w `temporal_metrics.py` (lub osobny moduł)
   - Reguła w `rules.py`: stride < 1.0×wzrost → krok zbyt krótki, > 1.5×wzrost → overstride
     (wymaga input wzrostu lub korzystaj tylko z `stride/cycle_time` proxy)
2. **Combinatorical low quality detection** — Janek edge case z notatki 2026-05-12:
   - Pojedyncze proxy zawiodły (conf 0.882 > 0.85, steps 98/99 balanced, ale GCT/DF SI 60%)
   - Propozycja logiki: `conf<0.85 OR steps_SI>20% OR (max_SI>50% AND conf<0.90)`
3. **Stable segment detection** dla mixed-tempo (film 20):
   - Detekcja outlierów cycle time (> 1.5×median lub < 0.5×median)
   - Statystyki tylko z stable segments
4. **Generator PDF** z wykresami matplotlib:
   - Sygnał Y_hip per cykl, kadencja w czasie, mapa faz
   - `reportlab` lub `matplotlib.backends.backend_pdf`

**Cel**: zamknięcie Etapu 6 produkcyjnie. Iteracja 2 = sufit Etapu 6.

### ⏭️ Sesja C (PO B) — Walidacja foot strike (~1-2h)

1. Wybrać 3-5 klatek entry-into-STANCE per film (Adam, 22, Janek) — render PNG ze szkieletem
2. Manualna inspekcja: jaki rzeczywiście jest wzorzec lądowania w tych klatkach
3. Porównać z predykcją `compute_foot_strike_pattern`
4. **Zaktualizować limitation #9** w notatkach — Janek dał normalne kąty (−4°, −3°),
   więc hipoteza "systematyczny błąd metody" wymaga rewizji (może to wrażliwość na
   ujęcie/aspect ratio, nie systematyczny błąd)
5. Jeśli wzorzec rzeczywiście błędny → naprawa algorytmu `compute_foot_strike_pattern`
   (np. zmiana klatki kontaktu z "entry into STANCE" na "pierwsze 3 klatki STANCE")

**Cel**: rozwiązanie limitation #9 + ostateczne zamknięcie spatial metrics.

### Co po A+B+C

Po C zostaje:
- (warunkowo) Etap 7 walidacja na własnym filmie biegowym
- (opcjonalnie) krok 8 z planu accuracy: ręczna walidacja etykiet
- Pisanie pracy magisterskiej (rozdziały 6 i 7 mają już pełny materiał)

---

## 🔹 Co użytkownik chce osiągnąć dalej (long-term)

1. ✅ **Iteracja 1** (zrobiona): pipeline na test set + analyze.py + raporty per biegacz
2. ✅ **Etap 7** (zrobiony): silnik rekomendacji z literatury
3. ⏭️ **Sesja A**: integracja Etap 7 ↔ analyze.py (krótkie, ~30-60 min) — **kolejna sesja**
4. ⏭️ **Sesja B**: Iteracja 2 (stride length + combinatorical low quality + stable segment + PDF, ~3-4h)
5. ⏭️ **Sesja C**: walidacja foot strike (rewizja limitation #9, ~1-2h)
6. (warunkowo) walidacja na własnym filmie biegowym

---

## 🔹 Znane pułapki — czego NIE zrobić

### Nie dotykać (krytyczne)

- **`data/splits.json`** — fair comparison wymaga identycznego splitu
- **`models/lstm_run1_overfit/`** — to **primary model** (LSTM r1 + aspect fix). Nazwa katalogu mylna ("overfit"), ale po aspect fix już nie overfittuje
- **`models/*_pre_aspect_fix/`** i **`models/*_pre_extension/`** — backupy do rozdziału 5
- **Notatki thesis już napisane** — bez zgody usera. Aktualizuj jako sekcja "po dalszej pracy"
- **CLAUDE.md** — bez zgody usera
- **`src/recommendations/rules.py` progi** — kalibrowane vs `docs/reference-values.md` + literatura. Zmiana progu = zmiana citation (sprawdź źródło przed)

### Reguły rekomendacji — używaj świadomie

- **Severity ordering**: critical → warning → watch → info. Reguły quality_predykcji idą na początek listy
- **Citation jest częścią rekomendacji** — każda zmiana progu wymaga sprawdzenia/aktualizacji źródła
- **Reguły deterministyczne, nie ML** — zgodnie z CLAUDE.md sekcja "Rekomendacje". Nie próbuj uczyć z danych
- **Edge case Janka**: pojedyncze proxy jakości nie wystarczają. Combinatorical check w Iteracji 2

### Tu są open issues z poprzednich sesji

1. **Bug `postprocess_median.predict_lstm`** — pokazuje LSTM r1 = 66.4%, ale metrics.json mówi 70.9%. Niezmieniony.
2. **Foot strike kąty** — Janek kontrhipoteza (−4°, −3° = OK), reszta (−33° do −58°) wymaga walidacji wizualnej
3. **Torso lean 2.3°** Adam — niskie, ale stabilne (możliwy szum keypointów lub running tall)
4. **Adam meta.json** — dalej nie wygenerowany (uruchom `analyze.py --skip-inference` żeby utworzyć)

### Nie robić bez wyraźnego sygnału

- **Hyperparameter sweep LSTM** — sufit ~71% jest niezależny od architektury
- **Augmentacja flip** — wymaga przerobienia auto_label na anatomiczną konwencję (future work)
- **Velocity features** — globalnie regresja
- **Ensemble** — modele mają skorelowane błędy, nie pomaga
- **3D motion capture** — poza scope projektu, ale ważny argument w Limitations
- **Dodawanie reguł bez citation** — każda reguła w `rules.py` ma źródło literackie

---

## 🔹 Szybka pigułka — jeden akapit

Sesja 2026-05-12 zamknęła **Etap 7**: stworzono `src/recommendations/` z silnikiem reguł
biomechanicznych z literatury (Heiderscheit, Novacheck, Souza, Diaz, Robinson, Daoud). 10 funkcji
`check_*` (kadencja, GCT, flight, DF, torso, knee@contact, vert_osc, symetria, foot strike,
jakość predykcji), severity 4-poziomowe, citation w każdej rekomendacji. CLI `recommend.py`
generuje JSON + sekcję MD. Test na 3 biegaczach: Adam (sanity, 0 critical), 22 (test, 3 warning),
**Janek (nowy test z kiepskim materiałem, 2 critical)**. Janek jako edge case ujawnił, że
pojedyncze proxy jakości (conf<0.85, steps_SI>20%, max_SI>30%) nie wystarczają — potrzebny
**combinatorical check** w Iteracji 2. Foot strike Janka **rozsądny** (−4°, −3°) co podważa
hipotezę "systematyczny błąd" z limitation #9. **Ustalony plan kolejnych sesji**: **Sesja A**
(integracja Etapu 7 z `analyze.py` — krótkie, ~30-60 min, test na 22 + Adam) → **Sesja B**
(Iteracja 2: stride length + combinatorical low quality + stable segment + PDF) → **Sesja C**
(walidacja foot strike, rewizja limitation #9).
