# Briefing na następną sesję

> **Ostatnia sesja**: 2026-05-28 (Sesja H: pełna walidacja rozdziału 3 przez usera, kompleksowe poprawki)
> **Następna sesja**: walidacja rozdziału 4 LUB pisanie rozdziału 5 (Współczynniki biegu — wyniki P1)

## Rozdział 3 — OFICJALNIE ZAMKNIĘTY ✅ (2026-05-28)

Wszystkie sekcje 3.1–3.8 przeszły walidację usera. Poprawki sesji H:
- 3.4.3: overfitting, konkatenacja kierunków, ukryty wymiar, parametry, dropout+inferencja, weight decay — wyjaśnione
- 3.4.4: aspect ratio fix rozbudowany (Δx vs Δy, przykład 608×1080)
- Tabela 3.4: „(raw)/(eng.)" → „(surowe)/(inżynierowane)"
- 3.5 wstęp: „temporalne", std z cykli, „osobno L/P"
- 3.5.1: przykład run-length encoding (12 klatek → 5 segmentów)
- 3.5.2 GCT: naprawiony wzór (pełna suma)
- 3.5.3: noga oporowa / faza wahadła zdefiniowane, oscylacja pionowa rozbita na 4 wzory, foot strike θ wyjaśnione
- 3.5.4 symetria: pełne wyjaśnienie SI Robinsona, czemu dla każdego współczynnika osobno
- 3.6: flaga `critical` wyjaśniona (ryzyko biomechaniczne + artefakty predykcji)
- 3.7: usunięta sekcja „Ograniczenia podziału" (przeniesione do rozdz. 8)
- 3.8: macro F1 vs micro F1, uzasadnienie wyboru
- Notacja: wszystkie `°` → `^\circ` (math mode), liczby klatek w prozie → `≈`
- Anti-AI: usunięte „Słownie:", „Stąd sformułowanie...", meta-komentarze o własnym tekście

---

## Co przeczytać na starcie (MINIMALNA lista)

1. **Ten plik** — kontekst + co robić
2. **`CLAUDE.md`** — zasady kodowania, pipeline, konwencje (ładowane automatycznie)
3. **`thesis/chapters/05-wspolczynniki.tex`** — aktualny stan rozdziału do pisania

**Sięgnij głębiej TYLKO gdy potrzebujesz konkretnych danych:**
- Liczby/metryki modeli → `docs/thesis-notes/figures/comparison_summary.json`
- Wyniki per-film → `docs/thesis-notes/figures/per_file_test.md`
- Decyzje metodologiczne → `docs/thesis-notes/2026-05-14-temat-pracy-finalny.md`
- Wyjaśnienia pojęć → `docs/thesis-notes/2026-05-14-wyjasnienia-pojec-do-pisania.md`
- Pełna historia → `history.md` (1260+ linii — NIE czytaj w całości)

---

## Projekt w jednym akapicie

Praca magisterska SGGW: *"Analiza podstawowych współczynników biegu przy pomocy uczenia maszynowego"*. Pipeline: wideo bieżni (ujęcie z boku) → MediaPipe Pose (33 keypointy) → Savitzky-Golay → auto-etykietowanie faz (peak-based) → klasyfikator BiLSTM (70.9% test acc) → 12 współczynników biomechanicznych (5 temporalnych + 7 przestrzennych) → 13+ reguł rekomendacji z literaturą. Wszystkie etapy implementacyjne (1-7) zakończone. Praca jest gotowa do pisania bez dodatkowych eksperymentów.

---

## Stan pracy magisterskiej (thesis/)

**Szablon**: SGGW-thesis.cls, `\MAGISTERSKAtrue`, `\WZIMtrue`
**Kompilacja**: `pdflatex main.tex` (3×) lub `latexmk -pdf main.tex`
**Metadane**: TODO w `main.tex` linie 13-19 (autor, album, promotor)

### Rozdziały — stan na 2026-05-24 (po sesji F)

