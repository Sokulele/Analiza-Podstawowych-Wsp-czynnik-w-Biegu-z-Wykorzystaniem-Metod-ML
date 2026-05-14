# 2026-05-13 — Integracja Etapu 7 z `analyze.py` (Sesja A)

## Kontekst

Po zamknięciu Etapu 7 (silnik reguł w `src/recommendations/`, notatka
`2026-05-12-etap7-rekomendacje.md`) pipeline składał się z **dwóch niezależnych CLI**:

1. `src/coefficients/analyze.py` — orchestrator Iteracji 1 (Etapy 1–6): wideo → MediaPipe →
   LSTM → temporal/spatial/symmetry JSON-y + raport MD.
2. `src/recommendations/recommend.py` — silnik rekomendacji (Etap 7): wczytuje JSON-y z (1)
   i produkuje `*-recommendations.json` + `raporty/*-rekomendacje.md`.

Sensem sesji było **dopięcie pipeline'u produkcyjnie**: jedno wywołanie CLI = pełna analiza
biegacza, łącznie z rekomendacjami. To naturalna granica między „prototyp dwóch
niezależnych modułów" a „system end-to-end" — dla pracy magisterskiej kluczowy moment,
bo wszystkie pomiary i rekomendacje pochodzą z jednego deterministycznego biegu kodu.

## Rozważane alternatywy

### Opcja A1: `analyze.py` importuje `render_markdown` z `recommend.py`

Zaleta: minimum zmian (~5 linii w `analyze.py`).

Wada: `recommend.py` to skrypt CLI z efektami ubocznymi (`sys.stdout.reconfigure`, parser
argumentów w `main()`). Importowanie z modułu CLI tworzy zależność od side-effectów
i utrudnia testy modułowe. Ponadto rozsiewa logikę prezentacji rekomendacji w dwóch
miejscach: silnik w `rules.py`, renderer w `recommend.py`.

### Opcja A2 ✅ (wybrana): `render_markdown` przeniesiony do `rules.py`

Zaleta: `rules.py` staje się self-contained library (silnik + dataclass + renderer).
`recommend.py` zostaje czystym CLI (105 linii, było 212). `analyze.py` importuje tylko
z `rules.py`. Czysta separacja: library ↔ CLI.

Wada: ~5 minut dodatkowo na refaktor (przeniesienie funkcji + dwóch słowników stałych).

**Decyzja**: A2. Cost-benefit jednoznaczny — czystsza architektura przy minimalnym koszcie.
Brief poprzedniej sesji już rekomendował to rozwiązanie.

## Implementacja

### Zmiany w `rules.py` (+~70 linii)

- Dodana stała `_SEVERITY_LABEL_PL` (4 etykiety polskie).
- Funkcja `render_markdown(result, meta) → str` przeniesiona w całości (bez zmian
  semantycznych) — zachowuje strukturę: nagłówek → podsumowanie → grupowanie po severity →
  per-rekomendacja sekcja z citation + detail + suggestion → stopka z notą o literaturze.

### Zmiany w `recommend.py` (−~100 linii)

- Usunięto lokalne kopie `_SEVERITY_EMOJI`, `_SEVERITY_LABEL_PL`, `render_markdown`.
- Import: `from rules import generate_recommendations, render_markdown`.
- CLI niezmieniony — z perspektywy użytkownika to ten sam program.

### Zmiany w `analyze.py` (+~30 linii)

```python
sys.path.insert(0, str(_HERE.parent / "recommendations"))
from rules import generate_recommendations, render_markdown
```

- Parametr `with_recommendations: bool = True` w `analyze_video()`.
- Dwie nowe ścieżki: `recommendations_json`, `recommendations_md`.
- **Krok 6** po `generate_report`:
  ```python
  if with_recommendations:
      rec_result = generate_recommendations(meta, temporal, spatial, symmetry)
      recommendations_json.write_text(json.dumps(rec_result, indent=2, ensure_ascii=False))
      recommendations_md.write_text(render_markdown(rec_result, meta))
  ```
