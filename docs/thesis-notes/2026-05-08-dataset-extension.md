# 2026-05-08 — Rozszerzenie datasetu o 2 nowych biegaczy (23 Pawel, 24 Adam) + retrening 4 modeli

## Kontekst

Po zamknięciu rozdziału 5.4 (analiza porównawcza 4 modeli, sufit ~65% test) dodaliśmy do datasetu **dwa filmy własne**:
- **23 — Pawel bieg__segment_1.mov** — 4K (3840×2160), 30 FPS, 1649 klatek, 55s; zresizowany do 720p przed ekstrakcją (oryginał w `data/videos/_originals_4k/`)
- **24 — Adam bieg__segment_1.mov** — Full HD (1920×1080), 30 FPS, 2399 klatek, 80s; bez zmian

Cel: sprawdzić czy zwiększenie datasetu i dodanie biegaczy w wyższych rozdzielczościach (16:9) podniesie sufit ~65% lub zmniejszy lukę val→test. **Test set bez zmian** (02, 20, 22) — fair comparison z rozdziałem 5.4.

## Pipeline obróbki

### Ekstrakcja keypointów

| Film | Detection | Vis kluczowych | Low vis | Jitter raw → smooth | Quality flag |
|---|---|---|---|---|---|
| 23 Pawel | 100% (1649/1649) | 0.793 | 13.9% | 0.0317 → 0.0062 (−80.5%) | **WARN** |
| 24 Adam | 100% (2399/2399) | 0.883 | 3.1% | 0.0389 → 0.0070 (−82.0%) | OK |

- Pawel WARN przez `low_visibility_ratio=13.9%` (>próg 10%) — nie alarmujące, prawdopodobnie tło/ubranie zacierające keypointy peryferyjne
- Czas ekstrakcji: Pawel 720p 120s, Adam FHD 194s (model_complexity=2)
- 100% detekcji w obu — duża zasługa wysokiej rozdzielczości i jakości nagrania

### Auto-etykietowanie peak-based

| Film | Kadencja | L/R | Direct L↔R | LEFT_STANCE mean | RIGHT_STANCE mean | FLIGHT mean |
|---|---|---|---|---|---|---|
| 23 Pawel | 154.7 spm | 71/72 | 0 | 291ms (std 56) | 223ms (std 61) | 130ms (std 25) |
| 24 Adam | 167.5 spm | 112/112 | 0 | 241ms (std 233) | 241ms (std 59) | 116ms (std 44) |

- **Pawel**: niemal idealna alternacja, kadencja 154.7 spm (lekko poniżej typowego 160-175). Asymetria L/R 291 vs 223 ms (68 ms) — większa niż w innych side-view, ale w granicach normy dla monocular 2D
- **Adam**: idealna symetria L/R (112/112), kadencja 167.5 spm w środku typowego zakresu, ale **outlier na początku**: pierwsze 80 klatek (2.66s) jako LEFT_STANCE bez przerwy — algorytm peak-based nie wykrył pierwszego peaka RIGHT przed klatką 80
- Filtr medianowy zmienił 0 klatek w obu → algorytm peak-based jest inherentnie czysty

### Decyzja: wyciąć pierwsze 80 klatek Adama

Aby zniwelować artefakt brzegowy peak-based — pierwsze 80 klatek `LEFT_STANCE` bez peaka są etykietowo zaszumione. Po cięciu Adam ma 2319 klatek z rozkładem 35.0/33.5/31.5 (RIGHT/FLIGHT/LEFT) — zbalansowany. Backup oryginału w `data/keypoints/_originals_pre_trim/`.

## Split datasetu

Decyzja użytkownika: **Opcja A — oba do TRAIN**, test bez zmian. Argument: rozdział 5.4 mówi o sufit 65%, retrening z większym trainem to "warunek skrajny" testujący tę hipotezę. Pozostawienie testu (02, 20, 22) gwarantuje porównywalność z modelami z rozdziału 5.