| # | Plik | Tytuł | Stan | Materiał źródłowy |
|---|---|---|---|---|
| 1 | `01-wstep.tex` | Wstęp | **✅ NAPISANY** (motywacja, 3 pytania badawcze, cel/zakres, struktura; user waliduje) | `2026-05-14-temat-pracy-finalny.md` |
| 2 | `02-state-of-the-art.tex` | Stan wiedzy | **✅ NAPISANY** (5 sekcji, ~21 cytatów, user waliduje) | `2026-05-14-research-podobnych-prac.md` |
| 3 | `03-materialy-metody.tex` | Materiały i metody | **✅ GOTOWY** (3.1–3.8). UWAGA: sekcja 3.6 ZNACZNIE SKRÓCONA — pełny silnik reguł przeniesiony do rozdz. Rekomendacje, w 3.6 został tylko akapit + odesłanie. | CLAUDE.md, history.md, src/ |
| 4 | `04-klasyfikator.tex` | Klasyfikator faz (P2) | **✅ GOTOWY** (4.1–4.7, user waliduje) | `figures/comparison_*.md`, `metrics.json` |
| ~~5~~ | ~~`05-wspolczynniki.tex`~~ | ~~Współczynniki biegu (P1)~~ | **❌ USUNIĘTY z pracy** (2026-05-28). Plik zostaje jako draft, nie inputowany. | — |
| 6 | `06-rekomendacje.tex` | System rekomendacji | **✅ NAPISANY** (user waliduje). Pełny opis silnika reguł PRZENIESIONY z 3.6 + dodany przykład raportu (Adam). | `2026-05-12-etap7-rekomendacje.md`, `rules.py` |
| 7 | `07-wrazliwosc.tex` | Wrażliwość (P3) | szkielet TODO | `2026-05-14-sesja-c-foot-strike-walidacja.md` |
| 8 | `08-dyskusja-wnioski.tex` | Dyskusja i wnioski | **✅ NAPISANY** (odpowiedzi na pytania, wkład, ograniczenia, implikacje, dalsze badania, wnioski; user waliduje) | wszystkie rozdziały |

## 🎉 CAŁA PRACA MA PIERWSZY SZKIC (2026-06-03)

Wszystkie 7 rozdziałów napisane. Konwencje utrzymane: 1. osoba, pełne zdania bez kodów P1/P2/P3 i H1–H7, `^\circ`, `≈` dla klatek, „klatek" nie „okien", brak meta-komentarzy AI, brak duplikacji (cross-referencje zamiast powtórzeń). Bibliografia 32/32 cytowana (vincent dodany w Wstępie). Walidacja Garmin (Wojtek) wpisana do rozdz. Wrażliwość + 4.6.

**Zostało (NIE treść rozdziałów):**
- `main.tex`: streszczenie PL/EN (pisać na końcu) + metadane (autor, album, promotor) — user uzupełnia
- Walidacja całości przez usera (czyta i dopytuje)
- Opcjonalnie: poprawić cytat Diaz→Novacheck w `rules.py`/raportach (kod, nie tekst pracy)
- Opcjonalnie: render klatek foot strike dla Wojtka (wzrokowe potwierdzenie kąta kamery)
- Pierwsza kompilacja `pdflatex` (sprawdzić czy wszystko się składa)

**Kolejność pisania**: ~~3~~ → ~~4~~ → ~~5 (usunięty)~~ → 7 → 6 → 2 → 1 → 8

**Nowa struktura pracy (8 → 7 rozdziałów):**
1. Wstęp | 2. State of the art | 3. Materiały i metody | 4. Klasyfikator | 5. ~~Współczynniki~~ → **Rekomendacje** (był 6) | 6. **Wrażliwość** (był 7) | 7. **Dyskusja** (był 8)
LaTeX numeruje automatycznie, ale w odwołaniach `\ref{ch:rekomendacje}` itp. działają niezależnie od numeru.

### Bibliografia

`chapters/bibliography.tex` — **28 zweryfikowanych wpisów** (dodany Kingma 2015 — Adam optimizer).
Diaz 2019 usunięty (niepotwierdzony). Wszystkie wpisy mają DOI (poza Goodfellow/PyTorch/OpenCV).

---

