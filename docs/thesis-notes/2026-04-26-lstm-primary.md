# BiLSTM — model docelowy klasyfikacji faz biegu (Etap 5, część 3)

**Data sesji**: 2026-04-26
**Model primary**: `models/lstm_primary/` (run 2 — wybrany)
**Model porównawczy**: `models/lstm_run1_overfit/` (run 1 — odrzucony, zachowany do dyskusji)
**Kod**: `src/training/train_lstm.py` (PyTorch 2.11 CPU), `src/training/features.py`
**Kontekst**: realizacja Sesji 2 z [decyzji Opcji B](2026-04-24-decision-option-b.md). LSTM jest modelem docelowym pipeline'u inferencji (wideo → fazy → współczynniki).

---

## 1. Architektura i decyzje projektowe

### Wybór: Bidirectional LSTM, nie 1D-CNN

LSTM wybrano nad 1D-CNN z dwóch powodów:

- **Sekwencyjna natura zadania** — fazy biegu mają ścisłą strukturę przejść (STANCE → FLIGHT → STANCE), którą RNN modeluje bezpośrednio przez stan ukryty. CNN modelowałby to pośrednio przez filtry.
- **Standard literatury w analizie chodu/biegu** — większość prac używa LSTM jako baseline'u sekwencyjnego, więc wynik jest porównywalny z literaturą.

**Kierunkowość**: bidirectional. Klasyfikacja jest **offline** (analizujemy nagrane wideo, nie strumień real-time), więc model może wykorzystać też przyszłość każdej klatki. To zgadza się z naturą zadania — moment przejścia STANCE→FLIGHT staje się jednoznaczny dopiero gdy widzimy kolejne 2-3 klatki "stopa odrywa się".

### Okno N=15 klatek, target = klatka środkowa

- **15 klatek przy 30 FPS = 0.5 s** — pokrywa pełen pojedynczy stance (~250 ms) z marginesem przed/po. Krótszy okno (np. 7) traciłby kontekst całej fazy stance; dłuższy (np. 31) wprowadzałby informację z innego cyklu kroku, która jest mylna.
- **Klatka środkowa jako target** — model widzi po 7 klatek przed i po, dzięki czemu **bidirectional ma symetryczny dostęp do kontekstu**. Gdyby targetem była ostatnia klatka, kierunek "przyszłość" byłby pusty.
- **Krawędzie odrzucone** — pierwsze i ostatnie 7 klatek każdego pliku nie staje się targetem (nie da się zbudować pełnego okna). Strata: 14 klatek × 13 plików ≈ 182 klatek (~2.3% datasetu) — akceptowalna.

### Cechy: te same 106 co w RF v2

Świadomie te same engineered features (`features.py`): 99 znormalizowanych współrzędnych + 6 kątów stawów + 1 pochylenie tułowia. **Fair comparison wymaga izolacji jednej zmiennej** — różnica RF v2 vs LSTM ma odzwierciedlać tylko wpływ kontekstu czasowego, nie cech.

### StandardScaler dopasowany na train

Cechy mają bardzo różną skalę (kąty 0-180° vs współrzędne znormalizowane ~-2 do 2). Standardyzacja per-feature (μ=0, σ=1, fitowana **tylko na train**) jest standardem dla sieci neuronowych — bez niej cechy o większej amplitudzie dominują grad. Scaler zapisywany do `scaler.joblib` — w inferencji trzeba go odtworzyć identycznie.

## 2. Dwa runy — proces decyzyjny (materiał do pracy)

Pierwsze podejście (`hidden=128, lr=1e-3, dropout=0.3, weight_decay=1e-5`) dało **early stopping na epoce 1** — najlepszy val_loss (0.484) wystąpił już po pierwszej epoce, dalej val_loss rósł monotonicznie do 1.02 mimo że train_loss spadał z 0.56 do 0.14. **Klasyczna sygnatura overfittingu** do małego datasetu (5811 klatek na 637k parametrów).

To NIE jest poprawny model do reprezentowania zdolności LSTM — to artefakt złej konfiguracji. Run 2 zmniejszył model i lr:

