# Random Forest — baseline klasyfikacji faz biegu

**Data sesji**: 2026-04-24
**Etap**: 5, część 1 (baseline — bez modelu sekwencyjnego LSTM/CNN)
**Pliki**: `src/training/split_data.py`, `src/training/train_rf.py`, `models/rf_baseline/`

---

## 1. Uzasadnienie wyboru Random Forest jako baseline

Random Forest wybrano świadomie **jako referencję, nie jako model docelowy**:

- **Nie modeluje zależności czasowych** — klasyfikuje każdą klatkę niezależnie (bag-of-frames), podczas gdy fazy biegu mają wyraźną strukturę sekwencyjną (STANCE → FLIGHT → STANCE). Daje to LSTM/1D-CNN jasny target: "o ile lepiej dałoby się klasyfikować, wykorzystując okno czasowe?".
- **Interpretowalny** — feature importance daje biomechaniczne intuicje (które keypointy faktycznie niosą informację o fazie).
- **Szybki w trenowaniu** — ~13 s na CPU, co pozwala na wiele iteracji feature engineeringu bez GPU.
- **Ugruntowana literatura** — RF był stosowany do klasyfikacji faz chodu w starszych pracach (przed erą deep learning na pose'ach), więc dobra baza porównawcza.

## 2. Metodologia podziału danych

### Zasada: split per filmik, nie per klatka

Kluczowa decyzja projektowa: nie losowy podział klatek, tylko **podział per nagranie**. Powód: klatki z jednego filmiku są silnie skorelowane (ten sam biegacz, kamera, oświetlenie, pozycja w kadrze). Losowy podział klatkowy dałby sztucznie zawyżoną accuracy, bo test set zawierałby klatki "bardzo podobne" do train. Dla generalizacji na nowych użytkowników jedyny uczciwy sposób to split per nagranie.

### Dodatkowa zasada: rozdzielenie biegacza

Filmy 02 i 03 pochodzą od tego samego biegacza na tej samej bieżni (różnią się tylko prędkością 13 vs 15 km/h). Gdyby oba trafiły po tej samej stronie (np. oba w train), nie testowałoby to generalizacji między biegaczami. Finalnie: **02 w test, 03 w val** — fizycznie rozdzieleni.

### Finalny podział (13 filmów, 8039 klatek)

| Split | Filmy | Klatek | Udział |
| --- | --- | --- | --- |
| Train | 01, 06, 08 seg1/seg2, 09 seg1, 15, 19, Running at 4ms | 5811 | 72.3% |
| Val | 03, 09 seg2 | 738 | 9.2% |
| Test | 02, 20, 22 | 1490 | 18.5% |

Klasy zbalansowane (~33% każda z: LEFT_STANCE, RIGHT_STANCE, FLIGHT). DOUBLE_SUPPORT = 0% — przy biegu dwa kontakty jednocześnie praktycznie nie występują.

## 3. Konfiguracja modelu

- **Cechy**: 132 = 33 keypointy MediaPipe × 4 atrybuty (x, y, z, visibility)
- **Hiperparametry**: `n_estimators=300`, `max_depth=None`, `class_weight="balanced"`, `random_state=42`
- **Zbalansowane wagi klas** — mimo że klasy są ~równe frekwencją, to profilaktycznie
- **Brak feature engineeringu** — świadomie surowe keypointy, żeby pokazać, co daje sam model vs. co wymaga lepszych cech

## 4. Wyniki

### Metryki globalne

| Split | Accuracy | F1 macro |
| --- | --- | --- |
| **Val** | **80.6%** | 0.803 |
| **Test** | **59.0%** | 0.583 |

### Per-film na teście

| Film | n | Accuracy | F1 macro | Uwagi |
| --- | --- | --- | --- | --- |
| 02 — Running at 13km/h | 300 | **47.0%** | 0.352 | krytyczna awaria RIGHT_STANCE (recall 0.07) |
| 20 — Running (0.8→3.5 m/s) | 870 | 60.9% | 0.605 | najbardziej zrównoważony |
| 22 — Physiotherapist | 320 | 65.0% | 0.605 | pionowe wideo, mimo to radzi sobie |

### Confusion matrix TEST (wiersze = true, kolumny = pred)

```
              FLIGHT   L_STANCE   R_STANCE
FLIGHT           203        192         81
LEFT_STANCE       74        372         79
RIGHT_STANCE      79        106        304
```

Największy pojedynczy błąd: **192 klatek FLIGHT → LEFT_STANCE** i mylenie R/L ogółem. Macierz jest symetryczna-ish (nie ma jednego dominującego biasu), co utrudnia prostą korektę post-hoc.

## 5. Kluczowa obserwacja: luka val vs test

Różnica **81% → 59%** (22 punkty procentowe) to silny sygnał, że model nauczył się czegoś specyficznego dla train+val, czego nie ma w test. Uwaga: split jest per filmik, więc nie mówimy o overfittingu klasycznym (memoryzacji klatek) — chodzi o **słabą generalizację międzyfilmową**.

### Hipoteza robocza

MediaPipe zwraca x, y znormalizowane **względem całego kadru** (0 = lewa krawędź, 1 = prawa), nie względem biegacza. W konsekwencji:

- Jeśli biegacz na filmie 02 stoi w innej pozycji horyzontalnej w kadrze niż w train set, wartości `LEFT_ANKLE_x`, `RIGHT_ANKLE_x` mają inne rozkłady
- Model nauczył się reguł typu "jeśli RIGHT_ANKLE_x ∈ [0.55, 0.58] i LEFT_HEEL_y > 0.85, to LEFT_STANCE" — reguł związanych z **kadrem**, nie z **pozą**
- Film 02 to ten sam biegacz co 03, więc sylwetka ta sama — ale kamera prawdopodobnie kadrowana inaczej → awaria

### Dowód w feature importances (TOP 5)

1. `RIGHT_ANKLE_y` — 0.036
2. `LEFT_FOOT_INDEX_y` — 0.034
3. `LEFT_HEEL_y` — 0.033
4. `LEFT_ANKLE_y` — 0.033
5. `RIGHT_FOOT_INDEX_y` — 0.032

**Dobra wiadomość**: top features to `_y` stóp — biomechanicznie sensowne (w stance stopa ma wyższe y, w flight niższe). Oś Y jest też mniej wrażliwa na kadr niż X (biegacz biegnie w osi X, ale zawsze w tym samym zakresie Y).

**Zła wiadomość (dalej w liście)**: visibility kciuków, ust, barku (`RIGHT_SHOULDER_visibility: 0.013`, `MOUTH_RIGHT_visibility: 0.010`). Te cechy **nie mają biomechanicznego znaczenia** dla fazy biegu — to sygnał, że model uczy się artefaktów kadrowania (gdy kciuk/twarz są zasłonięte ciałem w określonej pozie, visibility spada).

## 6. Wnioski biomechaniczne

Niezależnie od metryk, TOP-10 feature importance zgadza się z intuicją biomechaniczną:

- **Oś Y stóp** (ankle, heel, foot_index) dominuje — bo to bezpośredni wskaźnik kontaktu z podłożem
- **X kolan i stóp** — informacja o fazie cyklu (przód-tył nogi)
- **Górna połowa ciała prawie nieobecna** w top features — zgadza się z faktem, że fazę biegu definiuje **kontakt stopy**, nie pozycja rąk

To jest spójne z literaturą (np. analiza GCT przez detekcję peaków stopy) i potwierdza, że **feature space jest sensowny** — problem nie jest w tym, że keypointy są bezużyteczne, tylko że są **nienormalizowane**.

## 7. Ocena w dwóch kontekstach

### Jako baseline pracy magisterskiej — ✅ akceptowalny

- Daje jasny punkt odniesienia (59% test) do porównań z modelami sekwencyjnymi
- Sama luka val↔test jest **materiałem źródłowym do rozdziału o feature engineering** — pokazuje, że surowe keypointy nie wystarczają i uzasadnia potrzebę normalizacji / cech inżynierowanych
- Analiza błędów (mylenie L↔R) daje narrację "co poprawić w kolejnym modelu"

### Jako model produkcyjny — ❌ niewystarczający

- Pipeline: fazy → współczynniki (kadencja, GCT, flight time, symetria L/R)
- Przy recall RIGHT_STANCE = 7% na filmie 02, obliczona **asymetria L/R byłaby skrajnie błędna** — dla biegacza komunikat byłby mylący
- Minimalny akceptowalny próg do produktu: ~90% test accuracy i **<5% mylenia L↔R** (bo to bezpośrednio rujnuje współczynnik symetrii)
- Do produktu konieczne są kolejne iteracje (normalizacja, cechy kątowe, model sekwencyjny)

## 8. Co to znaczy dla struktury pracy magisterskiej

Propozycja umieszczenia tego wyniku w pracy:

- **Rozdział "Baseline"** — RF jako punkt odniesienia, pełna analiza
- **Podrozdział "Analiza błędów"** — luka val↔test, mylenie L↔R, feature importances artefaktów kadru
- **Uzasadnienie dla następnych modeli** — te same dane z normalizacją vs. RF; potem model sekwencyjny vs. RF
- Wyniki pokazują, że **każdy kolejny krok (normalizacja, sekwencja) musi udowodnić wartość** — porównanie 59% → X% → Y% to trzon eksperymentalnej części pracy

## 9. Ograniczenia i zastrzeżenia (do uczciwego omówienia w pracy)

- **Mały dataset** — 13 filmów, ~10 unikalnych biegaczy. Nie możemy odróżnić "czy model się myli, bo keypointy są złe" od "czy ma za mało danych, żeby się nauczyć"
- **Etykiety pochodzą z algorytmu peak-based**, nie z ręcznego etykietowania — więc ewentualne błędy autoetykietowania propagują się do metryk (recall FLIGHT może być zaniżony częściowo dlatego, że algo etykietujący sam myli się w granicznych klatkach)
- **Brak DOUBLE_SUPPORT** w datasecie — model nie zobaczył tej klasy, więc faktycznie rozwiązuje problem 3-klasowy, nie 4-klasowy jak zakłada pipeline
- **Test set 1490 klatek** — statystycznie wystarczająco, ale zdominowany przez jeden film (20: 870 klatek). Metryka "TEST accuracy 59%" ważona jest głównie wynikiem filmu 20
- **Dwa filmy slow-motion w train** (01, 06, 08 seg2, 15, 19) — klatki pokazują pozy "pośrednie" których nie ma w normalnym FPS. Może to pomagać (więcej wariantów) albo szkodzić (rozkład klas na klatkę może być zaburzony)

## 10. Surowe metryki (do tabel w pracy)

### Val classification report

```
              precision    recall  f1-score   support
      FLIGHT      0.742     0.732     0.737       224
 LEFT_STANCE      0.799     0.838     0.818       260
RIGHT_STANCE      0.872     0.838     0.855       253
    accuracy                          0.806       737
   macro avg      0.804     0.803     0.803       737
weighted avg      0.807     0.806     0.806       737
```

### Test classification report

```
              precision    recall  f1-score   support
      FLIGHT      0.570     0.426     0.488       476
 LEFT_STANCE      0.555     0.709     0.623       525
RIGHT_STANCE      0.655     0.622     0.638       489
    accuracy                          0.590      1490
   macro avg      0.594     0.586     0.583      1490
weighted avg      0.593     0.590     0.585      1490
```

Pełne metryki + TOP-30 feature importances: `models/rf_baseline/metrics.json`.
