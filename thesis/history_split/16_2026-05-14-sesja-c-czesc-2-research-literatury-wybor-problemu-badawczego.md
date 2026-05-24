# 2026-05-14 — Sesja C część 2: Research literatury + wybór problemu badawczego ✅

**Opis dla agenta:** Research literatury i wybór problemu badawczego pracy magisterskiej

**Słowa kluczowe:** literatura, problem badawczy, research gap, praca magisterska

---

## 2026-05-14 — Sesja C część 2: Research literatury + wybór problemu badawczego ✅

### Kontekst

Po Sesji C część 1 (walidacja foot strike) i napisaniu README projektu, user zadał
pytanie strategiczne: praca magisterska musi mieć **problem badawczy** (nie tylko opis
systemu). Sesja C część 2 wykonała research literatury i wybór formuły problemu badawczego.

### Zrobione

1. **Odblokowanie WebSearch + WebFetch** dla 10 domen naukowych (PMC, Frontiers, MDPI,
   ScienceDirect, IEEE, arXiv, Springer, PLOS, github.com, nature.com).
2. **Research 7 peer-reviewed prac** (WebSearch + WebFetch, paralel): Stenum 2021 (PLOS Comp Bio),
   Ali 2024 (PMC BioMed Inform), Frontiers Phys 2025 mini review, Hannigan 2024 (Front Sport),
   Ripic 2023 (Front Rehab), Bouchabou 2024 (PMC Heliyon narrative review), HGcnMLP 2023
   (Front Bioeng). Każda z cytatem problemu badawczego z abstraktu + linkiem weryfikowalnym.
3. **Identyfikacja 4 wzorców sformułowań** problemu badawczego w domenie:
   - Szablon A "lack of validation"
   - Szablon B "cost/accessibility gap"
   - Szablon C "specific gap in conditions/methodology"
   - Szablon D "detection accuracy motivating automation"
4. **Identyfikacja 5 gap'ów w literaturze**, które ta praca wypełnia:
   - Running-specific (vs chód kliniczny)
   - Systematyczne porównanie 4 klasyfikatorów na małym datasecie
   - Aspect ratio fix jako pre-processing
   - System rekomendacji rule-based z citation z literatury
   - Auto-detekcja niskiej wiarygodności predykcji
5. **Wybór Propozycji A** (z 3 zaproponowanych) jako problemu badawczego pracy.
6. **Notatka thesis** `2026-05-14-research-podobnych-prac.md` — research + wzorce + gap.
7. **Notatka thesis** `2026-05-14-problem-badawczy-propozycja-a.md` — tytuł roboczy,
   3 pytania badawcze (P1/P2/P3), 6 hipotez (wszystkie potwierdzone istniejącymi danymi),
   struktura 10 rozdziałów, lista cytatów do State of the Art, mapping case studies na P3.

### Wybrany tytuł roboczy

> *"Klasyfikacja faz biegu z monocular 2D wideo: porównanie podejść uczenia maszynowego
> i analiza wrażliwości metryk biomechanicznych na warunki akwizycji"*

### 3 pytania badawcze

| Pytanie | Hipotezy | Materiał empiryczny |
|---|---|---|
| **P1** porównanie 4 klasyfikatorów | H1: LSTM>RF +5pp; H2: engineered RF ≥ raw RF +10pp | comparison_table.md, 4 wytrenowane modele |
| **P2** aspect ratio fix ablation | H3: aspect fix +5pp, kluczowe dla portrait | per_file_test.md, backupy pre_aspect_fix |
| **P3** wrażliwość metryk na warunki akwizycji | H4: foot strike wrażliwy na perspektywę; H5: FPS<15 = 15% błąd; H6: auto-detekcja low_confidence | Case 1 Sesja C (foot strike), Case 2 film 22, Case 3 film 16 |

**Wszystkie 6 hipotez potwierdzone istniejącymi danymi** — praca może być pisana
bez nowych eksperymentów.

### Do zrobienia w następnej sesji

**Sesja D** — pisanie pracy magisterskiej. Rozdziały 4 (Eksperyment 1), 5 (Eksperyment 2),
6 (Współczynniki), 7 (Rekomendacje), 8 (Eksperyment 3) mają komplet materiału. Wymaga
decyzji formalnej z promotorem (tytuł, scope, pozycjonowanie, deadline).

### Drobne obserwacje

- WebSearch działa z Polski (poprzedni komunikat agentów "only available in the US"
  okazał się niepoprawny po nadaniu uprawnień).
- WebFetch ma limit per-domena — `mdpi.com` zwraca 403, `nature.com`/`springer.com` wymagają
  IDP auth; PMC/PLOS/Frontiers/GitHub są open access i działają.
- Plik `README.md` projektu napisany przed researchem — pozycjonuje pracę jako "system",
  nie "research". Warto rozważyć update po finalizacji tytułu z promotorem.

---
