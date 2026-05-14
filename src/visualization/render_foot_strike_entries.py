"""Renderowanie klatek entry-into-STANCE z kątem foot strike (walidacja Sesji C).

Dla każdego biegacza wybiera N (domyślnie 3) klatek entry-into-LEFT_STANCE
i N entry-into-RIGHT_STANCE, równomiernie rozłożonych w całym filmie.
Na każdej klatce renderuje szkielet MediaPipe + pasek informacyjny z:
- numerem klatki
- stroną wchodzącą w STANCE (L/R)
- obliczonym kątem stopy (heel → foot_index, atan2(-dy, dx), w stopniach)
- klasyfikacją: heel strike (>5°), midfoot (-5..+5°), forefoot (<-5°)

Cel: manualna weryfikacja `compute_foot_strike_pattern` z `spatial_metrics.py`.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

POSE = mp.solutions.pose
MP_DRAWING = mp.solutions.drawing_utils
MP_STYLES = mp.solutions.drawing_styles


def _classify_angle(angle_deg: float) -> str:
    """Konwencja zgodna z compute_foot_strike_pattern w spatial_metrics.py."""
    if angle_deg > 5:
        return "heel strike"
    if angle_deg < -5:
        return "forefoot strike"
    return "midfoot strike"


def _compute_foot_angle(df: pd.DataFrame, side: str, frame_idx: int) -> float:
    """Kąt stopy w klatce — heel → foot_index, atan2(-dy, dx), w stopniach.

    Identyczna konwencja jak w `compute_foot_strike_pattern`:
    - dy = foot_index_y - heel_y; pomnożone przez -1 (bo MediaPipe Y-down).
    - >0 = heel strike (palce wyżej niż pięta).
    """
    heel_x = df[f"{side}_HEEL_x"].iloc[frame_idx]
    heel_y = df[f"{side}_HEEL_y"].iloc[frame_idx]
    fi_x = df[f"{side}_FOOT_INDEX_x"].iloc[frame_idx]
    fi_y = df[f"{side}_FOOT_INDEX_y"].iloc[frame_idx]
    dx = fi_x - heel_x
    dy = fi_y - heel_y
    return float(np.degrees(np.arctan2(-dy, dx)))


def _entry_indices(phases: np.ndarray, target: str) -> list[int]:
    entries: list[int] = []
    n = len(phases)
    if n > 0 and phases[0] == target:
        entries.append(0)
    for i in range(1, n):
        if phases[i] == target and phases[i - 1] != target:
            entries.append(i)
    return entries


def _pick_evenly(entries: list[int], n: int) -> list[int]:
    """Wybierz n równomiernie rozłożonych elementów z listy."""
    if len(entries) <= n:
        return entries
    idxs = np.linspace(0, len(entries) - 1, n).round().astype(int)
    return [entries[i] for i in idxs]


def render_frame_with_angle(
    video_path: Path,
    frame_idx: int,
    side: str,            # "LEFT" or "RIGHT"
    angle_deg: float,
    classification: str,
    output_path: Path,
) -> None:
    """Wyrenderuj klatkę ze szkieletem i paskiem info (frame + side + kąt + klasyfikacja)."""
    cap = cv2.VideoCapture(str(video_path))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        log.error("Nie udalo sie odczytac klatki %d z %s", frame_idx, video_path.name)
        return

    h, w = frame.shape[:2]

    # MediaPipe Pose na tej klatce (static_image_mode dla pojedynczych klatek)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pose = POSE.Pose(static_image_mode=True, model_complexity=2)
    result = pose.process(rgb)
    pose.close()

    if result.pose_landmarks:
        MP_DRAWING.draw_landmarks(
            frame,
            result.pose_landmarks,
            POSE.POSE_CONNECTIONS,
            landmark_drawing_spec=MP_STYLES.get_default_pose_landmarks_style(),
        )

    # Pasek info: kolor zależny od klasyfikacji
    color = {
        "heel strike":     (0, 200, 0),     # zielony
        "midfoot strike":  (0, 165, 255),   # pomarańczowy
        "forefoot strike": (0, 0, 220),     # czerwony
    }.get(classification, (128, 128, 128))

    bar_h = 90
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, bar_h), color, -1)
    frame = cv2.addWeighted(overlay, 0.75, frame, 0.25, 0)

    line1 = f"Klatka {frame_idx} | Entry into {side}_STANCE"
    line2 = f"angle = {angle_deg:+.1f}° -> {classification}"
    cv2.putText(frame, line1, (15, 35), cv2.FONT_HERSHEY_SIMPLEX,
                0.9, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, line2, (15, 75), cv2.FONT_HERSHEY_SIMPLEX,
                0.9, (255, 255, 255), 2, cv2.LINE_AA)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), frame)
    log.info("Zapisano: %s (frame=%d, %s, angle=%.1f°)",
             output_path.name, frame_idx, side, angle_deg)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Renderowanie klatek entry-into-STANCE z kątem foot strike."
    )
    parser.add_argument("--video", required=True, help="Ścieżka do filmiku (.mp4/.mov)")
    parser.add_argument("--phases-csv", required=True, help="Ścieżka do phases.csv z kolumną phase_predicted")
    parser.add_argument("--output-dir", required=True, help="Katalog docelowy na PNG")
    parser.add_argument("--n-per-side", type=int, default=3,
                        help="Ile klatek entry per noga (domyślnie 3)")
    parser.add_argument("--phase-column", default="phase_predicted",
                        help="Nazwa kolumny z fazą (domyślnie phase_predicted)")
    args = parser.parse_args()

    df = pd.read_csv(args.phases_csv)
    if args.phase_column not in df.columns:
        log.error("Brak kolumny %s w %s", args.phase_column, args.phases_csv)
        sys.exit(1)

    phases = df[args.phase_column].values

    video_path = Path(args.video)
    output_dir = Path(args.output_dir)

    for side in ("LEFT", "RIGHT"):
        target = f"{side}_STANCE"
        entries = _entry_indices(phases, target)
        log.info("%s_STANCE: %d entries total", side, len(entries))
        chosen = _pick_evenly(entries, args.n_per_side)
        log.info("%s_STANCE: wybrano %d klatek: %s", side, len(chosen), chosen)

        for frame_idx in chosen:
            angle = _compute_foot_angle(df, side, frame_idx)
            classification = _classify_angle(angle)
            out_name = f"entry_{side}_frame{frame_idx:04d}_angle{angle:+06.1f}.png"
            render_frame_with_angle(
                video_path=video_path,
                frame_idx=frame_idx,
                side=side,
                angle_deg=angle,
                classification=classification,
                output_path=output_dir / out_name,
            )

    log.info("Gotowe. Output: %s", output_dir)


if __name__ == "__main__":
    main()
