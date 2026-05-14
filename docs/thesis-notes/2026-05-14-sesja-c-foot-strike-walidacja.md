# 2026-05-14 — Sesja C: walidacja foot strike pattern (rewizja limitation #9)

## Kontekst

Notatka Iteracji 1 (`2026-05-09-iteracja1-test-set.md`) wymieniała **limitation #9**:

> Foot strike kąty ekstremalne (−46° dla 02 PRAWA, −58° dla 22 LEWA) — wzorzec się
> powtarza, **prawdopodobnie systematyczny błąd metody** (klatka entry-into-stance
> vs faktyczny moment kontaktu).

Hipoteza "systematyczny błąd" zakładała, że klatka wybierana jako moment kontaktu
(`phase[i-1] != STANCE AND phase[i] == STANCE`) trafia **po** rzeczywistym initial
contact — gdy stopa jest już w mid-stance, palce dotykają ziemi, a pięta jest
oderwana. Stąd kąt `forefoot strike` (heel wyżej niż foot_index) który dominuje
w wynikach.

Ale **Janek** w sesji Etapu 7 (2026-05-12) dał kąty **−4° / −3°** — rozsądne midfoot
strike — co podważa hipotezę "systematycznie". Sesja C zaplanowana jako manualna
walidacja na 3 biegaczach, by zdecydować: naprawa algorytmu czy reformulacja
limitation.

## Metodyka

### Wybór klatek

Dla każdego z 3 biegaczy (Adam, 22, Janek):
- z `phases.csv` wybrano **wszystkie** indeksy entry-into-LEFT_STANCE i entry-into-RIGHT_STANCE
- z każdej listy wybrano **3 klatki równomiernie rozłożone** (1/4, 1/2, 3/4 listy)
- razem: 18 klatek (3 biegaczy × 2 nogi × 3 klatki)

### Renderowanie

Nowy skrypt `src/visualization/render_foot_strike_entries.py`:
- MediaPipe Pose (static_image_mode) → szkielet na klatce
- Pasek informacyjny: numer klatki + strona STANCE + obliczony kąt + klasyfikacja
- Kolor paska: zielony=heel, pomarańczowy=midfoot, czerwony=forefoot
- Kąt liczony identyczną konwencją co w `compute_foot_strike_pattern`:
  `atan2(-(foot_index_y - heel_y), foot_index_x - heel_x)`, w stopniach

Output: `data/visualizations/foot_strike_validation/{slug}/`.

### Predykcja globalna (referencyjna)

Z istniejących `*-spatial.json`:

| Biegacz | mean L | mean R | dominant L | dominant R | n_klatek L | n_klatek R |
|---|---|---|---|---|---|---|
| 22 | −97.0° | −98.8° | forefoot (15/15) | forefoot (14/14) | 15 | 14 |
| Adam | −32.9° | −11.5° | forefoot (110/5/0) | forefoot (87/27/2) | 115 | 116 |
| Janek | −4.2° | −2.8° | midfoot (38/60) | midfoot (24/72) | 98 | 99 |

## Wyniki walidacji wizualnej (per biegacz)

### Janek — POTWIERDZONE ✓

Kąty wybranych klatek: **L = −6.5°, −7.8°, +1.8°; R = −11.7°, −5.6°, +4.6°**.

Wizualna inspekcja: stopa płasko na bieżni w klatce kontaktu, brak wyraźnej dominacji
pięty ani palców. **Kąty zgadzają się z wzorcem midfoot strike.**

**Wniosek**: dla standardowego ujęcia z boku (landscape, kamera na wysokości bieżni)
metoda działa poprawnie. Predykcja dominującej klasy "midfoot strike" jest wiarygodna.

### Adam — CZĘŚCIOWO

Kąty wybranych klatek: **L = −15.9°, −18.3°, −55.8°; R = −4.0°, −24.5°, −12.0°**.

Wizualna inspekcja: prawa noga (bliżej kamery) wygląda OK — niewielka dominacja palców
zgodna z forefoot strike. **Lewa noga** (dalej od kamery, kąt zdjęcia lekko od dołu)
ma kąt przesadzony — wektor heel→foot_index jest skrócony przez perspektywę, co
matematycznie wzmacnia komponent y (kąt bardziej ujemny).

**Wniosek**: asymetria L vs R (−33° vs −12°) to **artefakt perspektywy kamery**,
nie biomechaniki. Dominacja "forefoot strike" prawdopodobnie prawdziwa, ale
ilościowy kąt zaniżony dla lewej.

### Film 22 — ZAWODZI

Kąty wybranych klatek: **L = −159.7°, −104.7°, −93.7°; R = −81.8°, −116.6°, −101.2°**.

Wizualna inspekcja: film **pionowy** (portrait) — biegacz w wąskim kadrze, kamera
ustawiona z innego kąta niż standardowe ujęcie z boku. Wszystkie kąty wykraczają poza
fizjologiczny zakres (|kąt| > 90° oznacza, że wektor heel→foot_index pokazuje "w tył"
w osi X, co jest geometrycznie niemożliwe dla biegacza obróconego twarzą w kierunku biegu).

**Wniosek**: **predykcja foot strike pattern jest bezwartościowa dla 22.** Dominacja
"forefoot strike" to artefakt pionowej orientacji kadru, nie biomechaniki.

## Decyzja: reformulacja limitation #9

Hipoteza "systematyczny błąd metody" **odwołana**. Metoda działa dla standardowego
ujęcia, zawodzi przy nietypowym. Nowa formulacja limitation:

> **Foot strike pattern jest wrażliwy na perspektywę kamery.** Wiarygodny przy
> standardowym ujęciu z boku (landscape, kamera na wysokości bieżni, prostopadle
> do toru biegu). Zawodny przy pionowym lub ukośnym ujęciu. System ostrzega
> użytkownika flagą `low_confidence` gdy `|mean_angle| > 45°`, ale nie produkuje
> wartościowych wskazań co do wzorca lądowania.

