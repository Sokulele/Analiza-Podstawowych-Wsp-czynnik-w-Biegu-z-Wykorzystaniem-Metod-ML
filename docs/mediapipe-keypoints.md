# MediaPipe Pose — keypointy istotne dla analizy biegu

## Pełna lista 33 keypointów MediaPipe
Indeksy najważniejsze dla projektu oznaczone **[KLUCZOWY]**

| Index | Nazwa | Rola w projekcie |
|-------|-------|-----------------|
| 0 | NOSE | orientacja głowy |
| 11 | LEFT_SHOULDER | **[KLUCZOWY]** pochylenie tułowia |
| 12 | RIGHT_SHOULDER | **[KLUCZOWY]** pochylenie tułowia |
| 23 | LEFT_HIP | **[KLUCZOWY]** kąt biodra, vertical oscillation, overstriding |
| 24 | RIGHT_HIP | **[KLUCZOWY]** kąt biodra, vertical oscillation, overstriding |
| 25 | LEFT_KNEE | **[KLUCZOWY]** kąt kolana |
| 26 | RIGHT_KNEE | **[KLUCZOWY]** kąt kolana |
| 27 | LEFT_ANKLE | **[KLUCZOWY]** detekcja kontaktu z podłożem, kąt kostki |
| 28 | RIGHT_ANKLE | **[KLUCZOWY]** detekcja kontaktu z podłożem, kąt kostki |
| 29 | LEFT_HEEL | **[KLUCZOWY]** foot strike pattern, detekcja kontaktu |
| 30 | RIGHT_HEEL | **[KLUCZOWY]** foot strike pattern, detekcja kontaktu |
| 31 | LEFT_FOOT_INDEX | **[KLUCZOWY]** foot strike pattern |
| 32 | RIGHT_FOOT_INDEX | **[KLUCZOWY]** foot strike pattern |

## Uwagi
- Współrzędne znormalizowane do 0–1 (x: szerokość obrazu, y: wysokość obrazu)
- Z (głębokość) jest mniej wiarygodna z jednej kamery — używaj ostrożnie
- Visibility < 0.5 oznacza niską pewność detekcji — oznacz te klatki jako niepewne
- Przy ujęciu z boku: bliższa noga (do kamery) jest bardziej wiarygodna niż dalsza
