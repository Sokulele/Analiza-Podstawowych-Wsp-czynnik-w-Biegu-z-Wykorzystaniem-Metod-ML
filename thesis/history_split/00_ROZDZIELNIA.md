# Rozdzielnia dla `history.md`

Krótki router dla agenta AI: **nie czytaj całego `history.md`**. Najpierw sprawdź tę rozdzielnię, wybierz 1–3 najbardziej pasujące pliki i dopiero je otwórz.

## Jak używać

1. Znajdź temat w tabeli lub w sekcji „Szybkie ścieżki”.
2. Otwórz wskazany plik sesyjny.
3. Gdy potrzebujesz kontekstu poprzedzającego, otwórz maksymalnie jeden plik wcześniejszy z tego samego etapu.

## Szybkie ścieżki

- **Ekstrakcja keypointów / MediaPipe / jakość wideo** → [01](./01_2026-04-15-etap-2-ekstrakcja-keypointow.md)
- **Auto-etykietowanie faz biegu** → [02](./02_2026-04-16-etap-3-auto-etykietowanie-test-na-filmie-02.md), [03](./03_2026-04-20-etap-3-dokonczony-audyt-datasetu-auto-etykietowanie-wszystkich-filmow.md)
- **Split danych i Random Forest** → [04](./04_2026-04-24-etap-5-czesc-1-split-datasetu-random-forest-baseline.md), [05](./05_2026-04-24-etap-5-czesc-2-rf-z-cechami-inzynierowanymi-folder-notatek-magisterskich.md)
- **LSTM / BiLSTM / wybór modelu** → [06](./06_2026-04-26-etap-5-czesc-3-bilstm-model-docelowy.md), [08](./08_2026-05-08-rozszerzenie-datasetu-o-2-biegaczy-23-24-retrening-4-modeli.md), [09](./09_2026-05-08-plan-poprawy-accuracy-lstm-r1-aspect-fix-to-70-9-test-acc-prog-70-przekroczony.md)
- **Porównanie modeli, macierze pomyłek, rozdział 5.4** → [07](./07_2026-04-26-etap-5-4-analiza-porownawcza-4-modeli.md), [08](./08_2026-05-08-rozszerzenie-datasetu-o-2-biegaczy-23-24-retrening-4-modeli.md), [09](./09_2026-05-08-plan-poprawy-accuracy-lstm-r1-aspect-fix-to-70-9-test-acc-prog-70-przekroczony.md)
- **Aspect ratio fix i wynik 70.9%** → [09](./09_2026-05-08-plan-poprawy-accuracy-lstm-r1-aspect-fix-to-70-9-test-acc-prog-70-przekroczony.md)
- **Pipeline współczynników biomechanicznych** → [10](./10_2026-05-09-etap-6-mvp-pipeline-wspo-czynnikow-biegu-test-na-adamie.md), [11](./11_2026-05-09-iteracja-1-pipeline-na-test-set-raporty-z-porownaniem-do-referencji.md), [14](./14_2026-05-13-sesja-b-czesc-1-stride-length-combinatorical-low-quality.md)
- **Raporty Markdown i quality gate** → [11](./11_2026-05-09-iteracja-1-pipeline-na-test-set-raporty-z-porownaniem-do-referencji.md), [13](./13_2026-05-13-sesja-a-integracja-etapu-7-z-analyze-py.md), [14](./14_2026-05-13-sesja-b-czesc-1-stride-length-combinatorical-low-quality.md)
- **Rekomendacje biegowe** → [12](./12_2026-05-12-etap-7-modu-rekomendacji-biegowych.md), [13](./13_2026-05-13-sesja-a-integracja-etapu-7-z-analyze-py.md)
- **Foot strike pattern** → [15](./15_2026-05-14-sesja-c-walidacja-foot-strike-pattern.md)
- **Problem badawczy, tytuł pracy, literatura** → [16](./16_2026-05-14-sesja-c-czesc-2-research-literatury-wybor-problemu-badawczego.md), [17](./17_2026-05-14-sesja-c-czesc-3-finalizacja-tytu-u-pracy.md), [18](./18_2026-05-23-sesja-d-setup-latex-bibliografii-plan-pisania.md)
- **Pisanie rozdziału 3** → [19](./19_2026-05-23-sesja-e-pisanie-rozdzia-u-3-sekcje-3-1-3-3.md)

## Mapa plików

