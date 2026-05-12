"""Baseline: Random Forest na wektorze keypointów z pojedynczej klatki.

Input: 132 cechy = 33 keypointy × (x, y, z, visibility)
Output: klasa fazy biegu (LEFT_STANCE / RIGHT_STANCE / FLIGHT / DOUBLE_SUPPORT)

Uruchomienie:
    python -m src.training.train_rf
    python -m src.training.train_rf --no-visibility --n-estimators 500
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

sys.path.insert(0, str(Path(__file__).parent))
from augmentation import flip_horizontal_dataframe  # noqa: E402
from features import apply_aspect_ratio_correction, load_video_metadata  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# 33 keypointy MediaPipe Pose (kolejność zgodna z enum PoseLandmark)
KEYPOINT_NAMES: list[str] = [
    "NOSE", "LEFT_EYE_INNER", "LEFT_EYE", "LEFT_EYE_OUTER",
    "RIGHT_EYE_INNER", "RIGHT_EYE", "RIGHT_EYE_OUTER",
    "LEFT_EAR", "RIGHT_EAR", "MOUTH_LEFT", "MOUTH_RIGHT",
    "LEFT_SHOULDER", "RIGHT_SHOULDER", "LEFT_ELBOW", "RIGHT_ELBOW",
    "LEFT_WRIST", "RIGHT_WRIST", "LEFT_PINKY", "RIGHT_PINKY",
    "LEFT_INDEX", "RIGHT_INDEX", "LEFT_THUMB", "RIGHT_THUMB",
    "LEFT_HIP", "RIGHT_HIP", "LEFT_KNEE", "RIGHT_KNEE",
    "LEFT_ANKLE", "RIGHT_ANKLE", "LEFT_HEEL", "RIGHT_HEEL",
    "LEFT_FOOT_INDEX", "RIGHT_FOOT_INDEX",
]


def build_feature_cols(include_visibility: bool) -> list[str]:
    """Lista kolumn cech: 132 (z visibility) lub 99 (bez)."""
    attrs = ("x", "y", "z", "visibility") if include_visibility else ("x", "y", "z")
    return [f"{kp}_{a}" for kp in KEYPOINT_NAMES for a in attrs]


def load_split(
    keypoints_dir: Path,
    files: list[str],
    feat_cols: list[str],
    augment_flip: bool = False,
    aspect_fix: bool = False,
    metadata: dict[str, dict] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Wczytaj CSV z listy i zwróć X (cechy), y (fazy), src (nazwa pliku per klatka).

    Jeśli `augment_flip=True`, każdy plik dostaje też wersję horyzontalnie odbitą.
    Jeśli `aspect_fix=True`, x*width i y*height z metadanych przed kompresją cech.
    """
    if aspect_fix and metadata is None:
        raise ValueError("aspect_fix=True wymaga `metadata`")

    X_parts, y_parts, src_parts = [], [], []
    for fname in files:
        path = keypoints_dir / fname
        df = pd.read_csv(path)
        # Bugfix dla filmu 20 — spacje w nagłówkach kolumn
        df.columns = [c.strip() for c in df.columns]
        # Pomijamy klatki bez pozy i bez etykiety fazy
        df = df[df["pose_detected"] == 1]
        df = df.dropna(subset=["phase"])

        if aspect_fix:
            md = metadata.get(fname)
            if md is None:
                raise KeyError(f"Brak metadanych dla {fname} w videos_metadata.csv")
            df = apply_aspect_ratio_correction(df, md["width"], md["height"])

        missing = [c for c in feat_cols if c not in df.columns]
        if missing:
            raise KeyError(f"{fname}: brakujące kolumny cech: {missing[:5]}")
        X_parts.append(df[feat_cols].to_numpy(dtype=np.float32))
        y_parts.append(df["phase"].to_numpy())
        src_parts.append(np.full(len(df), fname, dtype=object))
        log.info(f"  {fname}: {len(df)} klatek")

        if augment_flip:
            df_flip = flip_horizontal_dataframe(df)
            X_parts.append(df_flip[feat_cols].to_numpy(dtype=np.float32))
            y_parts.append(df_flip["phase"].to_numpy())
            src_parts.append(np.full(len(df_flip), f"{fname}__flip", dtype=object))
            log.info(f"  {fname}__flip: {len(df_flip)} klatek (augmentacja)")

    return (
        np.concatenate(X_parts),
        np.concatenate(y_parts),
        np.concatenate(src_parts),
    )