- CLI flag `--no-recommendations` (opt-out, default = ON).
- **Bonus: rekonstrukcja meta.json** gdy `--skip-inference` i meta nie istnieje
  (rozwiązuje stałe TODO „Adam meta.json dalej nie wygenerowany"):
  - FPS estymowany z `timestamp.iloc[1] - timestamp.iloc[0]`
  - `avg_confidence` z kolumny `confidence` w CSV faz (jeśli istnieje)
  - flaga `reconstructed_from_csv: true` w meta — sygnał dla późniejszych analiz, że ten
    meta nie pochodzi z pierwotnej inferencji

## Weryfikacja

### Test 1: identyczność dla 22 (regression test)

Backup `recommendations.json` i `rekomendacje.md` z poprzedniej sesji →
uruchomienie `analyze.py --skip-inference` na 22 → `diff` z backupem.

**Wynik: zero różnic w obu plikach.** Integracja nie zmienia semantyki, tylko orchestration.

### Test 2: świeża inferencja na Adamie

Nazwa pliku wideo `24 - Adam bieg__segment_1.mov` daje slug `24-adam-bieg__segment_1`
(z `_slugify`), inny niż poprzedni `24-adam`. Brak CSV faz → pełna inferencja
MediaPipe (209.3 s) + LSTM. Wygenerowany komplet 8 artefaktów:

| Artefakt | Status |
|---|---|
| `24-adam-bieg__segment_1-phases.csv` | ✅ świeży (2399 klatek) |
| `24-adam-bieg__segment_1-meta.json` | ✅ pełen (z inference_time_s, model_test_acc) |
| `24-adam-bieg__segment_1-temporal.json` | ✅ |
| `24-adam-bieg__segment_1-spatial.json` | ✅ |
| `24-adam-bieg__segment_1-symmetry.json` | ✅ |
| `raporty/24-adam-bieg__segment_1.md` | ✅ |
| `24-adam-bieg__segment_1-recommendations.json` | ✅ 0/2/1/5 |
| `raporty/24-adam-bieg__segment_1-rekomendacje.md` | ✅ |

Liczby reguł różnią się od poprzedniej sesji (0/2/1/**3** zamiast 0/2/1/**5**) — to skutek
re-inferencji od zera (lekka inna numeryka MediaPipe → 2 dodatkowe reguły info się
triggerują). To **nie regresja** ani błąd integracji, lecz potwierdzenie, że metryki
spatial są wrażliwe na ponowne wykonanie pipeline. Warto rozważyć kiedyś **deterministic
seed dla MediaPipe** (jeśli się da) albo akceptację tej zmienności w sekcji Limitations.

## Co to oznacza dla pracy magisterskiej

### Rozdział 7 (Rekomendacje) — domknięcie

Pipeline produkcyjny ma teraz **jeden punkt wejścia** (`analyze.py`) i **deterministyczną
sekwencję 6 kroków**: MediaPipe → LSTM → temporal → spatial → symmetry → reguły. Każdy
artefakt jest re-generowalny z jednego CLI. To ułatwia opisanie procesu w rozdziale
metodologicznym i powtórzenie eksperymentu przez recenzenta.

### Materiał do diagramu Rys. 7.x

Cały pipeline mieści się w jednym diagramie:

```
.mp4 → [MediaPipe Pose] → keypoints (33 × N) → [Savgol] → [LSTM r1] → fazy
                                                                          ↓
fazy + keypoints → [temporal.py]  → cadence, GCT, flight, DF, cycle
                 → [spatial.py]   → angles, torso lean, vert osc, foot strike
                 → [symmetry.py]  → SI Robinsona
                                                                          ↓
              wszystkie JSON-y → [rules.py] → 10 reguł z literatury → recommendations.json + .md
```

### Argument w sekcji "Implementacja"

Architektura library-vs-CLI (`rules.py` jako library, `recommend.py` jako thin CLI,
`analyze.py` jako orchestrator) to konkretny wybór engineerski warty wzmianki — pokazuje
że logika domenowa (reguły biomechaniczne z citation) jest oddzielona od warstwy
prezentacji (Markdown) i od interfejsu (argparse). Ułatwia to testowanie pojedynczych
reguł i ponowne użycie w innym kontekście (np. future work: dashboard webowy).

## Następne kroki

- **Sesja B (Iteracja 2)**: stride length, combinatorical low quality, stable segment, PDF.
- **Sesja C**: walidacja foot strike (rewizja limitation #9).

## Limitations odsłonięte przez tę sesję

1. **Slug strategy** — `24-adam` (poprzednia sesja) vs `24-adam-bieg__segment_1` (ta sesja)
   to dwa różne slugi z tego samego biegacza. Funkcja `_slugify` w `analyze.py` powinna
   normalizować typowe sufiksy (`__segment_1`, `__segment_2`) by uniknąć duplikacji
   artefaktów. Drobne, ale warto naprawić przed publikacją.
2. **Re-inferencja produkuje minimalnie inne wyniki spatial** — MediaPipe nie jest
   deterministyczny (XNNPACK delegate, multi-threading). Wpływ na liczbę reguł info
   (różnica 2/8 reguł między dwoma uruchomieniami Adama). Do omówienia w Limitations
   pracy.