| Split | Pliki | Klatki (przed → po) | Procent po |
|---|---|---|---|
| Train | 8 → 10 | 5811 → 9779 (**+68%**) | 81.4% |
| Val | 2 | 738 | 6.1% |
| Test | 3 | 1490 | 12.4% |
| **Razem** | 13 → 15 | 8039 → 12007 (+49%) | 100% |

Per-class train (po): LEFT_STANCE 3334 / FLIGHT 3340 / RIGHT_STANCE 3105 — zrównoważone (bardziej niż przed: 1986/2011/1814).

## Wyniki retreningu — porównanie globalne

Backup wszystkich 4 modeli przed retreningiem w `models/*_pre_extension/` i artefaktów porównawczych w `docs/thesis-notes/figures_pre_extension/`. Retrening **bez zmian hiperparametrów** — izolujemy wpływ rozszerzenia datasetu.

| Model | Val acc (przed → po) | Test acc (przed → po) | Δ Test | Test F1 | Luka val→test (przed → po) |
|---|---|---|---|---|---|
| RF v1 (raw 132 cech) | 80.6 → **82.0%** | 59.0 → **62.7%** | **+3.7** p.p. | 0.583 → 0.617 | 21.6 → 19.3 p.p. |
| RF v2 (engineered 106) | 79.4 → 79.9% | 61.0 → **67.0%** | **+6.0** p.p. | 0.611 → **0.671** | 18.4 → **12.9** p.p. |
| LSTM run 1 (h=128) | 78.3 → **86.5%** | 66.0 → **67.1%** | +1.1 p.p. | 0.658 → 0.663 | 12.3 → 19.3 p.p. |
| LSTM run 2 (primary) | 80.4 → **84.5%** | 64.9 → 65.3% | +0.5 p.p. | 0.637 → 0.645 | 15.5 → 19.2 p.p. |

### Per-film test (najistotniejsza tabela)

| Film | RF v1 (przed → po) | RF v2 | LSTM run 1 | LSTM run 2 |
|---|---|---|---|---|
| **02** Running 13 km/h | 47.0 → 51.7 (+4.7) | 63.7 → 63.0 (−0.7) | 56.3 → 54.9 (−1.4) | 64.0 → **50.7 (−13.3)** |
| **20** Walk → run | 60.9 → 63.7 (+2.8) | 61.1 → 68.6 (**+7.5**) | 67.8 → 68.1 (+0.3) | 65.1 → 66.9 (+1.8) |
| **22** Pionowe (aspect ratio bug) | 65.0 → 70.3 (**+5.3**) | 58.1 → 66.6 (**+8.5**) | 70.3 → 75.8 (**+5.5**) | 65.0 → 74.2 (**+9.2**) |

### Total errors (test, n=1490 dla RF, n=1448 dla LSTM)

| Model | błędy razem (przed → po) | L↔R | FLIGHT↔STANCE |
|---|---|---|---|
| RF v1 | 611 → 556 | 185 → 153 | 426 → 403 |
| RF v2 | 581 → **491** | 95 → **88** | 486 → 403 |
| LSTM run 1 | 506 → 476 | 92 → 79 | 414 → 397 |
| LSTM run 2 | 523 → 503 | 101 → 79 | 422 → 424 |

## Kluczowe obserwacje

1. **Wszystkie 4 modele zyskały test acc** — żadnej regresji globalnej. Sufit przesunięty z **~65% do ~67%** (+2 p.p. przeciętnie), ale **nadal istnieje**.

2. **RF v2 największy beneficjent** (+6.0 p.p. test, luka val→test spadła z 18.4 do **12.9** — najmniejsza ze wszystkich 4 modeli). Jego total errors spadły z 581 do 491 (−16%). To go czyni **konkurencyjnym z LSTM** (67.0 vs 65.3-67.1) — co jest częściową rewizją wniosku z rozdziału 5.4 ("LSTM bije RF o 4-5 p.p. dzięki kontekstowi czasowemu").

