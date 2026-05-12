"""Inferencja faz biegu na nowym wideo.

Pipeline: wideo → MediaPipe Pose → savgol smoothing → aspect ratio fix
→ engineered features → scaler → BiLSTM → sekwencja faz per klatka.

Output: CSV z frame, timestamp, pose_detected, phase_predicted, confidence
oraz (opcjonalnie) wszystkimi keypointami (--include-keypoints).

Uruchomienie:
    .venv/Scripts/python.exe src/coefficients/run_inference.py \\
        --video "data/videos/24 - Adam bieg__segment_1.mov" \\
        --output data/inference/24-adam-phases.csv

Domyślny model: `models/lstm_run1_overfit/` (LSTM r1 + aspect fix, 70.9% test acc).
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import cv2
import joblib
import mediapipe as mp
import numpy as np
import pandas as pd
import torch
from scipy.signal import savgol_filter

# Import z src/training/
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "training"))
from features import apply_aspect_ratio_correction, compute_engineered_features  # noqa: E402
from train_lstm import BiLSTMClassifier  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

POSE = mp.solutions.pose
LANDMARK_NAMES = [lm.name for lm in POSE.PoseLandmark]
ATTRS = ("x", "y", "z", "visibility")


def extract_keypoints_from_video(
    video_path: Path,
    model_complexity: int = 2,
    savgol_window: int = 11,
    savgol_polyorder: int = 3,
) -> tuple[pd.DataFrame, float, int, int]:
    """Wyekstrahuj keypointy z wideo + savgol smoothing.

    Zwraca (df, fps, width, height). df: kolumny frame, timestamp, pose_detected
    + 33 keypointy × {x, y, z, visibility} (po savgol smoothing dla x/y/z).
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Nie można otworzyć: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    log.info(f"Wideo: FPS={fps:.2f}, {n_frames} klatek, {width}x{height}, czas {n_frames/fps:.1f}s")

    data = np.full((n_frames, 33, 4), np.nan, dtype=np.float64)
    pose_detected = np.zeros(n_frames, dtype=bool)

    pose = POSE.Pose(static_image_mode=False, model_complexity=model_complexity)
    t0 = time.time()
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret or idx >= n_frames:
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

    actual = idx
    data = data[:actual]
    pose_detected = pose_detected[:actual]

    elapsed = time.time() - t0
    log.info(f"MediaPipe: {pose_detected.sum()}/{actual} klatek z pozą, czas {elapsed:.1f}s "
             f"(detection {pose_detected.mean()*100:.1f}%)")

    # Savgol smoothing — tylko x, y, z (visibility to confidence, nie kinematyka)
    win = min(savgol_window, actual if actual % 2 == 1 else actual - 1)
    if win % 2 == 0:
        win -= 1
    if win >= savgol_polyorder + 2:
        for lm_i in range(33):
            for attr_i in range(3):  # x, y, z
                series = pd.Series(data[:, lm_i, attr_i])
                if series.isna().all():
                    continue
                filled = series.interpolate(limit_direction="both").to_numpy()
                data[:, lm_i, attr_i] = savgol_filter(filled, window_length=win, polyorder=savgol_polyorder)
        log.info(f"Savgol smoothing: window={win}, polyorder={savgol_polyorder}")
    else:
        log.warning(f"Wideo za krótkie ({actual} kl.) na savgol — pomijam smoothing")

    # DataFrame
    frames = np.arange(actual, dtype=int)
    timestamps = frames / fps if fps > 0 else np.zeros(actual)
    cols: dict = {
        "frame": frames,
        "timestamp": np.round(timestamps, 4),
        "pose_detected": pose_detected.astype(int),
    }
    for i, name in enumerate(LANDMARK_NAMES):
        for j, attr in enumerate(ATTRS):
            cols[f"{name}_{attr}"] = data[:, i, j]
    df = pd.DataFrame(cols)
    return df, float(fps), width, height


