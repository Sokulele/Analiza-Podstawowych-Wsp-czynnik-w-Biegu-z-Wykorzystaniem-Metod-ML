# Analiza Podstawowych Współczynników Biegu z Wykorzystaniem Metod ML

## Projekt

Praca magisterska. System analizujący wideo biegu na bieżni i obliczający współczynniki biomechaniczne z rekomendacjami poprawy formy.

## Pipeline

```
Wideo (bieżnia, ujęcie z boku) → MediaPipe Pose (33 keypointy) → Klasyfikator faz → Obliczenie współczynników → Rekomendacje
```

## Architektura

### Fazy biegu (klasy klasyfikatora)

- `LEFT_STANCE` — lewa stopa na ziemi
- `RIGHT_STANCE` — prawa stopa na ziemi
- `FLIGHT` — obie stopy w powietrzu
- `DOUBLE_SUPPORT` — obie na ziemi (rzadkie przy biegu)

### Współczynniki do obliczenia

**Z faz (sekwencja etykiet + FPS):** kadencja, czas kontaktu, czas lotu, stride length, duty factor
**Z keypointów (geometria):** kąty kolana/biodra/kostki, pochylenie tułowia, vertical oscillation, overstriding, foot strike pattern, symetria L/P

### Modele ML

- Baseline: Random Forest na wektorze keypointów z jednej klatki
- Primary: LSTM lub 1D CNN na sekwencji klatek (okno czasowe)

### WAŻNE: Rozdzielenie trenowania od inferencji

**Trenowanie modelu** i **obliczanie współczynników** to DWA OSOBNE etapy. Nie mieszaj ich.

**Etap trenowania (na datasecie):**

- Cel: nauczyć model klasyfikować fazę biegu (LEFT_STANCE / RIGHT_STANCE / FLIGHT / DOUBLE_SUPPORT) na podstawie keypointów
- Input: keypointy z MediaPipe, output: etykieta fazy
- FPS filmiku, slow-motion, prędkość bieżni — NIE MAJĄ ZNACZENIA. Model uczy się rozpoznawać pozycję ciała, nie czas.
- Filmiki slow-motion są pełnoprawnym materiałem treningowym — więcej klatek na cykl = precyzyjniejsze etykiety
- Na filmikach treningowych NIE obliczamy współczynników biegu

**Etap inferencji (na nowym wideo od użytkownika):**

- Użytkownik wrzuca swój filmik nagrany w normalnej prędkości
- Model klasyfikuje fazy → z sekwencji faz + FPS filmu obliczamy współczynniki
- Tutaj FPS JEST krytyczny (musi być znany i poprawny)
- Tutaj prędkość bieżni jest potrzebna (do stride length)

### Rekomendacje

Reguły kodowane ręcznie na podstawie literatury biomechanicznej — NIE uczone z danych.

## Struktura katalogów

```
/data/
  /videos/          — surowe filmiki (.mp4)
  /keypoints/        — wyekstrahowane keypointy (CSV/JSON)
  /labels/           — etykiety faz biegu
/src/
  /extraction/       — ekstrakcja keypointów (MediaPipe)
  /labeling/         — auto-etykietowanie + narzędzia korekty
  /training/         — trenowanie klasyfikatorów
  /coefficients/     — obliczanie współczynników biegu
  /recommendations/  — reguły rekomendacji
/models/             — wytrenowane modele
/docs/               — dokumentacja, notatki, literatura
```

## Zasady kodowania

- Język: Python 3.10+
- Komentarze w kodzie: po polsku
- Nazwy zmiennych/funkcji/klas: po angielsku (snake_case dla funkcji, PascalCase dla klas)
- Docstringi: po polsku, krótkie
- Każdy skrypt musi być uruchamialny standalone z `if __name__ == "__main__"`
- Logowanie: moduł `logging`, nie `print()` (poza szybkim debugowaniem)
- Dane wejściowe/wyjściowe: ścieżki jako argumenty CLI (argparse)

## Kluczowe zależności

- mediapipe — ekstrakcja keypointów
- opencv-python — operacje na wideo/klatkach
- pandas, numpy — dane tabelaryczne, obliczenia
- scikit-learn — Random Forest, metryki
- torch lub tensorflow — LSTM/CNN (do ustalenia)
- scipy — filtry wygładzające (Savitzky-Golay)
- matplotlib — wizualizacje

## Ważne konteksty

- Filmiki w datasecie: ujęcie z boku, bieżnia mechaniczna, cała sylwetka, min 10s ciągłego biegu
- MediaPipe keypoints skaczą (szum) — ZAWSZE wygładzaj sygnał przed obliczeniami
- FPS filmiku jest krytyczny dla precyzji obliczeń czasowych — zawsze odczytuj z metadanych wideo, nie zakładaj
- Stride length wymaga podania prędkości bieżni przez użytkownika (nie da się wyliczyć z samego wideo)

## Czego NIE robić

- Nie twórz modelu end-to-end (wideo → współczynniki) — za mało danych
- Nie ucz rekomendacji z danych — to reguły z literatury
- Nie zakładaj stałego FPS — odczytuj z wideo
- Nie ignoruj szumu MediaPipe — zawsze filtruj
