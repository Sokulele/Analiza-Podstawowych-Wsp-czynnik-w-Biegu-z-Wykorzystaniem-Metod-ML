"""Random Forest v2 — na cechach inżynierowanych (znormalizowane keypointy + kąty stawów).

Ten sam split co baseline (`data/splits.json`), te same hiperparametry RF
(fair comparison — izolujemy wpływ cech, nie konfiguracji modelu).

Cel: sprawdzić czy normalizacja względem biegacza + cechy biomechaniczne
zamykają lukę val↔test z baseline'u (81% → 59%).

Uruchomienie:
    python src/training/train_rf_v2.py
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
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

sys.path.insert(0, str(Path(__file__).parent))
from augmentation import flip_horizontal_dataframe  # noqa: E402
from features import (  # noqa: E402
    apply_aspect_ratio_correction,
    compute_engineered_features,
    compute_velocity_features,
    load_video_metadata,
)

sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def load_split(
    keypoints_dir: Path,
    files: list[str],
    augment_flip: bool = False,
    include_velocity: bool = False,
    aspect_fix: bool = False,
    metadata: dict[str, dict] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    """Wczytaj CSV, policz cechy inżynierowane, zwróć (X, y, src, feature_cols).

    Jeśli `augment_flip=True`, każdy plik dostaje też wersję horyzontalnie odbitą.
    Jeśli `include_velocity=True`, doklejamy 99 cech velocity per filmik.
    Jeśli `aspect_fix=True`, x*width i y*height z `metadata` przed `compute_engineered_features`.
    """
    if aspect_fix and metadata is None:
        raise ValueError("aspect_fix=True wymaga `metadata`")

    X_parts, y_parts, src_parts = [], [], []
    feature_cols: list[str] | None = None

    def _add_one(df: pd.DataFrame, fname_tag: str) -> None:
        nonlocal feature_cols
        feats, cols = compute_engineered_features(df)
        if include_velocity:
            vel, vel_cols = compute_velocity_features(feats)
            feats = pd.concat([feats, vel], axis=1)
            cols = cols + vel_cols
        if feature_cols is None:
            feature_cols = cols
        elif feature_cols != cols:
            raise RuntimeError(f"Niezgodne kolumny cech dla {fname_tag}")
        X_parts.append(feats.to_numpy(dtype=np.float32))
        y_parts.append(df["phase"].to_numpy())
        src_parts.append(np.full(len(df), fname_tag, dtype=object))
        log.info(f"  {fname_tag}: {len(df)} klatek")

    for fname in files:
        path = keypoints_dir / fname
        df = pd.read_csv(path)
        df.columns = [c.strip() for c in df.columns]  # bugfix dla filmu 20
        df = df[df["pose_detected"] == 1]
        df = df.dropna(subset=["phase"])

        if aspect_fix:
            md = metadata.get(fname)
            if md is None:
                raise KeyError(f"Brak metadanych dla {fname} w videos_metadata.csv")
            df = apply_aspect_ratio_correction(df, md["width"], md["height"])

        _add_one(df, fname)

        if augment_flip:
            df_flip = flip_horizontal_dataframe(df)
            _add_one(df_flip, f"{fname}__flip")

    if feature_cols is None:
        raise RuntimeError("Brak plików do wczytania")

    return (
        np.concatenate(X_parts),
        np.concatenate(y_parts),
        np.concatenate(src_parts),
        feature_cols,
    )


def evaluate(model, X: np.ndarray, y: np.ndarray, name: str) -> dict:
    """Oblicz metryki, wypisz raport, zwróć słownik."""
    y_pred = model.predict(X)
    labels = sorted(set(np.unique(y)) | set(np.unique(y_pred)))
    acc = accuracy_score(y, y_pred)
    f1_macro = f1_score(y, y_pred, average="macro", labels=labels, zero_division=0)
    cm = confusion_matrix(y, y_pred, labels=labels)
    report = classification_report(y, y_pred, labels=labels, zero_division=0, digits=3)
    log.info(f"=== {name} (n={len(y)}) ===")
    log.info(f"accuracy={acc:.4f}  F1_macro={f1_macro:.4f}")
    log.info("confusion matrix (rows=true, cols=pred):")
    log.info("            " + "  ".join(f"{lbl[:10]:>10}" for lbl in labels))
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
    parser = argparse.ArgumentParser(description="RF v2 — engineered features")
    parser.add_argument("--splits", type=Path, default=Path("data/splits.json"))
    parser.add_argument("--keypoints-dir", type=Path, default=Path("data/keypoints"))
    parser.add_argument("--output-dir", type=Path, default=Path("models/rf_engineered"))
    parser.add_argument("--n-estimators", type=int, default=300)
    parser.add_argument("--max-depth", type=int, default=None)
    parser.add_argument("--min-samples-leaf", type=int, default=1)
    parser.add_argument("--class-weight", type=str, default="balanced",
                        choices=["balanced", "none"])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-jobs", type=int, default=-1)
    parser.add_argument("--augment-flip", action="store_true",
                        help="Augmentacja: dla każdego filmu w TRAIN dorzuć wersję flipped (L↔R swap + x'=1-x)")
    parser.add_argument("--include-velocity", action="store_true",
                        help="Dołącz 99 cech velocity (Δ znormalizowanych keypointów per klatka per filmik)")
    parser.add_argument("--aspect-fix", action="store_true",
                        help="Korekcja aspect ratio: x*width, y*height przed normalizacją")
    parser.add_argument("--metadata-csv", type=Path, default=Path("data/videos_metadata.csv"))
    args = parser.parse_args()

    splits_cfg = json.loads(args.splits.read_text(encoding="utf-8"))
    files_train = splits_cfg["splits"]["train"]
    files_val = splits_cfg["splits"]["val"]
    files_test = splits_cfg["splits"]["test"]

    if args.augment_flip:
        log.info("Augmentacja flip: TRAIN podwojony przez horizontal flip + L/R swap")
    if args.include_velocity:
        log.info("Velocity features: dołączone 99 cech Δ znormalizowanych keypointów (per klatka per filmik)")
    metadata = None
    if args.aspect_fix:
        metadata = load_video_metadata(args.metadata_csv)
        log.info(f"Aspect ratio fix: x*width, y*height z {args.metadata_csv} ({len(metadata)} filmów)")

    log.info("Wczytywanie TRAIN:")
    X_train, y_train, _, feature_cols = load_split(
        args.keypoints_dir, files_train, augment_flip=args.augment_flip,
        include_velocity=args.include_velocity, aspect_fix=args.aspect_fix, metadata=metadata,
    )
    log.info("Wczytywanie VAL:")
    X_val, y_val, _, _ = load_split(
        args.keypoints_dir, files_val, augment_flip=False,
        include_velocity=args.include_velocity, aspect_fix=args.aspect_fix, metadata=metadata,
    )
    log.info("Wczytywanie TEST:")
    X_test, y_test, src_test, _ = load_split(
        args.keypoints_dir, files_test, augment_flip=False,
        include_velocity=args.include_velocity, aspect_fix=args.aspect_fix, metadata=metadata,
    )

    log.info(f"Liczba cech: {len(feature_cols)}")
    log.info(f"train={X_train.shape}  val={X_val.shape}  test={X_test.shape}")
    uniq, cnt = np.unique(y_train, return_counts=True)
    log.info(f"rozkład train: {dict(zip(uniq.tolist(), cnt.tolist()))}")

    # Sanity check — NaN w cechach zepsułby trening
    if np.isnan(X_train).any() or np.isnan(X_val).any() or np.isnan(X_test).any():
        n_nan = int(np.isnan(X_train).sum() + np.isnan(X_val).sum() + np.isnan(X_test).sum())
        raise ValueError(f"Znaleziono {n_nan} NaN w cechach — sprawdź compute_engineered_features()")

    class_weight = None if args.class_weight == "none" else args.class_weight
    model = RandomForestClassifier(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        class_weight=class_weight,
        random_state=args.seed,
        n_jobs=args.n_jobs,
    )
    log.info(f"Trenowanie RF v2: n_estimators={args.n_estimators}, class_weight={class_weight}")
    model.fit(X_train, y_train)
    log.info(f"Trenowanie zakończone. Klasy: {list(model.classes_)}")

    metrics_val = evaluate(model, X_val, y_val, "VAL")
    metrics_test = evaluate(model, X_test, y_test, "TEST")

    per_file_test: dict[str, dict] = {}
    for fname in np.unique(src_test):
        mask = src_test == fname
        m = evaluate(model, X_test[mask], y_test[mask], f"TEST[{fname}]")
        per_file_test[fname] = {
            "n": m["n"],
            "accuracy": m["accuracy"],
            "f1_macro": m["f1_macro"],
        }

    fi_sorted = sorted(zip(feature_cols, model.feature_importances_), key=lambda t: -t[1])
    log.info("TOP-20 feature importances:")
    for name, imp in fi_sorted[:20]:
        log.info(f"  {name:<32} {imp:.4f}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.output_dir / "model.joblib")
    metrics_out = {
        "config": {
            "n_estimators": args.n_estimators,
            "max_depth": args.max_depth,
            "min_samples_leaf": args.min_samples_leaf,
            "class_weight": class_weight,
            "seed": args.seed,
            "n_features": len(feature_cols),
            "feature_set": (
                "engineered+velocity (normalized + angles + Δ_norm)"
                if args.include_velocity else "engineered (normalized + angles)"
            ),
            "augment_flip": bool(args.augment_flip),
            "include_velocity": bool(args.include_velocity),
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
        json.dumps(metrics_out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log.info(f"Model + metryki zapisane do {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
