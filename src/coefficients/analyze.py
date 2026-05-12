"""End-to-end analiza wideo biegu — orchestration script.

Łączy wszystkie kroki Etapu 6 w jednym wywołaniu CLI:
    1. `run_inference.extract_keypoints_from_video` — MediaPipe + savgol
    2. `run_inference.predict_phases` — LSTM r1 (primary) z aspect fix
    3. `compute_temporal_metrics` — kadencja, GCT, flight, cycle, duty factor
    4. `compute_spatial_metrics` — kąty, torso lean, vertical osc, foot strike
    5. `compute_symmetry` — Symmetry Index L/P
    6. `generate_report` — Markdown raport z porównaniem do `reference-values.md`

Uruchomienie:
    .venv/Scripts/python.exe src/coefficients/analyze.py \\
        --video "data/videos/02 - Running at 13km⧸h - Side View.mp4" \\
        --output-dir data/inference

Output (per wideo, np. dla 02 - Running...):
    data/inference/02-running-at-13km-side-view-phases.csv  (predykcje + keypointy)
    data/inference/02-running-at-13km-side-view-temporal.json
    data/inference/02-running-at-13km-side-view-spatial.json
    data/inference/02-running-at-13km-side-view-symmetry.json
    data/inference/raporty/02-running-at-13km-side-view.md  (← główny output)

Z `--skip-inference` reużywamy istniejące CSV faz i pomijamy MediaPipe (dużo szybsze
przy iteracjach raportu).
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from report_generator import generate_report  # noqa: E402
from run_inference import extract_keypoints_from_video, predict_phases  # noqa: E402
from spatial_metrics import compute_spatial_metrics  # noqa: E402
from symmetry import compute_symmetry  # noqa: E402
from temporal_metrics import compute_temporal_metrics  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _slugify(name: str) -> str:
    """Slug nazw plików z polskim Unicode i spacjami."""
    s = name.lower()
    s = re.sub(r"[⧸／/\\]+", "-", s)
    s = re.sub(r"[^\w\-.]+", "-", s, flags=re.UNICODE)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def analyze_video(
    video_path: Path,
    output_dir: Path,
    model_dir: Path = Path("models/lstm_run1_overfit"),
    skip_inference: bool = False,
    model_complexity: int = 2,
) -> dict:
    """Pełna analiza wideo. Zwraca dict z ścieżkami wszystkich artefaktów."""
    output_dir.mkdir(parents=True, exist_ok=True)
    raporty_dir = output_dir / "raporty"
    raporty_dir.mkdir(exist_ok=True)

    slug = _slugify(video_path.stem)
    phases_csv = output_dir / f"{slug}-phases.csv"
    temporal_json = output_dir / f"{slug}-temporal.json"
    spatial_json = output_dir / f"{slug}-spatial.json"
    symmetry_json = output_dir / f"{slug}-symmetry.json"
    meta_json = output_dir / f"{slug}-meta.json"
    report_md = raporty_dir / f"{slug}.md"

    # 1. Inferencja (lub reuse)
    if skip_inference and phases_csv.exists():
        log.info(f"[skip-inference] reuse istniejącego {phases_csv}")
        df_phases = pd.read_csv(phases_csv)
        # Wczytaj meta jeśli istnieje
        if meta_json.exists():
            meta = json.loads(meta_json.read_text(encoding="utf-8"))
        else:
            # Estymacja FPS z timestampu
            dt = df_phases["timestamp"].iloc[1] - df_phases["timestamp"].iloc[0]
            fps = 1.0 / dt if dt > 0 else 30.0
            meta = {
                "video": video_path.name,
                "fps": round(fps, 2),
                "n_frames": len(df_phases),
                "duration_s": round(len(df_phases) / fps, 2),
                "model_dir": str(model_dir),
            }
    else:
        log.info("=" * 60)
        log.info(f"Inferencja: {video_path}")
        log.info("=" * 60)
        t0 = time.time()
        df_kp, fps, width, height = extract_keypoints_from_video(
            video_path, model_complexity=model_complexity,
        )
        phases, labels, confidence = predict_phases(df_kp, model_dir, width, height)

        # Zbuduj output CSV (predykcje + keypointy do downstream metrics)
        df_phases = pd.DataFrame({
            "frame": df_kp["frame"].values,
            "timestamp": df_kp["timestamp"].values,
            "pose_detected": df_kp["pose_detected"].values,
            "phase_predicted": phases,
            "confidence": confidence,
        })
        kp_cols = [c for c in df_kp.columns if c not in {"frame", "timestamp", "pose_detected"}]
        df_phases = pd.concat([df_phases, df_kp[kp_cols]], axis=1)
        df_phases.to_csv(phases_csv, index=False, encoding="utf-8")
        log.info(f"Zapisano predykcje: {phases_csv}")

        # Meta
        avg_conf = float(confidence[confidence > 0].mean()) if (confidence > 0).any() else 0.0
        # Wczytaj test_acc z metrics.json modelu
        model_test_acc = None
        try:
            mtr = json.loads((model_dir / "metrics.json").read_text(encoding="utf-8"))
            model_test_acc = round(mtr["test"]["accuracy"], 3)
        except Exception:
            pass

        meta = {
            "title": video_path.stem,
            "video": video_path.name,
            "fps": round(fps, 2),
            "n_frames": int(len(df_phases)),
            "duration_s": round(len(df_phases) / fps, 2),
            "width": int(width),
            "height": int(height),
            "model_dir": str(model_dir),
            "model_test_acc": model_test_acc,
            "avg_confidence": round(avg_conf, 3),
            "inference_time_s": round(time.time() - t0, 1),
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        meta_json.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    # 2. Temporal
    log.info("Obliczam temporal metrics...")
    fps = float(meta.get("fps", 30.0))
    phases_arr = df_phases["phase_predicted"].to_numpy()
    temporal = compute_temporal_metrics(phases_arr, fps)
    temporal_json.write_text(json.dumps(temporal, indent=2, ensure_ascii=False), encoding="utf-8")

    # 3. Spatial — wymaga keypointów w df
    log.info("Obliczam spatial metrics...")
    if "LEFT_HIP_x" not in df_phases.columns:
        raise RuntimeError(f"{phases_csv}: brak keypointów. Re-run bez --skip-inference.")
    spatial = compute_spatial_metrics(df_phases, phases_arr, fps)
    spatial_json.write_text(json.dumps(spatial, indent=2, ensure_ascii=False), encoding="utf-8")

    # 4. Symmetry
    log.info("Obliczam symmetry...")
    symmetry = compute_symmetry(temporal, spatial)
    symmetry_json.write_text(json.dumps(symmetry, indent=2, ensure_ascii=False), encoding="utf-8")

    # 5. Report MD
    log.info("Generuję raport MD...")
    report = generate_report(meta, temporal, spatial, symmetry)
    report_md.write_text(report, encoding="utf-8")
    log.info(f"✅ Raport: {report_md}")

    return {
        "video": str(video_path),
        "phases_csv": str(phases_csv),
        "temporal_json": str(temporal_json),
        "spatial_json": str(spatial_json),
        "symmetry_json": str(symmetry_json),
        "meta_json": str(meta_json),
        "report_md": str(report_md),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="End-to-end analiza wideo biegu (Etap 6)")
    parser.add_argument("--video", type=Path, required=True, help="Wideo (.mp4/.mov)")
    parser.add_argument("--output-dir", type=Path, default=Path("data/inference"))
    parser.add_argument("--model-dir", type=Path, default=Path("models/lstm_run1_overfit"))
    parser.add_argument("--skip-inference", action="store_true",
                        help="Reuse istniejące phases CSV (skip MediaPipe + LSTM)")
    parser.add_argument("--model-complexity", type=int, default=2)
    args = parser.parse_args()

    paths = analyze_video(
        args.video, args.output_dir, args.model_dir,
        skip_inference=args.skip_inference, model_complexity=args.model_complexity,
    )
    log.info("=" * 60)
    log.info("Artefakty:")
    for k, v in paths.items():
        log.info(f"  {k:<20} {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
