"""Postprocessing predykcji — median filter na sekwencji etykiet per filmik.

Krok 2 z planu poprawy accuracy (`docs/thesis-notes/2026-05-08-accuracy-improvements.md`).
Wczytuje 4 wytrenowane modele, generuje predykcje per klatka, aplikuje median filter
PER FILMIK (granice respektowane) dla różnych rozmiarów kernela. Cel: usunąć 1-2 klatkowe
"migotania" predykcji bez uszkadzania długich segmentów.

Uruchomienie:
    .venv/Scripts/python.exe src/training/postprocess_median.py
    .venv/Scripts/python.exe src/training/postprocess_median.py --kernels 3,5,7,9,11

Skrypt nie nadpisuje `metrics.json` modeli — postprocess to opcjonalny krok inferencji.
Zapisuje raport `docs/thesis-notes/figures/postprocess_median.md` z tabelami acc/F1
per model × kernel + per-film breakdown.
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
import torch
from scipy.signal import medfilt
from sklearn.metrics import accuracy_score, f1_score

sys.path.insert(0, str(Path(__file__).parent))
from features import (  # noqa: E402
    apply_aspect_ratio_correction,
    compute_engineered_features,
    compute_velocity_features,
    load_video_metadata,
)
from train_lstm import BiLSTMClassifier  # noqa: E402
from train_rf import build_feature_cols  # noqa: E402

# Cache metadata raz na cały run
_VIDEO_METADATA: dict[str, dict] | None = None


def _get_metadata() -> dict[str, dict]:
    """Lazy-load videos_metadata.csv (singleton per run)."""
    global _VIDEO_METADATA
    if _VIDEO_METADATA is None:
        _VIDEO_METADATA = load_video_metadata(Path("data/videos_metadata.csv"))
    return _VIDEO_METADATA

sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Definicja modeli — kolejność = kolejność w raporcie
MODEL_SPECS: list[dict] = [
    {"id": "rf_v1", "label": "RF v1 (raw)", "dir": "models/rf_baseline", "kind": "rf", "engineered": False},
    {"id": "rf_v2", "label": "RF v2 (engineered)", "dir": "models/rf_engineered", "kind": "rf", "engineered": True},
    {"id": "lstm_r1", "label": "LSTM run 1 (h=128)", "dir": "models/lstm_run1_overfit", "kind": "lstm"},
    {"id": "lstm_r2", "label": "LSTM run 2 (primary)", "dir": "models/lstm_primary", "kind": "lstm"},
]


def load_keypoints(keypoints_dir: Path, fname: str) -> pd.DataFrame:
    """Wczytaj CSV, przefiltruj pose_detected==1 i braki phase, reset index."""
    df = pd.read_csv(keypoints_dir / fname)
    df.columns = [c.strip() for c in df.columns]
    df = df[df["pose_detected"] == 1].dropna(subset=["phase"]).reset_index(drop=True)
    return df


def predict_rf(
    model_dir: Path, test_files: list[str], keypoints_dir: Path, engineered: bool,
) -> list[tuple[str, np.ndarray, np.ndarray]]:
    """Predykcje RF per filmik. Zwraca listę (fname, y_true, y_pred).

    Auto-detect z `metrics.json`: czy model używa velocity features i/lub aspect fix.
    """
    model = joblib.load(model_dir / "model.joblib")
    feat_cols = None if engineered else build_feature_cols(include_visibility=True)

    # Auto-detect z config
    metrics_path = model_dir / "metrics.json"
    include_velocity = False
    aspect_fix = False
    if metrics_path.exists():
        cfg = json.loads(metrics_path.read_text(encoding="utf-8")).get("config", {})
        include_velocity = bool(cfg.get("include_velocity", False))
        aspect_fix = bool(cfg.get("aspect_fix", False))
    if include_velocity:
        log.info(f"  model {model_dir.name} używa velocity features")
    if aspect_fix:
        log.info(f"  model {model_dir.name} używa aspect_fix")

    metadata = _get_metadata() if aspect_fix else None

    out: list[tuple[str, np.ndarray, np.ndarray]] = []
    for fname in test_files:
        df = load_keypoints(keypoints_dir, fname)
        if aspect_fix:
            md = metadata.get(fname)
            if md is None:
                raise KeyError(f"Brak metadanych dla {fname}")
            df = apply_aspect_ratio_correction(df, md["width"], md["height"])
        if engineered:
            feats, _ = compute_engineered_features(df)
            if include_velocity:
                vel, _ = compute_velocity_features(feats)
                feats = pd.concat([feats, vel], axis=1)
            X = feats.to_numpy(dtype=np.float32)
        else:
            X = df[feat_cols].to_numpy(dtype=np.float32)
        y_true = df["phase"].to_numpy()
        y_pred = model.predict(X)
        out.append((fname, y_true, y_pred))
        log.info(f"  {fname}: {len(df)} klatek (RF predict)")
    return out


def predict_lstm(
    model_dir: Path, test_files: list[str], keypoints_dir: Path,
) -> list[tuple[str, np.ndarray, np.ndarray]]:
    """Predykcje BiLSTM per filmik z oknami W=15. Zwraca listę (fname, y_true, y_pred).

    UWAGA: y_true i y_pred mają długość len(filmik) - 2*half (klatki krawędzi odrzucone).
    Auto-detect aspect_fix z config.json.
    """
    config = json.loads((model_dir / "config.json").read_text(encoding="utf-8"))
    scaler = joblib.load(model_dir / "scaler.joblib")
    aspect_fix = bool(config.get("aspect_fix", False))
    if aspect_fix:
        log.info(f"  model {model_dir.name} używa aspect_fix")
    metadata = _get_metadata() if aspect_fix else None

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
    idx_to_label = {i: l for i, l in enumerate(labels)}
    window_size = config["window_size"]
    half = window_size // 2

    out: list[tuple[str, np.ndarray, np.ndarray]] = []
    for fname in test_files:
        df = load_keypoints(keypoints_dir, fname)
        feats, _ = compute_engineered_features(df)
        X = scaler.transform(feats.to_numpy(dtype=np.float32)).astype(np.float32)
        if len(X) < window_size:
            log.warning(f"  pomijam {fname}: za krótki ({len(X)} < {window_size})")
            continue
        # Okna: target = klatka środkowa
        Xw = np.stack([X[i - half : i + half + 1] for i in range(half, len(X) - half)]).astype(np.float32)

        # Predict w batchach
        preds: list[np.ndarray] = []
        with torch.no_grad():
            for i in range(0, len(Xw), 512):
                xb = torch.from_numpy(Xw[i : i + 512])
                preds.append(model(xb).argmax(dim=1).cpu().numpy())
        y_pred_idx = np.concatenate(preds)
        y_pred = np.array([idx_to_label[int(i)] for i in y_pred_idx])

        y_true_full = df["phase"].to_numpy()
        y_true = y_true_full[half : len(X) - half]
        assert len(y_true) == len(y_pred), f"{fname}: y_true ({len(y_true)}) != y_pred ({len(y_pred)})"

        out.append((fname, y_true, y_pred))
        log.info(f"  {fname}: {len(y_true)} okien (LSTM predict)")
    return out


def apply_median_filter_per_file(
    per_file: list[tuple[str, np.ndarray, np.ndarray]],
    kernel: int,
    labels: list[str],
) -> list[tuple[str, np.ndarray, np.ndarray]]:
    """Aplikuj median filter na sekwencji predykcji per filmik (granice filmów respektowane).

    Filtr działa na intach (mapowanie label→idx), wynik mapowany z powrotem na stringi.
    """
    if kernel < 3 or kernel % 2 == 0:
        raise ValueError("kernel musi być nieparzysty i >= 3")
    label_to_idx = {l: i for i, l in enumerate(labels)}
    idx_to_label = {i: l for i, l in enumerate(labels)}

    out: list[tuple[str, np.ndarray, np.ndarray]] = []
    for fname, y_true, y_pred in per_file:
        y_pred_int = np.array([label_to_idx[p] for p in y_pred], dtype=np.float64)
        y_filt_int = medfilt(y_pred_int, kernel_size=kernel).astype(int)
        y_filt = np.array([idx_to_label[int(i)] for i in y_filt_int])
        out.append((fname, y_true, y_filt))
    return out


def compute_metrics(
    per_file: list[tuple[str, np.ndarray, np.ndarray]],
    labels: list[str],
) -> tuple[float, float, dict[str, dict]]:
    """Globalne acc/F1 + per-film. Skleja predykcje wszystkich filmów."""
    y_true_all = np.concatenate([yt for _, yt, _ in per_file])
    y_pred_all = np.concatenate([yp for _, _, yp in per_file])
    acc = float(accuracy_score(y_true_all, y_pred_all))
    f1m = float(f1_score(y_true_all, y_pred_all, average="macro", labels=labels, zero_division=0))

    per_film: dict[str, dict] = {}
    for fname, y_true, y_pred in per_file:
        per_film[fname] = {
            "n": int(len(y_true)),
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "f1_macro": float(f1_score(y_true, y_pred, average="macro", labels=labels, zero_division=0)),
        }
    return acc, f1m, per_film


def write_report_md(
    results: dict, kernels: list[int], output_path: Path,
) -> None:
    """Zapisz tabelę wyników postprocess do MD (materiał do pracy magisterskiej)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = ["# Postprocessing median filter — krok 2 planu accuracy improvements", ""]
    lines.append(f"Generated: 2026-05-08 (krok 2)")
    lines.append("")
    lines.append("## Globalne accuracy / F1 macro vs kernel size")
    lines.append("")
    header = "| Model | baseline | " + " | ".join(f"k={k}" for k in kernels) + " | best |"
    sep = "|" + "---|" * (2 + len(kernels) + 1)
    lines.append(header)
    lines.append(sep)

    for spec_id, data in results.items():
        label = data["label"]
        base_acc = data["baseline"]["acc"]
        base_f1 = data["baseline"]["f1"]
        cells = [f"{label}", f"acc={base_acc:.3f} F1={base_f1:.3f}"]
        best_k = None
        best_acc = base_acc
        for k in kernels:
            r = data["filtered"][k]
            acc = r["acc"]
            f1 = r["f1"]
            cells.append(f"acc={acc:.3f} F1={f1:.3f} ({(acc-base_acc)*100:+.2f}pp)")
            if acc > best_acc:
                best_acc = acc
                best_k = k
        if best_k is None:
            cells.append("baseline")
        else:
            cells.append(f"k={best_k} ({best_acc:.3f}, +{(best_acc-base_acc)*100:.2f}pp)")
        lines.append("| " + " | ".join(cells) + " |")

    lines.append("")
    lines.append("## Per-film accuracy (best kernel each model)")
    lines.append("")
    lines.append("| Model | best k | film 02 | film 20 | film 22 |")
    lines.append("|---|---|---|---|---|")
    for spec_id, data in results.items():
        # Wybierz best kernel (max global acc)
        base_acc = data["baseline"]["acc"]
        best_k = None
        best_acc = base_acc
        for k in kernels:
            if data["filtered"][k]["acc"] > best_acc:
                best_acc = data["filtered"][k]["acc"]
                best_k = k
        per_film = data["baseline"]["per_film"] if best_k is None else data["filtered"][best_k]["per_film"]
        per_film_base = data["baseline"]["per_film"]

        cells = [data["label"], "baseline" if best_k is None else f"k={best_k}"]
        for film_substr in ("02 -", "20 -", "22 -"):
            match = next((k for k in per_film if k.startswith(film_substr)), None)
            if match is None:
                cells.append("—")
                continue
            acc = per_film[match]["accuracy"]
            base = per_film_base[match]["accuracy"]
            delta = (acc - base) * 100
            cells.append(f"{acc:.3f} ({delta:+.2f}pp)")
        lines.append("| " + " | ".join(cells) + " |")

    lines.append("")
    lines.append("## Interpretacja")
    lines.append("")
    lines.append("Median filter wymusza lokalną spójność etykiet w czasie. Pojedyncze migotania")
    lines.append("(1-2 klatki anomalii) są usuwane, ale długie segmenty zachowane. Filtr działa")
    lines.append("PER FILMIK (granice filmów respektowane — nie crossuje plików).")
    lines.append("")
    lines.append("Spodziewany efekt:")
    lines.append("- Zmniejszenie L↔R direct transitions (typowy artefakt 1-2 klatkowy)")
    lines.append("- Marginalny wpływ na FLIGHT↔STANCE (te błędy często są dłuższymi segmentami)")
    lines.append("- Większe kernele (k≥7) mogą zacząć usuwać krótkie poprawne segmenty FLIGHT (~3-4 klatki przy 30 FPS)")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    log.info(f"Zapisano raport: {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Median filter na predykcjach (krok 2 planu)")
    parser.add_argument("--splits", type=Path, default=Path("data/splits.json"))
    parser.add_argument("--keypoints-dir", type=Path, default=Path("data/keypoints"))
    parser.add_argument("--kernels", default="3,5,7,9", help="CSV nieparzystych kerneli")
    parser.add_argument("--output", type=Path, default=Path("docs/thesis-notes/figures/postprocess_median.md"))
    parser.add_argument("--json-output", type=Path, default=Path("docs/thesis-notes/figures/postprocess_median.json"))
    args = parser.parse_args()

    kernels = [int(k) for k in args.kernels.split(",")]
    for k in kernels:
        if k < 3 or k % 2 == 0:
            raise ValueError(f"kernel {k}: musi być nieparzysty i >= 3")

    splits_cfg = json.loads(args.splits.read_text(encoding="utf-8"))
    test_files = splits_cfg["splits"]["test"]
    log.info(f"Test files: {len(test_files)}")

    results: dict[str, dict] = {}
    for spec in MODEL_SPECS:
        log.info("=" * 60)
        log.info(f"Model: {spec['label']} ({spec['dir']})")
        model_dir = Path(spec["dir"])

        if spec["kind"] == "rf":
            per_file = predict_rf(model_dir, test_files, args.keypoints_dir, engineered=spec["engineered"])
        else:
            per_file = predict_lstm(model_dir, test_files, args.keypoints_dir)

        # Etykiety: alfabetycznie, jak sklearn
        all_labels = sorted({lbl for _, yt, _ in per_file for lbl in yt})

        # Baseline (bez filtra)
        acc_b, f1_b, per_film_b = compute_metrics(per_file, all_labels)
        log.info(f"baseline: acc={acc_b:.4f}  F1={f1_b:.4f}")

        results[spec["id"]] = {
            "label": spec["label"],
            "baseline": {"acc": acc_b, "f1": f1_b, "per_film": per_film_b},
            "filtered": {},
        }

        for k in kernels:
            filt = apply_median_filter_per_file(per_file, k, all_labels)
            acc, f1, per_film = compute_metrics(filt, all_labels)
            results[spec["id"]]["filtered"][k] = {"acc": acc, "f1": f1, "per_film": per_film}
            delta = (acc - acc_b) * 100
            log.info(f"  k={k}: acc={acc:.4f}  F1={f1:.4f}  (Δ acc {delta:+.2f}pp)")

    write_report_md(results, kernels, args.output)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"Zapisano JSON: {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