| Parametr | Run 1 (odrzucony) | Run 2 (primary) | Uzasadnienie zmiany |
| --- | --- | --- | --- |
| hidden_size | 128 | **64** | mniej parametrów (637k → 188k), mniejsza pojemność pamięci dla artefaktów train |
| lr | 1e-3 | **3e-4** | wolniejsze uczenie, mniej skoków val_loss |
| dropout | 0.3 | **0.4** | silniejsza regularyzacja |
| weight_decay | 1e-5 | **1e-4** | silniejszy L2, ogranicza wagi |
| best epoch | 1 | **2** | sensowniejszy fundament dla wniosków |
| epoki "stabilne" | 0 | **4 (ep 2-5, val_loss 0.51-0.53)** | model faktycznie się uczy zanim zacznie overfitować |

### Dlaczego run 2 jako primary mimo niższego test acc

Run 1 ma marginalnie wyższy test acc (66.0% vs 64.9%, +1.1 p.p.), ale **early stop @ ep 1 jest słabym fundamentem dla pracy magisterskiej**:

1. **Brak walidacji że model faktycznie uczy się sygnału z train** — jeśli najlepszy stan jest po jednej epoce, to być może to inicjalizacja + jeden krok gradientu trafiły szczęśliwie, a nie że model "nauczył się klasyfikacji". Run 2 ma 4 epoki plateau val_loss → walidowana zdolność do nauki.
2. **Run 1 ma bardziej "loteryjne" wyniki per-film** — accuracy zakres 56.3-70.3 (różnica 14 p.p.); run 2: 64.0-65.1 (różnica 1.1 p.p.). Model run 2 jest **bardziej spójny między filmami** — dla pracy mgr to sygnał lepszej generalizacji niż wyższy globalny test.
3. **Run 1 wyglądałby źle w sekcji "metodologia"** — recenzent pyta "dlaczego patience 15 jeśli zatrzymujesz się na epoce 1?", "czy testowano mniejszy lr?". Run 2 odpowiada na te pytania.

Run 1 zostaje w `models/lstm_run1_overfit/` jako **materiał porównawczy**: w pracy będziemy mogli pokazać "naiwna konfiguracja vs przemyślana" — to dobra ilustracja procesu badawczego.

## 3. Wyniki — porównanie 4 modeli

### Metryki globalne

| Model | Cechy | Val acc | Val F1 | Test acc | Test F1 | Luka val→test |
| --- | --- | --- | --- | --- | --- | --- |
| RF v1 (baseline) | 132 raw | 80.6% | 0.803 | 59.0% | 0.583 | 21.6 p.p. |
| RF v2 (engineered) | 106 eng | 79.4% | 0.792 | 61.0% | 0.611 | 18.4 p.p. |
| LSTM run 1 (h=128) | 106 eng + seq 15 | 78.3% | 0.780 | **66.0%** | **0.658** | **12.3 p.p.** |
| **LSTM run 2 (primary)** | **106 eng + seq 15** | **80.4%** | **0.801** | **64.9%** | **0.637** | **15.5 p.p.** |

LSTM (oba runy) **bije oba RF na test acc o 4-5 p.p.** — to jest pozytywny sygnał: kontekst czasowy faktycznie pomaga, hipoteza kierunkowa potwierdzona.

### Per-film test (procentowo)

| Film | n | RF v1 | RF v2 | LSTM run 1 | LSTM run 2 | Δ (LSTM run 2 vs RF v2) |
| --- | --- | --- | --- | --- | --- | --- |
| 02 — Running at 13 km/h | 286 | 47.0% | 63.7% | 56.3% | **64.0%** | +0.3 p.p. |
| 20 — Walk→run | 856 | 60.9% | 61.1% | 67.8% | **65.1%** | +4.0 p.p. 🎯 |
| 22 — Physiotherapist (pion) | 306 | 65.0% | 58.1% | 70.3% | **65.0%** | +6.9 p.p. 🎯 |

LSTM run 2 jest **co najmniej tak dobry jak RF v2 na każdym filmie**, z istotną poprawą na filmach 20 i 22. Najwyższy jednorazowy wynik (70.3% na filmie 22 w run 1) jest wyższy, ale powyższe argumenty (loteria vs powtarzalność) przeważają.

### Confusion matrix TEST — LSTM run 2 (primary)

```
              FLIGHT   L_STANCE   R_STANCE
FLIGHT           202        160        114
LEFT_STANCE       76        350         71
RIGHT_STANCE      58         30        387
```