## Kluczowe liczby (żeby nie szukać)

| Metryka | Wartość |
|---|---|
| Dataset | 15 filmów (nr 1–13, w tym 5a/5b i 6a/6b), ~12 biegaczy, 12 087 klatek |
| Klasy | LEFT_STANCE / RIGHT_STANCE / FLIGHT (3 klasy, ~33% każda) |
| Split | Train 10 filmów (72%), Val 2 (9%), Test 3 (19%) |
| RF v1 (raw) test | 62.7% acc, F1 0.617 |
| RF v2 (engineered) test | 67.0% acc, F1 0.671 |
| LSTM r1 + aspect fix test | **70.9% acc, F1 0.709** ← PRIMARY |
| LSTM r2 + aspect fix test | 68.2% acc, F1 0.681 |
| Współczynniki | 12 (5 temporalnych + 7 przestrzennych) |
| Reguły rekomendacji | 13+ z literaturą (Heiderscheit, Novacheck, Souza, Daoud, Robinson) |
| Walidacja pipeline | 3 biegaczy (Adam=train, 22=test, Janek=edge case) |

---

## Preferencje usera (z memory)

- **Pisanie sekcja po sekcji** — NIE cały rozdział naraz. Jedna \section{} na raz.
- **Komentarze w kodzie po polsku**, nazwy zmiennych po angielsku
- **Proaktywnie zapisuj** notatki do `docs/thesis-notes/` i wyjaśnienia do `2026-05-14-wyjasnienia-pojec-do-pisania.md`
- **Limit stron zniesiony** — może być więcej niż 60, wstawiamy kod/wykresy/diagramy
- **Własny filmik z biegu** — user jeszcze nie nagrał, nie blokuje pisania

---

## Czego NIE dotykać

- `data/splits.json` — fair comparison
- `models/lstm_run1_overfit/` — primary model
- `models/*_pre_aspect_fix/`, `models/*_pre_extension/` — backupy
- Notatki thesis już napisane — bez zgody usera
- Progi w `rules.py` — kalibrowane vs literatura
- CLAUDE.md — bez zgody usera

---

## Do uwzględnienia w rozdziale Dyskusja (ostatni, była 8)

- **Wyciek Sage Canaday (film 6a/6b)** — segmenty tego samego biegacza w train + val. Usunięte z rozdziału 3 (zapraszało pytania egzaminatora). Naturalne miejsce: sekcja „Ograniczenia pracy".
- **Podział per-film, nie per-runner** — kompromis przy 12 biegaczach/15 filmach.
- **Ograniczenia obliczeń współczynników** (z draftu 05-wspolczynniki.tex): brak kalibracji piksel→metr, monocular 2D artefakty perspektywy, non-determinizm MediaPipe, stride wymaga inputu, brak ground truth → walidacja tylko literaturowa.

## Rozdział Wrażliwość (była 7) — ✅ NAPISANY, wszystkie problemy szkieletu naprawione

Wszystkie 4 problemy z przeglądu nagłówków rozwiązane przy pisaniu:
- ✅ Usunięto „Studium 2: Aspect ratio fix" (dublowało 4.4) — zostało jednozdaniowe odesłanie do sek. 4.4.
- ✅ Numeracja filmów ujednolicona: Film 10 (pionowy), Film 7 (13,33 FPS).
- ✅ „Mitygant w kodzie" → „Automatyczna detekcja niewiarygodnych pomiarów".
- ✅ „Dyskusja: H5,H6,H7" → „Podsumowanie"; hipotezy opisane słownie bez etykiet H (jak w rozdz. 4).

Struktura finalna: Hipotezy → Studium 1 (foot strike vs perspektywa) → Studium 2 (FPS vs metryki temporalne) → Synteza (tabela) → Automatyczna detekcja → Podsumowanie.

## Do uwzględnienia gdy user nagra własny filmik

- Dodać jako PRIMARY case study walidacyjny. Naturalne miejsce: rozdz. 6 (Wrażliwość) albo rozdz. 7 (Dyskusja). Pozwoli pokazać end-to-end użycie pipeline na nowym, niewidzianym materiale.

