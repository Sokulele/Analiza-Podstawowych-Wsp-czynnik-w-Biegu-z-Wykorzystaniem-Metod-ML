# 2026-05-14 — Sesja C: walidacja foot strike pattern ✅

**Opis dla agenta:** Walidacja foot strike pattern, poprawki algorytmu i wyniki

**Słowa kluczowe:** foot strike, heel, midfoot, forefoot, walidacja

---

## 2026-05-14 — Sesja C: walidacja foot strike pattern ✅

### Zrobione

- **Nowy skrypt** `src/visualization/render_foot_strike_entries.py`: dla danego biegacza
  wybiera N (domyślnie 3) klatek entry-into-LEFT_STANCE i N entry-into-RIGHT_STANCE
  równomiernie rozłożonych w filmie, liczy kąt foot strike na każdej klatce (identyczna
  konwencja co `compute_foot_strike_pattern`) i renderuje PNG ze szkieletem MediaPipe
  + paskiem info (klatka + strona + kąt + klasyfikacja, kolor paska wg klasyfikacji).
- **18 PNG** wygenerowanych (3 biegaczy × 2 nogi × 3 klatki) w
  `data/visualizations/foot_strike_validation/{22,24-adam,25-janek}/`.
- **Walidacja wizualna** użytkownika:
  - **Janek**: kąty −12° do +5° **zgadzają się** wizualnie z midfoot strike. Metoda działa.
  - **Adam**: prawa noga OK (−12°), lewa przesadzona perspektywą (−33° do −56°). Asymetria
    to **artefakt kamery od dołu**, nie biomechaniki.
  - **22**: kąty −82° do −160° to **artefakt pionowego wideo**, geometrycznie nonsens.
- **Decyzja**: hipoteza "systematyczny błąd metody" z limitation #9 **odwołana**.
  Zastąpiona "foot strike jest wrażliwy na perspektywę — wiarygodny przy ujęciu z boku".

### Implementacja mityganta

- `spatial_metrics.py`: `compute_foot_strike_pattern` dorzuca klucz `low_confidence: True`
  per noga, gdy `|mean_angle| > 45°`. Próg wybrany na podstawie walidacji (Janek ≤12°,
  Adam border 33°, 22 ≥82°).
- `rules.py`: nowa reguła `foot_strike_low_confidence` (warning, citation "Walidacja
  wizualna 2026-05-14 (Sesja C)"). Sprawdza flagę `low_confidence` lub fallback
  `abs(mean)>45°` dla legacy spatial.json. Gdy fire — **blokuje** reguły semantyczne
  (`consistent`/`inconsistent`), bo przy tych kątach klasyfikacja jest artefaktem.

### Weryfikacja (smoke test)

| Biegacz | Przed Sesją C | Po Sesji C | Komentarz |
|---|---|---|---|
| 22 | 0/3/5/2 = 10 | **0/4/5/1** = 10 | `foot_strike_consistent` (info) → `foot_strike_low_confidence` (warning) ✅ |
| Adam | 0/2/1/5 = 8 | 0/2/1/5 = 8 | bez zmian (poniżej progu 45°) ✅ |
| Janek | 3/3/3/2 = 11 | 3/3/3/2 = 11 | bez zmian (poniżej progu 45°) ✅ |

Nowa reguła nie produkuje false positives — łapie tylko 22 (pionowe wideo).

### Notatka thesis

`docs/thesis-notes/2026-05-14-sesja-c-foot-strike-walidacja.md` — pełna sesja
(metodyka, predykcja referencyjna, walidacja wizualna per biegacz, reformulacja
limitation #9, implementacja, weryfikacja, otwarte pytania).
Limitation #9 w `2026-05-09-iteracja1-test-set.md` dopisana sekcją "Po dalszej pracy"
(zgodnie z konwencją CLAUDE.md: nie nadpisywać notatek, dopisywać).

### Do zrobienia w następnej sesji

Plan kolejnych sesji (z briefu pre-C, wciąż aktualny):
1. **Stable segment detection** + **PDF generator** — odłożone z Sesji B, kosmetyka.
2. **Walidacja Etapu 7 na własnym filmie biegowym** użytkownika.
3. **Pisanie pracy magisterskiej** — rozdziały 6 i 7 mają komplet materiału po A+B+C.

Wszystkie pozycje **warunkowe** — Sesja C zamyka ostatnią nierozwiązaną kwestię
metody. Decyzja o priorytecie należy do użytkownika.

### Otwarte sprawy (zaktualizowane)

- Limitation #9 **rozwiązana** (z mitygantem w kodzie).
- Limitation #1 (combinatorical quality) **częściowo rozwiązana** w Sesji B.
- Limitation #8 (stable segment detection) **nierozwiązana** — odłożona w Sesji B.
- Bug `postprocess_median.predict_lstm` — niezmieniony.
- Slug strategy + non-determinizm MediaPipe — niezmienione (do Limitations pracy).

---