def evaluate(model, X: np.ndarray, y: np.ndarray, name: str) -> dict:
    """Oblicz metryki i wypisz raport. Zwróć słownik z wynikami."""
    y_pred = model.predict(X)
    labels = sorted(set(np.unique(y)) | set(np.unique(y_pred)))
    acc = accuracy_score(y, y_pred)
    f1_macro = f1_score(y, y_pred, average="macro", labels=labels, zero_division=0)
    cm = confusion_matrix(y, y_pred, labels=labels)
    report = classification_report(y, y_pred, labels=labels, zero_division=0, digits=3)
    log.info(f"=== {name} (n={len(y)}) ===")
    log.info(f"accuracy={acc:.4f}  F1_macro={f1_macro:.4f}")
    log.info("confusion matrix (rows=true, cols=pred):")
    header = "            " + "  ".join(f"{lbl[:10]:>10}" for lbl in labels)
    log.info(header)
    for lbl, row in zip(labels, cm):
        log.info(f"{lbl[:10]:>10}  " + "  ".join(f"{v:>10d}" for v in row))
    log.info("classification report:\n" + report)
    return {
        "name": name,
        "n": int(len(y)),
        "accuracy": float(acc),
        "f1_macro": float(f1_macro),
        "labels": labels,
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Random Forest baseline na keypointach")
    parser.add_argument("--splits", type=Path, default=Path("data/splits.json"))
    parser.add_argument("--keypoints-dir", type=Path, default=Path("data/keypoints"))
    parser.add_argument("--output-dir", type=Path, default=Path("models/rf_baseline"))
    parser.add_argument("--no-visibility", action="store_true",
                        help="Pomiń visibility (99 cech zamiast 132)")
    parser.add_argument("--n-estimators", type=int, default=300)
    parser.add_argument("--max-depth", type=int, default=None)
    parser.add_argument("--min-samples-leaf", type=int, default=1)
    parser.add_argument("--class-weight", type=str, default="balanced",
                        choices=["balanced", "none"])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-jobs", type=int, default=-1)
    parser.add_argument("--augment-flip", action="store_true",
                        help="Augmentacja: dla każdego filmu w TRAIN dorzuć wersję flipped (LEFT↔RIGHT swap + x'=1-x)")
    parser.add_argument("--aspect-fix", action="store_true",
                        help="Korekcja aspect ratio: x*width, y*height przed normalizacją (z videos_metadata.csv)")
    parser.add_argument("--metadata-csv", type=Path, default=Path("data/videos_metadata.csv"))
    args = parser.parse_args()

    splits_cfg = json.loads(args.splits.read_text(encoding="utf-8"))
    files_train = splits_cfg["splits"]["train"]
    files_val = splits_cfg["splits"]["val"]
    files_test = splits_cfg["splits"]["test"]

    feat_cols = build_feature_cols(include_visibility=not args.no_visibility)
    log.info(f"Liczba cech: {len(feat_cols)} (visibility={'off' if args.no_visibility else 'on'})")
    if args.augment_flip:
        log.info("Augmentacja flip: TRAIN podwojony przez horizontal flip + L/R swap")
    metadata = None
    if args.aspect_fix:
        metadata = load_video_metadata(args.metadata_csv)
        log.info(f"Aspect ratio fix: x*width, y*height z {args.metadata_csv} ({len(metadata)} filmów)")

    log.info("Wczytywanie TRAIN:")
    X_train, y_train, _ = load_split(args.keypoints_dir, files_train, feat_cols,
                                     augment_flip=args.augment_flip, aspect_fix=args.aspect_fix, metadata=metadata)
    log.info("Wczytywanie VAL:")
    X_val, y_val, _ = load_split(args.keypoints_dir, files_val, feat_cols,
                                 augment_flip=False, aspect_fix=args.aspect_fix, metadata=metadata)
    log.info("Wczytywanie TEST:")
    X_test, y_test, src_test = load_split(args.keypoints_dir, files_test, feat_cols,
                                          augment_flip=False, aspect_fix=args.aspect_fix, metadata=metadata)

    log.info(f"train={X_train.shape}  val={X_val.shape}  test={X_test.shape}")
    uniq, cnt = np.unique(y_train, return_counts=True)
    log.info(f"rozkład train: {dict(zip(uniq.tolist(), cnt.tolist()))}")

    class_weight = None if args.class_weight == "none" else args.class_weight
    model = RandomForestClassifier(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        class_weight=class_weight,
        random_state=args.seed,
        n_jobs=args.n_jobs,
    )
    log.info(f"Trenowanie RF: n_estimators={args.n_estimators}, max_depth={args.max_depth}, "
             f"min_samples_leaf={args.min_samples_leaf}, class_weight={class_weight}")
    model.fit(X_train, y_train)
    log.info(f"Trenowanie zakończone. Liczba klas: {len(model.classes_)}")

    metrics_val = evaluate(model, X_val, y_val, "VAL")
    metrics_test = evaluate(model, X_test, y_test, "TEST")

    # Per-file na test — sprawdza czy model generalizuje cross-film
    per_file_test: dict[str, dict] = {}
    for fname in np.unique(src_test):
        mask = src_test == fname
        m = evaluate(model, X_test[mask], y_test[mask], f"TEST[{fname}]")
        per_file_test[fname] = {
            "n": m["n"],
            "accuracy": m["accuracy"],
            "f1_macro": m["f1_macro"],
        }

    # TOP-20 feature importances
    fi_sorted = sorted(zip(feat_cols, model.feature_importances_), key=lambda t: -t[1])
    log.info("TOP-20 feature importances:")
    for name, imp in fi_sorted[:20]:
        log.info(f"  {name:<28} {imp:.4f}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.output_dir / "model.joblib")
    metrics_out = {
        "config": {
            "n_estimators": args.n_estimators,
            "max_depth": args.max_depth,
            "min_samples_leaf": args.min_samples_leaf,
            "class_weight": class_weight,
            "seed": args.seed,
            "n_features": len(feat_cols),
            "include_visibility": not args.no_visibility,
            "augment_flip": bool(args.augment_flip),
            "aspect_fix": bool(args.aspect_fix),
        },
        "classes": list(model.classes_),
        "n_train": int(len(y_train)),
        "n_val": int(len(y_val)),
        "n_test": int(len(y_test)),
        "val": metrics_val,
        "test": metrics_test,
        "per_file_test": per_file_test,
        "top_features": [(n, float(i)) for n, i in fi_sorted[:30]],
    }
    (args.output_dir / "metrics.json").write_text(
        json.dumps(metrics_out, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    log.info(f"Model + metryki zapisane do {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
