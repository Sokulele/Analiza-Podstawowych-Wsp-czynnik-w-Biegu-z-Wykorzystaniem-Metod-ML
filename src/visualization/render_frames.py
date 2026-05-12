"""Renderowanie wybranych klatek z nałożonym szkieletem MediaPipe i etykietą fazy.

Generuje pliki PNG z kolorowym szkieletem i oznaczeniem fazy biegu —
do prezentacji i wizualnej weryfikacji auto-etykietowania.
"""
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

# Kolory faz (BGR)
PHASE_COLORS = {
    "LEFT_STANCE":    (0, 200, 0),      # zielony
    "RIGHT_STANCE":   (200, 130, 0),    # niebieski
    "FLIGHT":         (0, 100, 255),    # pomarańczowy
    "DOUBLE_SUPPORT": (0, 0, 220),      # czerwony
}

# Czytelne etykiety po polsku
PHASE_LABELS_PL = {
    "LEFT_STANCE":    "LEWA NOGA (stance)",
    "RIGHT_STANCE":   "PRAWA NOGA (stance)",
    "FLIGHT":         "LOT (flight)",
    "DOUBLE_SUPPORT": "PODWOJNE PODPARCIE",
}


def pick_interesting_frames(df: pd.DataFrame, n_per_phase: int = 2) -> list[int]:
    """Wybierz ciekawe klatki — po kilka z każdej fazy, w środku segmentu."""
    frames = []
    phases = df["phase"].values

    for target_phase in ["LEFT_STANCE", "RIGHT_STANCE", "FLIGHT"]:
        # Znajdź segmenty tej fazy
        segments = []
        start = None
        for i in range(len(phases)):
            if phases[i] == target_phase and start is None:
                start = i
            elif phases[i] != target_phase and start is not None:
                segments.append((start, i - 1))
                start = None
        if start is not None:
            segments.append((start, len(phases) - 1))

        # Sortuj po długości (najdłuższe = najciekawsze)
        segments.sort(key=lambda s: s[1] - s[0], reverse=True)

        # Weź środek najdłuższych segmentów
        for seg_start, seg_end in segments[:n_per_phase]:
            mid = (seg_start + seg_end) // 2
            frames.append(mid)

    frames.sort()
    return frames


def render_frame(
    video_path: Path,
    frame_idx: int,
    phase: str,
    output_path: Path,
) -> None:
    """Wyrenderuj jedną klatkę z nałożonym szkieletem i etykietą fazy."""
    cap = cv2.VideoCapture(str(video_path))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        log.error("Nie udało się odczytać klatki %d", frame_idx)
        return

    h, w = frame.shape[:2]

    # MediaPipe Pose na tej klatce
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pose = POSE.Pose(static_image_mode=True, model_complexity=2)
    result = pose.process(rgb)
    pose.close()

    if result.pose_landmarks:
        # Szkielet
        MP_DRAWING.draw_landmarks(
            frame,
            result.pose_landmarks,
            POSE.POSE_CONNECTIONS,
            landmark_drawing_spec=MP_STYLES.get_default_pose_landmarks_style(),
        )

    # Etykieta fazy — pasek na górze
    color = PHASE_COLORS.get(phase, (128, 128, 128))
    label = PHASE_LABELS_PL.get(phase, phase)

    # Tło paska
    bar_h = 60
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, bar_h), color, -1)
    frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

    # Tekst
    text = f"Klatka {frame_idx} | {label}"
    cv2.putText(frame, text, (15, 42), cv2.FONT_HERSHEY_SIMPLEX,
                1.0, (255, 255, 255), 2, cv2.LINE_AA)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), frame)
    log.info("Zapisano: %s", output_path.name)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Renderowanie klatek ze szkieletem i etykietą fazy biegu."
    )
    parser.add_argument("--video", required=True, help="Ścieżka do filmiku")
    parser.add_argument("--keypoints", required=True, help="Ścieżka do CSV z keypointami i fazami")
    parser.add_argument("--output-dir", default="data/visualizations", help="Katalog na PNG")
    parser.add_argument("--frames", default=None,
                        help="Numery klatek do wyrenderowania (np. '18,53,83'), domyślnie auto-wybór")
    parser.add_argument("--n-per-phase", type=int, default=2,
                        help="Ile klatek per faza przy auto-wyborze (domyślnie 2)")
    args = parser.parse_args()

    df = pd.read_csv(args.keypoints)
    if "phase" not in df.columns:
        log.error("Brak kolumny 'phase' w %s — uruchom najpierw auto_label.py", args.keypoints)
        return

    video_path = Path(args.video)
    output_dir = Path(args.output_dir)
    video_stem = video_path.stem[:30]  # skrócona nazwa do plików

    # Wybór klatek
    if args.frames:
        frame_list = [int(f.strip()) for f in args.frames.split(",")]
    else:
        frame_list = pick_interesting_frames(df, n_per_phase=args.n_per_phase)

    log.info("Klatki do wyrenderowania: %s", frame_list)

    for frame_idx in frame_list:
        if frame_idx >= len(df):
            log.warning("Klatka %d poza zakresem (max %d)", frame_idx, len(df) - 1)
            continue

        phase = df["phase"].iloc[frame_idx]
        out_path = output_dir / f"{video_stem}_frame{frame_idx:04d}_{phase}.png"
        render_frame(video_path, frame_idx, phase, out_path)

    log.info("Gotowe — %d klatek w %s", len(frame_list), output_dir)


if __name__ == "__main__":
    main()
