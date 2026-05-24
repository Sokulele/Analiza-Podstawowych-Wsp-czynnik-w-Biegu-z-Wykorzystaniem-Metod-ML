# 2026-05-23 — Sesja D: setup LaTeX bibliografii + plan pisania ✅

**Opis dla agenta:** Setup LaTeX bibliografii, struktura pracy i plan pisania

**Słowa kluczowe:** LaTeX, bibliografia, bibliography.tex, plan pisania, rozdziały

---

## 2026-05-23 — Sesja D: setup LaTeX bibliografii + plan pisania ✅

### Decyzje sesji

1. **Limit stron zniesiony** — może być więcej niż 60, wstawiamy kod/wykresy/diagramy
2. **Pisanie sekcja po sekcji** (nie cały rozdział naraz) — oszczędność tokenów
3. **Kolejność pisania**: 3 → 4 → 5 → 7 → 6 → 2 → 1 → 8
4. **Diaz 2019 usunięty z bibliografii** — niepotwierdzony artykuł

### Zrobione

**Bibliografia — z 20 do 27 zweryfikowanych wpisów**:
- Dodane 8 nowych pozycji: Jeon 2024 (BiLSTM), Su 2020 (DCNN gait), Vu 2020 (review gait phase),
  Dimmick 2023 (RF fatigue), Martínez-Gramage 2020 (RF injuries), Young 2023 (smartphone running),
  Crenna 2021 (filtering), Figueiredo 2025 (cadence review)
- Dodane 3 fundamentalne: Savitzky-Golay 1964, Goodfellow 2016, Hochreiter 1997, Breiman 2001
- Poprawione 5 błędów (weryfikacja 3× agentami + ręcznie przez usera):
  - `ripic2023` → `menychtas2023` (błędni autorzy)
  - `bouchabou2024review` → `roggio2024review` (błędni autorzy)
  - `hannigan2024footstrike` → `vincent2024footstrike` (błędny klucz)
  - `cao2018openpose` → `cao2021openpose` (rok 2021, nie 2018)
  - `hgcnmlp2023` → `hgcnmlp2024` (rok publikacji 2024)
- Usunięty `diaz2019` (niepotwierdzony)
- Dopisane brakujące DOI do 8 wpisów (Novacheck, Souza, Heiderscheit, Daoud, Savitzky-Golay,
  Hochreiter, Breiman, SciPy, COCO)

**Spis treści zatwierdzony** — 8 rozdziałów, struktura jak w `temat-pracy-finalny.md`

**System dokumentacji sesyjnej** — `next-session-brief.md` przerobiony na kompaktowy
onboarding, żeby kolejne sesje nie musiały czytać całego projektu

### Notatka o filmie usera

User nie zdążył nagrać własnego filmiku z biegu ani pobrać danych z Garmina. Zrobi to
gdy będzie miał czas — nie blokuje pisania pracy.

### Stan plików

- `thesis/chapters/bibliography.tex` — 27 zweryfikowanych wpisów z DOI
- `docs/next-session-brief.md` — zaktualizowany na sesję pisania

### Do zrobienia w następnej sesji

**Pisanie rozdziału 3 (Materiały i metody)**, sekcja po sekcji:
- 3.1 Dataset → 3.2 Pipeline ekstrakcji → 3.3 Auto-etykietowanie → 3.4 Architektury
  → 3.5 Obliczanie współczynników → 3.6 Silnik reguł → 3.7 Splity i metryki

---
