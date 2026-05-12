# Przewodnik po projekcie — analiza biomechaniczna biegu

Dokument do prezentacji pracy magisterskiej. Wyjaśnia co, jak i po co robimy na każdym etapie.

---

## 1. Cel projektu

System, który na wejściu dostaje **nagranie wideo osoby biegnącej na bieżni** (ujęcie z boku), a na wyjściu zwraca **współczynniki biomechaniczne** (kadencja, czas kontaktu, kąty stawów itp.) z **rekomendacjami poprawy techniki**.

### Pipeline (łańcuch przetwarzania)

```
Wideo MP4 → Szkielet (33 punkty ciała) → Fazy biegu → Współczynniki → Rekomendacje
```

Każdy krok opiera się na poprzednim — nie ma drogi na skróty.

---

## 2. Punkty na ciele — co to jest i po co

### Czym jest MediaPipe Pose?

MediaPipe Pose to gotowy model AI od Google, który na **każdej klatce wideo** wykrywa **33 punktów na ciele** człowieka (tzw. keypointy / landmarki). Nie trzeba go trenować — działa „z pudełka" na dowolnym nagraniu z osobą.

### Co to są te „kropki" na ciele?

Każdy punkt to **estymowana pozycja konkretnego stawu lub części ciała** w przestrzeni obrazu. Dla każdego punktu dostajemy 4 wartości:

| Wartość        | Co oznacza                                | Zakres                           |
| -------------- | ----------------------------------------- | -------------------------------- |
| **x**          | pozycja pozioma na klatce                 | 0.0 (lewa krawędź) → 1.0 (prawa) |
| **y**          | pozycja pionowa na klatce                 | 0.0 (góra) → 1.0 (dół)           |
| **z**          | szacowana głębokość (odległość od kamery) | wartości ujemne = bliżej kamery  |
| **visibility** | pewność detekcji                          | 0.0 (niewidoczny) → 1.0 (pewny)  |

### Pełna mapa 33 punktów

```
                     NOSE (0)
                    /        \
    L_EYE_OUTER(7) L_EYE(2)   R_EYE(5) R_EYE_OUTER(6)
    L_EYE_INNER(1)             R_EYE_INNER(4)
    L_EAR (8)                  R_EAR (7)
    L_MOUTH (9)                R_MOUTH (10)

         L_SHOULDER (11) ———— R_SHOULDER (12)
              |                     |
         L_ELBOW (13)          R_ELBOW (14)
              |                     |
         L_WRIST (15)          R_WRIST (16)
        / |  \                  / |  \
  L_PINKY L_INDEX L_THUMB  R_PINKY R_INDEX R_THUMB
   (17)    (19)    (21)     (18)    (20)    (22)

         L_HIP (23) ————————— R_HIP (24)
              |                     |
         L_KNEE (25)           R_KNEE (26)
              |                     |
         L_ANKLE (27)          R_ANKLE (28)
              |                     |
         L_HEEL (29)           R_HEEL (30)
              |                     |
         L_FOOT_INDEX (31)     R_FOOT_INDEX (32)
```

### Podział punktów ze względu na znaczenie w projekcie

Nie wszystkie 33 punkty są równie ważne. Dzielimy je na 3 grupy:

**Grupa A — kluczowe (12 punktów, indeksy 11–12, 23–32):**
Używane bezpośrednio do obliczeń współczynników i detekcji faz biegu.

| Punkt                   | Do czego służy w naszym projekcie                                                |
| ----------------------- | -------------------------------------------------------------------------------- |
| **SHOULDER (11, 12)**   | Pochylenie tułowia — kąt linii ramiona→biodra względem pionu                     |
| **HIP (23, 24)**        | Centrum masy ciała, vertical oscillation (podskakiwanie), kąt biodra             |
| **KNEE (25, 26)**       | Kąt kolana przy lądowaniu — za prosty = overstriding, za ugięty = strata energii |
| **ANKLE (27, 28)**      | Kąt kostki, pozycja stopy względem biodra                                        |
| **HEEL (29, 30)**       | Detekcja kontaktu z podłożem, foot strike pattern (czy ląduje na pięcie)         |
| **FOOT_INDEX (31, 32)** | Palce stopy — uzupełnienie detekcji kontaktu (toe-off)                           |

**Grupa B — pomocnicze (1 punkt):**