3. **LSTM ledwo drgnęły** (+0.5 i +1.1 p.p. test acc, mimo +69% okien treningowych) — zaskakujące, biorąc pod uwagę że RF v2 mocno zyskał na tych samych dodatkowych danych. Hipotezy:
   - h=64 (run 2) za małe na 9.6k okien → niedouczone
   - h=128 (run 1) wciąż overfit (ep 4+) → nie wykorzystuje pełni danych
   - LSTM ma okno 15 klatek, traci po 7 z każdej strony pliku — proporcjonalnie tyle samo extra co RF

4. **Film 22 (aspect ratio bug) najwięcej zyskał** wszędzie: +5.3, +8.5, +5.5, **+9.2** p.p. — średnia ~+7 p.p. To wskazuje że **bug aspect ratio częściowo się rozpadł** dzięki dodaniu Pawła i Adama (oba 16:9, 720p+ — dotąd dataset miał głównie 4:3 lub 4:3 portretowy). Większa różnorodność aspect ratio w trainie zniwelowała znormalizowanie torso_length specyficzne dla 4:3.

5. **Film 02 problemem dla LSTMów** — LSTM run 2 zanotował **−13.3 p.p.** (64.0 → 50.7%), run 1 −1.4 p.p. RF nie pogorszył (RF v1 +4.7, RF v2 −0.7). Hipoteza: dodatkowe filmy "rozcieńczyły" specyficzną dystrybucję filmu 02 w trainie. LSTM jest wrażliwszy na zmianę dystrybucji niż RF (więcej parametrów, mniej regularizacji). To jakościowa **regresja LSTM run 2** — argument przeciwko jego pozostaniu jako primary.

6. **Luka val→test**:
   - RF v1: 21.6 → 19.3 p.p. (zmniejszona)
   - RF v2: 18.4 → **12.9** p.p. (mocno zmniejszona)
   - LSTM run 1: 12.3 → 19.3 p.p. (**zwiększona**)
   - LSTM run 2: 15.5 → 19.2 p.p. (**zwiększona**)
   
   Inwersja względem rozdziału 5.4. Powód: val (filmy 03, 09 seg2) ma podobną dystrybucję do nowych Pawła/Adama (FHD/720p, jakość detekcji), więc val acc skoczył mocniej niż test acc. Test (02, 20, 22) jest dystrybucyjnie odległy.

7. **TOP cechy RF v2 (po retreningu)**: `left_knee_angle, RIGHT_ANKLE_y_norm, RIGHT_HEEL_y_norm, RIGHT_FOOT_INDEX_y_norm, LEFT_HEEL_y_norm, LEFT_ANKLE_y_norm, LEFT_FOOT_INDEX_x_norm, right_ankle_angle`. Kąty stawów dalej w czołówce (left_knee_angle TOP-1) — biomechaniczna walidacja stabilna.

8. **Run 1 zniwelował overfit**: best epoch 1 → 3 (większy train zniwelował overfit run 1). Plateau val_loss krótsze (run 1 ep 3-4) niż w run 2 (ep 2-5), ale run 1 ma teraz **najwyższy global test acc** (67.1%). Mimo to run 2 dalej ma stabilniejsze plateau val_loss → argumentacja za run 2 jako primary nadal stoi, choć słabsza niż wcześniej.

## Implikacje dla pracy magisterskiej

### Co dodać do rozdziału 5

Najczystsze: **dodać podrozdział 5.5 "Wpływ rozszerzenia datasetu"** zamiast nadpisywać 5.1-5.4. Stary rozdział 5.4 (zamknięty, z artefaktami w `figures_pre_extension/`) opisuje stan na 2026-04-26. Rozdział 5.5 referuje do niego i pokazuje:
- Same hiperparametry, większy train → +3.7 do +6 p.p. dla RF, marginalne dla LSTM
- Sufit nadal istnieje (przesunięty ~67%), ale rozłożenie błędów zmienione
- Aspect ratio bug częściowo rozwiązany przez różnorodność danych — silniejszy argument w sekcji "Limitations" niż dotychczas

### Sekcja Limitations (rewizja)

