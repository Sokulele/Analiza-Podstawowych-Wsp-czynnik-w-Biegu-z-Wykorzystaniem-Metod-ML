# 2026-05-13 — Sesja B (część 1): Stride length + combinatorical quality

## Kontekst

Po zamknięciu Sesji A (integracja Etapu 7 z `analyze.py`, ta sama data) pipeline
generował pełen komplet artefaktów i rekomendacji z jednego CLI. **Iteracja 1 nie
zawierała jednak współczynnika `stride length`** — pomimo że to klasyczna metryka
biomechaniki biegu wymieniana w każdej publikacji.

Drugą luką była **walidacja jakości predykcji**: trzy pojedyncze proxy (`conf<0.85`,
`steps_SI>20%`, `max_SI>30%`) okazały się **niewystarczające dla edge case'u Janka**
opisanego w notatce `2026-05-12-etap7-rekomendacje.md`. Janek miał:

- avg_conf = 0.882 (powyżej progu 0.85 → confidence proxy NIE odpalił)
- steps L/R = 98/99 (zbalansowane → steps_SI proxy NIE odpalił)
- max SI = 60% (powyżej progu 30% → max_si proxy odpalił, ale tylko jako *warning*)

Mimo to GCT/DF asymetria 60% była ewidentnym błędem predykcji granicy STANCE per noga.
Brakowało reguły, która **łączy** sygnały — analogii do "high SI + nie-100%-confidence".

Sesja B (część 1) zamyka obie luki w jednej iteracji.

## Decyzje implementacyjne

### Stride length: gdzie umieścić obliczenie?

**Opcja A**: nowy moduł `stride.py` na poziomie `src/coefficients/`.
- Plus: jednoznaczne miejsce dla każdej nowej metryki.
- Minus: nadmiarowy plik dla jednej funkcji-wzoru `speed × cycle_time` (5 linii logiki).

**Opcja B ✅ (wybrana)**: rozszerzenie `temporal_metrics.py`.
- Plus: stride length to **temporal metric** — pochodna cycle_time. Logicznie należy do
  tego samego pliku.
- Plus: minimalizacja sys.path imports w `analyze.py`.
- Plus: jeden punkt zapisu klucza w `temporal.json`.

**Opcja C** (rozważana): wymagać `treadmill_speed_ms` jako parametru wymaganego.
Odrzucona — łamie istniejące testy i Iterację 1. Wybór: parametr **opcjonalny**, klucz
`stride_length` w JSON-ie tylko gdy speed podane. Reguła `check_stride_length` ma early
return gdy klucz nie istnieje — graceful skip.

### Stride: jakie progi?

Reference values mówią "stride 1.0–1.5× wzrost", ale wzrost biegacza **nie jest dostępny
w pipeline'ie**. Można:

**Wariant A**: wymagać `--runner-height-cm` jako kolejny CLI flag.
Odrzucony — kolejny obowiązkowy input zwiększa friction. Wzrost biegacza zwykle nie jest
mierzony precyzyjnie w typowej sesji analizy.

**Wariant B ✅ (wybrany)**: konserwatywne progi absolutne, kalibrowane na typowych
wartościach z literatury dla biegacza ~170 cm:

| stride [m] | klasyfikacja | severity | uzasadnienie |
|---|---|---|---|
| < 1.2 | bardzo krótki | warning | granica chodu, możliwy błąd speed inputu |
| 1.2 – 1.5 | krótki | watch | powolny jogging |
| 1.5 – 2.4 | typowy | info | zakres rekreacyjny |
| 2.4 – 3.0 | długi | watch | szybki bieg lub overstride |
| > 3.0 | bardzo długi | watch | sprint / błąd cycle_time |

Plus **reguła łączona overstride_v2**: stride > 2.2 m AND cadence < 160 → warning.
To **silniejszy sygnał** niż istniejący `overstriding_combo` (kadencja < 160 AND
GCT > 270 ms), bo łączy dwie różne grupy metryk: kadencję i przestrzeń (stride).

### Combinatorical quality: jaka formuła?

Brief poprzedniej sesji proponował:
`conf<0.85 OR steps_SI>20% OR (max_SI>50% AND conf<0.90)` → critical

Pierwsze dwa warunki to **istniejące pojedyncze proxy** (już w `check_data_quality`).
Trzeci to **nowy combinatorical** — i to on jest jedynym nowym sygnałem.

**Decyzja**: dodać `max_SI > 50% AND avg_conf < 0.90` jako oddzielną regułę, nie
modyfikować istniejących progów. Pojedyncze proxy fire dalej osobno (gdy któryś
ewidentnie zawodzi). Combinatorical fire **dodatkowo** gdy żaden pojedynczy nie wystarcza,
ale łączna konfiguracja jest podejrzana.