| Punkt        | Do czego służy                                                                                                                                           |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **NOSE (0)** | Detekcja kierunku biegu — porównujemy pozycję X nosa z biodrem. Nos na prawo od bioder = biegacz biegnie w prawo. To jedyny punkt twarzy, który używamy. |

**Grupa C — nieużywane w projekcie (20 punktów, indeksy 1–10, 13–22):**

| Punkty                                             | Dlaczego ich nie używamy                                                                                                                                          |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Oczy, uszy, usta (1–10)**                        | MediaPipe Pose to model ogólnego przeznaczenia — te punkty służą do rozpoznawania gestów, wyrazu twarzy, języka migowego. Do analizy biegu nie mają zastosowania. |
| **Łokcie, nadgarstki (13–16)**                     | Praca rąk ma pewien wpływ na technikę biegu, ale w tym projekcie się na nich nie skupiamy. Mogłyby służyć np. do analizy symetrii pracy ramion.                   |
| **Dłonie — kciuk, wskazujący, mały palec (17–22)** | Szczegółowa pozycja palców dłoni jest kompletnie nieistotna dla biomechaniki biegu.                                                                               |

Tych 20 punktów jest w CSV bo MediaPipe zwraca je automatycznie — nie filtrujemy ich, bo narzut jest minimalny (dodatkowe 80 kolumn), a mogą się przydać w przyszłości (np. analiza pozycji głowy lub pracy ramion).

Pozostałe punkty (oczy, uszy, usta, dłonie) mają marginalne znaczenie — służą głównie do orientacji głowy i pozycji rąk.

### Dlaczego „visibility" jest ważne?

Gdy biegacz jest ujęty z boku, noga **dalsza od kamery** jest częściowo zasłonięta przez bliższą nogę. MediaPipe wtedy „zgaduje" jej pozycję — visibility spada poniżej 0.5. Monitorujemy to, bo niska visibility = mniej wiarygodne dane.

---

## 3. Etapy pracy — co, jak, po co

### Etap 1: Zebranie filmików

**Co:** Pobraliśmy 9 filmów z YouTube — bieżnia, ujęcie z boku, cała sylwetka widoczna.

**Po co:** Potrzebujemy materiału treningowego dla klasyfikatora faz biegu. Różne filmy = różni biegacze, prędkości, kąty kamery → model uczy się rozpoznawać fazy biegu niezależnie od warunków.

**Ważne:** Filmy w datasecie służą TYLKO do trenowania modelu. Nie obliczamy na nich współczynników biegu — to robi się dopiero na nowym wideo od użytkownika.

### Etap 2: Ekstrakcja keypointów

**Co:** Skrypt `extract_keypoints.py` przetwarza każdy filmik klatka po klatce przez MediaPipe Pose. Wynik: plik CSV z 33 punktami × 4 wartości na każdą klatkę.

**Jak działa:**

1. Otwieramy wideo → odczytujemy FPS z metadanych
2. Dla każdej klatki: MediaPipe wykrywa 33 punktów → zapisujemy do macierzy
3. Po przetworzeniu WSZYSTKICH klatek: wygładzamy sygnał filtrem Savitzky-Golay
4. Zapisujemy do CSV + raport jakości

**Po co wygładzanie (Savitzky-Golay)?**

MediaPipe nie jest idealny — pozycje punktów „skaczą" między klatkami (jitter/szum). Filtr Savitzky-Golay wygładza sygnał zachowując kształt krzywej (nie zniekształca peaków). Bez wygładzania obliczone kąty i odległości byłyby zaszumione.

Efekt: redukcja jittera o **53–86%** w zależności od filmiku.

**Po co raport jakości?**

Nie każdy filmik jest równie dobry. Raport mierzy:

- **Detection rate** — w ilu % klatek MediaPipe w ogóle wykrył osobę
- **Visibility** — jak pewne są wykryte punkty
- **Jitter** — jak bardzo punkty skaczą (przed i po wygładzeniu)
- **FPS** — ile klatek na sekundę (krytyczne dla obliczeń czasowych)

Na tej podstawie klasyfikujemy filmy: OK / WARN / BAD.

### Etap 3: Auto-etykietowanie faz biegu

**Co:** Skrypt `auto_label.py` automatycznie przypisuje każdej klatce jedną z 4 faz biegu.

**Fazy biegu — co oznaczają:**

