---
globs: src/labeling/**
---

# Auto-etykietowanie faz biegu

## Logika heurystyczna
1. Wyznacz poziom podłoża (ground_level) — mediana pozycji Y stopy w najniższych 10% klatek
2. Stopa "na ziemi" gdy: Y_heel <= ground_level + threshold (threshold ~0.02 w normalizowanych współrzędnych)
3. Klasyfikuj klatkę na podstawie stanu obu stóp:
   - Lewa na ziemi, prawa nie → LEFT_STANCE
   - Prawa na ziemi, lewa nie → RIGHT_STANCE
   - Obie na ziemi → DOUBLE_SUPPORT
   - Obie w powietrzu → FLIGHT

## Problemy do obsłużenia
- Szum może powodować "migotanie" etykiet (np. FLIGHT→LEFT_STANCE→FLIGHT w 1 klatce) — zastosuj filtr medianowy na sekwencji etykiet (kernel=5)
- Przy wolnym biegu DOUBLE_SUPPORT jest normalne; przy szybkim biegu powinno prawie nie występować
- LEFT/RIGHT mogą być zamienione jeśli biegacz jest zwrócony w drugą stronę — wykryj kierunek biegu z pozycji keypointów

## Format wyjściowy
- Dopisz kolumnę `phase` do CSV z keypointami
- Dopisz kolumnę `phase_auto` (oryginalna etykieta) i `phase` (po korekcie ręcznej)
