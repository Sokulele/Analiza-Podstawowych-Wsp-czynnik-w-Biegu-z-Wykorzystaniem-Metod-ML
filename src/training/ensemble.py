"""Ensemble — soft voting probabilistyczny kilku klasyfikatorów.

Krok 5 z planu poprawy accuracy. Wczytuje 2-4 wytrenowane modele, generuje
probabilistyczne predykcje per klatka i uśrednia. Cel: eksploatacja **różnych
typów błędów** modeli (RF v2 myli się głównie na film 02, LSTM r1 najlepszy na film 22).

Soft voting: średnia P(class) z kilku modeli, argmax = predykcja.

UWAGA — interpolacja klatek brzegowych LSTM:
LSTM ma okno 15 klatek, więc predykcje są dla klatek `half..len-half` per filmik.
RF ma predykcje dla wszystkich klatek. W ensemble bierzemy **przecięcie** czasowe
(klatki dla których wszystkie modele dały predykcje) — to zapewnia spójną ewaluację.

Uruchomienie:
    .venv/Scripts/python.exe src/training/ensemble.py
    .venv/Scripts/python.exe src/training/ensemble.py --median-kernel 3
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
from features import compute_engineered_features, compute_velocity_features  # noqa: E402
from train_lstm import BiLSTMClassifier  # noqa: E402
from train_rf import build_feature_cols  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Modele do dostępne dla ensemble — kolejność = priorytety
MODEL_SPECS: list[dict] = [
    {"id": "rf_v1", "label": "RF v1 (raw)", "dir": "models/rf_baseline", "kind": "rf", "engineered": False},
    {"id": "rf_v2", "label": "RF v2 (engineered)", "dir": "models/rf_engineered", "kind": "rf", "engineered": True},
    {"id": "lstm_r1", "label": "LSTM run 1 (h=128)", "dir": "models/lstm_run1_overfit", "kind": "lstm"},
    {"id": "lstm_r2", "label": "LSTM run 2 (primary)", "dir": "models/lstm_primary", "kind": "lstm"},
]

# Kombinacje do ewaluacji w ensemble — kolejność = kolejność w raporcie
ENSEMBLES: list[dict] = [
    {"id": "rf_v2_lstm_r1", "members": ["rf_v2", "lstm_r1"]},
    {"id": "rf_v2_lstm_r2", "members": ["rf_v2", "lstm_r2"]},
    {"id": "rf_v2_lstm_r1_r2", "members": ["rf_v2", "lstm_r1", "lstm_r2"]},
    {"id": "all_4", "members": ["rf_v1", "rf_v2", "lstm_r1", "lstm_r2"]},
]

CANONICAL_LABELS = ["FLIGHT", "LEFT_STANCE", "RIGHT_STANCE"]


def load_keypoints(keypoints_dir: Path, fname: str) -> pd.DataFrame:
    """Wczytaj CSV, przefiltruj pose_detected i braki phase."""
    df = pd.read_csv(keypoints_dir / fname)
    df.columns = [c.strip() for c in df.columns]
    df = df[df["pose_detected"] == 1].dropna(subset=["phase"]).reset_index(drop=True)
    return df


def predict_proba_rf(
    model_dir: Path, test_files: list[str], keypoints_dir: Path, engineered: bool,
) -> dict[str, dict]:
    """Predykcje probabilistyczne RF per filmik. Zwraca dict {fname: {y_true, proba, classes, n}}."""
    model = joblib.load(model_dir / "model.joblib")
    feat_cols = None if engineered else build_feature_cols(include_visibility=True)

    metrics_path = model_dir / "metrics.json"
    include_velocity = False
    if metrics_path.exists():
        cfg = json.loads(metrics_path.read_text(encoding="utf-8")).get("config", {})
        include_velocity = bool(cfg.get("include_velocity", False))

    classes = list(model.classes_)
    out: dict[str, dict] = {}
    for fname in test_files:
        df = load_keypoints(keypoints_dir, fname)
        if engineered:
            feats, _ = compute_engineered_features(df)
            if include_velocity:
                vel, _ = compute_velocity_features(feats)
                feats = pd.concat([feats, vel], axis=1)
            X = feats.to_numpy(dtype=np.float32)
        else:
            X = df[feat_cols].to_numpy(dtype=np.float32)
        proba = model.predict_proba(X)
        out[fname] = {
            "y_true": df["phase"].to_numpy(),
            "proba": proba,
            "classes": classes,
            "n": len(df),
        }
    return out


def predict_proba_lstm(
    model_dir: Path, test_files: list[str], keypoints_dir: Path,
) -> dict[str, dict]:
    """Predykcje probabilistyczne LSTM per filmik (z oknami W=15)."""
    config = json.loads((model_dir / "config.json").read_text(encoding="utf-8"))
    scaler = joblib.load(model_dir / "scaler.joblib")

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

    classes = config["labels"]
    window_size = config["window_size"]
    half = window_size // 2

    out: dict[str, dict] = {}
    for fname in test_files:
        df = load_keypoints(keypoints_dir, fname)
        feats, _ = compute_engineered_features(df)
        X = scaler.transform(feats.to_numpy(dtype=np.float32)).astype(np.float32)
        if len(X) < window_size:
            log.warning(f"  pomijam {fname}: za krótki ({len(X)} < {window_size})")
            continue
        Xw = np.stack([X[i - half : i + half + 1] for i in range(half, len(X) - half)]).astype(np.float32)

        proba_chunks: list[np.ndarray] = []
        with torch.no_grad():
            for i in range(0, len(Xw), 512):
                xb = torch.from_numpy(Xw[i : i + 512])
                logits = model(xb)
                proba_chunks.append(torch.softmax(logits, dim=1).cpu().numpy())
        proba = np.concatenate(proba_chunks)

        y_true_full = df["phase"].to_numpy()
        out[fname] = {
            "y_true": y_true_full[half : len(X) - half],
            "proba": proba,
            "classes": list(classes),
            "n_full": len(df),
            "half": half,
        }
    return out


def align_proba_to_canonical(
    proba: np.ndarray, classes: list[str], canonical: list[str],
) -> np.ndarray:
    """Permutuj kolumny proba żeby pasowały do canonical kolejności klas."""
    if classes == canonical:
        return proba
    idx = [classes.index(c) for c in canonical]
    return proba[:, idx]


def aligned_predictions_per_file(
    model_predictions: dict[str, dict[str, dict]],
    test_files: list[str],
) -> dict[str, dict]:
    """Sklej predykcje wielu modeli w **wspólnej** przestrzeni klatek per filmik.

    Wspólna przestrzeń: dla każdego filmiku bierzemy klatki które są w **przecięciu**
    wszystkich modeli. RF ma wszystkie klatki (n=N filmu), LSTM ma N - 2*half klatek.
    Bierzemy zakres `[half, N - half)` (LSTM-determined) i obcinamy RF predykcje.

    Zwraca dict {fname: {y_true, model_id_to_proba (dict), n}}.
    """
    out: dict[str, dict] = {}
    for fname in test_files:
        # Zbieraj predykcje per model dla tego filmu
        per_model = {}
        for model_id, preds in model_predictions.items():
            if fname not in preds:
                log.warning(f"  brak {fname} w predykcjach {model_id}")
                continue
            per_model[model_id] = preds[fname]
        if not per_model:
            continue

        # Wyznacz wspólny zakres klatek
        # RF: y_true ma length N (wszystkie klatki)
        # LSTM: y_true ma length N - 2*half (klatki [half, N-half))
        # Bierzemy LSTM zakres jako "common"
        max_half = 0
        n_full = None
        for pred in per_model.values():
            if "half" in pred:
                max_half = max(max_half, pred["half"])
                n_full = pred.get("n_full") or n_full
            else:
                # RF: pred["n"] = N
                n_full = pred["n"] if n_full is None else n_full

        if n_full is None:
            continue

        common_n = n_full - 2 * max_half
        if common_n <= 0:
            log.warning(f"  {fname}: za krótki dla wspólnej przestrzeni (max_half={max_half}, n_full={n_full})")
            continue

        # Wytnij wszystkie predykcje do wspólnego zakresu
        y_true_canonical = None
        model_id_to_proba: dict[str, np.ndarray] = {}
        for model_id, pred in per_model.items():
            proba_full = pred["proba"]
            classes = pred["classes"]
            proba_canonical = align_proba_to_canonical(proba_full, classes, CANONICAL_LABELS)

            if "half" in pred:
                # LSTM: proba ma length N - 2*pred_half. Trzeba dociąć żeby odpowiadało zakresowi LSTM-max
                pred_half = pred["half"]
                if pred_half == max_half:
                    proba_aligned = proba_canonical
                    y_true_aligned = pred["y_true"]
                else:
                    # Wytnij dodatkowe (max_half - pred_half) z każdej strony
                    extra = max_half - pred_half
                    proba_aligned = proba_canonical[extra : len(proba_canonical) - extra]
                    y_true_aligned = pred["y_true"][extra : len(pred["y_true"]) - extra]
            else:
                # RF: proba ma length N. Wytnij [max_half, N - max_half)
                proba_aligned = proba_canonical[max_half : n_full - max_half]
                y_true_aligned = pred["y_true"][max_half : n_full - max_half]

            assert len(proba_aligned) == common_n, (
                f"{fname}/{model_id}: aligned proba ({len(proba_aligned)}) != common_n ({common_n})"
            )

            model_id_to_proba[model_id] = proba_aligned
            if y_true_canonical is None:
                y_true_canonical = y_true_aligned
            else:
                assert (y_true_canonical == y_true_aligned).all(), f"{fname}/{model_id}: y_true rozjazd"

        out[fname] = {
            "y_true": y_true_canonical,
            "model_proba": model_id_to_proba,
            "n": common_n,
        }
    return out


def soft_vote(model_proba: dict[str, np.ndarray], member_ids: list[str]) -> np.ndarray:
    """Średnia probabilistyczna członków ensemble. Zwraca proba (N, K)."""
    stacked = np.stack([model_proba[mid] for mid in member_ids], axis=0)  # (M, N, K)
    return stacked.mean(axis=0)


def proba_to_pred(proba: np.ndarray, canonical: list[str]) -> np.ndarray:
    """Argmax na proba → string labels."""
    return np.array([canonical[i] for i in proba.argmax(axis=1)])


def apply_median_per_file(
    pred_per_file: dict[str, dict], kernel: int, canonical: list[str],
) -> dict[str, dict]:
    """Aplikuj median filter na predykcjach per filmik."""
    label_to_idx = {l: i for i, l in enumerate(canonical)}
    idx_to_label = {i: l for i, l in enumerate(canonical)}
    out: dict[str, dict] = {}
    for fname, d in pred_per_file.items():
        y_pred = d["y_pred"]
        y_int = np.array([label_to_idx[p] for p in y_pred], dtype=np.float64)
        y_filt = medfilt(y_int, kernel_size=kernel).astype(int)
        out[fname] = {
            "y_true": d["y_true"],
            "y_pred": np.array([idx_to_label[int(i)] for i in y_filt]),
        }
    return out


def compute_metrics(pred_per_file: dict[str, dict], canonical: list[str]) -> dict:
    """Globalne acc/F1 + per-film."""
    y_true_all = np.concatenate([d["y_true"] for d in pred_per_file.values()])
    y_pred_all = np.concatenate([d["y_pred"] for d in pred_per_file.values()])
    acc = float(accuracy_score(y_true_all, y_pred_all))
    f1m = float(f1_score(y_true_all, y_pred_all, average="macro", labels=canonical, zero_division=0))

    per_film: dict[str, dict] = {}
    for fname, d in pred_per_file.items():
        per_film[fname] = {
            "n": int(len(d["y_true"])),
            "accuracy": float(accuracy_score(d["y_true"], d["y_pred"])),
            "f1_macro": float(
                f1_score(d["y_true"], d["y_pred"], average="macro", labels=canonical, zero_division=0)
            ),
        }
    return {"acc": acc, "f1_macro": f1m, "per_film": per_film}


def main() -> int:
    parser = argparse.ArgumentParser(description="Ensemble soft voting (krok 5 planu)")
    parser.add_argument("--splits", type=Path, default=Path("data/splits.json"))
    parser.add_argument("--keypoints-dir", type=Path, default=Path("data/keypoints"))
    parser.add_argument("--median-kernels", default="0,3,5",
                        help="CSV kerneli median filtra (0 = bez filtra). Nieparzyste >= 3 lub 0.")
    parser.add_argument("--output", type=Path, default=Path("docs/thesis-notes/figures/ensemble.md"))
    parser.add_argument("--json-output", type=Path, default=Path("docs/thesis-notes/figures/ensemble.json"))
    args = parser.parse_args()

    median_kernels = [int(k) for k in args.median_kernels.split(",")]
    for k in median_kernels:
        if k != 0 and (k < 3 or k % 2 == 0):
            raise ValueError(f"kernel {k}: musi być 0 lub nieparzysty >= 3")

    splits_cfg = json.loads(args.splits.read_text(encoding="utf-8"))
    test_files = splits_cfg["splits"]["test"]
    log.info(f"Test files: {len(test_files)}")

    # 1. Generuj proba per model
    log.info("=" * 60)
    log.info("Predykcje probabilistyczne 4 modeli...")
    model_predictions: dict[str, dict[str, dict]] = {}
    for spec in MODEL_SPECS:
        log.info(f"  {spec['label']}")
        if spec["kind"] == "rf":
            preds = predict_proba_rf(Path(spec["dir"]), test_files, args.keypoints_dir, engineered=spec["engineered"])
        else:
            preds = predict_proba_lstm(Path(spec["dir"]), test_files, args.keypoints_dir)
        model_predictions[spec["id"]] = preds

    # 2. Align na wspólną przestrzeń klatek (LSTM-determined: half=7)
    log.info("=" * 60)
    log.info("Aligning predictions na wspólnej przestrzeni klatek...")
    aligned = aligned_predictions_per_file(model_predictions, test_files)
    total_frames = sum(d["n"] for d in aligned.values())
    log.info(f"Łącznie klatek po align: {total_frames}")

    # 3. Single model baselines (na tej samej wspólnej przestrzeni — fair comparison)
    log.info("=" * 60)
    log.info("Single-model baselines (na wspólnej przestrzeni klatek):")
    single_results: dict[str, dict] = {}
    for spec in MODEL_SPECS:
        mid = spec["id"]
        pred_pf = {
            fname: {
                "y_true": d["y_true"],
                "y_pred": proba_to_pred(d["model_proba"][mid], CANONICAL_LABELS),
            }
            for fname, d in aligned.items()
        }
        m = compute_metrics(pred_pf, CANONICAL_LABELS)
        single_results[mid] = {"label": spec["label"], "raw": m, "filtered": {}}
        log.info(f"  {spec['label']}: acc={m['acc']:.4f}  F1={m['f1_macro']:.4f}")
        for k in median_kernels:
            if k == 0:
                continue
            pred_f = apply_median_per_file(pred_pf, k, CANONICAL_LABELS)
            mf = compute_metrics(pred_f, CANONICAL_LABELS)
            single_results[mid]["filtered"][k] = mf
            log.info(f"    + median k={k}: acc={mf['acc']:.4f}  F1={mf['f1_macro']:.4f}")

    # 4. Ensembles soft-voting
    log.info("=" * 60)
    log.info("Ensembles (soft voting):")
    ensemble_results: dict[str, dict] = {}
    for ens in ENSEMBLES:
        members = ens["members"]
        pred_pf = {
            fname: {
                "y_true": d["y_true"],
                "y_pred": proba_to_pred(soft_vote(d["model_proba"], members), CANONICAL_LABELS),
            }
            for fname, d in aligned.items()
        }
        m = compute_metrics(pred_pf, CANONICAL_LABELS)
        ensemble_results[ens["id"]] = {
            "members": members,
            "label": " + ".join(members),
            "raw": m,
            "filtered": {},
        }
        log.info(f"  ensemble {ens['id']} ({' + '.join(members)}): acc={m['acc']:.4f}  F1={m['f1_macro']:.4f}")
        for k in median_kernels:
            if k == 0:
                continue
            pred_f = apply_median_per_file(pred_pf, k, CANONICAL_LABELS)
            mf = compute_metrics(pred_f, CANONICAL_LABELS)
            ensemble_results[ens["id"]]["filtered"][k] = mf
            log.info(f"    + median k={k}: acc={mf['acc']:.4f}  F1={mf['f1_macro']:.4f}")

    # 5. Zapis raportu
    write_report_md(single_results, ensemble_results, median_kernels, args.output)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    full = {
        "single_models": single_results,
        "ensembles": ensemble_results,
        "median_kernels": median_kernels,
        "total_frames": total_frames,
    }
    args.json_output.write_text(json.dumps(full, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"Zapisano: {args.output}, {args.json_output}")
    return 0


def write_report_md(
    single_results: dict, ensemble_results: dict, median_kernels: list[int], output: Path,
) -> None:
    """Zapisz raport MD: tabele single + ensemble × median, per-film."""
    output.parent.mkdir(parents=True, exist_ok=True)
    nonzero_kernels = [k for k in median_kernels if k != 0]
    lines = ["# Ensemble soft voting + median filter — krok 5 planu", ""]
    lines.append("Wspólna przestrzeń klatek: zakres LSTM (half=7 z każdej strony filmu obcięty).")
    lines.append("Single-model wyniki **na tej samej przestrzeni** dla fair comparison vs ensemble.")
    lines.append("")
    lines.append("## Single models (baseline na wspólnej przestrzeni)")
    lines.append("")
    header_extra = " | ".join(f"+median k={k}" for k in nonzero_kernels)
    lines.append(f"| Model | acc | F1 macro | {header_extra} |")
    lines.append("|---|---|---|" + "|".join(["---"] * len(nonzero_kernels)) + "|")
    for mid, data in single_results.items():
        raw = data["raw"]
        cells = [data["label"], f"{raw['acc']:.4f}", f"{raw['f1_macro']:.4f}"]
        for k in nonzero_kernels:
            mf = data["filtered"].get(k)
            if mf is None:
                cells.append("—")
            else:
                cells.append(f"{mf['acc']:.4f} ({(mf['acc']-raw['acc'])*100:+.2f}pp)")
        lines.append("| " + " | ".join(cells) + " |")

    lines.append("")
    lines.append("## Ensembles (soft voting probabilistyczny)")
    lines.append("")
    lines.append(f"| Ensemble | acc | F1 macro | {header_extra} |")
    lines.append("|---|---|---|" + "|".join(["---"] * len(nonzero_kernels)) + "|")
    for eid, data in ensemble_results.items():
        raw = data["raw"]
        cells = [data["label"], f"{raw['acc']:.4f}", f"{raw['f1_macro']:.4f}"]
        for k in nonzero_kernels:
            mf = data["filtered"].get(k)
            if mf is None:
                cells.append("—")
            else:
                cells.append(f"{mf['acc']:.4f} ({(mf['acc']-raw['acc'])*100:+.2f}pp)")
        lines.append("| " + " | ".join(cells) + " |")

    lines.append("")
    lines.append("## Per-film (best ensemble + median)")
    lines.append("")
    # Wyznacz best ensemble (max acc raw lub z median)
    best_id = None
    best_acc = 0.0
    best_kernel = 0
    for eid, data in ensemble_results.items():
        if data["raw"]["acc"] > best_acc:
            best_acc, best_id, best_kernel = data["raw"]["acc"], eid, 0
        for k, mf in data["filtered"].items():
            if mf["acc"] > best_acc:
                best_acc, best_id, best_kernel = mf["acc"], eid, k

    if best_id:
        lines.append(f"**Best**: ensemble `{best_id}` (median k={best_kernel}) → acc {best_acc:.4f}")
        lines.append("")
        lines.append("| Film | n | accuracy | F1 macro |")
        lines.append("|---|---|---|---|")
        data = ensemble_results[best_id]
        per_film = data["raw"]["per_film"] if best_kernel == 0 else data["filtered"][best_kernel]["per_film"]
        for fname, d in per_film.items():
            lines.append(f"| {fname[:40]} | {d['n']} | {d['accuracy']:.4f} | {d['f1_macro']:.4f} |")

    lines.append("")
    lines.append("## Interpretacja")
    lines.append("")
    lines.append("Soft voting uśrednia probability każdej klasy z N modeli, argmax = predykcja.")
    lines.append("Spodziewana wartość: ensemble eksploatuje **różne typy błędów** modeli składowych.")
    lines.append("Wymóg: modele składowe muszą mieć **różne** błędy (decorrelated). Jeśli się myli")
    lines.append("ten sam zestaw klatek, ensemble nie pomaga.")

    output.write_text("\n".join(lines), encoding="utf-8")
    log.info(f"Zapisano raport: {output}")


if __name__ == "__main__":
    raise SystemExit(main())