```
  LEFT_STANCE         FLIGHT         RIGHT_STANCE        FLIGHT
  (lewa na ziemi)   (obie w         (prawa na ziemi)   (obie w
                     powietrzu)                          powietrzu)

  ┌─────────┐       ┌───────┐       ┌──────────┐       ┌───────┐
  │  L na   │       │ obie  │       │  R na    │       │ obie  │
  │  ziemi  │──────▶│  w    │──────▶│  ziemi   │──────▶│  w    │──▶ ...
  │  R w    │       │ powie-│       │  L w     │       │ powie-│
  │  powiet.│       │ trzu  │       │  powiet. │       │ trzu  │
  └─────────┘       └───────┘       └──────────┘       └───────┘

  ◄────────────── jeden pełny cykl (stride) ──────────────────────►
```

Jeden cykl biegu to: **L_STANCE → FLIGHT → R_STANCE → FLIGHT → powtórz**. Przy chodzeniu nie ma fazy FLIGHT, a może być DOUBLE_SUPPORT (obie stopy na ziemi jednocześnie).

**Jak algorytm wykrywa fazy:**

1. **Sygnał kontaktu**: Dla każdej stopy bierzemy `max(heel_y, foot_index_y)` — to wartość Y (pionowa pozycja) najniższej części stopy. Wysoki Y = stopa blisko ziemi.

