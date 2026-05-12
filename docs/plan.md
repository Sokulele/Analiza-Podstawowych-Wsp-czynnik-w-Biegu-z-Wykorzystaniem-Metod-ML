# Plan pracy — etapy projektu

## Etap 1: Przygotowanie datasetu ✅
- [x] Zebranie filmików z YouTube (bieżnia, profil, cała sylwetka) — 14 filmów (+ segmenty)
- [x] Pobranie filmików za pomocą yt-dlp do data/videos/
- [x] Weryfikacja jakości: FPS, rozdzielczość, widoczność nóg
- [x] Audyt datasetu: film 09 pocięty (luka bez detekcji), film 16 → test_edge_cases

## Etap 2: Ekstrakcja keypointów ✅
- [x] Skrypt: src/extraction/extract_keypoints.py
- [x] Przetworzenie wszystkich filmików → CSV w data/keypoints/
- [x] Wizualna weryfikacja keypointów na kilku klatkach — src/visualization/render_frames.py
- [x] Wygładzenie sygnału (Savitzky-Golay) — redukcja jittera 53–86%

## Etap 3: Auto-etykietowanie ✅
- [x] Skrypt: src/labeling/auto_label.py (algorytm peak-based)
- [x] Test na filmie 02 — kadencja 162 spm, 0 direct L↔R, wyniki zgodne z literaturą
- [x] Uruchomienie na wszystkich 13 filmach — 0 direct L↔R, 0 zmian filtra medianowego
- [x] Film 09: pocięty na 2 czyste segmenty (ffmpeg), oba OK
- [x] Film 16: przeniesiony do test_edge_cases (13 FPS)
- [x] Finalny dataset: 13 filmów, 8039 klatek, ~33/32/34% rozkład klas

## Etap 4: Korekta ręczna etykiet — POMINIĘTY
Algorytm peak-based okazał się wystarczająco czysty (0 zmian filtra medianowego, 0 direct L↔R we wszystkich filmach). Korekta ręczna niepotrzebna na tym etapie. Jeśli model będzie słaby → wrócić.

## Etap 5: Trenowanie klasyfikatora
- [ ] Podział danych: train/val/test (per filmik, nie per klatka!)
- [ ] Baseline: Random Forest — src/training/train_rf.py
- [ ] Primary: LSTM — src/training/train_lstm.py
- [ ] Porównanie metryk (accuracy, confusion matrix, F1 per klasa)

## Etap 6: Obliczanie współczynników
- [ ] Skrypt: src/coefficients/calculate.py
- [ ] Implementacja wszystkich współczynników (fazy + keypointy)
- [ ] Testowanie na znanych filmikach — porównanie z ręcznymi pomiarami

## Etap 7: Rekomendacje
- [ ] Skrypt: src/recommendations/recommend.py
- [ ] Reguły na podstawie docs/reference-values.md
- [ ] Generowanie raportu tekstowego dla użytkownika

## Etap 8: Walidacja i dokumentacja
- [ ] Walidacja end-to-end na nowych filmikach
- [ ] Opis metodologii do pracy magisterskiej
- [ ] Wizualizacje i wykresy do pracy