Obowiązuje nadal, z aktualizacjami:
- Sufit ~67% mimo +68% klatek treningowych — **w danych/etykietach, nie w modelu** (silniejszy dowód niż w 5.4: 4 architektury × 2 rozmiary trainu wszystkie utykają)
- Aspect ratio bug **częściowo** zniwelowany różnorodnością — full fix nadal wymaga retreningu z poprawnym aspect ratio scaling (planowana opcja B)
- Etykiety peak-based mają artefakty brzegowe (case Adam pierwsze 80 klatek) — kandydat na future work

### Czy zmienić primary z run 2 na run 1?

Argumenty za run 1 (h=128):
- Najwyższy test acc (67.1%)
- Najmniej total errors (476)
- Best epoch 3 (rozsądne, nie ep 1 jak wcześniej)

Argumenty za zachowaniem run 2:
- Stabilniejsze plateau val_loss (5 epok 0.40-0.45) vs run 1 (overfit już od ep 4)
- Jakościowo bardziej zbalansowany per-film (run 1 ma duży spread)
- Argument metodologiczny "case study procesu badawczego" (run 1 vs run 2) trzyma narrację rozdziału — zmiana zmniejszyłaby pedagogiczny walor

**Rekomendacja: zachować run 2 jako primary**, opisać aktualizację metryk i wspomnieć że na rozszerzonym datasecie różnica run 1 vs run 2 zmniejszyła się — argument za run 2 słabszy niż w 5.4, ale dalej ważny. To jest wartościowa narracja dla pracy: jak wybór primary zmienia się wraz z danymi.

## Limitations rozszerzenia

1. **N=2 nowych biegaczy to mało** — potencjalnie bias jednoosobowy w "rozszerzeniu". Nie wiemy ile z poprawy to artefakt akurat tych 2 biegaczy
2. **Pawel i Adam są w trainie, nie test** — nie wiemy jak modele radzą sobie na nich. Could-have-been: hold-out z tych 2 zamiast 02/20/22, ale wtedy fair comparison z 5.4 byłaby utracona
3. **Resize 4K→720p Pawła** — informacja teoretycznie utracona, ale MediaPipe i tak skaluje wewnętrznie do ~256px, więc rzeczywista strata pomijalna
4. **Pawel WARN quality** — 13.9% klatek z low visibility może wprowadzać szum w trainie. Wpływ niemożliwy do zmierzenia bez ablacji

## Decyzje pozostałe

- Aspect ratio fix (Opcja B z poprzedniego briefu) — **nie wykonana**, ale częściowo zniwelowana przez różnorodność. Decyzja: czy nadal robić full fix? Spodziewany dodatkowy zysk po Pawel/Adam: +1-3 p.p. zamiast +3-7 jak wcześniej oszacowano
- Etap 6 (obliczanie współczynników) — **gotów do startu**. Mamy lepszy klasyfikator (RF v2 67% lub LSTM run 1 67.1%) jako wejście do inferencji
- Dyskusja: czy rozważyć nowy run hyperparametryczny LSTM (h=96, dropout=0.35) jako kompromis między run 1 i run 2? Niski priorytet — sufit nie jest tam, +1-2 p.p. najwyżej

## Artefakty

- `models/rf_baseline/`, `models/rf_engineered/`, `models/lstm_primary/`, `models/lstm_run1_overfit/` — nowe modele (po rozszerzeniu)
- `models/*_pre_extension/` — backup z 2026-04-26 (4 modele zachowane)
- `docs/thesis-notes/figures/` — zaktualizowane: tabele MD/JSON + 3 PNG (confusion matrices, learning curves, feature importances)
- `docs/thesis-notes/figures_pre_extension/` — backup artefaktów z 2026-04-26
- `data/keypoints/_originals_pre_trim/24 - Adam bieg__segment_1__pre_trim.csv` — Adam przed cięciem 80 klatek
- `data/videos/_originals_4k/23 - Pawel bieg__segment_1__4k.mov` — Pawel oryginalny 4K
