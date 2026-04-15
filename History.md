# Historia sesji

Log pracy między sesjami — krótki recap + kontekst do kontynuacji.

---

## 2026-04-15 — Etap 2: Ekstrakcja keypointów ✅

### Zrobione
- **Środowisko**: utworzony `.venv/` (Python 3.11), plik `requirements.txt`, `.gitignore`
  - Kluczowe: `mediapipe==0.10.14` (ostatnia z legacy `mp.solutions.pose` API wymaganego przez CLAUDE.md; 0.10.21+ ma tylko nowe Tasks API)
- **Skrypty**:
  - `src/extraction/probe_videos.py` — sonduje metadane wideo → `data/videos_metadata.csv`
  - `src/extraction/extract_keypoints.py` — MediaPipe Pose (complexity=2) + Savitzky-Golay (window=11, polyorder=3) + raport jakości
- **Wyjście**: 9 CSV w `data/keypoints/` (135 kolumn: frame, timestamp, pose_detected + 33×{x,y,z,visibility}), raport w `_quality_report.{csv,md}`
- **Metryki**: filtr savgol redukuje jitter o 53–86%

### Stan datasetu (9 filmików)
| Flag | Filmiki |
|------|---------|
| OK (6) | 01, 02, 03, 08×2, 20 — detection 100%, vis 0.88–0.97 |
| WARN (1) | 18 (exoskeleton) — FPS 23.98 |
| **BAD (2)** | **09** Sage Canaday (detection 88.9%, 166 klatek bez pozy), **16** (FPS 13.33 — za niski do precyzyjnego GCT) |

### Znane pułapki
- **Film 01** to slow-motion — kadencja/GCT wyjdą zaniżone bez znajomości rzeczywistego współczynnika spowolnienia
- **Film 09** — brakujące detekcje wymagają zbadania (czy zgrupowane, czy rozproszone → czy da się wyciąć problematyczny fragment)
- **Film 16** — 13 FPS daje błąd kwantyzacji ~15% na czasie kontaktu; kandydat do test-set lub odrzucenia
- Nazwy plików zawierają Unicode (`⧸`, `｜`) — trzeba `sys.stdout.reconfigure(encoding="utf-8")` na Windows (już w skryptach)

### Do zrobienia w następnej sesji — Etap 3: Auto-etykietowanie
Plan: `src/labeling/auto_label.py` wg reguł z `.claude/rules/labeling.md`:
1. Wyznaczyć `ground_level` per filmik (mediana Y stopy w najniższych 10% klatek)
2. Klasyfikacja faz: `LEFT_STANCE` / `RIGHT_STANCE` / `FLIGHT` / `DOUBLE_SUPPORT` na podstawie Y_heel vs ground_level + threshold
3. Filtr medianowy (kernel=5) na sekwencji etykiet — przeciw migotaniu
4. Detekcja kierunku biegu (L/P może być zamienione)
5. Dopisać kolumny `phase_auto` i `phase` do istniejących CSV w `data/keypoints/`

Przed startem: sprawdzić dla 09 czy brakujące klatki są zgrupowane; zdecydować co zrobić z filmikami 09 i 16 (wyciąć fragment / odrzucić / zostawić jako test).

### Odkładane decyzje
- Czy wersjonować `data/keypoints/` (14 MB) czy dodać do .gitignore + LFS
- Czy generować wizualną weryfikację (szkielet na klatkach) — plan.md etap 2 to wymienia, ale zostawiłem na potem