def predict_phases(
    df: pd.DataFrame,
    model_dir: Path,
    video_width: int,
    video_height: int,
) -> tuple[np.ndarray, list[str], np.ndarray]:
    """Predykcje fazy BiLSTM na keypointach. Zwraca (phases, labels, confidence).

    Klatki krawędzi okna (pierwsze/ostatnie half=window_size//2) dostają fazę
    pierwszej/ostatniej predykcji (extend) z confidence=0 — oznaczenie że niepewne.

    Auto-detect aspect_fix z `model_dir/config.json`.
    """
    config = json.loads((model_dir / "config.json").read_text(encoding="utf-8"))
    scaler = joblib.load(model_dir / "scaler.joblib")

    aspect_fix = bool(config.get("aspect_fix", False))
    log.info(f"Model: {model_dir.name}, n_features={config['n_features']}, "
             f"window={config['window_size']}, aspect_fix={aspect_fix}")

    # Pomijamy klatki bez detekcji (LSTM nie ma na czym pracować, ale do MVP — zachowujemy
    # je jako "pose_detected=0" w output, bez predykcji)
    has_pose = df["pose_detected"] == 1
    if not has_pose.all():
        log.warning(f"Klatki bez detekcji pozy: {(~has_pose).sum()}/{len(df)}")
    df_predict = df[has_pose].reset_index(drop=True)

    # Aspect ratio fix
    if aspect_fix:
        df_predict = apply_aspect_ratio_correction(df_predict, video_width, video_height)
        log.info(f"Aspect fix: x*{video_width}, y*{video_height}, z*{video_width}")

    feats, _ = compute_engineered_features(df_predict)
    X = scaler.transform(feats.to_numpy(dtype=np.float32)).astype(np.float32)

    # Model
    model = BiLSTMClassifier(
        n_features=config["n_features"],
        hidden_size=config["hidden_size"],
        num_layers=config["num_layers"],
        dropout=config["dropout"],
        n_classes=len(config["labels"]),
    )
    state = torch.load(model_dir / "model.pt", map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()

    labels = config["labels"]
    window_size = config["window_size"]
    half = window_size // 2
    n_p = len(X)

    if n_p < window_size:
        raise ValueError(f"Za mało klatek z detekcją ({n_p} < window_size {window_size})")

    # Okna: target = klatka środkowa
    Xw = np.stack([X[i - half : i + half + 1] for i in range(half, n_p - half)]).astype(np.float32)

    # Predict + softmax dla confidence
    proba_chunks: list[np.ndarray] = []
    with torch.no_grad():
        for i in range(0, len(Xw), 512):
            xb = torch.from_numpy(Xw[i : i + 512])
            logits = model(xb)
            proba_chunks.append(torch.softmax(logits, dim=1).cpu().numpy())
    proba = np.concatenate(proba_chunks)

    pred_idx = proba.argmax(axis=1)
    pred_inner = np.array([labels[int(i)] for i in pred_idx], dtype=object)
    conf_inner = proba.max(axis=1)

    # Rozszerz na pełną długość df_predict — krawędzie extend
    phases_predict = np.empty(n_p, dtype=object)
    phases_predict[:half] = pred_inner[0]
    phases_predict[half : n_p - half] = pred_inner
    phases_predict[n_p - half :] = pred_inner[-1]

    conf_predict = np.zeros(n_p, dtype=np.float32)
    conf_predict[half : n_p - half] = conf_inner

    # Rozszerz na pełen df (klatki bez detekcji dostają "FLIGHT" jako placeholder, conf=0)
    phases_full = np.full(len(df), "FLIGHT", dtype=object)
    conf_full = np.zeros(len(df), dtype=np.float32)
    phases_full[has_pose.values] = phases_predict
    conf_full[has_pose.values] = conf_predict

    return phases_full, labels, conf_full


def main() -> int:
    parser = argparse.ArgumentParser(description="Inferencja faz biegu (Etap 6)")
    parser.add_argument("--video", type=Path, required=True, help="Ścieżka do wideo (.mp4/.mov)")
    parser.add_argument("--model-dir", type=Path, default=Path("models/lstm_run1_overfit"),
                        help="Katalog modelu (default: lstm_run1_overfit = primary)")
    parser.add_argument("--output", type=Path, default=Path("data/inference/phases.csv"))
    parser.add_argument("--include-keypoints", action="store_true",
                        help="Dołącz wszystkie keypointy do output (większy plik, użyteczny dla downstream)")
    parser.add_argument("--model-complexity", type=int, default=2, choices=[0, 1, 2])
    args = parser.parse_args()

    log.info("=" * 60)
    log.info(f"Etap 6 — inferencja faz: {args.video.name}")
    log.info("=" * 60)

    df, fps, width, height = extract_keypoints_from_video(
        args.video, model_complexity=args.model_complexity,
    )

    phases, labels, confidence = predict_phases(df, args.model_dir, width, height)

    # Output DataFrame
    out_df = pd.DataFrame({
        "frame": df["frame"].values,
        "timestamp": df["timestamp"].values,
        "pose_detected": df["pose_detected"].values,
        "phase_predicted": phases,
        "confidence": confidence,
    })
    if args.include_keypoints:
        kp_cols = [c for c in df.columns if c not in {"frame", "timestamp", "pose_detected"}]
        out_df = pd.concat([out_df, df[kp_cols]], axis=1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(args.output, index=False, encoding="utf-8")
    log.info(f"Zapisano predykcje: {args.output}")

    # Diagnostyka
    log.info("Rozkład faz predykcji:")
    counts = pd.Series(phases).value_counts()
    for ph in labels:
        cnt = int(counts.get(ph, 0))
        pct = cnt / len(phases) * 100
        log.info(f"  {ph:<14} {cnt:>5d} klatek ({pct:5.1f}%)")
    avg_conf = float(np.mean(confidence[confidence > 0]))
    log.info(f"Średnia confidence (predykcje wewnętrzne): {avg_conf:.3f}")

    # Także zwróć dla użycia jako library
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