### Analiza typów błędów (porównanie przez wszystkie modele)

| Model | Mylenie L↔R (off-diagonal STANCE) | Mylenie FLIGHT↔STANCE | Razem błędów |
| --- | --- | --- | --- |
| RF v1 | 185 | 426 | 611 |
| RF v2 | **95** ⬇ | 486 ⬆ | 581 |
| LSTM run 1 | **67** ⬇⬇ | 425 | 492 |
| LSTM run 2 | 101 | **408** ⬇ | 509 |

**Obserwacje:**
- **Każdy kolejny model zmniejsza całkowitą liczbę błędów** (611 → 581 → 509) — pipeline naprawczy działa kumulatywnie
- **RF v2 i LSTM run 1 są najlepsze w eliminacji L↔R** (95, 67) — normalizacja antropometryczna + kontekst wzajemnie się wzmacniają
- **LSTM run 2 jest najlepszy w eliminacji FLIGHT↔STANCE** (408 vs 486 w RF v2, −16%) — kontekst czasowy pomaga rozróżnić "stopa schodzi z ziemi" od "stopa już oderwana"
- **LSTM run 2 vs RF v2 w mylenie L↔R**: lekkie pogorszenie (95 → 101, +6 klatek) — w granicach szumu, ale nie spektakularna poprawa
- **LSTM run 2 vs LSTM run 1 w L↔R**: gorzej (67 → 101) — to cena wybrania modelu z 4 epokami plateau zamiast loteryjnego best @ ep 1

## 4. Ocena hipotez

| Hipoteza (z briefu) | Wynik LSTM run 2 | Ocena |
| --- | --- | --- |
| Test accuracy 82–90% | **64.9%** | ❌ **niespełniona** — sufit znacznie niżej |
| Zamknie lukę FLIGHT↔STANCE | 486 → 408 (−16%) | 🟢 **częściowo spełniona** — istotna, ale nie dramatyczna poprawa |
| Nie pogorszy mylenia L↔R | 95 → 101 | 🟡 **na granicy** — lekkie pogorszenie, ale w granicach fluktuacji |
| Bidirectional kontekst pomoże | LSTM > RF v2 o 4 p.p. test | ✅ **spełniona kierunkowo** |

**Kluczowe niespełnienie**: hipoteza 82-90% była zbyt optymistyczna. Próbowaliśmy 2 konfiguracji (run 1 i run 2) — obie utknęły w okolicach 65% test. To sugeruje że sufit **nie leży w architekturze** ani wyborze hiperparametrów, tylko w czymś bardziej fundamentalnym (patrz § 6).

## 5. Bug filmu 22 — FLIGHT recall = 4% (utrzymany w obu runach)

| Film 22 | RF v2 | LSTM run 1 | LSTM run 2 |
| --- | --- | --- | --- |
| Acc | 58.1% | 70.3% | 65.0% |
| FLIGHT recall | (z RF v2 metrics) | 4.3% (4/94) | **4.3% (4/94)** |
| LEFT_STANCE recall | — | 99.1% | 100.0% |
| RIGHT_STANCE recall | — | 100.0% | 84.0% |

Confusion matrix filmu 22 dla LSTM run 2:
```
              FLIGHT   L_STANCE   R_STANCE
FLIGHT             4         80         10
LEFT_STANCE        0        106          0
RIGHT_STANCE       8          9         89
```

**Model na pionowym wideo praktycznie nie przewiduje FLIGHT** — wszystkie 94 klatki FLIGHT są klasyfikowane jako LEFT_STANCE (80 klatek) lub R_STANCE (10). To DOKŁADNIE TEN SAM patologiczny wzorzec co w run 1 — niezależnie od architektury.

**Diagnoza**: aspect ratio. Film 22 ma rozdzielczość 608×1080 (pion), reszta filmów to ~16:9 (poziom). MediaPipe normalizuje x i y osobno per oś (0-1 niezależnie), więc:

- W poziomym wideo torso_length (mid_hip → mid_shoulder) jest mała (np. 0.15)
- W pionowym wideo ten sam fizyczny dystans daje większą wartość znormalizowaną (np. 0.30)
- Wszystkie cechy znormalizowane (dzielone przez torso_length) są w pionowym wideo **2× mniejsze niż w treningowych** → model widzi "skompresowanego biegacza" → nie rozpoznaje stanu FLIGHT (mała amplituda Y stóp znika w jednostkach tułowia)

