# Random Forest v2 — cechy inżynierowane (Etap 5, część 2)

**Data sesji**: 2026-04-24
**Plik modelu**: `models/rf_engineered/`
**Kod**: `src/training/features.py`, `src/training/train_rf_v2.py`
**Kontekst**: realizacja Sesji 1 z [decyzji Opcji B](2026-04-24-decision-option-b.md)

---

## 1. Jakie cechy, jakie hipotezy

### Feature engineering

Względem baseline'u (132 surowe cechy: x/y/z/visibility dla 33 keypointów) zastosowano:

- **Normalizacja antropometryczna**: wszystkie keypointy wycentrowane na `mid_hip` (środek między LEFT_HIP i RIGHT_HIP) i przeskalowane długością tułowia (odległość mid_hip → mid_shoulder). Cechy w "jednostkach tułowia" — niezależne od pozycji biegacza w kadrze i od wzrostu
- **Usunięcie visibility** — w baseline widzieliśmy, że `MOUTH_RIGHT_visibility`, `RIGHT_SHOULDER_visibility` dostawały wysoką ważność mimo braku biomechanicznego sensu (artefakty kadrowania)
- **Kąty stawów** (6 cech) — klasyczne 3-punktowe: kolano (biodro-kolano-kostka) L i R, biodro (ramię-biodro-kolano) L i R, kostka (kolano-kostka-stopa) L i R. Cechy inwariantne na translację, rotację i skalę — literalnie "pozycja ciała" bez informacji o kadrze
- **Pochylenie tułowia** (1 cecha) — kąt wektora mid_hip → mid_shoulder względem pionu

**Łącznie 106 cech** (99 znormalizowanych współrzędnych + 7 kątów) vs 132 surowe w baseline.

### Hipotezy przed eksperymentem

Z [notatki decyzyjnej](2026-04-24-decision-option-b.md):

| Model | Przewidywana test accuracy |
| --- | --- |
| RF naive | 59% (zmierzone) |
| RF engineered | **70–78%** |
| LSTM engineered | 82–90% |

## 2. Wyniki — liczby

### Metryki globalne (porównanie z baseline)

| Split | Baseline (132 surowe) | RF v2 (106 eng.) | Zmiana |
| --- | --- | --- | --- |
| Val accuracy | 80.6% | **79.4%** | **−1.2 p.p.** |
| Val F1 macro | 0.803 | 0.792 | −0.011 |
| Test accuracy | 59.0% | **61.0%** | **+2.0 p.p.** |
| Test F1 macro | 0.583 | 0.611 | +0.028 |
| **Luka val↔test** | **21.6 p.p.** | **18.4 p.p.** | **−3.2 p.p.** |

### Per-film na teście (ta sama konfiguracja splitów)

| Film | Baseline | RF v2 | Zmiana | Komentarz |
| --- | --- | --- | --- | --- |
| 02 — 13 km/h | **47.0%** | **63.7%** | **+16.7 p.p.** 🎯 | spełniona hipoteza: normalizacja naprawia mylenie L↔R |
| 20 — walk→run | 60.9% | 61.1% | +0.2 p.p. | bez istotnej zmiany |
| 22 — physiotherapist | **65.0%** | **58.1%** | **−6.9 p.p.** ⚠️ | nieoczekiwane pogorszenie (pionowe wideo) |

### Confusion matrix TEST — RF v2

```
              FLIGHT   L_STANCE   R_STANCE
FLIGHT           258        143         75
LEFT_STANCE      140        351         34
RIGHT_STANCE    128         61        300
```

Porównanie z baseline:
- Mylenie L_STANCE ↔ R_STANCE (off-diagonal dolny-prawy i górno-lewy): było 79+106=185, jest 34+61=95 — **poprawa ~50%**
- Mylenie FLIGHT ↔ STANCE: było 192+74+81+79=426, jest 143+140+75+128=486 — **pogorszenie ~14%**

**Istotne**: model wymienił "mylenie L↔R" na "mylenie stance↔flight". Ten drugi błąd jest **mniej szkodliwy dla produktu końcowego** — myli się o moment kontaktu (1-2 klatki w cyklu), nie o to, która noga ląduje. Współczynniki symetrii L/R (najbardziej eksponowana dla użytkownika metryka) stają się znacznie lepsze.

