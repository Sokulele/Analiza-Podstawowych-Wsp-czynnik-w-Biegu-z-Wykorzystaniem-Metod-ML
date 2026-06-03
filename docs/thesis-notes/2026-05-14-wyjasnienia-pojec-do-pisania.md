# 2026-05-14 — Wyjaśnienia pojęć i decyzji projektowych do pisania pracy

## Cel notatki

**Rosnący dokument** z wyjaśnieniami pojęć technicznych i decyzji projektowych, które
pojawiają się w trakcie rozmów. Każde wyjaśnienie ma:
- **Definicję / odpowiedź** (zwięzła)
- **Kontekst metodologiczny** (skąd to się wzięło, jak się różni od alternatyw)
- **Cytat-szablon** gotowy do wklejenia do pracy
- **Gdzie w pracy to umieścić** (sugerowany rozdział)
- **Linki do literatury** (jeśli były referencje)

**Konwencja dopisywania**: za każdym razem gdy podczas rozmowy wyjaśnimy jakieś
pojęcie (definicja, decyzja, "czemu tak a nie inaczej"), dopisujemy nową sekcję
poniżej z datą. Notatka pozostaje **jednym plikiem** — nie tworzymy osobnych plików
per pojęcie, bo wszystkie razem są wartościowe jako "encyklopedia metodologii projektu".

---

## [2026-05-14] Monocular 2D wideo

### Definicja

**Monocular** = "jednooczne", czyli nagrane z **jednej kamery** (mono = jeden).
**2D** = obraz pikselowy, każdy punkt ma tylko współrzędne `(x, y)` — **brak głębi** (`z`).
**Wideo** = sekwencja klatek w czasie.

W praktyce: **standardowe nagranie ze smartfona, kamery USB lub GoPro**.

### Kluczowa cecha: brak informacji o głębi

Kamera pikseluje **rzut 3D świata na płaszczyznę 2D**. W tym rzucie giną informacje:
- jak daleko od kamery jest dany punkt (`z`)
- jaka jest faktyczna odległość w metrach (brak *metric scale* bez kalibracji)
- ruchy **prostopadłe do obrazu** (out-of-plane) są ledwo widoczne

Przykład: biegacz biegnący w stronę kamery vs prostopadle do kamery. Z boku widzisz
pełną długość kroku, z przodu — prawie nic.

### Porównanie z innymi technikami

| Technika | Liczba kamer | Wymiar danych | Koszt | Przykład |
|---|---|---|---|---|
| **Monocular 2D** (ta praca) | 1 | 2D `(x, y)` | ~0 zł (smartfon) | nagranie bieżni telefonem |
| **Stereoscopic** | 2 | 2D + estymacja 3D z triangulacji | ~1-5 tys. zł | ZED Camera, dwie kamery USB |
| **RGB-D / depth cameras** | 1 + sensor głębi | 2D + zmierzona `z` | ~2-5 tys. zł | Kinect, Intel RealSense |
| **3D Motion Capture (gold standard)** | 8-12 kamer IR + markery | 3D `(x, y, z)` precyzja mm | 100 tys. zł+ | Vicon, Qualisys (laboratorium) |

### A co z `z` w MediaPipe Pose?

MediaPipe daje 33 keypointy w formacie `(x, y, z, visibility)` — wyglądałoby na 3D.
**Ale**: `z` jest **estymowane** przez sieć neuronową na podstawie kontekstu obrazu,
**nie zmierzone**. To "wnioskowana głębia" — przybliżona, nie wiarygodna do precyzyjnych
obliczeń kątów stawów w 3D. W tej pracy używamy głównie `x` i `y` (płaszczyzna obrazu),
a `z` służy najwyżej do wskaźników typu "która noga jest bliżej kamery".

### Cytat-szablon

> *"Niniejsza praca opiera się na **monocular 2D wideo** — pojedynczym nagraniu wideo
> bez informacji o głębi, dostępnym z każdej standardowej kamery (smartfon, kamera
> USB, GoPro). W odróżnieniu od trójwymiarowych systemów motion capture (Vicon, Qualisys),
> które wymagają laboratorium, markerów i wielu kamer kosztujących setki tysięcy złotych,
> monocular 2D pozwala na analizę biomechaniczną dostępną szerokiej publiczności kosztem
> wyższych ograniczeń metodologicznych (Stenum et al. 2021, Ripic et al. 2023)."*

### Gdzie w pracy

- **Rozdział 1.1 Motywacja** — pozycjonowanie pracy (NIE laboratoryjna, dostępna każdemu)
- **Rozdział 3.2 Pipeline** — wyjaśnienie konwencji danych wejściowych
- **Rozdział 7 Wrażliwość** — uzasadnienie limitations (out-of-plane, perspective)
- **Rozdział 8.3 Limitations** — uczciwe omówienie ograniczeń metody

### Linki