| # | Plik | Co zawiera | Słowa kluczowe |
|---:|---|---|---|
| 01 | [`01_2026-04-15-etap-2-ekstrakcja-keypointow.md`](./01_2026-04-15-etap-2-ekstrakcja-keypointow.md) | Ekstrakcja keypointów, środowisko, MediaPipe, jakość filmów 01/09/16 | keypoints, MediaPipe, extract_keypoints, jakość wideo, film 09, film 16 |
| 02 | [`02_2026-04-16-etap-3-auto-etykietowanie-test-na-filmie-02.md`](./02_2026-04-16-etap-3-auto-etykietowanie-test-na-filmie-02.md) | Pierwszy test auto-etykietowania na filmie 02 i wybór algorytmu peak-based | auto_label, phase, peak-based, film 02, GCT, FLIGHT |
| 03 | [`03_2026-04-20-etap-3-dokonczony-audyt-datasetu-auto-etykietowanie-wszystkich-filmow.md`](./03_2026-04-20-etap-3-dokonczony-audyt-datasetu-auto-etykietowanie-wszystkich-filmow.md) | Dokończenie auto-etykietowania, audyt datasetu, segmentacja filmu 09, finalny dataset 13 filmów | dataset, film 09, film 16, etykiety, training set, split |
| 04 | [`04_2026-04-24-etap-5-czesc-1-split-datasetu-random-forest-baseline.md`](./04_2026-04-24-etap-5-czesc-1-split-datasetu-random-forest-baseline.md) | Split train/val/test i pierwszy baseline Random Forest na surowych keypointach | Random Forest, RF baseline, split_data, metrics, confusion matrix |
| 05 | [`05_2026-04-24-etap-5-czesc-2-rf-z-cechami-inzynierowanymi-folder-notatek-magisterskich.md`](./05_2026-04-24-etap-5-czesc-2-rf-z-cechami-inzynierowanymi-folder-notatek-magisterskich.md) | RF v2 z cechami inżynierowanymi, normalizacja względem biegacza, wnioski do pracy | engineered features, normalizacja, kąty stawów, RF v2, aspect ratio |
| 06 | [`06_2026-04-26-etap-5-czesc-3-bilstm-model-docelowy.md`](./06_2026-04-26-etap-5-czesc-3-bilstm-model-docelowy.md) | BiLSTM, dwa runy, wybór LSTM run 2 jako primary przed późniejszymi zmianami | BiLSTM, LSTM, run 1, run 2, primary, PyTorch |
| 07 | [`07_2026-04-26-etap-5-4-analiza-porownawcza-4-modeli.md`](./07_2026-04-26-etap-5-4-analiza-porownawcza-4-modeli.md) | Analiza porównawcza 4 modeli i artefakty do rozdziału 5.4 | compare_models, rozdział 5.4, macierze pomyłek, feature importances, learning curves |
| 08 | [`08_2026-05-08-rozszerzenie-datasetu-o-2-biegaczy-23-24-retrening-4-modeli.md`](./08_2026-05-08-rozszerzenie-datasetu-o-2-biegaczy-23-24-retrening-4-modeli.md) | Rozszerzenie datasetu o Pawła i Adama, retrening modeli, wpływ większego train setu | Pawel, Adam, dataset extension, retraining, 5.5 |
| 09 | [`09_2026-05-08-plan-poprawy-accuracy-lstm-r1-aspect-fix-to-70-9-test-acc-prog-70-przekroczony.md`](./09_2026-05-08-plan-poprawy-accuracy-lstm-r1-aspect-fix-to-70-9-test-acc-prog-70-przekroczony.md) | Plan poprawy accuracy, testy augmentacji/median/velocity/ensemble/aspect fix, osiągnięcie 70.9% | accuracy, aspect fix, augmentacja, velocity, ensemble, 70.9 |
| 10 | [`10_2026-05-09-etap-6-mvp-pipeline-wspo-czynnikow-biegu-test-na-adamie.md`](./10_2026-05-09-etap-6-mvp-pipeline-wspo-czynnikow-biegu-test-na-adamie.md) | Etap 6 MVP: pipeline współczynników biegu i test end-to-end na Adamie | coefficients, MVP, temporal_metrics, spatial_metrics, symmetry, Adam |
| 11 | [`11_2026-05-09-iteracja-1-pipeline-na-test-set-raporty-z-porownaniem-do-referencji.md`](./11_2026-05-09-iteracja-1-pipeline-na-test-set-raporty-z-porownaniem-do-referencji.md) | Iteracja 1: test pipeline na test set, raporty Markdown, jakość downstream metryk | raporty, reference_values, analyze.py, low quality, test set |
| 12 | [`12_2026-05-12-etap-7-modu-rekomendacji-biegowych.md`](./12_2026-05-12-etap-7-modu-rekomendacji-biegowych.md) | Etap 7: moduł rekomendacji biegowych oparty o reguły literaturowe | recommendations, rules.py, Heiderscheit, Novacheck, Daoud, Janek |
| 13 | [`13_2026-05-13-sesja-a-integracja-etapu-7-z-analyze-py.md`](./13_2026-05-13-sesja-a-integracja-etapu-7-z-analyze-py.md) | Integracja rekomendacji z analyze.py, raport końcowy i quality gate | integracja, analyze.py, quality gate, raport, recommendations |
| 14 | [`14_2026-05-13-sesja-b-czesc-1-stride-length-combinatorical-low-quality.md`](./14_2026-05-13-sesja-b-czesc-1-stride-length-combinatorical-low-quality.md) | Stride length, combinatorial low quality detection i parametry prędkości bieżni | stride length, treadmill speed, low quality, stable segments |
| 15 | [`15_2026-05-14-sesja-c-walidacja-foot-strike-pattern.md`](./15_2026-05-14-sesja-c-walidacja-foot-strike-pattern.md) | Walidacja foot strike pattern, poprawki algorytmu i wyniki | foot strike, heel, midfoot, forefoot, walidacja |
| 16 | [`16_2026-05-14-sesja-c-czesc-2-research-literatury-wybor-problemu-badawczego.md`](./16_2026-05-14-sesja-c-czesc-2-research-literatury-wybor-problemu-badawczego.md) | Research literatury i wybór problemu badawczego pracy magisterskiej | literatura, problem badawczy, research gap, praca magisterska |
| 17 | [`17_2026-05-14-sesja-c-czesc-3-finalizacja-tytu-u-pracy.md`](./17_2026-05-14-sesja-c-czesc-3-finalizacja-tytu-u-pracy.md) | Finalizacja tytułu pracy, zakresu i narracji badawczej | tytuł pracy, zakres, narracja, magisterka |
| 18 | [`18_2026-05-23-sesja-d-setup-latex-bibliografii-plan-pisania.md`](./18_2026-05-23-sesja-d-setup-latex-bibliografii-plan-pisania.md) | Setup LaTeX bibliografii, struktura pracy i plan pisania | LaTeX, bibliografia, bibliography.tex, plan pisania, rozdziały |
| 19 | [`19_2026-05-23-sesja-e-pisanie-rozdzia-u-3-sekcje-3-1-3-3.md`](./19_2026-05-23-sesja-e-pisanie-rozdzia-u-3-sekcje-3-1-3-3.md) | Pisanie rozdziału 3: sekcje 3.1–3.3, metodologia i treść pracy | rozdział 3, metodologia, sekcje 3.1-3.3, pisanie |

