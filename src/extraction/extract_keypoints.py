"""Ekstrakcja keypointów z filmików za pomocą MediaPipe Pose + wygładzanie (Savitzky-Golay).

Dla każdego filmiku w katalogu produkuje jeden CSV w katalogu wyjściowym,
z kolumnami: frame, timestamp, pose_detected, oraz 33 keypointy × (x, y, z, visibility).
"""
import argparse
import logging
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

# Wymuszamy UTF-8 na stdout — nazwy plików mogą zawierać Unicode (⧸, ｜)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

POSE = mp.solutions.pose
LANDMARK_NAMES = [lm.name for lm in POSE.PoseLandmark]  # 33 nazwy w kolejności indeksów
ATTRS = ("x", "y", "z", "visibility")

# Kluczowe landmarki dla biegu (zgodnie z docs/mediapipe-keypoints.md)
KEY_LANDMARK_INDICES = [11, 12, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]


@dataclass
class ExtractionQuality:
    """Miary jakości ekstrakcji dla jednego filmiku."""
    video: str
    fps: float
    duration_s: float
    frames_total: int
    frames_with_pose: int
    detection_rate: float                       # udział klatek z wykrytą pozą
    key_visibility_mean: float                  # średnia visibility na kluczowych landmarkach
    key_low_visibility_ratio: float             # % klatek z vis<0.5 na kluczowych
    jitter_raw: float                           # std(drugiej różnicy) x,y — surowe
    jitter_smoothed: float                      # std(drugiej różnicy) x,y — po savgol
    jitter_reduction_pct: float                 # % redukcji jittera
    quality_flag: str                           # OK / WARN / BAD (heurystyka)