- Stenum et al. 2021, PLOS Comp Bio: [journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1008935](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1008935)
- Ripic et al. 2023, Front Rehab Sci: [frontiersin.org/journals/rehabilitation-sciences/articles/10.3389/fresc.2023.1238134](https://www.frontiersin.org/journals/rehabilitation-sciences/articles/10.3389/fresc.2023.1238134/full)

---

## [2026-05-14] Dlaczego MediaPipe Pose ma akurat 33 keypointy

### Skład 33 keypointów

| Grupa | Liczba | Co konkretnie |
|---|---|---|
| **Twarz** | 11 | NOSE (środek) + 6 punktów oczu (3 L + 3 R: inner/middle/outer) + 2 uszy + 2 usta (mouth_left, mouth_right) |
| **Tułów** | 6 | 2 ramiona + 2 łokcie + 2 nadgarstki |
| **Dłonie** | 6 | 2× (pinky + index + thumb) |
| **Miednica** | 2 | 2 biodra |
| **Nogi** | 8 | 2 kolana + 2 kostki + 2 pięty + 2 czubki stopy (foot_index) |
| **RAZEM** | **33** | 1 środkowy (NOSE) + 16 par symetrycznych L/P |

### Dlaczego nieparzyste 33, nie 34

**Wszystkie punkty są symetryczne L/P z jednym wyjątkiem — NOSE (indeks 0)**.
Stąd `33 = 1 + 2×16`.

34. punkt musiałby być **kolejnym środkowym** (np. mid-shoulder, mid-hip, crown-of-head).
**Takie punkty można policzyć** ze średniej dwóch sąsiednich:
```
mid_hip = (LEFT_HIP + RIGHT_HIP) / 2
mid_shoulder = (LEFT_SHOULDER + RIGHT_SHOULDER) / 2
```

Dodawanie ich jako osobnych output landmarks **nie daje nowej informacji**,
tylko zwiększa rozmiar modelu i koszt obliczeniowy. NOSE z kolei **NIE da się
policzyć** ze średniej innych punktów — to anatomicznie unikalny landmark.

### Historia: ewolucja standardów keypointów

| Standard | Liczba | Co dodaje vs poprzedni |
|---|---|---|
| **COCO** (2014, benchmark referencyjny) | 17 | NOSE + 2 oczu + 2 uszu + 4 tułów + 4 dłonie + 2 biodra + 2 kolana + 2 kostki |
| **OpenPose BODY_25** (2018) | 25 | + mid-hip, neck, 6 punktów stopy (heel, big_toe, small_toe × 2) |
| **MediaPipe BlazePose** (2020) | **33** | + szczegóły twarzy (eye_inner/outer), dłonie (pinky/index/thumb × 2), `foot_index` zamiast big/small_toe |
| **DensePose / SMPL** (mesh-based) | 6890 vertices | całe mesh ciała |

### Argumenty projektowe MediaPipe (BlazePose paper, Bazarevsky 2020)

- **Dłonie** (kciuki, pinky, index) — BlazePose miał obsługiwać aplikacje fitness/yoga
  gdzie liczy się "dotknij stopy ręką"
- **Stopy** (heel + foot_index) — biomechanika, foot strike pattern (kluczowe dla tej pracy)
- **Twarz** szczegółowo — BlazePose dzieli model z BlazeFace, "dziedziczy" detale twarzy
- **Niewydatne dla biegu**: dłonie i twarz są nadmiarowe (rękawiczki, czapka mogą maskować),
  ale są w modelu, bo Google chciał uniwersalności

### Co to znaczy dla tej pracy

Z 33 keypointów **realnie używane jest 13** (z `docs/mediapipe-keypoints.md`):
NOSE + 2 ramiona + 2 biodra + 2 kolana + 2 kostki + 2 pięty + 2 foot_index.
Pozostałe 20 (twarz, dłonie, łokcie, nadgarstki) są **policzone, ale zignorowane** —
nie wnoszą informacji do analizy biegu.

**Kluczowe**: foot strike pattern w tej pracy opiera się na wektorze
HEEL → FOOT_INDEX (`atan2(-dy, dx)`). To **konkretne uzasadnienie** wyboru MediaPipe
nad OpenPose BODY_25 (który ma `big_toe`, `small_toe`, ale nie rozróżnia ich
od `foot_index`).

### Cytat-szablon

> *"MediaPipe Pose (Bazarevsky et al. 2020) wykrywa **33 keypointy** w każdej klatce
> wideo: 1 punkt środkowy (nos) oraz 16 par punktów symetrycznych L/P obejmujących
> twarz, tułów, kończyny górne (z dłońmi), miednicę i kończyny dolne (z piętami i
> czubkami stóp). Liczba 33 jest rozszerzeniem standardu COCO (17 keypointów) i OpenPose
> BODY_25 (25 keypointów) — w stosunku do nich BlazePose dodaje szczegóły dłoni
> (kluczowe dla aplikacji fitness) oraz osobne punkty pięty (`HEEL`) i czubka stopy
> (`FOOT_INDEX`) per noga (kluczowe dla biomechaniki biegu, w szczególności detekcji
> wzorca lądowania foot strike). W niniejszej pracy z 33 keypointów wykorzystywane
> jest realnie 13 — pozostałe (twarz, dłonie, łokcie, nadgarstki) nie wnoszą
> informacji do analizy faz biegu i parametrów temporalnych."*

### Gdzie w pracy

- **Rozdział 3.2 Pipeline** — opis ekstrakcji keypointów MediaPipe
- **Rozdział 3.3 Architektury klasyfikatorów** — uzasadnienie wyboru MediaPipe vs OpenPose
- **Rozdział 5.2 Współczynniki przestrzenne** — sekcja o foot strike pattern, gdzie
  HEEL + FOOT_INDEX są krytyczne

### Linki

- BlazePose paper: Bazarevsky et al. 2020, *"BlazePose: On-device Real-time Body
  Pose Tracking"*, arXiv:2006.10204 — [arxiv.org/abs/2006.10204](https://arxiv.org/abs/2006.10204)
- COCO dataset: Lin et al. 2014, *"Microsoft COCO: Common Objects in Context"*
- OpenPose BODY_25: Cao et al. 2018, *"OpenPose: Realtime Multi-Person 2D Pose
  Estimation using Part Affinity Fields"*
- Diagram 33 keypointów MediaPipe: [google.github.io/mediapipe/solutions/pose](https://google.github.io/mediapipe/solutions/pose.html)
  (legacy docs, od 2024 Google przeniósł na MediaPipe Tasks API)

---

## Sekcje do uzupełnienia w przyszłych rozmowach

Lista pojęć, które prawdopodobnie wymagają wyjaśnienia podczas pisania pracy
(uzupełnimy je gdy wyjdą w rozmowach):

- [ ] **Savitzky-Golay filter** — dlaczego window=11, polyorder=3, jak działa
- [ ] **LSTM vs BiLSTM vs GRU** — wybór architektury, czemu LSTM r1 a nie inne
- [ ] **Aspect ratio fix** — co dokładnie robi, czemu działa, ablation
- [ ] **Symmetry Index (SI) Robinson 1987** — wzór, interpretacja progów
- [ ] **Peak-based labeling** (auto_label.py) — czemu peak detection a nie progowanie Y
- [ ] **Foot strike pattern angle** — konwencja kąta heel→foot_index, atan2(-dy, dx)
- [ ] **MediaPipe model_complexity=2** — co to zmienia, czemu nie 1 lub 0
- [ ] **Severity (critical/warning/watch/info)** — uzasadnienie 4-poziomowej skali
- [ ] **Reguły łączone (combinatorical)** — czemu AND, nie OR; czemu te konkretne progi
- [ ] **Wybór 16 filmów** — czemu nie więcej, czemu te konkretne, kryteria inkluzji
- [ ] **Splity train/val/test** — strategia (per-biegacz vs per-film), dlaczego ta a nie inna
- [ ] **Reference values** (`docs/reference-values.md`) — skąd pochodzą, jak kalibrowane
- [ ] **MediaPipe Y-down** — konwencja osi vs intuicja matematyczna (Y-up)
- [ ] **Visibility threshold** — czemu 0.5, jak wykorzystany w pipeline

Każdy z tych punktów warto rozwinąć **gdy temat się pojawi**, nie wcześniej —
inaczej zaśmiecamy notatkę pojęciami które mogą nie być potrzebne.



Wyjaśniam punkt po punkcie.

## Random Forest vs LSTM — czym się różnią

**Random Forest na pojedynczych klatkach:**
Model dostaje jedną klatkę (132 liczby opisujące pozycję ciała w tym momencie) i mówi "to jest LEFT_STANCE". Nie wie co było klatka wcześniej ani co będzie klatka później. Jak zdjęcie — patrzysz na fotografię biegacza i zgadujesz w jakiej jest fazie.

**Dwukierunkowa sieć LSTM na sekwencji klatek:**
Model dostaje okno 15 klatek (7 przed + aktualna + 7 po) i klasyfikuje środkową. Widzi ruch — wie że noga szła w dół i zaraz pójdzie w górę. Jak filmik zamiast zdjęcia. "Dwukierunkowa" znaczy że czyta sekwencję od przodu do tyłu i od tyłu do przodu jednocześnie.

## 4 warianty klasyfikatorów — czym się różnią

1. **RF baseline (RF v1)** — Random Forest na surowych danych z MediaPipe (132 cechy: pozycje x,y,z + visibility dla 33 punktów ciała). Najprostszy możliwy model.

2. **RF z inżynierią cech (RF v2)** — Random Forest, ale zamiast surowych pozycji dostaje przetworzone cechy: kąty stawów, znormalizowane pozycje względem tułowia (106 cech). Lepszy input → lepszy wynik.

3. **LSTM run 1 (h=128)** — duży LSTM, szybko się uczył (lr=1e-3), ale szybko zaczął się "przeuczać" (zapamiętywać dane zamiast generalizować). Po korekcji aspect ratio dał najlepszy wynik 70.9%.

4. **LSTM run 2 (h=64)** — mniejszy LSTM, wolniej się uczył (lr=3e-4), bardziej stabilny trening. Dał 68.2% po korekcji aspect ratio.

Każdy kolejny wariant buduje na doświadczeniach z poprzedniego — to nie losowe eksperymenty, tylko systematyczna progresja.

## "Niewidziani biegacze" — o co chodzi

Model trenowałeś na biegaczach A, B, C, D, E. Potem testujesz go na biegaczu F, którego **nigdy nie widział** podczas trenowania. To odpowiada realnemu scenariuszowi — Twój system ma działać na nowym użytkowniku, nie na kimś z datasetu treningowego.

Gdybyś testował na tych samych biegaczach na których trenowałeś, model mógłby mieć 95% — ale to byłoby oszustwo. Zapamiętałby "jak biegacz A wygląda", zamiast nauczyć się "jak wygląda faza lotu".

70.9% na niewidzianych biegaczach to uczciwa metryka — mówi wprost jak system poradzi sobie z kimś nowym.

## Walidacja wrażliwości — co to jest

Sprawdzenie: **czy wyniki systemu zmieniają się w zależności od tego JAK nagrasz wideo**, a nie od tego jak ktoś biega. Konkretnie zbadałeś:

- **Orientacja kamery** — filmik nagrany pionowo (telefonem trzymanym pionowo) daje dramatycznie gorsze wyniki foot strike pattern (4% wykrywalności fazy lotu vs 86% na filmie landscape)
- **Perspektywa** — kamera z dołu (jak u Adama) zaburza kąty stopy lewej nogi bardziej niż prawej
- **Korekcja aspect ratio** — po dodaniu normalizacji proporcji kadru accuracy skoczyła z 67% na 71%

To ważne bo mówi użytkownikowi: "nagraj z boku, poziomo, na wysokości bieżni — inaczej wyniki będą niepewne".

## Rekomendacje — skąd się biorą i czy są takie same dla każdego

**Nie, każdy użytkownik dostaje inne rekomendacje** — zależne od jego wyników. Działa to tak:

System oblicza współczynniki danego biegacza (np. kadencja 155 spm, GCT 310 ms), a potem porównuje je z **wartościami referencyjnymi z literatury naukowej** (Novacheck 1998, Heiderscheit 2011, Souza 2016, Diaz 2019). Reguły mają postać:

- Kadencja < 160 spm → "Kadencja poniżej zalecanego zakresu. Zwiększenie kadencji do 170–180 kroków/min zmniejsza obciążenie stawów (Heiderscheit 2011)"
- GCT > 300 ms → "Długi czas kontaktu z podłożem. Typowy zakres to 200–280 ms przy biegu rekreacyjnym"
- Kąt kolana przy lądowaniu > 175° → "Zbyt wyprostowane kolano przy kontakcie — ryzyko overstriding"

**Reguły są stałe** (zakodowane w kodzie z cytatami z literatury), ale **wyniki i rekomendacje są indywidualne** — zależą od tego co model zmierzy u danego biegacza. Ktoś z kadencją 180 spm nie dostanie ostrzeżenia o niskiej kadencji, a ktoś z 150 spm — tak.

## Odpowiedzi na 3 pytania badawcze

**P1 (czy da się zbudować taki system):** Tak, system działa end-to-end. Z jednego nagrania wideo oblicza 12 współczynników i generuje rekomendacje. Ograniczenie: wymaga ujęcia z boku w formacie landscape, stride length wymaga ręcznego podania prędkości bieżni.

**P2 (który klasyfikator lepszy):** LSTM jest lepszy od Random Forest o ~4–9 pp w zależności od wariantu. Kontekst czasowy (sekwencja klatek) pomaga, szczególnie w rozróżnianiu fazy lotu od fazy oparcia. Ale RF z inżynierią cech daje zaskakująco bliskie wyniki — różnica nie jest przepaść.

**P3 (wrażliwość na warunki nagrania):** Foot strike pattern i symetria L/R są najbardziej wrażliwe na perspektywę kamery. Kadencja i czas cyklu są odporne. System automatycznie wykrywa przypadki niskiej wiarygodności (gdy kąt stopy > 45° lub kombinacja niskiej pewności modelu + wysokiej asymetrii).

---

## [Korekta po weryfikacji 2026-05-14] Uściślenia do wklejki powyżej

Wklejka powyżej została zwalidowana przeciwko kodowi (`train_lstm.py`, `splits.json`)
i artefaktom porównawczym (`comparison_summary.json`, `per_file_test.md`,
`error_breakdown.md`). **Większość zgadza się** (BiLSTM, okno 15 klatek, 132 cech RF v1,
106 cech RF v2, overfit w LSTM run 1, 4 warianty modeli, reguły indywidualne z literatury).
Trzy punkty wymagają uściślenia przed wstawieniem do pracy:

### Korekta 1 — "Niewidziani biegacze"

**Wklejka mówi**: *"Model trenowałeś na biegaczach A, B, C, D, E. Potem testujesz go
na biegaczu F, którego nigdy nie widział podczas trenowania."*

**Stan faktyczny** (z `splits.json`): splity są **per-film, NIE per-biegacz**:
- **09 Sage Canaday segment_1 w train, segment_2 w val** → ten sam biegacz w obu zbiorach,
  czyli **data leakage w walidacji** (drobne, ale formalnie istniejące)
- Test: filmy 02 (Running at 13km/h), 20 (walk→run), 22 (Physiotherapist) — to wideo
  z YouTube, **prawdopodobnie** różni biegacze niż w train (Pawel, Adam), ale
  **bez formalnej weryfikacji per-biegacz**

**Propozycja przeformułowania** (uczciwsza dla pracy):

> *Splity (train/val/test) zostały wykonane **per-film**, nie per-biegacz. Test set
> zawiera 3 filmy z YouTube (02, 20, 22) — prawdopodobnie różnych biegaczy niż
> w zbiorze treningowym, choć formalna weryfikacja per-biegacz wymagałaby ręcznej
> identyfikacji każdej osoby na nagraniu. Wyjątkiem od separacji jest Sage Canaday
> (film 09), którego segmenty znalazły się zarówno w train, jak i w val — wynik
> wykorzystania długich nagrań wysokiej jakości w treningu, co należy uznać za
> drobne ograniczenie metodologiczne i wzmiankować w sekcji Limitations.*

**Gdzie w pracy**: rozdział 3.5 (Splity) + 8.3 (Limitations).

### Korekta 2 — Liczby 70.9% / 68.2% są PO aspect ratio fix

**Wklejka mówi**: *"LSTM run 1 ... Po korekcji aspect ratio dał najlepszy wynik 70.9%"*
oraz *"LSTM run 2 ... Dał 68.2% po korekcji aspect ratio."*

**To jest poprawne**, ale wymaga uściślenia źródła. W projekcie istnieją **dwa zestawy
wyników**:

| Model | PRZED aspect fix (`comparison_summary.json`) | PO aspect fix (brief Sesji C, primary model) |
|---|---|---|
| RF v1 (raw) | 62.7% | nie był re-trenowany (aspect fix tylko dla LSTM) |
| RF v2 (engineered) | 67.0% | nie był re-trenowany |
| LSTM run 1 (h=128, overfit) | 67.1% | **70.9%** ← primary model |
| LSTM run 2 (primary, mniejszy) | 65.3% | ≈68% (zgodne ze wklejką 68.2%) |

**Konsekwencja dla pracy**: w rozdz. 4 (Klasyfikator) trzeba **wyraźnie odróżniać**
dwie tabele:
- Tabela "porównanie 4 modeli" → **przed aspect fix** (uczciwie pokazuje baseline)
- Tabela "ablation aspect ratio fix" → **przed/po fix** tylko dla LSTM (różnica +3.8 pp
  dla r1, +~3 pp dla r2)

To dobrze, bo wprowadza **dwa rozdziały badawcze** zamiast jednego: porównanie modeli
**i osobno** ablation pre-processingu.

**Gdzie w pracy**: rozdział 4.1-4.3 (porównanie 4 modeli, przed fix) + 4.4 (ablation
aspect fix, przed/po).

### Korekta 3 — "4% wykrywalności fazy lotu vs 86% na filmie landscape" — usunąć

**Wklejka mówi**: *"filmik nagrany pionowo daje dramatycznie gorsze wyniki foot strike
pattern (4% wykrywalności fazy lotu vs 86% na filmie landscape)"*.

**Źródło**: user wskazał że to liczby z **Claude.ai webowego** (przeglądarka), bez
podstawy w artefaktach projektu.

**Stan faktyczny**:
- W `per_file_test.md`, `error_breakdown.md`, `comparison_summary.json` **nie ma**
  metryki "wykrywalność fazy lotu" per-film
- Film 22 (pionowy) ma accuracy klasyfikatora: 75.8% (przed fix) → 85.9% (po fix) —
  **86% pasuje jako zaokrąglenie** do drugiej liczby
- **4%** nie znajduje się w żadnym z istniejących artefaktów

**To prawdopodobnie halucynacja Claude.ai webowego** — model nie miał dostępu do
artefaktów projektu i wygenerował konkretne liczby na podstawie domysłu.

**Propozycja przeformułowania** (bez konkretnej liczby 4%):

> *Film nagrany pionowo (Physiotherapist demo, film 22) ma niższą accuracy klasyfikatora
> niż filmy poziome — przed normalizacją aspect ratio różnica wynosi około 10 pp
> w stosunku do filmów landscape, po aspect ratio fix film 22 osiąga **85.9%** accuracy
> klasyfikatora (LSTM run 1). Ponadto **foot strike pattern** dla pionowego wideo
> jest **całkowicie nieinterpretowalny** geometrycznie (`|kąt| > 90°`), niezależnie
> od accuracy klasyfikatora — to osobny problem walidowany w Sesji C (rozdział 7).*

**Gdzie w pracy**: rozdział 4.4 (ablation aspect fix) + rozdział 7 (wrażliwość na
warunki akwizycji).

### Ogólna uwaga metodologiczna (dla pracy)

**Liczby otrzymane od Claude.ai webowego BEZ DOSTĘPU DO ARTEFAKTÓW PROJEKTU należy
traktować jako halucynacje, dopóki nie są zweryfikowane przeciwko kodowi/danym.**
W trakcie pisania pracy:
- każda konkretna liczba (accuracy, F1, MAE, %) musi mieć **konkretne źródło** w `data/inference/`,
  `docs/thesis-notes/figures/` lub log treningowy
- jeśli liczba nie ma źródła — usunąć lub zastąpić ostrożnym sformułowaniem ("około",
  "rzędu", bez konkretnej wartości)
- dobre praktyki: **cytuj artefakt** przy konkretnej liczbie, np. *"...accuracy 70.9%
  (LSTM run 1 + aspect fix, źródło: model `models/lstm_run1_overfit/metrics.json`)"*

---

## [2026-05-23] Pojęcia z rozdziału 3 — sesja pisania

### Estymowana głębia z (MediaPipe)

MediaPipe podaje dla każdego keypointu wartość `z` — przybliżoną głębię (odległość od kamery) **względem punktu centralnego bioder**. To NIE jest pomiar czujnikiem głębi (jak Kinect czy Intel RealSense). Sieć neuronowa wnioskuje `z` z wskazówek wizualnych:
- **Relatywne rozmiary kończyn** — bliższe części ciała wyglądają większe na obrazie
- **Efekty perspektywy** — kończyna skierowana ku kamerze ulega skróceniu (foreshortening)
- **Wzorce zasłonięć** — jeśli jedno ramię zasłania drugie, to jest bliżej kamery
- **Wyuczone proporcje anatomiczne** — sieć wie jakie powinny być proporcje ciała

Sieć trenowana jest na zbiorach z adnotacjami 2D (zdjęcia z ręcznymi keypointami) **i** danymi 3D z motion capture (Vicon/Qualisys). Dlatego potrafi "domyślić się" głębi, choć widzi tylko 2D obraz.

**W tej pracy:** korzystam głównie z `x` i `y`. Wartość `z` jest za mało wiarygodna do precyzyjnych obliczeń kątów stawów w 3D.

### Visibility (wskaźnik pewności detekcji)

`visibility ∈ [0, 1]` — prawdopodobieństwo, że dany keypoint jest **widoczny w kadrze i nie jest zasłonięty** przez inne części ciała. Sieć neuronowa ocenia:
- Czy okolica keypointu jest przesłonięta przez inne kończyny
- Czy keypoint wykracza poza kadr (obcięty przez krawędź obrazu)
- Czy cechy wizualne w otoczeniu keypointu są spójne z oczekiwaną pozą

Wartość generowana jest przez **warstwę sigmoidalną** na wyjściu modelu — sigmoid zamienia dowolną liczbę na zakres (0, 1), interpretowany jako prawdopodobieństwo.

**Przydatne:** visibility < 0.5 na kluczowych keypointach → materiał może być kiepski do analizy. Używam tego jako flaga jakości.

### Inferencja (inference)

**Inferencja** = uruchomienie wytrenowanego modelu na nowych danych w celu uzyskania predykcji. W odróżnieniu od **treningu** (uczenia modelu na danych treningowych), inferencja to "produkcyjne" użycie modelu.

Przykład: MediaPipe Pose uruchamiam na klatkach wideo → model wykonuje inferencję → wynik to 33 keypointów na każdą klatkę. Sam model jest już wytrenowany przez Google — ja tylko go używam.

W kontekście mojego klasyfikatora faz: trening = uczę model na 10 filmach, inferencja = puszczam wytrenowany model na nowym filmiku użytkownika.

### Jitter (szum w trajektoriach keypointów)

Keypoint (np. kolano) powinien poruszać się gładko z klatki na klatkę, bo ciało nie teleportuje się. Ale MediaPipe przetwarza każdą klatkę w dużej mierze niezależnie — predykcja sieci neuronowej nigdy nie jest identyczna. Dlatego pozycja keypointu **oscyluje o kilka pikseli** nawet gdy biegacz utrzymuje stałą pozę.

To **szum / jitter** — szybkie, losowe fluktuacje sygnału. Nie odzwierciedlają rzeczywistego ruchu ciała — to artefakt detekcji.

**Problem:** gdybym obliczał kąty stawów czy czas kontaktu na zaszumionych danych, wyniki byłyby przekłamane. Dlatego PRZED obliczeniami wygładzam sygnał.

### Filtr Savitzky-Golay — jak działa

Krok po kroku:
1. Weź **okno** 11 kolejnych klatek (np. klatki 5–15)
2. Do tych 11 punktów **dopasuj wielomian** 3. stopnia metodą najmniejszych kwadratów
3. Wygładzona wartość to **wartość wielomianu w środkowym punkcie** okna (klatka 10)
4. **Przesuń okno** o jedną klatkę (teraz klatki 6–16) i powtórz

**Dwa parametry:**
- **Długość okna w = 11** — ile klatek bierze pod uwagę. Większe okno = silniejsze wygładzenie, ale ryzyko rozmycia szybkich ruchów. Przy 30 FPS okno 11 klatek ≈ 0.37 sekundy.
- **Rząd wielomianu p = 3** — stopień wielomianu. Wielomian 3. stopnia potrafi odwzorować krzywiznę (szczyty i doliny). Prosta średnia ruchoma = wielomian stopnia 0 → spłaszcza ekstrema. To ważne, bo momenty kontaktu stopy z podłożem to właśnie szczyty/doliny w sygnale.

**Czemu nie prosta średnia ruchoma?** Średnia ruchoma obcina szczyty sygnału — jeśli pięta uderza o ziemię (ostry szczyt w trajektorii Y_heel), średnia ruchoma "spłaszczy" ten moment i zafałszuje czas kontaktu. Savitzky-Golay zachowuje kształt szczytu, bo wielomian 3. stopnia potrafi go odwzorować.

### Sygnał kinematyczny

**Kinematyka** = opis ruchu ciała w przestrzeni i czasie (pozycja, prędkość, przyspieszenie). **Sygnał kinematyczny** to ciąg wartości opisujących taki ruch — np. współrzędna Y kolana z klatki na klatkę.

Współrzędne `x, y, z` keypointów to sygnały kinematyczne — opisują fizyczny ruch.
Wartość `visibility` to **NIE** sygnał kinematyczny — to miara pewności algorytmu detekcji, nie ruch ciała. Dlatego visibility nie wygładzam.

### Interpolacja liniowa (uzupełnianie braków)

Jeśli MediaPipe nie wykrył pozy w klatkach 50–52, ale wykrył w klatce 49 (kolano na pozycji Y=0.65) i w klatce 53 (kolano na Y=0.73):

```
Klatka:  49   50    51    52    53
Surowe:  0.65  NaN   NaN   NaN  0.73
Po interp: 0.65  0.67  0.69  0.71  0.73
```

Rysuje **prostą linię** między ostatnią znaną a następną znaną wartością i rozkłada brakujące punkty równomiernie na tej linii. To proste przybliżenie — zakłada liniowy ruch w krótkim oknie brakujących danych.

Konieczne, bo filtr Savitzky-Golay wymaga ciągłego sygnału (bez NaN).

### Metryka jittera — jak mierzyłem skuteczność wygładzania

**Jitter** = odchylenie standardowe drugiej różnicy sygnału.

**Druga różnica** ciągu x₀, x₁, ..., xₙ to:
```
d²ᵢ = xᵢ₊₂ - 2·xᵢ₊₁ + xᵢ
```

To **przybliżenie przyspieszenia** sygnału (jak pochodna drugiego rzędu).

**Interpretacja:**
- Gładka trajektoria → przyspieszenie zmienia się wolno → std(d²) mała
- Zaszumiona trajektoria → przyspieszenie skacze losowo → std(d²) duża

**Redukcja procentowa:**
```
redukcja = (jitter_raw - jitter_smooth) / jitter_raw × 100%
```

Jeśli jitter_raw = 0.005 a jitter_smooth = 0.001, to redukcja = 80% — filtr usunął 80% szumu.

Metryke obliczam na współrzędnych x i y **12 kluczowych keypointów** (ramiona, biodra, kolana, kostki, pięty, czubki stóp) — te są najważniejsze dla biomechaniki biegu.

**Źródło:** miara stosowana w literaturze dot. filtracji sygnałów biomechanicznych (Crenna et al. 2021, "Filtering Biomechanical Signals in Movement Analysis").

### Standard COCO (Common Objects in Context)

COCO to duży benchmark (zbiór danych + format adnotacji) stworzony przez Microsoft w 2014 roku (Lin et al.). Definiuje m.in. **17 keypointów ciała** jako standard: nos, 2 oczy, 2 uszy, 2 ramiona, 2 łokcie, 2 nadgarstki, 2 biodra, 2 kolana, 2 kostki.

Większość modeli detekcji pozy jest trenowana na zbiorze COCO — dlatego 17 keypointów stało się "standardem". OpenPose rozszerzył go do 25 (dodając szyję, środek bioder, i 6 punktów stóp). MediaPipe do 33 (dodając dłonie, szczegóły twarzy, i foot_index).

**W mojej pracy:** COCO (17 keypointów) nie wystarczał — nie ma żadnych keypointów stopy poniżej kostki, a do foot strike pattern potrzebuję pięty i czubka stopy.

### Maksima i minima przy kontakcie stopy — skąd się biorą

W MediaPipe oś Y rośnie w dół (0 = góra kadru, 1 = dół kadru). Kiedy pięta uderza o bieżnię, keypoint HEEL osiąga **maksimum Y** — jest najniżej w kadrze. Kiedy stopa odrywa się od ziemi, Y_heel **spada**. W fazie lotu stopa jest najwyżej → **minimum Y**. Potem znowu ląduje → kolejne maximum.

Trajektoria Y_heel wygląda jak fala: szczyt (lądowanie) → dolina (lot) → szczyt (lądowanie). Algorytm auto-etykietowania (`find_peaks` z SciPy) wykrywa te szczyty i na tej podstawie oznacza fazy biegu. Filtr Savitzky-Golay musi zachowywać te szczyty/doliny — gdyby je spłaszczył, algorytm etykietowania źle by oznaczył momenty kontaktu.

### Prosta średnia ruchoma — jak działa i czemu nie wystarcza

Weź okno N kolejnych wartości, oblicz ich średnią arytmetyczną — to wygładzona wartość dla środkowego punktu. Przesuń okno o 1 i powtórz.

Przykład (okno = 5):
```
Surowe:      3, 7, 4, 8, 5, 9, 6
Okno [3,7,4,8,5] → średnia = 5.4 (wygładzona wartość dla "4")
Okno [7,4,8,5,9] → średnia = 6.6 (wygładzona wartość dla "8")
```

**Problem:** ostry szczyt (pięta uderza o bieżnię → Y skacze do 0.95 na jedną klatkę) zostaje "rozmyty" — uśredniony z sąsiadami, więc w wygładzonym sygnale szczyt jest niższy i szerszy. To przekłamuje moment kontaktu. Savitzky-Golay dopasowuje wielomian, który potrafi śledzić kształt szczytu.

Matematycznie: średnia ruchoma = Savitzky-Golay z wielomianem stopnia 0 (stała). Wielomian stopnia 3 potrafi odwzorować krzywą z jednym szczytem/doliną w obrębie okna.

### Wygładzanie oddzielnie dla x, y, z i każdego keypointu

Każdy keypoint (np. LEFT_KNEE) ma 3 współrzędne zmieniające się w czasie — 3 osobne ciągi liczbowe:
- `LEFT_KNEE_x`: [0.45, 0.46, 0.44, 0.47, ...] — pozycja pozioma
- `LEFT_KNEE_y`: [0.62, 0.63, 0.61, 0.64, ...] — pozycja pionowa
- `LEFT_KNEE_z`: [-0.12, -0.11, -0.13, ...] — głębia

Każdy ciąg wygładzam **osobno** — filtr przechodzi po ciągu x, potem po y, potem po z. Nie mieszam ich, bo ruch poziomy nie ma nic wspólnego z ruchem pionowym. Tak samo nie mieszam keypointów — trajektoria kolana to osobny sygnał niż trajektoria kostki.

33 keypointy × 3 współrzędne = **99 osobnych operacji wygładzania**.

Visibility (4. wartość) NIE jest wygładzany — to pewność detekcji, nie ruch ciała.

### Interpolacja liniowa — szczegółowo ze wzorem

Jeśli w klatce 49 kolano jest na Y=0.65, a w klatce 53 na Y=0.73, i klatki 50-52 nie mają danych:

```
Różnica wartości: 0.73 - 0.65 = 0.08
Różnica klatek:   53 - 49 = 4
Krok na klatkę:   0.08 / 4 = 0.02

Klatka 49: 0.65 (znana)
Klatka 50: 0.65 + 1×0.02 = 0.67
Klatka 51: 0.65 + 2×0.02 = 0.69
Klatka 52: 0.65 + 3×0.02 = 0.71
Klatka 53: 0.73 (znana)
```

**Wzór ogólny:** dla brakującej klatki k między znaną a i znaną b:

`x_k = x_a + (k - a) / (b - a) × (x_b - x_a)`

Zakłada liniowy ruch w brakujących klatkach. Przy 1-3 brakujących klatkach z rzędu (co zdarza się najczęściej) jest wystarczająco dokładne — ciało nie zmienia gwałtownie kierunku w 0.1 sekundy.

### Auto-etykietowanie faz biegu (peak-based)

**Problem:** mam ~12 000 klatek wideo i potrzebuję dla każdej etykiety: LEFT_STANCE, RIGHT_STANCE albo FLIGHT. Ręczne etykietowanie to setki godzin, więc opracowałem algorytm automatyczny.

**Dlaczego nie proste progowanie Y pięty?**
Pierwsze podejście: jeśli pięta jest nisko (y > próg) → STANCE, inaczej → FLIGHT. Nie zadziałało bo:
- Faza lotu trwa 2-3 klatki przy 30 FPS — łatwo ją przegapić lub zaklasyfikować błędnie
- Kamera boczna powoduje asymetrię L/R: stopa bliższa kamery ma inną wartość y niż dalsza
- Próg 0.02 dawał >70% FLIGHT (za ciasny), a luźniejszy nie łapał krótkich lotów

**Algorytm peak-based — krok po kroku:**

1. **Sygnał kontaktu:** Dla każdej stopy biorę `max(heel_y, foot_index_y)`. Maximum dlatego, że heel strike = pięta nisko (heel_y duże), a toe-off = palce nisko (foot_index_y duże). Maximum "łączy" oba momenty w jeden ciągły sygnał kontaktu.

2. **Detekcja foot strikes:** Szukam lokalnych maksimów (peaków) w sygnale kontaktu za pomocą `scipy.signal.find_peaks()`. Peak = moment gdy stopa jest najniżej = uderzenie o podłoże. Dwa parametry:
   - `distance` = min. odległość między peakami (12 klatek przy 30 FPS, wynika z max kadencji 150 kontaktów/min jednej stopy)
   - `prominence` = 0.03 (jak bardzo peak wystaje nad otoczenie; odrzuca szum, zachowuje prawdziwe kontakty)

3. **Alternacja L-R:** W prawidłowym biegu stopy lądują naprzemiennie. Jeśli algorytm wykryje dwa peaki lewej stopy z rzędu (L-L), zachowuję ten z wyższą prominencją. Wynik: ścisła sekwencja L-R-L-R.

4. **Podział STANCE/FLIGHT:** Region wokół każdego peaku dzielę na strefę centralną (STANCE) i marginesy brzegowe (FLIGHT). Parametr `flight_fraction = 0.4` oznacza, że ~40% klatek między kontaktami to FLIGHT. Margines `m = max(1, floor(długość_regionu × 0.4 / 2))`.

5. **Kierunek biegu:** Porównuję średnią pozycję X nosa ze średnią X bioder. Jeśli nos jest na lewo od bioder → biegacz biegnie w lewo → zamieniam LEFT↔RIGHT, żeby etykiety były anatomicznie poprawne.

6. **Filtr medianowy (kernel=3):** Na koniec filtruję sekwencję etykiet — eliminuje pojedyncze klatki z błędną etykietą. W praktyce zmienia niemal zero klatek, bo peak-based jest już czysty.

**Gdzie w pracy:** Sekcja 3.3 (Materiały i metody)

### Prominencja peaku (scipy.signal.find_peaks)

**Prominencja** mierzy, jak bardzo dany peak "wystaje" ponad swoje otoczenie. Nie chodzi o bezwzględną wysokość peaku, lecz o różnicę między wierzchołkiem a najwyższym punktem "doliny" po obu stronach.

Przykład: jeśli sygnał kontaktu stopy waha się między 0.7 a 0.9, a peak ma wartość 0.92, to prominencja ≈ 0.92 - 0.7 = 0.22 (wystarczająco powyżej progu 0.03). Drobna oscylacja szumu z 0.71 na 0.72 ma prominencję ~0.01 — odrzucona.

Prominencja jest lepsza niż bezwzględna wysokość, bo działa niezależnie od tego, jak wysoko lub nisko stopa jest w kadrze (eliminuje problem asymetrii kamery).

### Foot strike vs toe-off

Dwa kluczowe momenty cyklu biegowego:
- **Foot strike (initial contact):** moment uderzenia stopy o podłoże. W sygnale kontaktu widoczny jako peak (lokalne maksimum y stopy).
- **Toe-off:** moment oderwania palców od podłoża. Kończy fazę stance, zaczyna fazę flight.

Cykl jednej nogi: foot strike → mid-stance → toe-off → swing (noga w powietrzu) → foot strike.
Cykl biegu: LEFT foot strike → LEFT stance → FLIGHT → RIGHT foot strike → RIGHT stance → FLIGHT → powtórz.

### Filtr medianowy na sekwencji etykiet

Filtr medianowy na sygnale ciągłym (np. trajektorii keypointów) wygładza wartości liczbowe. Na sekwencji **kategorycznych etykiet** (STANCE/FLIGHT) działa inaczej: zamieniam etykiety na liczby (LEFT_STANCE=0, RIGHT_STANCE=1, FLIGHT=2), stosuję filtr medianowy, i zamieniam z powrotem.

Efekt: jeśli mam sekwencję ...STANCE, STANCE, FLIGHT, STANCE, STANCE..., to ta pojedyncza klatka FLIGHT jest otoczona przez STANCE i filtr medianowy ją "naprawi" na STANCE. Eliminuje 1-2 klatkowe "migotania".

Kernel=3 oznacza okno 3 klatek (bieżąca + 1 przed + 1 po). Mediana z 3 wartości = wartość środkowa. Jeśli 2 z 3 to STANCE, mediana = STANCE.

### Jądro (kernel) filtru

**Jądro** (ang. *kernel*) to po prostu **rozmiar okna** filtru — ile sąsiednich elementów bierzemy pod uwagę przy obliczaniu wyniku filtracji. Słowo „jądro" to polskie tłumaczenie technicznego terminu *kernel*, które w kontekście filtrów cyfrowych oznacza „szablon/okno przesuwane po danych". Nie ma tu głębszego znaczenia matematycznego.

- Kernel=3 → okno 3 elementów (1 przed + bieżący + 1 po)
- Kernel=5 → okno 5 elementów (2 przed + bieżący + 2 po)
- Kernel musi być nieparzysty, żeby miał jednoznaczny element środkowy

W pracy piszę „filtr medianowy z jądrem $k = 3$" — to znaczy: dla każdej klatki biorę 3 sąsiednie etykiety i wybieram tę, która stanowi medianę (wartość środkową po posortowaniu).

---

## [2026-05-24] Pojęcia z sekcji 3.4 — architektury klasyfikatorów

### Random Forest (las losowy)

**Ensemble** wielu drzew decyzyjnych. Każde drzewo:
1. Dostaje losowy podzbiór danych treningowych (bootstrap sampling)
2. Na każdym rozgałęzieniu rozważa losowy podzbiór cech
3. Głosuje za jedną z klas

Finalna decyzja = głosowanie większościowe 300 drzew. Losowość zapobiega overfittingowi.

**Kluczowe hiperparametry:**
- `n_estimators=300` — liczba drzew. Więcej = stabilniejsze, ale wolniejsze
- `max_depth=None` — drzewa rosną do końca (nie ograniczam głębokości)
- `class_weight='balanced'` — automatycznie przypisuje wyższe wagi mniej licznym klasom, żeby model nie faworyzował klasy dominującej

**Ograniczenie:** klasyfikuje każdą klatkę osobno — nie widzi co było w poprzedniej klatce. Ignoruje kontekst czasowy.

### Surowe keypointy vs cechy inżynierowane

**Surowe keypointy** (132 cechy) = bezpośrednie wyjście z MediaPipe, bez żadnej obróbki. 33 punkty × 4 wartości (x, y, z, visibility). Problem: zależą od pozycji biegacza w kadrze (ta sama poza w lewym i prawym rogu daje inny wektor x), od wielkości ciała (wysoki vs niski), i zawierają punkty nieistotne dla biegu (oczy, usta, palce dłoni).

**Cechy inżynierowane** (106 cech) = te same keypointy, ale przetworzone na bardziej sensowną reprezentację:
1. **Normalizacja do ciała** — środek bioder = punkt (0,0), jednostka = długość tułowia → ta sama poza = te same liczby, niezależnie od pozycji/wielkości. 33 × 3 = 99 cech (visibility usunięte).
2. **Kąty stawów** (7 szt.) — zamiast surowych współrzędnych 3 keypointów, obliczam kąt w stawie. Np. kąt kolana ~170° = noga prosta (lot), ~120° = zgięta (kontakt). Kąt bezpośrednio mówi o fazie.

**Paradoks:** mniej cech (106 < 132), ale lepsze wyniki — bo usunęliśmy szum i dodaliśmy wiedzę domenową (kąty).


### BiLSTM (dwukierunkowy LSTM)

**LSTM** (Long Short-Term Memory) to typ sieci neuronowej rekurencyjnej zaprojektowany do przetwarzania sekwencji (tekst, dźwięk, serie czasowe). Kluczowa innowacja: mechanizm bramek (gates), które kontrolują jaką informację zapamiętać, a jaką zapomnieć.

**Bi** = dwukierunkowy: sieć przetwarza sekwencję zarówno od lewej do prawej, jak i od prawej do lewej. Wynik to konkatenacja obu kierunków. Dzięki temu model "widzi" kontekst zarówno z przeszłości jak i przyszłości danej klatki.

**W moim przypadku:**
- Wejście: okno 15 klatek × 106 cech = tensor (15, 106)
- Sieć: 2 warstwy BiLSTM (hidden=128 → 256 po konkatenacji kierunków)
- Wyjście: klasyfikacja klatki centralnej (7. z 15) na 3 klasy

**Dlaczego BiLSTM a nie zwykły LSTM?** W biegu znamy cały film z góry — nie przetwarzamy w czasie rzeczywistym. Klatka po fazie FLIGHT prawdopodobnie jest STANCE — dwukierunkowość pomaga to zobaczyć.

### Inżynieria cech (feature engineering)

Transformacja surowych danych (132 współrzędne keypointów) na **bardziej informatywną reprezentację** (106 cech). Dwa kroki:

1. **Normalizacja do układu ciała:** keypointy przeliczam do układu odniesienia biegacza (środek bioder = punkt 0, jednostka = długość tułowia). Eliminuje to wpływ pozycji w kadrze i różnic w wielkości ciała.

2. **Kąty stawów:** obliczam kąt kolana, biodra, kostki (po 2 na nogę) + pochylenie tułowia. Kąty mają bezpośredni sens biomechaniczny — np. kąt kolana ~170° = noga prawie wyprostowana (faza lotu), ~120° = noga zgięta (faza kontaktu).

**Paradoks:** RF v2 ma MNIEJ cech (106 vs 132), ale LEPSZE wyniki. Dlaczego? Bo usunęliśmy szum (visibility, pozycję w kadrze) i dodaliśmy kąty — cechę bezpośrednio powiązaną z fazą biegu.

### Okno sekwencji (window) w LSTM

LSTM nie dostaje pojedynczej klatki — dostaje **okno 15 kolejnych klatek**. Klasyfikuje klatkę środkową na podstawie kontekstu: 7 klatek przed + bieżąca + 7 klatek po.

**Window=15 przy 30 FPS ≈ 0.5 sekundy** — obejmuje mniej więcej jeden pełny krok biegowy. Model widzi więc cały kontekst jednego cyklu.

**Dlaczego nie dłuższe okno?** Dłuższe okno = więcej kontekstu, ale też więcej parametrów i ryzyko overfittingu. 15 klatek to kompromis.

**Ważne:** okna NIE przekraczają granic filmów. Nie tworzę sztucznej sekwencji łączącej koniec jednego filmiku z początkiem drugiego.

### StandardScaler — normalizacja cech

Przed podaniem do LSTM normalizuję każdą cechę: odejmuję średnią i dzielę przez odchylenie standardowe (obliczone TYLKO na danych treningowych). Po normalizacji każda cecha ma średnią ≈ 0 i std ≈ 1.

**Dlaczego?** Gdyby kąt kolana miał zakres [90°, 180°], a współrzędna X zakres [0.0, 1.0], sieć "myślałaby" że kąt kolana jest ważniejszy (większe wartości = większe gradienty). Normalizacja wyrównuje wagi.

**Dlaczego nie fitujemy na val/test?** Bo to **wyciek danych** (*data leakage*).

StandardScaler potrzebuje dwóch liczb: średniej i odchylenia standardowego. Te liczby obliczamy TYLKO z danych treningowych. Potem tymi samymi liczbami transformujemy dane walidacyjne i testowe.

Gdybyśmy obliczyli średnią i std z całego zbioru (train + val + test razem), to do tych statystyk „wsiąknęłyby" informacje z danych testowych — np. ich zakres wartości, rozkład. Model pośrednio „wiedziałby" coś o danych testowych, zanim je zobaczy. Wyniki ewaluacji byłyby sztucznie zawyżone — nie odzwierciedlałyby tego, jak model poradzi sobie z naprawdę nowym, nieznanym filmem.

**Analogia:** To jak uczeń, który przed egzaminem podejrzał odpowiedzi — nie uczył się z nich wprost, ale jego wynik nie jest uczciwy.

**Zasada ogólna:** NIGDY nie fituj (obliczaj statystyk) na danych testowych. Fituj na train, transformuj train+val+test tymi samymi parametrami.

### Aspect ratio fix (korekta proporcji obrazu)

**Problem:** MediaPipe normalizuje x i y niezależnie do [0, 1]. Dla filmiku 608×1080 px:
- Δx=0.1 = 60.8 pikseli
- Δy=0.1 = 108 pikseli

Gdy obliczam długość tułowia jako √(Δx² + Δy²), mieszam fizycznie różne jednostki — jak dodawanie metrów i kilometrów.

**Rozwiązanie:** mnożę x × szerokość, y × wysokość → obie współrzędne w pikselach → spójne jednostki.

**Efekt:** film 10 (pionowy) poprawia się z 75.8% na 85.9% (+10.1 pp). Dla filmów 16:9 prawie bez zmian (proporcje już bliskie 1:1 po normalizacji).

### Dropout — regularyzacja sieci neuronowej

Podczas treningu **losowo wyłącza** pewien procent neuronów w każdym kroku. Dropout=0.3 → 30% neuronów jest wyłączonych w danym kroku.

**Po co?** Zapobiega overfittingowi — sieć nie może polegać na konkretnych neuronach, musi rozłożyć wiedzę na wiele ścieżek. To zmusza model do uczenia się bardziej ogólnych wzorców.

**Podczas inferencji** dropout jest wyłączony — używamy pełnej sieci.

### Weight decay (L2 regularization)

Dodaje do funkcji straty karę proporcjonalną do sumy kwadratów wag sieci: `loss = loss_data + λ × Σ(w²)`. Parametr `weight_decay = λ` kontroluje siłę kary.

**Efekt:** duże wagi → duża kara → optymalizator preferuje mniejsze wagi → prostsza sieć → mniejszy overfitting.

LSTM r1: λ = 10⁻⁵ (słaba regularyzacja), LSTM r2: λ = 10⁻⁴ (10× silniejsza).

### Early stopping (wczesne zatrzymanie)

Trening kończy się nie po ustalonej liczbie epok, ale gdy **strata walidacyjna** przestaje się poprawiać. `patience=15` = toleruję 15 epok bez poprawy, potem przerywam.

Zachowuję wagi z najlepszej epoki, nie z ostatniej. Zapobiega to overfittingowi — trening zbyt długi pogarsza generalizację.

LSTM r1: najlepsza epoka 5/20. LSTM r2: najlepsza epoka 3/18. Oba modele szybko konwergowały i potem zaczynały się overfitować.

---

## [2026-05-24] Pojęcia z sekcji 3.5–3.8

### Run-length encoding (segmentacja sekwencji)

Metoda podziału sekwencji na ciągłe fragmenty o tej samej etykiecie. Przechodzisz po tablicy etykiet od początku do końca — gdy etykieta zmienia się, kończysz bieżący segment i zaczynasz nowy.

Przykład: `[L, L, L, F, F, R, R, R, F, F, L, L]` → 5 segmentów:
- L (3 klatki), F (2), R (3), F (2), L (2)

Użyłem tego do obliczenia GCT (czas trwania segmentów STANCE), czasu lotu (segmenty FLIGHT) itp.

### Kadencja (step rate) [spm]

Liczba kontaktów stóp z podłożem na minutę. Krok = wejście w fazę STANCE (przejście z nie-STANCE do STANCE).

**Formuła:** `kadencja = (n_kroków / czas_nagrania_s) × 60`

**Zakresy:** rekreacyjny 150–170 spm, zaawansowany 170–185, elita 180–200.

### GCT (Ground Contact Time)

Czas kontaktu stopy z podłożem — jak długo stopa jest na ziemi w jednym kroku. Obliczany osobno dla L i R jako średni czas trwania segmentów STANCE.

**Zakresy:** wolny bieg 250–350 ms, rekreacyjny 200–280, szybki 160–220 ms.

### Duty factor

Stosunek GCT do czasu cyklu: `DF = GCT / cycle_time`. Mówi, jaki procent cyklu stopa spędza na ziemi.

- **DF < 0.5** = bieg (stopa krócej na ziemi niż w powietrzu)
- **DF ≥ 0.5** = technicznie chód
- Typowy bieg rekreacyjny: 0.35–0.45

### Stride length (długość kroku)

Odległość od kontaktu jednej stopy do następnego kontaktu **tej samej** stopy. Na bieżni obliczamy ją z prędkości bieżni: `stride = speed × cycle_time`.

**Uwaga:** NIE można wyznaczyć z samego wideo — biegacz stoi w miejscu na bieżni. Wymaga podania prędkości przez użytkownika.

### Vertical oscillation (oscylacja pionowa)

Jak bardzo biodra poruszają się w górę-w dół w obrębie jednego cyklu biegowego. Mierzona jako `max(Y_hip) - min(Y_hip)` per cykl.

Normalizuję ją długością tułowia (bo wielkość w pikselach zależy od odległości kamery): `VO_norm = ΔY_hip / torso_length`.

**Zakresy:** dobry biegacz 0.12–0.16 torso (≈6–8 cm), rekreacyjny do 0.24 (≈12 cm).

### Foot strike pattern (wzorzec lądowania stopy)

Która część stopy pierwsza dotyka podłoża: pięta (heel strike), śródstopie (midfoot) czy przodostopie (forefoot). Klasyfikuję na podstawie kąta wektora HEEL→FOOT_INDEX w momencie kontaktu.

**Progi:** kąt > 5° = heel strike, < −5° = forefoot, pomiędzy = midfoot.

**Ważne:** ten współczynnik jest BARDZO wrażliwy na kąt kamery. Wideo pionowe daje bzdurne wyniki. Automatyczna flaga `low_confidence` gdy |kąt| > 45°.

### Symmetry Index (SI) — wskaźnik symetrii Robinsona

**Formuła:** `SI = 200 × |L − R| / (L + R)` [%]

Mierzy różnicę między lewą i prawą stroną ciała. SI = 0% to idealna symetria.

**Progi (Robinson 1987):**
- < 5% = norma
- 5–10% = łagodna asymetria, monitoruj
- > 10% = znacząca asymetria, rozważ konsultację

### Precision (precyzja) vs Recall (czułość)

**Precision:** "Gdy model mówi FLIGHT — jak często ma rację?" = TP / (TP + FP)
**Recall:** "Jaki % prawdziwych FLIGHT model wykrył?" = TP / (TP + FN)

Trade-off: model "ostrożny" (rzadko mówi FLIGHT) ma wysoką precision ale niski recall. Model "agresywny" (dużo mówi FLIGHT) odwrotnie.

### F1 (miara F1)

Średnia harmoniczna precision i recall: `F1 = 2 × precision × recall / (precision + recall)`.

Harmoniczna, nie arytmetyczna — każe model za słabszą z dwóch metryk. Jeśli precision=1.0 ale recall=0.01, F1≈0.02 (nie 0.5).

**Macro F1** = średnia arytmetyczna F1 ze wszystkich klas. Traktuje każdą klasę z równą wagą.

### Macierz pomyłek (confusion matrix)

Tablica 3×3 (dla 3 klas). Wiersz = prawdziwa klasa, kolumna = co model przewidział. Przekątna = poprawne, poza przekątną = pomyłki.

**Dwa typy pomyłek w naszym kontekście:**
1. **L↔R** (model myli lewą z prawą) — psuje symetrię L/P, ale kadencja i średni GCT zostają OK
2. **STANCE↔FLIGHT** (model myli kontakt z lotem) — psuje WSZYSTKIE współczynniki temporalne

### Overfitting (przeuczenie)

Model zbyt dokładnie zapamiętuje dane treningowe — włącznie z ich szumem i przypadkowymi wzorcami — i osiąga świetne wyniki na danych treningowych, ale znacząco gorsze na nowych danych.

**Analogia:** uczeń, który wykuł odpowiedzi do konkretnego zestawu pytań, ale nie rozumie materiału. Na egzaminie z innym zestawem pytań wypada słabo.

**Regularyzacja** = techniki ograniczające overfitting: dropout, weight decay, early stopping.

### Ukryty wymiar (hidden dimension)

Rozmiar wektora pamięci wewnętrznej sieci LSTM — ile liczb sieć wykorzystuje do zakodowania informacji o dotychczasowej sekwencji na każdym kroku. h=128 → na każdym kroku sieć tworzy wektor 128 liczb podsumowujący "co się wydarzyło do tej pory".

Większy ukryty wymiar = sieć może zapamiętać bardziej złożone wzorce, ale ma więcej parametrów = większe ryzyko przeuczenia.

### Konkatenacja kierunków w BiLSTM

BiLSTM przetwarza sekwencję dwukrotnie:
- Przejście "od lewej do prawej" → wektor 128 wartości (widział przeszłość)
- Przejście "od prawej do lewej" → wektor 128 wartości (widział przyszłość)

Te dwa wektory są **łączone (konkatenowane)** — sklejane jeden za drugim w jeden wektor o długości 128 + 128 = 256. Każda klatka ma więc kontekst z obu stron.

### Parametry modelu (wagi sieci)

Parametry = **liczby, które sieć dostosowuje podczas treningu**. Każde połączenie między neuronami ma wagę (mnożnik) — to te wagi tworzą "wiedzę" modelu. Sieć z 637 699 parametrami ma ponad 600 tysięcy liczb do dopasowania. Więcej parametrów = model może nauczyć się bardziej złożonych wzorców, ale też łatwiej się przeuczy.

Dla porównania: LSTM r2 ma 187 779 parametrów (3.4× mniej), co ogranicza pojemność modelu.

### Tempo uczenia (learning rate)

Określa, jak duże korekty wag wykonuje optymalizator w każdym kroku treningowym. Za duże tempo → model "przeskakuje" optimum i nie uczy się stabilnie. Za małe tempo → trening trwa bardzo długo i może utknąć w słabym minimum.

LSTM r1: lr=0.001 (standardowe), LSTM r2: lr=0.0003 (ostrożniejsze, bo mniejszy model).

### Inferencja (w kontekście dropoutu)

Podczas **treningu** dropout wyłącza losowo 30% neuronów. Podczas **inferencji** (użycie wytrenowanego modelu na nowych danych) dropout jest wyłączony — wszystkie neurony pracują. Wyjścia neuronów są odpowiednio przeskalowane (mnożone przez 0.7 = 1-dropout), żeby kompensować fakt, że w treningu część neuronów była wyłączona.

### Korekta proporcji (aspect ratio fix) — szczegółowo

MediaPipe normalizuje x do [0,1] i y do [0,1] NIEZALEŻNIE. Dla kadru 608×1080:
- x=0.5 = 304 pikseli od lewej krawędzi
- y=0.5 = 540 pikseli od górnej krawędzi

Przesunięcie Δx=0.1 = 60.8 px, ale Δy=0.1 = 108 px. Ta sama zmiana w "znormalizowanej przestrzeni" oznacza fizycznie INNY dystans w pionie niż w poziomie.

**Problem:** Gdy obliczam odległość euklidesową (np. długość tułowia) jako √(Δx² + Δy²), mieszam nierównoważne jednostki. To jak dodawanie metrów i mil.

**Fix:** Przemnóż x × szerokość (608), y × wysokość (1080) → obie współrzędne w pikselach → spójne.

Dla kadru 16:9 (1920×1080) stosunek szerokość/wysokość ≈ 1.78 — zniekształcenie umiarkowane. Dla kadru pionowego (608×1080) stosunek ≈ 0.56 — zniekształcenie znaczące.

---

## [2026-05-24] Pojęcia z sekcji 3.5 — współczynniki biomechaniczne

### Dlaczego „temporalne" (czasowe)?

Współczynniki biomechaniczne dzielą się na dwie grupy:
- **Temporalne** — ich wartość wynika z CZASU TRWANIA poszczególnych faz biegu. Np. kadencja (ile kroków na minutę), GCT (ile milisekund stopa jest na ziemi). Do ich obliczenia wystarczy sekwencja etykiet faz + FPS wideo. Nie trzeba wiedzieć, gdzie są keypointy — wystarczy, że klasyfikator powiedział "STANCE przez 8 klatek, potem FLIGHT przez 3 klatki".
- **Przestrzenne** — ich wartość wynika z POZYCJI keypointów w konkretnych klatkach. Np. kąt kolana (geometria trzech punktów: biodro-kolano-kostka). Tu etykiety faz służą tylko do wybrania odpowiednich klatek (np. "kąt kolana w momencie kontaktu").

Nazwa "temporalne" pochodzi od łac. *tempus* = czas.

### Segmentacja sekwencji faz — do czego służy i jak działa

**Problem:** Klasyfikator daje mi tablicę etykiet, jedną na klatkę:
```
[L, L, L, F, F, R, R, R, R, F, F, L, L, L, ...]
```
Żeby obliczyć np. GCT (czas kontaktu), muszę wiedzieć "ile klatek z rzędu trwał każdy kontakt?". Potrzebuję podzielić tę tablicę na segmenty.

**Jak to działa (run-length encoding):** Przechodzę tablicę od lewej do prawej. Dopóki kolejne klatki mają tę samą etykietę → ten sam segment. Gdy etykieta się zmienia → nowy segment.

Przykład:
```
Tablica: [L, L, L, F, F, R, R, R, R, F, F, L]
                ↓
Segmenty:
  1. LEFT_STANCE  (klatki 0-2, 3 klatki)
  2. FLIGHT       (klatki 3-4, 2 klatki)
  3. RIGHT_STANCE (klatki 5-8, 4 klatki)
  4. FLIGHT       (klatki 8-9, 2 klatki)
  5. LEFT_STANCE  (klatka 11,  1 klatka)
```

**Co z tego wychodzi:** Segment RIGHT_STANCE (4 klatki) przy 30 FPS = 4/30 = 0.133s = 133ms → to jest jeden pomiar GCT prawej stopy. Zbierając takie pomiary ze wszystkich segmentów STANCE danej nogi, wyliczam średnią ± std.

### Jak wyliczam średnią ± std ze wszystkich cykli

Każdy segment fazy to jeden pomiar. Np. w nagraniu 20s przy kadencji 170 spm mam ~28 kroków = ~14 segmentów LEFT_STANCE i ~14 RIGHT_STANCE.

Dla GCT lewej stopy:
1. Wybieram wszystkie segmenty LEFT_STANCE
2. Obliczam czas trwania każdego: t₁, t₂, ..., t₁₄
3. Średnia = (t₁ + t₂ + ... + t₁₄) / 14
4. Odchylenie standardowe = mierzy rozrzut tych 14 pomiarów wokół średniej

Raportowany wynik: np. "GCT_L = 245 ± 12 ms" — typowy kontakt lewej stopy trwa 245ms, z odchyleniem 12ms od cyklu do cyklu.

### Cykl biegowy (gait cycle)

Pełen cykl ruchu jednej nogi: od momentu gdy stopa dotyka podłoża do następnego momentu gdy TA SAMA stopa dotyka podłoża. Obejmuje:
1. Kontakt tej stopy (STANCE)
2. Lot (FLIGHT)
3. Kontakt DRUGIEJ stopy (STANCE)
4. Lot (FLIGHT)
5. Powrót do kontaktu pierwszej stopy

Czas cyklu ≈ 2 × czas kroku. Np. przy kadencji 170 spm → 85 cykli/min → czas cyklu ≈ 0.71s.

Duty factor = GCT / czas_cyklu → mówi jaki % cyklu stopa spędza na ziemi. DF < 0.5 = bieg (stopa krócej na ziemi niż w powietrzu).

### Osobno dla lewej i prawej

Współczynniki takie jak GCT, czas cyklu, duty factor, kąt kolana, kąt kostki obliczam DWIE RAZY — raz dla segmentów LEFT_STANCE (współczynnik lewej nogi) i raz dla RIGHT_STANCE (współczynnik prawej nogi). Daje to np.:
- GCT_L = 245 ± 12 ms
- GCT_R = 238 ± 10 ms

Porównanie L vs R = wskaźnik symetrii (Robinson SI).

---

## [2026-05-24] Pojęcia z sekcji 3.5.3 — współczynniki przestrzenne

### Wygładzone keypointy

To NIE są surowe wartości z MediaPipe, ale keypointy po przejściu przez filtr Savitzky-Golay (sekcja 3.2). Filtr usuwa szybkie, losowe fluktuacje (jitter), zachowując prawdziwy kształt ruchu. Dlaczego obliczenia robię na wygładzonych, a nie surowych?
- Surowe = mocno szumią → kąty stawów mogą skakać o 5-10° z klatki na klatkę nawet gdy ciało porusza się płynnie
- Wygładzone = pozbawione szumu → kąty zmieniają się płynnie, zgodnie z rzeczywistym ruchem

### Klatkach LUB fazach — czemu „lub"?

Część współczynników liczę z JEDNEJ klatki:
- Kąt kolana w momencie kontaktu = pierwszy klatka segmentu STANCE → jedna wartość
- Foot strike = ten sam moment → jedna wartość

Część współczynników liczę z WIELU klatek (całej fazy):
- Średni kąt kolana w fazie STANCE → uśredniam wszystkie klatki tej fazy
- Oscylacja pionowa = max(y) - min(y) w obrębie cyklu → potrzebuje wielu klatek

Stąd „lub" — w zależności od współczynnika.

### Noga oporowa vs faza wahadła

Klasyczne pojęcia z biomechaniki biegu:

**Noga oporowa (stance leg)** — noga z stopą na ziemi w danej chwili. Przejmuje ciężar ciała i siły reakcji podłoża. Odpowiada fazie LEFT_STANCE lub RIGHT_STANCE w naszym klasyfikatorze.

**Noga w fazie wahadła (swing leg)** — noga uniesiona, przesuwająca się do przodu. Mocno zgięta w kolanie (skraca długość wahadła → szybciej przeniesie się do przodu).

Kluczowa zasada: w biegu zawsze JEDNA noga jest oporowa, druga w wahadle. Wyjątek: w fazie FLIGHT obie są w powietrzu — wtedy ani jedna ani druga nie jest "oporowa" w klasycznym sensie.

**Liczby:**
- Kąt kolana nogi oporowej: 155-175° (prawie wyprostowane → amortyzuje uderzenie)
- Kąt kolana nogi w wahadle: 100-140° (mocno zgięte → szybsze przeniesienie)

### Kreska nad symbolem = średnia

W matematyce **pozioma kreska nad symbolem** to standardowa notacja oznaczająca **średnią arytmetyczną**:
- $\overline{x}$ = średnia z x
- $\overline{l_{torso}}$ = średnia długość tułowia

W naszym wzorze `VO_norm = Δy / l̄_torso`:
- Jedna pozioma kreska to znak DZIELENIA (ułamek)
- Kreska nad l_torso to znak ŚREDNIEJ (uśredniam długość tułowia przez wszystkie klatki cyklu)

Wzór czyta się: „delta y podzielone przez średnią długość tułowia".

### Theta (θ) w foot strike

W wzorze `θ = arctan2(-Δy, Δx)` mamy trzy zmienne:

- **Δx = x_foot_index − x_heel** — różnica poziomych pozycji czubka stopy i pięty. Mówi „na ile pikseli czubek jest dalej od pięty w poziomie".
- **Δy = y_foot_index − y_heel** — analogicznie w pionie. Minus przed Δy bo MediaPipe ma oś Y rosnącą w dół (0 góra, 1 dół), a my chcemy matematyczną konwencję (Y rosnące w górę).
- **θ (theta)** — kąt stopy względem poziomu, w stopniach. Interpretacja:
  - θ > 0 → czubek wyżej niż pięta → pięta nisko, pierwsza dotyka ziemi → heel strike
  - θ < 0 → pięta wyżej niż czubek → przód stopy nisko → forefoot strike
  - θ ≈ 0 → stopa równoległa do podłoża → midfoot

Funkcja `arctan2(y, x)` to wariant arctan, który zwraca pełny kąt w zakresie [−180°, 180°] z uwzględnieniem znaków obu argumentów (zwykły arctan zwraca tylko [−90°, 90°]).

---

## [2026-05-24] Wskaźnik symetrii Robinsona (SI)

### Wzór i intuicja

```
SI = 200 × |L − R| / (L + R)   [%]
```

Trzy elementy:
1. **|L − R|** — bezwzględna różnica między stroną lewą i prawą
2. **L + R** — suma, używana do normalizacji (dzięki niej wynik to procent, niezależny od skali)
3. **× 200** — mnożnik dający procent względem ŚREDNIEJ z lewej i prawej (czyli (L+R)/2)

Dlaczego 200, nie 100? Bo dzielimy przez SUMĘ (L+R), nie przez średnią ((L+R)/2). Łatwiej zapisać 200·|L-R|/(L+R) niż 100·|L-R|/((L+R)/2) — to dokładnie to samo.

**Przykład:** GCT_L = 250 ms, GCT_R = 240 ms
- |L − R| = 10
- L + R = 490
- SI = 200 × 10 / 490 ≈ 4.1%

### Progi (z literatury)

- **< 5%** — norma
- **5–10%** — łagodna asymetria, monitoruj
- **> 10%** — znacząca asymetria, rozważ konsultację

### Pochodzenie

Robinson, Herzog, Nigg (1987) — pierwotnie do oceny chodu po manipulacjach chiropraktycznych (force platform). Wzór działa dla DOWOLNEGO wskaźnika obliczanego osobno dla L i R. Dziś szeroko stosowany w analizie biegu.

### Dla jakich współczynników liczymy SI?

W mojej pracy: 5 par
- GCT (L vs R)
- Czas cyklu (L vs R)
- Duty factor (L vs R)
- Kąt kolana w fazie STANCE (L vs R)
- Kąt kostki w fazie STANCE (L vs R)

Plus foot strike pattern — ale to kategoryczne (heel/midfoot/forefoot), więc nie SI, tylko prosta flaga „spójność: tak/nie".

### Dlaczego dla każdego współczynnika osobno, a nie jedna ogólna „symetria nogi"?

Bo asymetria może manifestować się różnie i mówić co innego o problemie:

| Symetryczny | Asymetryczny | Interpretacja |
|---|---|---|
| Kąty kolan | GCT | Oszczędzanie nogi po kontuzji (mimo identycznej pracy stawów dłużej trzyma stopę na ziemi) |
| GCT | Kąty kolan | Słabość czworogłowego po jednej stronie (jedna noga ugina się mocniej) |
| GCT, czas cyklu | Duty factor | Zaburzony rytm między nogami |

Pojedyncza ogólna metryka "symetria L/R" by to zatraciła. Dla każdego współczynnika SI mówi coś innego diagnostycznie.

### Koszt obliczeniowy

Bardzo mały. Każda para L, R i tak jest już wyliczona w ramach obliczeń per-noga. SI to jedna prosta operacja (dwa odejmowania, dwa dodawania, jedna wartość bezwzględna, jedno dzielenie, jedno mnożenie). 5 par → 5 takich operacji. W kodzie to dosłownie pętla po słowniku par.