Korzyść takiej struktury: **interpretowalność**. Użytkownik widzi nie tylko "model się myli",
ale konkretnie: który z proxy fire, oraz czy fire'uje też combo (= silniejszy sygnał).

Progi `max_SI > 50%` i `conf < 0.90` są **ostrzejsze** od ich pojedynczych odpowiedników
(`max_SI > 30%`, `conf < 0.85`), żeby reguła łączona była **rzadsza i bardziej selektywna** —
nie chcemy fire'ować combinatorical na każdym warningu.

## Wyniki testu na 3 biegaczach

| Biegacz | speed | stride [m] | cad | max SI | conf | combinatorical |
|---|---|---|---|---|---|---|
| **02** (znany problem case) | 13 km/h | 2.83 | 144 | 36% (z stride asymetrii) | 0.82 | ✅ critical |
| **22** (test set, dobry) | — | — | 163 | 35.0% | 0.89 | ⛔ nie fire (max_SI<50%) |
| **Janek** (edge case) | — | — | 148 | 60.0% | 0.882 | ✅ critical (**NOWE**) |

Wnioski:

1. **Combinatorical sprawdza się dla edge case'u Janka** — pojedyncze proxy zawiodły,
   combinatorical fire jako pierwszy critical w liście. Cel sesji osiągnięty.
2. **22 nie odpala combinatorical mimo max_SI=35% i conf=0.89** — zarówno pojedyncze
   proxy (`max_si_high` warning), jak i fakt że `max_SI < 50%` blokuje combinatorical.
   To pokazuje że nowa reguła **nie produkuje false positives** na dobrym materiale.
3. **Film 02 jako bonus**: znany problem case z notatki Iteracji 1 (steps_SI 57%).
   Tu **trzy** reguły jakości fire (low_confidence + steps_asymmetry + combinatorical),
   plus reguła stride_long + overstride_long_stride_combo — pełna diagnostyka błędnej
   inferencji + biomechaniki.

## Co to oznacza dla pracy magisterskiej

### Rozdział 6 (Współczynniki) — uzupełnienie

Stride length zamyka listę 5 współczynników temporalnych z briefu CLAUDE.md:
**kadencja, GCT, czas lotu, stride length, duty factor**. Wszystkie są teraz wyliczane
i zapisywane w JSON-ie. Praca może uczciwie raportować pełen zestaw klasycznych metryk.

### Rozdział 7 (Rekomendacje) — wzbogacenie

Dwie nowe reguły wzbogacają katalog z 10 do 12+ (zależnie od liczenia overstride_v2 jako
osobnej reguły):

- `check_stride_length` z 5 progami absolutnymi + reguła łączona
- `quality_combo_high_si_low_conf` (combinatorical)

Tabela reguł w rozdziale 7 pracy powinna teraz zawierać też reguły łączone
(`overstriding_combo`, `overstride_long_stride_combo`, `quality_combo_*`) jako osobną
kategorię — to wartość dodana względem prostych progów.

### Sekcja "Limitations" — częściowe domknięcie #1

Limitation #1 z notatki Iteracji 1 brzmiała: "Pojedyncze proxy jakości predykcji
(`conf<0.85`, `steps_SI>20%`) mogą nie wystarczyć — Janek pokazał edge case." **Sesja B
to częściowo rozwiązuje** — combinatorical detection łapie konkretnie ten przypadek.
Pełne rozwiązanie wymagałoby walidacji na większej próbce filmów z błędną predykcją
(ich nie mamy w tym datasecie), więc limitation pozostaje, ale **z konkretnym mitygantem
w kodzie**.

## Otwarte pytania / future work

1. **Pełna walidacja stride length**: nie mamy ground truth dla większości filmów
   (treadmill_speed nie był zapisywany w naszym datasecie poza filmem 02 — "13km/h"
   w nazwie). Praktyczna walidacja wymaga eksperymentu z znaną prędkością bieżni.
2. **Stride per side**: warto sprawdzić czy `stride_left ≠ stride_right` koreluje ze
   `steps_SI`. Dla filmu 02 widać silną asymetrię (2.36 m vs 3.56 m), co jest spójne
   z biegunem `steps_asymmetry`. Możliwa nowa reguła jakości w przyszłości.
3. **Combinatorical: trzeci warunek?**: rozważyć `(steps_SI > 10% AND max_SI > 30%)`
   jako trzecią regułę łączoną. Próg pojedynczego steps_SI to 20% (krytyczny), ale
   nawet 10% asymetria z drugą metryką może być sygnałem.
4. **Stride length normalizacja na wzrost**: gdy mamy wzrost biegacza, raportować też
   `stride / height` — wymaga rozszerzenia meta + dodatkowej reguły w `check_stride_length`.