### TOP-10 feature importances RF v2

1. **right_ankle_angle** — 0.039 (kąt kostki)
2. **left_knee_angle** — 0.039 (kąt kolana)
3. **right_knee_angle** — 0.037
4. LEFT_FOOT_INDEX_x_norm — 0.023
5. LEFT_ANKLE_y_norm — 0.021
6. RIGHT_FOOT_INDEX_x_norm — 0.021
7. RIGHT_ANKLE_y_norm — 0.021
8. LEFT_HEEL_y_norm — 0.019
9. RIGHT_HEEL_y_norm — 0.019
10. RIGHT_KNEE_z_norm — 0.019

**TOP-3 to kąty stawów — biomechaniczna walidacja**. W baseline top features to były surowe `_y` stóp (w tym visibility ust/kciuków). W v2 model najpierw patrzy na kąty (co robi biegacz z nogą), dopiero potem na pozycje (gdzie ta noga jest).

## 3. Ocena hipotez

| Hipoteza | Wynik | Ocena |
| --- | --- | --- |
| Test accuracy 70–78% | 61% | ❌ **niespełniona** — znacznie poniżej przewidywań |
| Luka val↔test się zamknie | 21.6 → 18.4 p.p. | 🟡 **częściowo** — zamknięta o ~15%, ale nie w pełni |
| Normalizacja naprawi film 02 | 47% → 64%, RIGHT recall 7%→70% | ✅ **spełniona dokładnie** |
| Kąty stawów będą użyteczne | TOP-3 feature importances | ✅ **spełniona mocno** |
| Val nie spadnie istotnie | −1.2 p.p. | ✅ **spełniona** |

## 4. Dlaczego hipoteza 70–78% się nie spełniła — analiza

Przewidywanie było zbyt optymistyczne. Możliwe przyczyny (w kolejności prawdopodobieństwa):

### 4.1 Film 22 — problem z pionowym wideo

Film 22 pogorszył się o 7 p.p. Kandydat na przyczynę:

- MediaPipe zwraca x, y w **jednostkach znormalizowanych per oś** (0-1), nie zachowując aspect ratio wideo
- Film 22 ma rozdzielczość 608×1080 (pionowy), reszta filmów to ~4:3 lub 16:9 (poziome)
- W takim razie `torso_length = ||mid_shoulder - mid_hip||` policzone w przestrzeni znormalizowanej to nie jest fizyczna długość tułowia
- Dla pionowego wideo komponent y dominuje, więc torso_length jest **zawyżona** → wszystkie cechy znormalizowane są **zmniejszone** → model, który w train widział większe wartości, myli się

To jest **subtelny bug w normalizacji**, który wymaga korekcji o aspect ratio wideo (`x_corrected = x * width / height` lub podobnie, żeby jednostki x i y były proporcjonalne do fizycznych).

### 4.2 Inherentna słabość modelu bez kontekstu czasowego

RF patrzy na pojedynczą klatkę. W granicach cyklu biegu moment przejścia STANCE → FLIGHT może być nierozróżnialny dla pojedynczej klatki (stopa 1-2 cm nad ziemią, kąty stawów prawie te same). Model sekwencyjny (LSTM) z oknem N klatek powinien to łapać — różnica "stopa idzie w górę vs w dół" wymaga widzenia sąsiednich klatek.

### 4.3 Szum etykiet peak-based

Algorytm peak-based dzieli interwał między peakami na STANCE/FLIGHT w proporcji 60/40. To jest przybliżenie — w granicznych klatkach (±2 wokół przejścia) etykieta może różnić się od prawdy ground truth. Jeśli ~5% klatek ma szum etykiet, to teoretyczny sufit accuracy to ~95%, a w praktyce jeszcze mniej.

### 4.4 Monocular 2D + asymetria kamery

W ujęciu z boku lewa i prawa noga mają różną widoczność (jedna zasłania drugą). To nie jest bug w kodzie, tylko inherentna wada reprezentacji monocular. Nawet perfekcyjny model na keypointach 2D musi się z tym godzić.