## Do uwzględnienia w rozdziale 1 (Wstęp)

- **Hipotezy H1–H7** — wprowadzić formalną listę (z briefingu). W rozdz. 4 usunięto etykiety „H2"/„H4" i zastąpiono opisem słownym. Po wprowadzeniu hipotez w rozdz. 1 można albo dodać odwołania z powrotem, albo zostawić jako opisy słowne.
- **Pytania badawcze P1, P2, P3** — sformułować jako pytania badawcze pracy.

---

## Otwarte sprawy (niski priorytet)

1. Bug `postprocess_median.predict_lstm` (66.4% vs 70.9% — metrics.json autorytetywny)
2. Slug strategy (`24-adam` vs `24-adam-bieg__segment_1`)
3. Stable segment detection (film 20) — odłożone
4. PDF generator z wykresami — odłożone
5. Diaz 2019 — szukać pełnych danych bibliograficznych (vertical oscillation running)
6. Metadane `main.tex` — autor, album, promotor (user musi uzupełnić)

---

## Pytania badawcze i hipotezy (do wklejania w tekst)

**P1**: Jak zaprojektować pipeline ML wyliczający 12 współczynników z monocular 2D wideo?
**P2**: Który klasyfikator faz najlepiej przekłada się na precyzję metryk temporalnych?
**P3**: Które współczynniki są wrażliwe na warunki akwizycji i jak detekować automatycznie?

| Hipoteza | Status | Skrót |
|---|---|---|
| H1: pipeline 3-etapowy daje akceptowalne wyniki | potwierdzona | walidacja 3 biegaczy |
| H2: LSTM > RF o min. 5 pp | potwierdzona | 70.9 vs 67.0 |
| H3: engineered RF ≥ raw RF +10 pp | potwierdzona | 67.0 vs 62.7 (+4.3pp, nie 10 — częściowo) |
| H4: aspect fix +5 pp | potwierdzona | +3.8 pp LSTM r1 (film 22 +10.1 pp) |
| H5: metryki przestrzenne wrażliwe na perspektywę | potwierdzona | foot strike 22 → bzdura |
| H6: FPS<15 = 15% błąd kwantyzacji | potwierdzona | film 16 matematycznie |
| H7: auto-detekcja bez ground truth | potwierdzona | low_confidence próg 45° |

---

## Rozdział 3 — GOTOWY (user waliduje)

Wszystkie sekcje 3.1–3.8 napisane (sesje E+F). User przegląda i poprawia.

| Sekcja | Stan |
|---|---|
| 3.1 Dataset | ✅ |
| 3.2 Pipeline ekstrakcji | ✅ |
| 3.3 Auto-etykietowanie | ✅ |
| 3.4 Architektury klasyfikatorów | ✅ |
| 3.5 Obliczanie współczynników | ✅ |
| 3.6 Silnik reguł rekomendacji | ✅ |
| 3.7 Podział danych (splity) | ✅ |
| 3.8 Metryki ewaluacji | ✅ |

## Rozdział 4 — GOTOWY (user waliduje)

Wszystkie sekcje 4.1–4.7 napisane (sesja G). Dane z metrics.json (autorytetywne, post-aspect-fix).

| Sekcja | Stan |
|---|---|
| 4.1 Porównanie modeli (tabela val/test) | ✅ |
| 4.2 Macierz pomyłek LSTM r1 (precision/recall, L↔R vs S↔F) | ✅ |
| 4.3 Feature importance RF v1 vs v2 | ✅ |
| 4.4 Ablacja korekcji proporcji (pre/post per-film) | ✅ |
| 4.5 Analiza per-film (4 modele × 3 filmy testowe) | ✅ |
| 4.6 Wpływ na precyzję współczynników | ✅ |
| 4.7 Wnioski — LSTM r1 jako model główny | ✅ |

**Uwaga**: per_file_test.md zawiera liczby PRE-aspect-fix. Rozdział 4 używa POST-fix z metrics.json.
**Rozbieżność RF v2**: comparison_summary.json=67.0%, metrics.json=65.7% — użyto metrics.json.