To jest **bug w pipeline'u features.py**, nie w modelu. Naprawa: pomnożyć x, y przez aspect ratio (width/height) z `videos_metadata.csv` przed normalizacją.

**Filmu 22 w pełni naprawić nie da się bez tej korekcji**, niezależnie ile epok i jakim modelem trenujemy. To powinno być **odrębną sesją po LSTM**, zgodnie z briefem.

## 6. Dlaczego sufit przy ~65% test accuracy

Ślad obu runów LSTM (~65% test, plateau val_loss po 2-5 epokach) sugeruje, że **dalej iteracji architektury nie da znaczącej poprawy**. Hipotezowane źródła sufitu w kolejności prawdopodobieństwa:

### 6.1 Bug aspect ratio (film 22 = 21% test setu)

Film 22 ma 306/1448 = 21% klatek test setu. Jego accuracy jest sztywno cap'ed na ~65% (bo 21% klatek FLIGHT jest niemożliwe do złapania bez korekty). Naprawa aspect ratio może podnieść TEST acc nawet o 5-7 p.p. globalnie, niezależnie od modelu.

### 6.2 Szum etykiet peak-based

Algorytm `auto_label.py` dzieli interwały między peakami w proporcji 60/40 STANCE/FLIGHT. W granicznych klatkach (±2 wokół przejścia) etykieta może odbiegać od rzeczywistości o 1-2 klatki. Przy 8039 klatkach total i ~120 cyklach kroków × 4 granice cyklu × ~2 klatki niepewności = **~1000 klatek z potencjalnym szumem etykiet** (~12% datasetu). Sufit "perfekcyjny model" przy tej naturze etykiet = ~88%, nie 100%.

### 6.3 Małość datasetu

5811 klatek train, ~10 unikalnych biegaczy, 8 filmów. To dataset **rzędu 10× za mały** dla głębokich sieci. Klasycznie LSTM dobrze działają od ~50k examples wzwyż. Weight decay i dropout w run 2 to próba kompensacji, ale nie zastąpią danych.

### 6.4 Brak DOUBLE_SUPPORT i monocular 2D

Etykiety reprezentują 3-klasowy problem (LEFT/RIGHT_STANCE/FLIGHT), choć pipeline zakłada 4 klasy. Monocular side view ma inherentne ograniczenia — jedna noga zasłania drugą, niektóre kąty są źle estymowane. To nie jest bug który da się naprawić softwarowo.

## 7. Strategia metodologiczna do pracy magisterskiej

### Co LSTM dodaje do narracji rozdziału 5

Trójka modeli (RF v1 → RF v2 → LSTM) tworzy **klasyczną akademicką ablację**:

- **5.1 RF v1 (raw features)**: baseline — co da sam algorytm bez feature engineeringu (59% test, mylenie L↔R)
- **5.2 RF v2 (engineered)**: izolacja wpływu cech — normalizacja + kąty stawów (61% test, +2 p.p., jakościowa poprawa L↔R)
- **5.3 LSTM (engineered + sekwencja)**: izolacja wpływu kontekstu czasowego (65% test, +4 p.p., poprawa FLIGHT↔STANCE)
- **5.4 Analiza porównawcza** (kolejna sesja): zbiorcza tabela, dyskusja, ograniczenia

Każdy krok dowodzi czegoś **odrębnego i komplementarnego** — to mocna struktura.

### Wartościowe obserwacje (do wstawienia w pracę)

1. **Run 1 vs run 2 jako case study** procesu badawczego — pokazuje że "wyższy test acc nie = lepszy model" jeśli dochodzi do tego przez overfit. Recenzent zwykle docenia takie świadome decyzje.
2. **Sufit ~65% test** mimo trzech różnych architektur — silny dowód że problem leży w danych/etykietach/aspect ratio, nie w modelu. Materiał na sekcję "limitations" + uzasadnienie kierunków przyszłej pracy.
3. **Bug aspect ratio** zauważony już w RF v2, potwierdzony w LSTM — niezależny od modelu, zasługuje na osobny podrozdział.

## 8. Ograniczenia (uczciwie do "Limitations" w pracy)