2. **Detekcja foot strikes (peaków)**: Szukamy momentów, gdy stopa uderza w podłoże — to lokalne maksima sygnału Y. Używamy `scipy.signal.find_peaks` z parametrem `prominence` (minimalna „wyrazistość" peaka).

3. **Wymuszenie alternacji**: W prawidłowym biegu stopy kontaktują naprzemiennie: L, R, L, R... Jeśli algorytm wykryje dwa peaki tej samej stopy z rzędu, zachowuje ten wyraźniejszy.

4. **Podział na fazy**: Między dwoma kolejnymi peakami (np. L→R) szukamy momentu, gdy obie stopy są najdalej od ziemi — to centrum fazy FLIGHT. Reszta to STANCE odpowiedniej stopy.

5. **Filtr medianowy**: Końcowe wygładzenie — eliminuje sporadyczne błędy (1–2 klatki).

**Po co etykiety faz?**

Etykiety to „odpowiedzi", na których uczymy klasyfikator. W etapie 5 model dostaje keypointy jednej klatki i uczy się przewidywać fazę. Dzięki temu na NOWYM wideo od użytkownika model będzie w stanie powiedzieć „ta klatka to LEFT_STANCE".

Z sekwencji faz potem obliczamy współczynniki: kadencja, czas kontaktu, czas lotu itp.

---

## 4. Współczynniki biomechaniczne — co mierzymy i dlaczego

### Z faz biegu (wymagają sekwencji etykiet + FPS wideo)

| Współczynnik                       | Jak liczymy                    | Co mówi biegaczowi                                              |
| ---------------------------------- | ------------------------------ | --------------------------------------------------------------- |
| **Kadencja** [kroki/min]           | (liczba kontaktów / czas) × 60 | Optymalna: 170–180. Za niska → za długie kroki, ryzyko kontuzji |
| **GCT** (ground contact time) [ms] | czas trwania fazy STANCE       | Krótszy = lepsza ekonomia biegu (do pewnej granicy)             |
| **Czas lotu** [ms]                 | czas trwania fazy FLIGHT       | Brak lotu = chód. Za długi = za dużo podskakiwania              |
| **Stride length** [m]              | prędkość_bieżni × czas_cyklu   | Wymaga podania prędkości przez użytkownika                      |
| **Duty factor**                    | GCT / czas_cyklu               | < 0.5 = bieg, > 0.5 = technicznie chód                          |

### Z keypointów (geometria ciała w klatce)

| Współczynnik                  | Jak liczymy                                        | Co mówi biegaczowi                                             |
| ----------------------------- | -------------------------------------------------- | -------------------------------------------------------------- |
| **Kąt kolana** [°]            | kąt wektorów biodro→kolano i kolano→kostka         | 160–175° przy lądowaniu = OK. Za prosty = overstriding         |
| **Pochylenie tułowia** [°]    | kąt linii biodra→ramiona vs pion                   | 5–15° do przodu = OK. Za pionowy = nie wykorzystuje grawitacji |
| **Vertical oscillation** [cm] | max(Y_hip) − min(Y_hip) w cyklu                    | 6–8 cm = dobry. >12 cm = marnuje energię na podskakiwanie      |
| **Overstriding**              | odległość X między kostką a biodrem przy lądowaniu | Stopa powinna lądować pod biodrem, nie przed nim               |
| **Foot strike**               | kąt pięta vs palce w momencie kontaktu             | Pięta/midfoot/forefoot — bez jednoznacznej „najlepszej" opcji  |
| **Symetria L/P**              | porównanie wszystkich metryk osobno per noga       | Różnica >10% = potencjalny problem                             |

---

## 5. Wartości referencyjne — kiedy wynik jest „dobry"

| Metryka                   | Rekreacyjny | Zaawansowany | Elita     |
| ------------------------- | ----------- | ------------ | --------- |
| Kadencja [spm]            | 150–170     | 170–185      | 180–200   |
| GCT [ms]                  | 250–350     | 200–280      | 150–200   |
| Czas lotu [ms]            | 80–150      | 80–150       | 80–150    |
| Duty factor               | 0.35–0.45   | 0.30–0.40    | 0.22–0.30 |
| Kąt kolana (kontakt) [°]  | 155–175     | 160–175      | 165–175   |
| Pochylenie tułowia [°]    | 5–20        | 5–15         | 5–12      |
| Vertical oscillation [cm] | 8–12        | 6–10         | 6–8       |
| Symetria L/P              | <10%        | <5%          | <3%       |

Źródła: Novacheck 1998, Heiderscheit 2011, Souza 2016, Diaz 2019.

---

## 6. Narzędzia i biblioteki — po co każda

| Narzędzie              | Rola w projekcie                                                                    |
| ---------------------- | ----------------------------------------------------------------------------------- |
| **MediaPipe** (Google) | Wykrywa 33 punktów ciała na każdej klatce wideo — to „oczy" systemu                 |
| **OpenCV**             | Odczyt wideo (klatka po klatce), zapis obrazów, rysowanie wizualizacji              |
| **NumPy**              | Obliczenia numeryczne — kąty, odległości, statystyki                                |
| **Pandas**             | Dane tabelaryczne — CSV z keypointami, operacje na kolumnach                        |
| **SciPy**              | Filtr Savitzky-Golay (wygładzanie), detekcja peaków (`find_peaks`), filtr medianowy |
| **scikit-learn**       | Klasyfikator Random Forest (baseline), metryki (accuracy, F1)                       |
| **PyTorch/TensorFlow** | Klasyfikator LSTM/CNN (model główny) — do ustalenia                                 |
| **Matplotlib**         | Wykresy i wizualizacje do pracy magisterskiej                                       |

---

## 7. Dlaczego pipeline a nie model end-to-end?

Alternatywą byłby jeden model sieci neuronowej: wideo → współczynniki. Nie robimy tego, bo:

1. **Za mało danych** — 9 filmów to za mało do trenowania modelu end-to-end. Pipeline pozwala wykorzystać gotowe narzędzia (MediaPipe) i uczyć tylko klasyfikator faz.

2. **Interpretowalność** — pipeline pozwala zobaczyć co się dzieje na każdym etapie. Jeśli wynik jest zły, wiemy GDZIE jest problem (ekstrakcja? etykiety? obliczenia?).

3. **Rekomendacje oparte na literaturze** — współczynniki obliczamy ze wzorów biomechanicznych, rekomendacje kodujemy z reguł. To nie „czarna skrzynka".

---

## 8. Strategia modelowania — od prostego do zaawansowanego

### Po co w ogóle model?

Auto-etykietowanie (peak detection) działa, ale opiera się na heurystykach dopasowanych do danych treningowych. Na NOWYM wideo od użytkownika nie chcemy odpalać ręcznie tuningowanego algorytmu — chcemy model, który nauczył się rozpoznawać fazy biegu z samych keypointów.

### Model 1: Random Forest (baseline)

- **Wejście:** keypointy z JEDNEJ klatki — wektor ~96 wartości (33 punkty × 3 współrzędne)
- **Wyjście:** etykieta fazy (LEFT_STANCE / RIGHT_STANCE / FLIGHT)
- **Zalety:** trenuje się w sekundy, nie wymaga GPU, łatwy do interpretacji
- **Oczekiwana accuracy:** ~80–90%
- **Słaby punkt:** widzi tylko jedną klatkę — nie wie czy stopa idzie w dół (zaraz stance) czy w górę (odrywa się). Myli się na przejściach między fazami.

### Model 2: LSTM lub 1D CNN (model główny)

- **Wejście:** sekwencja keypointów z okna 15–30 klatek (0.5–1 sekundy). Nie jedna klatka, ale „filmik" pozycji ciała.
- **Wyjście:** etykieta fazy dla środkowej klatki okna
- **Zalety:** widzi kontekst czasowy — kierunek ruchu, prędkość, fazę cyklu. Bieg jest ruchem cyklicznym i sekwencja klatek niesie informację, której pojedyncza klatka nie ma.
- **Oczekiwana accuracy:** ~90–95%, szczególnie poprawa na przejściach faz

### Po co dwa modele?

Porównanie RF vs LSTM odpowiada na konkretne pytanie naukowe: **czy kontekst czasowy ma znaczenie dla klasyfikacji faz biegu?**

- Jeśli RF=85% a LSTM=87% → sekwencja niewiele dodaje, wystarczy prosty model
- Jeśli RF=70% a LSTM=92% → kontekst czasowy jest kluczowy

To nie jest „zróbmy dwa bo możemy" — to metodologia porównawcza.

### Podział danych: per filmik, nie per klatka

Gdybyśmy mieszali klatki z tego samego filmiku między train i test, model „zapamiętałby" konkretnego biegacza (jego sylwetkę, proporcje, tło) zamiast uczyć się faz biegu. Dlatego dzielimy:

- **Train:** np. filmy 01, 02, 03, 08a, 08b, 20 (6 filmów)
- **Validation:** np. film 18 (egzoszkielet — celowo inny od reszty)
- **Test:** np. film 03 lub inny (biegacz, którego model nigdy nie widział)

### Kryteria sukcesu

| Kryterium                                              | Próg sukcesu                   |
| ------------------------------------------------------ | ------------------------------ |
| F1 per klasa na zbiorze testowym                       | > 0.85                         |
| Kadencja z modelu vs z ręcznych etykiet                | ±5%                            |
| Wykrywanie overstriding u celowo overstriding biegacza | tak                            |
| Rekomendacje                                           | sensowne i zgodne z literaturą |

### Trzy niezależne warstwy — nie czarna skrzynka

```
Model      → uczy się TYLKO rozpoznawać fazy (jedyne co trenujemy z danych)
Współczynniki → obliczane ze wzorów biomechanicznych (nie uczone)
Rekomendacje  → reguły z peer-reviewed literatury (nie uczone)
```

Dzięki temu: jeśli model się myli, współczynniki będą błędne, ale rekomendacje nadal opierają się na solidnej literaturze. Każdą warstwę można testować, poprawiać i wymieniać niezależnie.

---

## 9. Słownik pojęć

| Termin                        | Wyjaśnienie                                                           |
| ----------------------------- | --------------------------------------------------------------------- |
| **Keypoint / Landmark**       | Punkt na ciele wykryty przez MediaPipe (np. kolano, pięta)            |
| **Visibility**                | Pewność detekcji punktu (0–1). Niska = punkt zasłonięty lub zgadnięty |
| **Jitter**                    | „Drganie" pozycji punktu między klatkami — szum detekcji              |
| **Savitzky-Golay**            | Filtr wygładzający, który zachowuje kształt sygnału (nie tępi peaków) |
| **Foot strike**               | Moment uderzenia stopy w podłoże — początek fazy stance               |
| **Toe-off**                   | Moment oderwania palców od podłoża — koniec fazy stance               |
| **Stance phase**              | Faza biegu, gdy stopa jest na ziemi (od foot strike do toe-off)       |
| **Flight phase**              | Faza biegu, gdy obie stopy są w powietrzu                             |
| **GCT (Ground Contact Time)** | Czas trwania fazy stance — jak długo stopa dotyka ziemi               |
| **Cadence (kadencja)**        | Liczba kroków na minutę [spm = steps per minute]                      |
| **Stride**                    | Pełny cykl biegu: L_stance → flight → R_stance → flight               |
| **Step**                      | Pół cyklu: od kontaktu jednej stopy do kontaktu drugiej               |
| **Duty factor**               | Stosunek GCT do czasu cyklu. <0.5 = bieg, >0.5 = chód                 |
| **Overstriding**              | Stopa ląduje za daleko przed środkiem ciężkości — hamuje biegacza     |
| **Vertical oscillation**      | Jak bardzo biegacz podskakuje w pionie [cm]                           |
| **Prominence (peaka)**        | „Wyrazistość" peaka — różnica między szczytem a otaczającymi dolinami |
| **Alternacja**                | Naprzemienność kontaktów: L, R, L, R... — wymuszamy ją algorytmicznie |
| **FPS**                       | Klatki na sekundę — kluczowe dla precyzji obliczeń czasowych          |

---

## 10. Potencjalne pytania na prezentacji

**P: Dlaczego MediaPipe a nie np. OpenPose?**
O: MediaPipe jest szybszy (działa w real-time), nie wymaga GPU, ma gotowe API w Pythonie i dokładność wystarczającą dla naszego zastosowania. OpenPose wymaga instalacji CUDA.

**P: Czy system działa w czasie rzeczywistym?**
O: Ekstrakcja keypointów (MediaPipe) tak — ~30 FPS. Pełny pipeline nie — obliczenia wymagają przetworzenia całego wideo.

**P: Jak pewne są wyniki?**
O: Dokładność zależy od jakości wideo. Przy dobrych warunkach (bieżnia, profil, cała sylwetka) visibility keypointów >0.85, a auto-etykietowanie daje kadencję zgodną z oczekiwaniami biomechanicznymi (±5%). Największe źródło błędu: noga dalsza od kamery.

**P: Dlaczego nie uczysz rekomendacji z danych?**
O: Za mało danych do uczenia reguł rekomendacji. Wartości referencyjne pochodzą z peer-reviewed literatury biomechanicznej — to pewniejsze źródło niż model nauczony na 9 filmach.

**P: Co z różnymi kątami kamery?**
O: System wymaga ujęcia z boku. Algorytm automatycznie wykrywa kierunek biegu (lewo/prawo). Inne kąty (z przodu, z tyłu) wymagałyby innego podejścia.

**P: Dlaczego proste progowanie Y nie wystarczyło do etykietowania faz?**
O: Przy 30 FPS faza lotu trwa zaledwie 2–3 klatki. Stały próg nie radzi sobie z różnicami amplitudy między lewą a prawą stopą (artefakt kąta kamery). Przeszliśmy na detekcję peaków (foot strikes) + wymuszoną alternację — to daje czystą sekwencję L→FLIGHT→R→FLIGHT.

**P: Dlaczego Random Forest a nie od razu LSTM?**
O: RF to baseline — punkt odniesienia. Jeśli LSTM daje tylko 2% więcej niż RF, to kontekst czasowy niewiele wnosi i prosty model wystarczy. Jeśli różnica to 15–20%, to dowód że sekwencja klatek jest kluczowa. Porównanie dwóch modeli to element metodologii, nie lenistwo.

**P: Dlaczego dzielisz dane per filmik a nie per klatkę?**
O: Gdybyśmy mieszali klatki z tego samego filmiku między train i test, model mógłby „zapamiętać" konkretnego biegacza (jego sylwetkę, tło, proporcje ciała) zamiast uczyć się rozpoznawać fazy biegu. Podział per filmik wymusza generalizację na niewidzianych biegaczach.

**P: Czy 9 filmów to nie za mało do trenowania?**
O: To mało, ale wystarczająco dla naszego podejścia. Nie trenujemy modelu end-to-end (wideo→współczynniki), tylko klasyfikator faz na keypointach. Każdy filmik to setki–tysiące klatek z etykietami. Przy 6 filmach treningowych mamy ~3000–4000 etykietowanych klatek. Dla Random Forest i prostego LSTM to sensowna ilość.

**P: Co jeśli model się myli?**
O: Błąd modelu (np. 2 klatki stance zaklasyfikowane jako flight) przełoży się na niedokładność GCT rzędu 60–70 ms. Kadencja będzie nadal poprawna (liczy peaki, nie dokładne granice). Rekomendacje opierają się na średnich wartościach, nie pojedynczych klatkach — są odporne na drobne błędy klasyfikacji.

---

1.  Podział danych: train/val/test (per filmik, nie per klatka!)

Mamy 13 filmów z etykietami. Musimy podzielić je na 3 zbiory:

- Train (~70%) — model uczy się na tych danych
- Val (~15%) — model sprawdza się w trakcie trenowania (dobór hiperparametrów, early stopping)
- Test (~15%) — finalna ocena, dotykamy TYLKO RAZ na końcu

Dlaczego per filmik, nie per klatka? Gdybyśmy losowo mieszali klatki, to klatka 100 z filmu 02 mogłaby trafić do train, a klatka 101 do
test. Są prawie identyczne — model "zna" odpowiedź. To wyciek danych (data leakage), daje zawyżone metryki, a model nie generalizuje na
nowe filmiki.

Dzielimy więc całymi filmami. Np.:

- Train: 01, 02, 06, 08×2, 09×2, 15, 19, Running4ms (~9 filmów)
- Val: 03, 20b (~2 filmy)
- Test: 20, 22 (~2 filmy)

Konkretny podział dobierzemy tak, żeby każdy split miał zbliżoną liczbę klatek i różnorodność (slow-mo, normalne, różni biegacze).
Ważne, żeby ten sam biegacz nie był w train i test jednocześnie.

2. Baseline: Random Forest na wektorze keypointów

Najprostszy model — traktuje każdą klatkę niezależnie.

Input: wektor 132 cech z jednej klatki (33 keypointy × 4 wartości: x, y, z, visibility)
Output: jedna z 3 klas (LEFT_STANCE / RIGHT_STANCE / FLIGHT)

Random Forest to zestaw drzew decyzyjnych, które "głosują". Nie wymaga GPU, trenuje się w sekundy, działa out-of-the-box. Daje nam dolną
granicę jakości — jeśli RF osiąga np. 85% accuracy, to wiemy, że samo ułożenie ciała w jednej klatce niesie dużo informacji. LSTM/CNN
powinien być lepszy.

To jest nasz punkt odniesienia — jeśli LSTM nie pobije RF, to coś jest nie tak z architekturą lub danymi.

3. Primary: LSTM lub 1D CNN na sekwencji klatek

Tu wykorzystujemy kontekst czasowy — model widzi nie jedną klatkę, ale np. 15 klatek (okno czasowe).

Input: sekwencja np. 15 klatek × 132 cechy = macierz (15, 132)
Output: klasa dla środkowej klatki w oknie

LSTM (Long Short-Term Memory) — sieć rekurencyjna, przetwarza sekwencję klatka po klatce, pamięta co było wcześniej. Dobra w wyłapywaniu
wzorców typu "stopa idzie w dół → kontakt → stopa idzie w górę".

1D CNN — filtr konwolucyjny przesuwa się po osi czasu, wyłapuje lokalne wzorce (np. nagłą zmianę pozycji stóp w 3-5 klatkach). Szybszy w
trenowaniu niż LSTM.

Przewaga nad RF: model "widzi" ruch, nie tylko pozę. Przejście STANCE→FLIGHT to nie nagły skok — ciało zmienia pozycję stopniowo. Okno
czasowe pozwala to uchwycić.

4. Metryki: accuracy, confusion matrix, F1 per klasa

Samo "accuracy = 90%" nie wystarczy. Musimy wiedzieć gdzie model się myli:

- Accuracy — ogólny % poprawnych klasyfikacji. Dobra ogólna miara, ale u nas klasy są zbalansowane (~33% każda), więc jest wiarygodna.
- Confusion matrix — tabela 3×3 pokazująca co z czym model myli. Np.:

                Predicted:  L_STANCE  R_STANCE  FLIGHT

  Actual L_STANCE: 450 10 40
  Actual R_STANCE: 15 420 15
  Actual FLIGHT: 30 20 400

- Z tego czytamy: "model myli LEFT_STANCE z FLIGHT 40 razy" — to logiczne, bo granica STANCE↔FLIGHT jest rozmyta.
- F1 per klasa — średnia harmoniczna precision i recall, osobno dla każdej klasy. Powie nam czy model jest równomiernie dobry na
  wszystkich fazach, czy np. doskonale rozpoznaje FLIGHT ale myli L_STANCE z R_STANCE.

Najważniejsze pytanie z metryk: czy model myli L_STANCE z R_STANCE (źle rozpoznaje która noga) czy myli STANCE z FLIGHT (źle rozpoznaje
moment kontaktu). Pierwsze jest gorsze — oznacza, że model nie rozróżnia lewej od prawej strony ciała.
