# 2026-05-23 — Sesja E: Pisanie rozdziału 3 (sekcje 3.1–3.3) ✅

**Opis dla agenta:** Pisanie rozdziału 3: sekcje 3.1–3.3, metodologia i treść pracy

**Słowa kluczowe:** rozdział 3, metodologia, sekcje 3.1-3.3, pisanie

---

## 2026-05-23 — Sesja E: Pisanie rozdziału 3 (sekcje 3.1–3.3) ✅

### Zrobione

**Sekcja 3.1 Dataset** — GOTOWA
- Akapit otwarcia: 15 filmów, 2 źródła, klub Zabiegani na Szamę (Paweł, Adam, Janek)
- 3.1.1 Kryteria doboru: 5 minimalnych kryteriów + nota o celowych edge case'ach (pionowe wideo, slow-motion, bieg boso)
- 3.1.2 Charakterystyka zbioru: tabela ze **sekwencyjną numeracją 1–13** (zamiast oryginalnych numerów plików), opisy zmienione na czytelne (nie "Sage Canaday" tylko "Bieg maratoński"), filmy 16 i 18 usunięte (nieużywane)
- Wyjaśnienie slow-motion jako materiału treningowego
- Podsumowanie splitu: 12 087 klatek, 12 007 z etykietami, 10/2/3 train/val/test

**Sekcja 3.2 Pipeline ekstrakcji** — GOTOWA
- 3.2.1 MediaPipe Pose: porównanie COCO (17kp) / OpenPose BODY_25 (25kp) / BlazePose (33kp), opis x/y/z/visibility, model_complexity=2
- 3.2.2 Savitzky-Golay: problem jittera, mechanizm filtru (okno=11, wielomian 3. stopnia), interpolacja liniowa brakujących klatek, metryka jittera (std drugiej różnicy), wzory
- 3.2.3 Format wyjściowy: CSV, 132 kolumny keypointów

**Sekcja 3.3 Auto-etykietowanie faz** — GOTOWA
- 3.3.1 Odrzucone podejście: progowanie Y pięty (3 powody niepowodzenia)
- 3.3.2 Algorytm peak-based: sygnał kontaktu max(heel_y, foot_index_y), find_peaks (distance dynamiczny, prominence=0.03), alternacja L-R, podział STANCE/FLIGHT (flight_fraction=0.4), detekcja kierunku biegu, filtr medianowy kernel=3

**Wyjaśnienia pojęć** — dopisanych ~20 nowych wpisów do `2026-05-14-wyjasnienia-pojec-do-pisania.md`:
- estymowana głębia z, visibility, inferencja, jitter, filtr Savitzky-Golay, sygnał kinematyczny, interpolacja liniowa, metryka jittera, standard COCO, maxima/minima kontaktu stopy, prosta średnia ruchoma, wygładzanie x/y/z osobno, auto-etykietowanie peak-based, prominencja peaku, foot strike vs toe-off, filtr medianowy na etykietach

### Kluczowe poprawki z review usera
- Pisz w **pierwszej osobie** (zastosowałem, nie zastosowano) — cały rozdział
- Numeracja filmów **sekwencyjna 1–13** zamiast oryginalnych numerów plików
- Film 16 i 18 **usunięte** — nie były używane, nie wspominać
- OpenPose BODY_25 **ma** keypointy stopy (heel, big_toe, small_toe) — nie kłamać
- Kryteria doboru nagrań: **minimalne**, nie rygorystyczne (film 10 pionowy narusza "idealny" setup)
- Opisy filmów czytelne dla czytelnika (nie "R", "Sage Canaday", "Przejście chód-bieg")

### Stan plików
- `thesis/chapters/03-materialy-metody.tex` — sekcje 3.1–3.3 gotowe, 3.4–3.8 szkielet TODO
- `docs/thesis-notes/2026-05-14-wyjasnienia-pojec-do-pisania.md` — rozbudowany o ~20 pojęć

### Do zrobienia w następnej sesji
**Kontynuacja rozdziału 3**, od sekcji 3.4:
- 3.4 Architektury klasyfikatorów (RF raw/engineered, LSTM r1/r2, aspect fix)
- 3.5 Obliczanie współczynników (12 metryk, formuły)
- 3.6 Silnik reguł rekomendacji
- 3.7 Splity i metryki ewaluacji