## Indeks etapów

- **Etap 2–3: dane, keypointy, etykiety** → [01](./01_2026-04-15-etap-2-ekstrakcja-keypointow.md), [02](./02_2026-04-16-etap-3-auto-etykietowanie-test-na-filmie-02.md), [03](./03_2026-04-20-etap-3-dokonczony-audyt-datasetu-auto-etykietowanie-wszystkich-filmow.md)
- **Etap 5: modele i eksperymenty** → [04](./04_2026-04-24-etap-5-czesc-1-split-datasetu-random-forest-baseline.md), [05](./05_2026-04-24-etap-5-czesc-2-rf-z-cechami-inzynierowanymi-folder-notatek-magisterskich.md), [06](./06_2026-04-26-etap-5-czesc-3-bilstm-model-docelowy.md), [07](./07_2026-04-26-etap-5-4-analiza-porownawcza-4-modeli.md), [08](./08_2026-05-08-rozszerzenie-datasetu-o-2-biegaczy-23-24-retrening-4-modeli.md), [09](./09_2026-05-08-plan-poprawy-accuracy-lstm-r1-aspect-fix-to-70-9-test-acc-prog-70-przekroczony.md)
- **Etap 6: współczynniki i raporty** → [10](./10_2026-05-09-etap-6-mvp-pipeline-wspo-czynnikow-biegu-test-na-adamie.md), [11](./11_2026-05-09-iteracja-1-pipeline-na-test-set-raporty-z-porownaniem-do-referencji.md), [14](./14_2026-05-13-sesja-b-czesc-1-stride-length-combinatorical-low-quality.md)
- **Etap 7: rekomendacje** → [12](./12_2026-05-12-etap-7-modu-rekomendacji-biegowych.md), [13](./13_2026-05-13-sesja-a-integracja-etapu-7-z-analyze-py.md)
- **Walidacje specjalne** → [15](./15_2026-05-14-sesja-c-walidacja-foot-strike-pattern.md)
- **Praca magisterska: problem, tytuł, bibliografia, pisanie** → [16](./16_2026-05-14-sesja-c-czesc-2-research-literatury-wybor-problemu-badawczego.md), [17](./17_2026-05-14-sesja-c-czesc-3-finalizacja-tytu-u-pracy.md), [18](./18_2026-05-23-sesja-d-setup-latex-bibliografii-plan-pisania.md), [19](./19_2026-05-23-sesja-e-pisanie-rozdzia-u-3-sekcje-3-1-3-3.md)

## Zasada dla kolejnego agenta

> Gdy pytanie dotyczy konkretnego tematu, otwieraj tylko pliki z rozdzielni. Nie wczytuj pełnego `history.md`, chyba że pytanie wymaga audytu całej historii projektu.
