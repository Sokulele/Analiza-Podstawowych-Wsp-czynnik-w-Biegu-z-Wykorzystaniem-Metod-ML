# 2026-06-03 — Walidacja pipeline względem Garmina (własne nagranie Wojtek)

## Kontekst

Użytkownik (Wojtek) nagrał własny bieg na bieżni i dostarczył eksport FIT z zegarka Garmin
— **pierwszy w całej pracy ground truth z zewnętrznego urządzenia** (dotąd walidacja tylko
względem zakresów z literatury). Nagranie: `data/videos/Wojtek__segment_1.mov`.

- Wideo: 1920×1080 (poziome, HD), 29,97 FPS, 1228 klatek (~41 s)
- FIT: `data/inference/wojtek_garmin.fit` (154 rekordy per-sekunda, treadmill_running)
- Aktywność Garmin: 153 s łącznie; bieg właściwy ~93–138 s (reszta = rozbieganie + testy nagrania)
- **Okno wideo ↔ Garmin: 1:35–2:10 (95–130 s)** — wskazane przez użytkownika, potwierdzone w FIT
  (stabilna kadencja 158–167 spm, brak pauz)

## WAŻNE: porównywać tylko okno biegu właściwego

Średnia z CAŁEJ aktywności Garmina = 136 spm (skażona rozbieganiem i pauzami) — NIE używać.
Czyste porównanie = okno 95–130 s.

## Wyniki: Pipeline (lstm_run1_overfit) vs Garmin (okno 95–130 s)

| Metryka | Pipeline | Garmin | Błąd |
|---|---|---|---|
| Kadencja | 162,5 spm | 163,3 spm (158–167) | **−0,5%** |
| Czas cyklu | 737 ms | ~735 ms (z 163,3 spm) | +0,3% |
| GCT (śr. L/P) | 254,5 ms | 297,4 ms (292–309) | **−14,4%** |
| Stride (v=2,19 m/s) | 1,61 m | 1,61 m (2×806 mm step) | zgodne |
| Vert. oscylacja | 0,130 znorm. | 78,9 mm | nieporównywalne wprost |
| Balans L/P | 49,5/50,5% | brak w FIT (stance_time_balance=None) | — |

Prędkość bieżni wg Garmina: ~2,19 m/s (≈7,9 km/h). Step length Garmin ~806 mm.

## Kluczowy wniosek: "licznik vs czas trwania" potwierdzony ground-truthem

- **Kadencja (licznik kontaktów): 0,5% błędu** — odporna, bo liczy ŻE kontakt nastąpił.
- **GCT (czas trwania STANCE): 14% zaniżenia** — wrażliwy, bo zależy GDZIE pada granica STANCE↔FLIGHT.
- Oba z tej samej sekwencji faz → różnica wynika WYŁĄCZNIE z wrażliwości na granicę faz.
- Potwierdza liczbowo teoretyczny argument rozdz. 4.6 (dotąd tylko rachunek "±2 klatki=±30%").

## Dlaczego GCT zaniżony (spójna przyczyna)

`flight_fraction=0,4` w auto-etykietowaniu (auto_label.py) przypisuje 40% interwału między
kontaktami do FLIGHT → systematycznie skraca STANCE. Zaniża JEDNOCZEŚNIE:
- GCT: 255 vs 297 ms
- duty factor: 0,345 vs realne ~0,40 (=297/735)
Klasyfikator dziedziczy ten bias z etykiet treningowych. Dodatkowo różnica definicyjna:
Garmin liczy GCT z akcelerometru (heel strike→toe-off), pipeline z etykiety STANCE.

NIE potwierdzone na warm-upie: w oknie biegu właściwego (96–114 s) Garmin GCT 294–297 ms
przy kadencji 165 — czyli zaniżenie GCT jest REALNE, nie artefakt rozbiegania.

## Foot strike — auto-detekcja zadziałała mimo HD poziomego

- Pipeline foot strike: kąt **−90,5° / −98,4°** → obie nogi oflagowane `low_confidence` (>45°).
- To MOCNIEJSZY dowód niż Film 10 (pionowy): tu HD poziome 1080p, a kąt i tak bzdurny.
- Wniosek: orientacja pozioma KONIECZNA, ale NIEWYSTARCZAJĄCA — kamera musi być prostopadła
  i na właściwej wysokości. Wojtek prawdopodobnie filmował pod kątem (do potwierdzenia renderem).
- Kąt kolana @ kontakt 120/121° (też podejrzanie niski) — ta sama perspektywa psuje geometrię.

## Pozostałe liczby

- avg_confidence predykcji = 0,855 — NAJNIŻSZA ze wszystkich biegaczy (Adam 0,909, Film 10 0,89,
  Janek 0,882). Ledwo powyżej progu 0,85 (reguła jakości danych nie odpaliła).
- Symetria temporalna: max SI 9,5%, mean SI 3,1% — NAJLEPSZA w całym zbiorze.
- Rekomendacje: 0 critical / 1 warning (foot strike low_conf) / 4 watch / 2 info.

## Status decyzji o umiejscowieniu w pracy — ✅ NAPISANE (2026-06-03)

Zrealizowane jako hybryda opcji 1+3:
- **Rozdz. Wrażliwość**: nowa sekcja `\label{sec:walidacja-garmin}` „Walidacja na nagraniu własnym
  z pomiarem referencyjnym" — pełne studium (tabela pipeline vs Garmin, kadencja-vs-GCT, foot strike
  auto-flag, symetria, confidence). + wzmianka w Podsumowaniu rozdziału.
- **Rozdz. Klasyfikator (sek. 4.6 `sec:wplyw-na-metryki`)**: dopisany akapit — walidacja Garmin
  jako empiryczne potwierdzenie teoretycznego argumentu „licznik vs czas trwania".
- Cross-referencje obustronne (4.6 ↔ walidacja-garmin) zweryfikowane, kompilują się czysto.
- Tabela `tab:garmin-validation`: kadencja 162,5 vs 163,3 (−0,5%), cykl 737 vs 735 (+0,3%),
  GCT 255 vs 297 (−14%).
- L/P balans opisany jako „wg aplikacji Garmin Connect" (nie ma go w FIT — uczciwie).
- Diaz NIE cytowany.

## Do zrobienia / pamiętać

- Balans L/P (49-51%) użytkownik podał z ekranu Connect — NIE ma go w FIT. Do cytowania trzeba
  potwierdzić skąd (screenshot Connect) albo opisać jako "wg aplikacji Garmin Connect".
- Ewentualny render klatek foot strike dla wzrokowego potwierdzenia kąta kamery.
- Artefakty: `data/inference/wojtek__segment_1-*.json/csv`, raporty w `data/inference/raporty/`,
  FIT w `data/inference/wojtek_garmin.fit`.