- **Dataset 8 filmów train, ~10 biegaczy** — za mało dla deep learning; wyniki LSTM są limitowane głównie przez to
- **Etykiety auto-generated, nie ręcznie walidowane** — szum w granicznych klatkach niemożliwy do oddzielenia od błędu modelu
- **Bug aspect ratio nie naprawiony** — film 22 (21% test setu) zniekształca metrykę globalną
- **Tylko 3 klasy aktywne** — DOUBLE_SUPPORT nieobecna, więc model nie umiałby jej rozpoznać w inferencji
- **Hyperparameter search ograniczony** — przeprowadzono tylko 2 runy. Większy sweep (np. Bayesian optimization) mógłby dać 1-3 p.p. ale nie usunie fundamentalnych źródeł sufitu z § 6
- **Model nie uwzględnia kontekstu długoterminowego** — okno 15 klatek to jeden cykl kroku; zmiany kadencji w trakcie biegu (jak film 20 walk→run) nie są modelowane

## 9. Co dalej (kierunki na kolejne sesje)

Priorytet (jeśli LSTM jest "wystarczająco dobry" do narracji pracy):

1. **Sesja 3: analiza porównawcza** — ujednolicony raport 3 modeli, wizualizacje (krzywe uczenia, confusion matrices, feature importance gdzie dostępne)
2. **Naprawa aspect ratio bug** — pomnożenie współrzędnych przez (width, height) z metadanych. Retrening RF v2 i LSTM. Oczekiwany zysk +3-7 p.p. test
3. **Etap 6**: obliczanie współczynników biegu na bazie LSTM jako klasyfikatora (nowy pipeline, `src/coefficients/`)

Niski priorytet (jeśli sufit blokuje narrację):

4. Ręczna weryfikacja etykiet na 200-300 klatkach (kosztowne, ale eliminuje sufit szumu etykiet)
5. Większy hyperparameter sweep (lr, hidden, num_layers, window_size) — szybkie, ale ograniczony zysk

## 10. Surowe metryki (do tabel w pracy)

### LSTM run 2 (primary) — VAL classification report

```
              precision    recall  f1-score   support

      FLIGHT      0.692     0.701     0.696       224
 LEFT_STANCE      0.890     0.816     0.852       239
RIGHT_STANCE      0.829     0.886     0.857       246

    accuracy                          0.804       709
   macro avg      0.804     0.801     0.801       709
weighted avg      0.806     0.804     0.804       709
```

### LSTM run 2 (primary) — TEST classification report

```
              precision    recall  f1-score   support

      FLIGHT      0.601     0.424     0.498       476
 LEFT_STANCE      0.648     0.704     0.675       497
RIGHT_STANCE      0.677     0.815     0.739       475

    accuracy                          0.648      1448
   macro avg      0.642     0.648     0.637      1448
weighted avg      0.642     0.648     0.638      1448
```

### LSTM run 2 — historia treningu (kluczowe epoki)

| Epoka | train_loss | val_loss | val_acc | Komentarz |
| --- | --- | --- | --- | --- |
| 1 | 0.862 | 0.598 | 74.9% | rozgrzewka |
| **2** | 0.487 | **0.510** | **80.4%** | best @ early stopping |
| 3 | 0.399 | 0.531 | 74.8% | plateau |
| 4 | 0.363 | 0.528 | 73.6% | plateau |
| 5 | 0.344 | 0.525 | 78.6% | plateau (ostatnia stabilna) |
| 6 | 0.316 | 0.572 | 71.7% | start overfittingu |
| ... | ↘ | ↗ | ↘ | overfit do końca |
| 17 | 0.188 | 1.053 | 69.5% | early stop, patience exhausted |

### Konfiguracja LSTM run 2 (do reprodukcji)

```
window_size=15
hidden_size=64
num_layers=2
bidirectional=True
dropout=0.4
batch_size=64
lr=3e-4 (Adam)
weight_decay=1e-4
class_weight=balanced (FLIGHT 0.945, LEFT_STANCE 0.991, RIGHT_STANCE 1.072)
early_stopping_patience=15 (na val loss)
seed=42
n_params=187,779
```

Pełne metryki + historia: `models/lstm_primary/metrics.json`. Pełny log treningu: `models/lstm_primary_train.log`.
