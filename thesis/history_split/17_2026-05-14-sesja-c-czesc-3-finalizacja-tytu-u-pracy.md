# 2026-05-14 — Sesja C część 3: Finalizacja tytułu pracy ✅

**Opis dla agenta:** Finalizacja tytułu pracy, zakresu i narracji badawczej

**Słowa kluczowe:** tytuł pracy, zakres, narracja, magisterka

---

## 2026-05-14 — Sesja C część 3: Finalizacja tytułu pracy ✅

### Kontekst

Po Sesji C część 2 (research literatury + wybór Propozycji A z roboczym tytułem ML-centric)
user przekazał **formalny tytuł** uzgodniony z promotorem:

> **"Analiza podstawowych współczynników biegu przy pomocy uczenia maszynowego"**

Tytuł jest **biomechanics-centric** (główny obiekt: współczynniki biegu, ML jako narzędzie),
nie ML-centric (klasyfikator jako główny obiekt). Wymagana reformulacja problemu badawczego.

### Zrobione

1. **3 pytania badawcze przeformułowane** pod nowy framing:
   - **P1**: Jak zaprojektować pipeline ML wyliczający 12 współczynników z monocular 2D wideo?
   - **P2**: Który klasyfikator faz najlepiej przekłada się na precyzję metryk temporalnych?
   - **P3**: Które współczynniki są wrażliwe na warunki akwizycji + jak detekować auto?
2. **7 hipotez** (H1-H7) **wszystkie potwierdzone** istniejącymi danymi (bez nowych eksperymentów).
3. **Struktura 8 rozdziałów** (~60 stron, limit user):
   - 1. Wstęp (5)
   - 2. State of the Art (8)
   - 3. Materiały i metody (8)
   - 4. Klasyfikator faz — wybór modelu + aspect fix (10)
   - 5. Współczynniki biegu — pipeline obliczania (12, centralny rozdział)
   - 6. System rekomendacji (8, **Wariant 1 — pełny rozdział** wybrany)
   - 7. Wrażliwość na warunki akwizycji (6)
   - 8. Dyskusja i wnioski (5)
4. **Notatka thesis** `2026-05-14-temat-pracy-finalny.md` — finalna wytyczna do pisania:
   tytuł, 3 pytania, 7 hipotez, struktura 8 rozdziałów, cytaty z research (15-25 ref),
   limitations gotowe punkty.
5. **Update notatki Propozycji A** — dopis "Po dalszej pracy" wskazujący że jest
   wersją historyczną (ML-centric).
6. **Update README thesis-notes** — tytuł pracy na początku, link do finalnej notatki.

### Kluczowe decyzje user

- **Tytuł finalny** — bez zmian, *"Analiza podstawowych współczynników biegu
  przy pomocy uczenia maszynowego"*.
- **Zakres współczynników** — wszystkie 12 (5 temporalnych + 7 przestrzennych),
  uczciwie zaznaczone że pierwotny plan był węższy (rozkręciliśmy się w trakcie pracy).
- **Rekomendacje** — pełny rozdział (Wariant 1, ~8 stron). Materiał już istnieje
  (Sesje A/B/C, 13+ reguł z citation, walidacja na 3 biegaczach).
- **Limit stron** — ~60 max, fokus na esencję, nie szczegóły.

### Status do pisania

**Wszystkie 5 rozdziałów eksperymentalno-merytorycznych ma komplet materiału**:
- Rozdz. 4 (Klasyfikator + aspect fix) — 4 modele, comparison_table, backupy
- Rozdz. 5 (Współczynniki — centralny) — pełny pipeline, walidacja na 3 biegaczach
- Rozdz. 6 (Rekomendacje) — 13+ reguł, walidacja, notatki Sesji A/B/C
- Rozdz. 7 (Wrażliwość) — 3 case studies (Sesja C foot strike, film 22 aspect, film 16 FPS)
- Rozdz. 2 (SOTA) — 7 cytatów z researchu + 6 biomechanicznych z `rules.py`

**Praca może być pisana bez dodatkowych eksperymentów.**

### Do zrobienia w następnej sesji

**Sesja D** — pisanie pracy magisterskiej. Wytyczna: `2026-05-14-temat-pracy-finalny.md`.

### Drobne obserwacje

- Notatki thesis mają teraz **3 generacje** dla problemu badawczego: research 7 prac →
  Propozycja A (ML-centric, historyczna) → finalny tytuł (biomechanics-centric).
  To czysty cykl ewolucji decyzji metodologicznej, sam w sobie wartościowy materiał
  do sekcji "Metodologia projektowania pracy" (jeśli promotor uzna za potrzebne).
- README projektu napisany przed finalizacją tytułu — warto rozważyć update tak żeby
  pozycjonowanie zgadzało się z tytułem (akcent na współczynniki, nie na system).

---
