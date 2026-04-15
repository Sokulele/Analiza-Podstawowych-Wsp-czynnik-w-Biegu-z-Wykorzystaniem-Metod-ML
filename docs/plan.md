# Plan pracy — etapy projektu

## Etap 1: Przygotowanie datasetu
- [ ] Zebranie 15-20 filmików z YouTube (bieżnia, profil, cała sylwetka)
- [ ] Pobranie filmików za pomocą yt-dlp do data/videos/
- [ ] Weryfikacja jakości: FPS, rozdzielczość, widoczność nóg

## Etap 2: Ekstrakcja keypointów
- [ ] Skrypt: src/extraction/extract_keypoints.py
- [ ] Przetworzenie wszystkich filmików → CSV w data/keypoints/
- [ ] Wizualna weryfikacja keypointów na kilku klatkach (nałożenie szkieletu na obraz)
- [ ] Wygładzenie sygnału (Savitzky-Golay)

## Etap 3: Auto-etykietowanie
- [ ] Skrypt: src/labeling/auto_label.py
- [ ] Wyznaczenie poziomu podłoża dla każdego filmiku
- [ ] Automatyczne etykietowanie faz biegu
- [ ] Filtr medianowy na sekwencji etykiet

## Etap 4: Korekta ręczna etykiet
- [ ] Skrypt/narzędzie: src/labeling/label_viewer.py (wizualizacja klatka po klatce z etykietą)
- [ ] Przejrzenie i korekta problematycznych fragmentów
- [ ] Zapisanie finalnych etykiet do data/labels/

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
