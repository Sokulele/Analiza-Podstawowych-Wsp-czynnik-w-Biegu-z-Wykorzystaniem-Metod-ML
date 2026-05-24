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


