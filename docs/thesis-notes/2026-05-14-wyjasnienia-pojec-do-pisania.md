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