## Implementacja — mitygant w kodzie

### `src/coefficients/spatial_metrics.py`

Funkcja `compute_foot_strike_pattern` dorzuca klucz `low_confidence: bool`
w każdym `{side}_foot` w spatial.json:

```python
low_confidence = bool(mean_angle is not None and abs(mean_angle) > 45.0)
```

Próg **45°** wybrany na podstawie walidacji wizualnej:
- Janek (poprawnie): |kąt| ≤ 12°
- Adam (borderline): jedna noga 12°, druga 33° (asymetria perspektywy)
- 22 (zawodzi): |kąt| 82-160°

Próg 45° oddziela "OK z marginesem ergonomicznym" od "ewidentny artefakt".
Adam **nie** dostaje flagi (mean L=−33° < 45°) — bo lewa noga jest na granicy,
ale dominująca klasyfikacja "forefoot strike" jest spójna z prawą i prawdopodobnie
prawdziwa biomechanicznie.

### `src/recommendations/rules.py`

Funkcja `check_foot_strike` dodaje nową regułę przed regułami semantycznymi:

```python
def check_foot_strike(spatial, symmetry):
    # ... detekcja low_confidence per strona ...
    if low_conf_sides:
        out.append(Recommendation(
            rule_id="foot_strike_low_confidence",
            severity="warning",
            category="foot_strike",
            title="Foot strike: niska wiarygodność (perspektywa kamery)",
            citation="Walidacja wizualna 2026-05-14 (Sesja C)",
            # ...
        ))
        return out  # nie odpalaj reguł semantycznych — opierają się na klasyfikacji
                    # która przy |kąt|>45° jest artefaktem perspektywy
```

**Fallback dla legacy spatial.json**: jeśli klucz `low_confidence` nie istnieje
(stare pliki przed Sesją C), reguła sprawdza `abs(mean) > 45°` bezpośrednio.

## Weryfikacja (smoke test na 3 biegaczach)

| Biegacz | Przed Sesją C | Po Sesji C | Komentarz |
|---|---|---|---|
| 22 | 0/3/5/2 = 10 | **0/4/5/1** = 10 | `foot_strike_consistent` (info, "obie forefoot — konsystentne") **zastąpione** przez `foot_strike_low_confidence` (warning, "nie wierz, pionowe wideo") ✅ |
| Adam | 0/2/1/5 = 8 | 0/2/1/5 = 8 | Bez zmian — mean L=−33°, R=−12° pod progiem 45° ✅ |
| Janek | 3/3/3/2 = 11 | 3/3/3/2 = 11 | Bez zmian — mean L=−4°, R=−3° pod progiem ✅ |

Nowa reguła **nie produkuje false positives** na 24/Adam ani 25/Janek, łapie tylko 22.

## Co to oznacza dla pracy magisterskiej

### Rozdział 7 (Rekomendacje)

Katalog reguł rośnie z 12+ do 13+ (warning `foot_strike_low_confidence`). To **reguła
walidacji jakości** — analogiczna do `check_data_quality`, ale dotyczy
**warunków akwizycji wideo**, nie predykcji modelu LSTM.

### Rozdział "Limitations"

Limitation #9 z notatki Iteracji 1 **odwołana w starej formie** i **zastąpiona** nową
formulacją (wrażliwość na perspektywę). Dodatkowo: kod ma mitygant, więc limitation
ma **konkretny zapis w `rules.py`**, nie tylko w tekście pracy.

### Argument metodologiczny

Sesja C to **przykład iteracyjnej walidacji metody**: hipoteza z notatki Iteracji 1
("systematyczny błąd metody") została **falsyfikowana** manualną inspekcją 18 klatek,
a kod rozszerzony o ostrzeżenie dla użytkownika gdy warunki akwizycji są nietypowe.
To czysty cykl naukowy: hipoteza → walidacja empiryczna → reformulacja → implementacja.

## Otwarte pytania / future work

1. **Asymetria perspektywy (Adam case)**: lewa noga ma kąt 3× bardziej ujemny niż prawa,
   ale obie pod progiem 45°. Można rozważyć **drugi próg**: gdy `|mean_L - mean_R| > 20°`,
   flagować "asymetria perspektywy" (watch). Czy warto — zależy od czy false positives
   na innych biegaczach z naturalną asymetrią L/R.
2. **Inny algorytm dla pionowego wideo**: dla orientacji portrait można by zamienić
   konwencję osi (kąt liczony względem osi Y zamiast X). Wykracza poza scope pracy.
3. **Walidacja na większej próbce**: 3 biegaczy to mała próba. Większa walidacja (np. na
   10 biegaczach z znanym foot strike) wzmocniłaby konkluzje. Brakuje datasetu.
4. **Auto-detekcja orientacji wideo**: można sprawdzać aspect ratio i ostrzegać
   "video pionowe — wyniki spatial mogą być zaburzone" już na etapie ekstrakcji.

## Artefakty

```
src/coefficients/spatial_metrics.py
  + low_confidence flag w wyjściu compute_foot_strike_pattern (próg 45°)

src/recommendations/rules.py
  + foot_strike_low_confidence (warning) w check_foot_strike
  + fallback abs(mean)>45° dla legacy spatial.json

src/visualization/render_foot_strike_entries.py  (NOWY)
  + skrypt walidacji wizualnej: entry indeksy → szkielet + kąt + klasyfikacja

data/visualizations/foot_strike_validation/
  ├── 22/                 (6 PNG)
  ├── 24-adam/            (6 PNG)
  └── 25-janek/           (6 PNG)
```