def extract_one_video(
    video_path: Path,
    output_csv: Path,
    savgol_window: int = 11,
    savgol_polyorder: int = 3,
    model_complexity: int = 2,
) -> ExtractionQuality:
    """Ekstrahuje keypointy z jednego filmiku, wygładza i zapisuje do CSV."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Nie można otworzyć wideo: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    log.info("[%s] FPS=%.2f, klatek=%d, complexity=%d",
             video_path.name, fps, frame_count, model_complexity)

    # Macierz wyników: (frames, 33_landmarks, 4_attrs)
    data = np.full((frame_count, 33, 4), np.nan, dtype=np.float64)
    pose_detected = np.zeros(frame_count, dtype=bool)

    pose = POSE.Pose(static_image_mode=False, model_complexity=model_complexity)
    t0 = time.time()
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret or idx >= frame_count:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = pose.process(rgb)
        if result.pose_landmarks is not None:
            pose_detected[idx] = True
            for i, lm in enumerate(result.pose_landmarks.landmark):
                data[idx, i, 0] = lm.x
                data[idx, i, 1] = lm.y
                data[idx, i, 2] = lm.z
                data[idx, i, 3] = lm.visibility
        idx += 1
    pose.close()
    cap.release()

    actual_frames = idx
    data = data[:actual_frames]
    pose_detected = pose_detected[:actual_frames]

    elapsed = time.time() - t0
    log.info("[%s] MediaPipe: %d/%d klatek z pozą, czas %.1fs",
             video_path.name, int(pose_detected.sum()), actual_frames, elapsed)

    # Jitter raw — przed wygładzeniem
    jitter_raw = _compute_jitter(data, KEY_LANDMARK_INDICES)

    # Wygładzanie: savgol na x, y, z — osobno dla każdego landmarku
    # Visibility nie wygładzamy (to miara pewności, nie sygnał kinematyczny)
    smoothed = _smooth_keypoints(data, savgol_window, savgol_polyorder)

    jitter_smoothed = _compute_jitter(smoothed, KEY_LANDMARK_INDICES)

    # Zapis keypointów do CSV (wygładzonych — zgodnie z CLAUDE.md)
    df = _build_dataframe(smoothed, pose_detected, fps)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False, encoding="utf-8")
    log.info("[%s] Zapisano %s", video_path.name, output_csv.name)

    # Miary jakości
    key_vis = data[:, KEY_LANDMARK_INDICES, 3]
    has_pose = pose_detected.any()
    key_visibility_mean = float(np.nanmean(key_vis)) if has_pose else 0.0
    key_low_visibility_ratio = float(np.nanmean((key_vis < 0.5).astype(float))) if has_pose else 1.0
    detection_rate = float(pose_detected.mean())
    jitter_reduction = (
        100.0 * (jitter_raw - jitter_smoothed) / jitter_raw
        if jitter_raw > 0 else 0.0
    )

    quality_flag = _classify_quality(
        detection_rate, key_visibility_mean, key_low_visibility_ratio, fps,
    )

    return ExtractionQuality(
        video=video_path.name,
        fps=round(float(fps), 3),
        duration_s=round(actual_frames / fps if fps > 0 else 0.0, 2),
        frames_total=actual_frames,
        frames_with_pose=int(pose_detected.sum()),
        detection_rate=round(detection_rate, 3),
        key_visibility_mean=round(key_visibility_mean, 3),
        key_low_visibility_ratio=round(key_low_visibility_ratio, 3),
        jitter_raw=round(float(jitter_raw), 5),
        jitter_smoothed=round(float(jitter_smoothed), 5),
        jitter_reduction_pct=round(jitter_reduction, 1),
        quality_flag=quality_flag,
    )


def _smooth_keypoints(data: np.ndarray, window: int, polyorder: int) -> np.ndarray:
    """Wygładza x, y, z każdego landmarku filtrem Savitzky-Golay.

    Braki detekcji (NaN) wypełnia interpolacją liniową przed wygładzeniem.
    """
    n = data.shape[0]
    if n < polyorder + 2:
        log.warning("Za mało klatek (%d) na savgol — zwracam surowe dane", n)
        return data

    # Window musi być nieparzyste i <= liczbie klatek
    win = min(window, n if n % 2 == 1 else n - 1)
    if win % 2 == 0:
        win -= 1
    if win < polyorder + 2:
        log.warning("Window (%d) za mały dla polyorder=%d — pomijam wygładzanie", win, polyorder)
        return data

    smoothed = data.copy()
    for lm_i in range(33):
        for attr_i in range(3):  # x, y, z — bez visibility
            series = pd.Series(data[:, lm_i, attr_i])
            if series.isna().all():
                continue  # kompletnie brak detekcji dla tego kanału
            # interpolacja liniowa + brzegi (ffill/bfill)
            filled = series.interpolate(limit_direction="both").to_numpy()
            smoothed[:, lm_i, attr_i] = savgol_filter(
                filled, window_length=win, polyorder=polyorder
            )
    return smoothed


def _compute_jitter(data: np.ndarray, indices: list[int]) -> float:
    """Średni jitter = std(drugiej różnicy) w x, y dla kluczowych landmarków.

    Niskie wartości = gładki sygnał, wysokie = "drżenie" / szum.
    """
    values = []
    for lm_i in indices:
        for attr_i in range(2):  # x, y
            series = data[:, lm_i, attr_i]
            valid = series[~np.isnan(series)]
            if valid.size < 3:
                continue
            diff2 = np.diff(valid, n=2)
            values.append(float(np.std(diff2)))
    return float(np.mean(values)) if values else float("nan")


def _build_dataframe(data: np.ndarray, pose_detected: np.ndarray, fps: float) -> pd.DataFrame:
    """Buduje DataFrame z keypointami: frame, timestamp, pose_detected + 33×4 kolumn."""
    n = data.shape[0]
    frames = np.arange(n, dtype=int)
    timestamps = frames / fps if fps > 0 else np.zeros(n)
    cols: dict = {
        "frame": frames,
        "timestamp": np.round(timestamps, 4),
        "pose_detected": pose_detected.astype(int),
    }
    for i, name in enumerate(LANDMARK_NAMES):
        for j, attr in enumerate(ATTRS):
            cols[f"{name}_{attr}"] = data[:, i, j]
    return pd.DataFrame(cols)


def _classify_quality(
    detection_rate: float,
    key_vis_mean: float,
    low_vis_ratio: float,
    fps: float,
) -> str:
    """Heurystyczna klasyfikacja: OK / WARN / BAD."""
    if detection_rate < 0.9 or key_vis_mean < 0.5 or low_vis_ratio > 0.3 or fps < 15:
        return "BAD"
    if detection_rate < 0.98 or key_vis_mean < 0.7 or low_vis_ratio > 0.1 or fps < 24:
        return "WARN"
    return "OK"


def _write_quality_report(
    qualities: list[ExtractionQuality],
    csv_path: Path,
    md_path: Path,
) -> None:
    """Zapisuje raport jakości w formacie CSV oraz czytelnym Markdown."""
    qdf = pd.DataFrame([asdict(q) for q in qualities])
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    qdf.to_csv(csv_path, index=False, encoding="utf-8")

    lines = [
        "# Raport jakości ekstrakcji keypointów",
        "",
        f"Wygenerowano: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Filmików: {len(qualities)}",
        "",
        "## Klasyfikacja",
        "- **OK**: detection_rate≥98%, vis≥0.7, low_vis<10%, FPS≥24",
        "- **WARN**: detection_rate≥90%, vis≥0.5, low_vis<30%, FPS≥15",
        "- **BAD**: poniżej progów WARN",
        "",
        "## Podsumowanie per filmik",
        "",
        "| Flag | Film | FPS | Czas [s] | Klatek | Detekcja | Vis kluczowych | Low vis | Jitter raw→smooth |",
        "|------|------|-----|----------|--------|----------|----------------|---------|-------------------|",
    ]
    for q in qualities:
        lines.append(
            f"| {q.quality_flag} | {q.video} | {q.fps} | {q.duration_s} | "
            f"{q.frames_total} | {q.detection_rate:.1%} | {q.key_visibility_mean:.2f} | "
            f"{q.key_low_visibility_ratio:.1%} | "
            f"{q.jitter_raw:.5f} → {q.jitter_smoothed:.5f} ({q.jitter_reduction_pct:.0f}%) |"
        )

    lines += [
        "",
        "## Metryki",
        "- **detection_rate**: udział klatek, w których MediaPipe wykrył pozę",
        "- **key_visibility_mean**: średnia visibility na kluczowych landmarkach (11,12,23-32)",
        "- **key_low_visibility_ratio**: udział odczytów z visibility<0.5 na kluczowych",
        "- **jitter**: std(drugiej różnicy) x,y — niższy = gładszy sygnał",
        "- **jitter_reduction**: o ile % savgol obniżył jitter (wskaźnik skuteczności filtru)",
        "",
    ]
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines), encoding="utf-8")
    log.info("Zapisano raport: %s, %s", csv_path, md_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ekstrakcja keypointów z filmików (MediaPipe Pose) + wygładzanie."
    )
    parser.add_argument("--videos-dir", default="data/videos", help="Katalog z filmikami")
    parser.add_argument("--output-dir", default="data/keypoints", help="Katalog na CSV")
    parser.add_argument("--video", default=None, help="Ścieżka do pojedynczego filmiku (opcjonalnie)")
    parser.add_argument("--savgol-window", type=int, default=11)
    parser.add_argument("--savgol-polyorder", type=int, default=3)
    parser.add_argument("--model-complexity", type=int, default=2, choices=[0, 1, 2])
    parser.add_argument("--quality-csv", default="data/keypoints/_quality_report.csv")
    parser.add_argument("--quality-md", default="data/keypoints/_quality_report.md")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.video:
        videos = [Path(args.video)]
    else:
        # Obsługa .mp4 i .mov (case-insensitive na Windows)
        videos_dir = Path(args.videos_dir)
        videos = sorted(
            list(videos_dir.glob("*.mp4")) + list(videos_dir.glob("*.mov"))
        )

    log.info("Do przetworzenia: %d filmików", len(videos))

    qualities: list[ExtractionQuality] = []
    for video in videos:
        output_csv = output_dir / (video.stem + ".csv")
        try:
            q = extract_one_video(
                video,
                output_csv,
                savgol_window=args.savgol_window,
                savgol_polyorder=args.savgol_polyorder,
                model_complexity=args.model_complexity,
            )
            qualities.append(q)
        except Exception as e:
            log.error("Błąd przy %s: %s", video.name, e, exc_info=True)

    if qualities:
        _write_quality_report(qualities, Path(args.quality_csv), Path(args.quality_md))


if __name__ == "__main__":
    main()
