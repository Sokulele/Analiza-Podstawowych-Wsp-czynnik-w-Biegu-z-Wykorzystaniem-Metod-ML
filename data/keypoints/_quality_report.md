# Raport jakości ekstrakcji keypointów

Wygenerowano: 2026-04-15 22:48:57
Filmików: 9

## Klasyfikacja
- **OK**: detection_rate≥98%, vis≥0.7, low_vis<10%, FPS≥24
- **WARN**: detection_rate≥90%, vis≥0.5, low_vis<30%, FPS≥15
- **BAD**: poniżej progów WARN

## Podsumowanie per filmik

| Flag | Film | FPS | Czas [s] | Klatek | Detekcja | Vis kluczowych | Low vis | Jitter raw→smooth |
|------|------|-----|----------|--------|----------|----------------|---------|-------------------|
| OK | 01 - Slow Motion Treadmill Running - Shod Side View.mp4 | 29.97 | 31.66 | 949 | 100.0% | 0.97 | 0.0% | 0.01993 → 0.00284 (86%) |
| OK | 02 - Running at 13km⧸h - Side View.mp4 | 30.0 | 10.0 | 300 | 100.0% | 0.91 | 1.3% | 0.10625 → 0.01460 (86%) |
| OK | 03 - Running at 15km⧸h - Side View.mp4 | 30.0 | 10.0 | 300 | 100.0% | 0.88 | 5.4% | 0.02989 → 0.00926 (69%) |
| OK | 08 - Treadmill Running Technique - How to run safely on a treadmill.__segment_1__cropped.mp4 | 29.97 | 22.02 | 660 | 100.0% | 0.91 | 1.0% | 0.04240 → 0.00688 (84%) |
| OK | 08 - Treadmill Running Technique - How to run safely on a treadmill.__segment_2__cropped.mp4 | 29.97 | 10.01 | 300 | 100.0% | 0.92 | 0.9% | 0.03394 → 0.00535 (84%) |
| BAD | 09 - RUNNING FORM ANALYSIS AT MARATHON PACE： SAGE CANADAY TREADMILL TECHNIQUE__segment_3__cropped.mp4 | 29.97 | 49.98 | 1498 | 88.9% | 0.91 | 0.3% | 0.04539 → 0.00754 (83%) |
| BAD | 16 - Running at 5 m⧸s.mp4 | 13.333 | 60.0 | 800 | 100.0% | 0.91 | 1.1% | 0.07144 → 0.01022 (86%) |
| WARN | 18 - Running while wearing a hip exoskeleton ｜ Wearable Robotics ｜ Augmentation ｜ Biomechanics__segment_2__cropped.mp4 | 23.976 | 32.03 | 768 | 100.0% | 0.95 | 0.0% | 0.01218 → 0.00572 (53%) |
| OK | 20 - Transitioning from Walking to Running (0.8 to 3.5 m⧸s)__segment_1.mp4 | 30.0 | 29.0 | 870 | 100.0% | 0.95 | 0.0% | 0.02158 → 0.00499 (77%) |

## Metryki
- **detection_rate**: udział klatek, w których MediaPipe wykrył pozę
- **key_visibility_mean**: średnia visibility na kluczowych landmarkach (11,12,23-32)
- **key_low_visibility_ratio**: udział odczytów z visibility<0.5 na kluczowych
- **jitter**: std(drugiej różnicy) x,y — niższy = gładszy sygnał
- **jitter_reduction**: o ile % savgol obniżył jitter (wskaźnik skuteczności filtru)