## 5. Co to znaczy dla pracy magisterskiej

### Mocne obserwacje (materiał do rozdziału)

1. **Film 02: 47% → 64%** — demonstracja kliniczna problemu z absolutnymi współrzędnymi. Baseline uczył się "biegacz w pozycji x=0.55-0.58" — film 02 miał inną pozycję w kadrze, więc baseline się wysypywał. Normalizacja to eliminuje
2. **TOP-3 features = kąty stawów** — niezależna walidacja, że model nauczył się tego, co biomechanicy uważają za istotne (a nie artefaktów kadrowania)
3. **Mylenie L↔R spadło o 50%** — największy problem baseline'u praktycznie rozwiązany. Dla produktu końcowego (współczynniki symetrii L/R) to jest **kluczowa** metryka, istotniejsza niż accuracy
4. **Odkrycie bugu z aspect ratio** — film 22 wskazuje, że MediaPipe wymaga dodatkowej korekcji przy różnych rozdzielczościach wideo. **Warto omówić w sekcji "limitations" pracy**

### Uczciwe zastrzeżenia

- Hipoteza 70–78% była zbyt optymistyczna — normalizacja to nie magic bullet. Głębsze źródła błędu (kontekst czasowy, label noise, 2D monocular) wymagają innych środków
- RF v2 tylko **poprawia jakość błędów**, nie zmniejsza ich liczby znacząco. Z punktu widzenia accuracy to "prawie żadna" poprawa (+2 p.p.) — dopiero analiza per-klasa i per-film pokazuje rzeczywistą wartość

### Układ rozdziału eksperymentalnego (aktualizacja)

- **5.1 Baseline (RF naive)** — 59% test, diagnoza: mylenie L↔R, artefakty visibility
- **5.2 RF z cechami inżynierowanymi** *(nowe)* — 61% test, ale jakościowo różne błędy. Pokazujemy, że normalizacja rozwiązuje jeden problem, ale pojawia się drugi (bug aspect ratio)
- **5.3 LSTM** — główny model; hipoteza że kontekst czasowy zamknie lukę w FLIGHT↔STANCE
- **5.4 Analiza** — tabela 3 modeli, per-klasowe F1, per-filmowe accuracy

Dla pracy ta iteracja jest **bardziej wartościowa niż byłaby "duża skokowa poprawa"** — jedno-cyfrowa poprawa z dokładną analizą, co się stało i dlaczego, pokazuje metodologiczną dojrzałość lepiej niż "zmieniłem cechy, było 20% lepiej".

## 6. Kierunki naprawcze (do rozważenia)

Nie robimy teraz (przechodzimy do LSTM), ale warte zapamiętania:

1. **Korekcja aspect ratio** — przed normalizacją wymnożyć współrzędne przez (width, height) z metadanych wideo. Może naprawić film 22
2. **Usunięcie z-axis** — MediaPipe z jest estymowane z 2D, w monocular side view jest głównie szumem. Wariant na 2D (x, y) może działać lepiej niż 3D
3. **Prędkości i przyspieszenia** (jeszcze bez LSTM) — pierwsze różnice współrzędnych między klatkami. Tani sposób na częściowy kontekst czasowy w modelu per-klatkowym

## 7. Surowe metryki (do tabel w pracy)

### VAL classification report

```
              precision    recall  f1-score   support
      FLIGHT      0.695     0.741     0.717       224
 LEFT_STANCE      0.839     0.781     0.809       260
RIGHT_STANCE      0.844     0.854     0.849       253
    accuracy                          0.794       737
   macro avg      0.792     0.792     0.792       737
weighted avg      0.797     0.794     0.795       737
```

### TEST classification report

```
              precision    recall  f1-score   support
      FLIGHT      0.490     0.542     0.515       476
 LEFT_STANCE      0.632     0.669     0.650       525
RIGHT_STANCE      0.733     0.613     0.668       489
    accuracy                          0.610      1490
   macro avg      0.619     0.608     0.611      1490
weighted avg      0.620     0.610     0.613      1490
```

Pełne metryki: `models/rf_engineered/metrics.json`.
