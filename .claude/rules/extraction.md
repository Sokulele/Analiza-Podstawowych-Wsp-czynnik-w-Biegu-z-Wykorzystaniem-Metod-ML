---
globs: src/extraction/**
---

# Ekstrakcja keypointów

## MediaPipe Pose
- Używaj `mp.solutions.pose.Pose(static_image_mode=False, model_complexity=2)` — model_complexity=2 daje najdokładniejsze keypoints
- Dla każdej klatki zapisuj: numer klatki, timestamp, 33 keypointy (x, y, z, visibility)
- Keypointy normalizowane (0-1) — to jest domyślne zachowanie MediaPipe
- FPS odczytuj z `cv2.VideoCapture.get(cv2.CAP_PROP_FPS)`

## Wygładzanie
- Savitzky-Golay filter (scipy.signal.savgol_filter) — window_length=11, polyorder=3 jako punkt startowy
- Wygładzaj OSOBNO x, y, z dla każdego keypointu
- Wygładzaj DOPIERO po ekstrakcji wszystkich klatek, nie w trakcie

## Format wyjściowy
- CSV z kolumnami: frame, timestamp, {keypoint_name}_{x|y|z|visibility} dla każdego z 33 keypointów
- Jeden plik CSV na filmik
