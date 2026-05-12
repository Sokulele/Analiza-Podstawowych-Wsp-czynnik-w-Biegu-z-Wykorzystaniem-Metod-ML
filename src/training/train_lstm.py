"""BiLSTM na oknie 15 klatek z cechami engineered — model sekwencyjny (Etap 5.3).

Ten sam split (`data/splits.json`) i te same 106 cech (`features.py`) co RF v2.
Cel: izolować wpływ kontekstu czasowego — fair comparison vs RF v2.

Architektura:
- Bidirectional LSTM (num_layers=2, hidden_size=128, dropout=0.3)
- Window N=15 klatek, target = klasa klatki ŚRODKOWEJ (index 7)
- Krawędzie odrzucamy (po 7 klatek z każdej strony pliku)
- StandardScaler dopasowany TYLKO na train (zapisywany do scaler.joblib)
- CrossEntropyLoss z balanced class weights (zgodnie z RF)
- Early stopping na val loss (patience=15)

Uruchomienie:
    .venv/Scripts/python.exe src/training/train_lstm.py
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_class_weight
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, str(Path(__file__).parent))
from augmentation import flip_horizontal_dataframe  # noqa: E402
from features import (  # noqa: E402
    apply_aspect_ratio_correction,
    compute_engineered_features,
    load_video_metadata,
)

sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def load_per_file(
    keypoints_dir: Path, files: list[str], augment_flip: bool = False,
    aspect_fix: bool = False, metadata: dict[str, dict] | None = None,
) -> tuple[list[tuple[str, np.ndarray, np.ndarray]], list[str]]:
    """Wczytaj listę krotek (fname, X, y) per filmik.

    Klucze: NIE konkatenujemy plików, bo okna nie mogą crossować granic filmów.

    Jeśli `augment_flip=True`, dla każdego pliku dodajemy też wersję horyzontalnie odbitą.
    Jeśli `aspect_fix=True`, x*width i y*height z `metadata` przed compute_engineered_features.
    """
    if aspect_fix and metadata is None:
        raise ValueError("aspect_fix=True wymaga `metadata`")

    out: list[tuple[str, np.ndarray, np.ndarray]] = []
    feature_cols: list[str] | None = None

    def _add_one(df: pd.DataFrame, fname_tag: str) -> None:
        nonlocal feature_cols
        feats, cols = compute_engineered_features(df)
        if feature_cols is None:
            feature_cols = cols
        elif feature_cols != cols:
            raise RuntimeError(f"Niezgodne kolumny cech dla {fname_tag}")
        X = feats.to_numpy(dtype=np.float32)
        y = df["phase"].to_numpy()
        out.append((fname_tag, X, y))
        log.info(f"  {fname_tag}: {len(df)} klatek")

    for fname in files:
        df = pd.read_csv(keypoints_dir / fname)
        df.columns = [c.strip() for c in df.columns]  # bugfix dla filmu 20
        df = df[df["pose_detected"] == 1].dropna(subset=["phase"]).reset_index(drop=True)

        if aspect_fix:
            md = metadata.get(fname)
            if md is None:
                raise KeyError(f"Brak metadanych dla {fname} w videos_metadata.csv")
            df = apply_aspect_ratio_correction(df, md["width"], md["height"])

        _add_one(df, fname)

        if augment_flip:
            df_flip = flip_horizontal_dataframe(df).reset_index(drop=True)
            _add_one(df_flip, f"{fname}__flip")

    if feature_cols is None:
        raise RuntimeError("Brak plików do wczytania")
    return out, feature_cols


def make_windows(
    per_file: list[tuple[str, np.ndarray, np.ndarray]],
    window_size: int,
    label_to_idx: dict[str, int],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per-plik twórz okna. Target = klasa klatki środkowej.

    Zwraca:
        X_w: (M, W, F) float32
        y_w: (M,) int64
        src: (M,) object — fname każdego okna (do per-film analizy)
    """
    half = window_size // 2
    Xw, yw, src = [], [], []
    for fname, X, y in per_file:
        if len(X) < window_size:
            log.warning(f"  pomijam {fname}: za krótki ({len(X)} < {window_size})")
            continue
        for i in range(half, len(X) - half):
            Xw.append(X[i - half : i + half + 1])
            yw.append(label_to_idx[y[i]])
            src.append(fname)
    return (
        np.stack(Xw).astype(np.float32),
        np.array(yw, dtype=np.int64),
        np.array(src, dtype=object),
    )


class BiLSTMClassifier(nn.Module):
    """Dwukierunkowy LSTM → bierzemy wektor stanu klatki środkowej → FC do n_classes."""

    def __init__(
        self,
        n_features: int,
        hidden_size: int,
        num_layers: int,
        dropout: float,
        n_classes: int,
    ):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=n_features,
            hidden_size=hidden_size,
            num_layers=num_layers,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0,
            batch_first=True,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size * 2, n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, W, F) → out: (B, W, 2*H)
        out, _ = self.lstm(x)
        center = out.shape[1] // 2  # klatka środkowa = target
        return self.fc(self.dropout(out[:, center, :]))


def predict_batched(
    model: nn.Module, X: np.ndarray, device: str, batch_size: int = 512
) -> np.ndarray:
    """Predict w batchach (oszczędza pamięć). Zwraca tablicę indeksów klas."""
    model.eval()
    out: list[np.ndarray] = []
    with torch.no_grad():
        for i in range(0, len(X), batch_size):
            xb = torch.from_numpy(X[i : i + batch_size]).to(device)
            out.append(model(xb).argmax(dim=1).cpu().numpy())
    return np.concatenate(out) if out else np.array([], dtype=np.int64)


def evaluate(
    model: nn.Module,
    X: np.ndarray,
    y: np.ndarray,
    name: str,
    device: str,
    labels: list[str],
) -> dict:
    """Policz metryki na (X, y) i zwróć słownik (acc, f1_macro, cm, report)."""
    y_pred = predict_batched(model, X, device)
    label_idx = list(range(len(labels)))
    acc = accuracy_score(y, y_pred)
    f1m = f1_score(y, y_pred, average="macro", labels=label_idx, zero_division=0)
    cm = confusion_matrix(y, y_pred, labels=label_idx)
    report = classification_report(
        y, y_pred, labels=label_idx, target_names=labels, digits=3, zero_division=0
    )
    log.info(f"=== {name} (n={len(y)}) ===")
    log.info(f"accuracy={acc:.4f}  F1_macro={f1m:.4f}")
    log.info("confusion matrix (rows=true, cols=pred):")
    log.info("            " + "  ".join(f"{lbl[:10]:>10}" for lbl in labels))
    for lbl, row in zip(labels, cm):
        log.info(f"{lbl[:10]:>10}  " + "  ".join(f"{v:>10d}" for v in row))
    log.info("classification report:\n" + report)
    return {
        "name": name,
        "n": int(len(y)),
        "accuracy": float(acc),
        "f1_macro": float(f1m),
        "labels": labels,
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
    }


def train_loop(
    model: nn.Module,
    train_loader: DataLoader,
    Xv: np.ndarray,
    yv: np.ndarray,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: str,
    epochs: int,
    patience: int,
) -> tuple[dict, int, list[dict]]:
    """Trenuj z early stopping na val loss. Zwraca (best_state_dict, best_epoch, history)."""
    Xv_t = torch.from_numpy(Xv)
    yv_t = torch.from_numpy(yv)

    best_val_loss = float("inf")
    best_state: dict | None = None
    best_epoch = -1
    epochs_no_improve = 0
    history: list[dict] = []

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        n_batches = 0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            n_batches += 1
        train_loss /= max(n_batches, 1)

        # Validacja w batchach
        model.eval()
        v_loss = 0.0
        v_correct = 0
        v_n = 0
        with torch.no_grad():
            for i in range(0, len(Xv_t), 512):
                xb = Xv_t[i : i + 512].to(device)
                yb = yv_t[i : i + 512].to(device)
                logits = model(xb)
                v_loss += criterion(logits, yb).item() * len(xb)
                v_correct += (logits.argmax(dim=1) == yb).sum().item()
                v_n += len(xb)
        v_loss /= v_n
        v_acc = v_correct / v_n

        history.append(
            {"epoch": epoch, "train_loss": train_loss, "val_loss": v_loss, "val_acc": v_acc}
        )
        log.info(
            f"epoch {epoch:3d}  train_loss={train_loss:.4f}  "
            f"val_loss={v_loss:.4f}  val_acc={v_acc:.4f}"
        )

        # Early stopping (z lekką tolerancją żeby nie liczyć szumu numerycznego)
        if v_loss < best_val_loss - 1e-5:
            best_val_loss = v_loss
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            best_epoch = epoch
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                log.info(
                    f"Early stop @ epoch {epoch} "
                    f"(best val_loss={best_val_loss:.4f} @ epoch {best_epoch})"
                )
                break

    if best_state is None:
        raise RuntimeError("Trening nie ukończył ani jednej epoki")
    return best_state, best_epoch, history


def main() -> int:
    parser = argparse.ArgumentParser(description="BiLSTM na engineered features (Etap 5.3)")
    parser.add_argument("--splits", type=Path, default=Path("data/splits.json"))
    parser.add_argument("--keypoints-dir", type=Path, default=Path("data/keypoints"))
    parser.add_argument("--output-dir", type=Path, default=Path("models/lstm_primary"))
    parser.add_argument("--window-size", type=int, default=15,
                        help="Musi być nieparzyste — żeby było jednoznaczne centrum")
    parser.add_argument("--hidden-size", type=int, default=128)
    parser.add_argument("--num-layers", type=int, default=2)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--patience", type=int, default=15)
    parser.add_argument("--weight-decay", type=float, default=1e-5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--augment-flip", action="store_true",
                        help="Augmentacja: dla każdego filmu w TRAIN dorzuć wersję flipped (L↔R swap + x'=1-x)")
    parser.add_argument("--aspect-fix", action="store_true",
                        help="Korekcja aspect ratio: x*width, y*height przed normalizacją")
    parser.add_argument("--metadata-csv", type=Path, default=Path("data/videos_metadata.csv"))
    args = parser.parse_args()

    if args.window_size % 2 == 0:
        raise ValueError("--window-size musi być nieparzyste (jednoznaczna klatka środkowa)")

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    splits_cfg = json.loads(args.splits.read_text(encoding="utf-8"))

    if args.augment_flip:
        log.info("Augmentacja flip: TRAIN podwojony przez horizontal flip + L/R swap")
    metadata = None
    if args.aspect_fix:
        metadata = load_video_metadata(args.metadata_csv)
        log.info(f"Aspect ratio fix: x*width, y*height z {args.metadata_csv} ({len(metadata)} filmów)")

    log.info("Wczytywanie TRAIN:")
    train_pf, feature_cols = load_per_file(
        args.keypoints_dir, splits_cfg["splits"]["train"],
        augment_flip=args.augment_flip, aspect_fix=args.aspect_fix, metadata=metadata,
    )
    log.info("Wczytywanie VAL:")
    val_pf, _ = load_per_file(
        args.keypoints_dir, splits_cfg["splits"]["val"],
        augment_flip=False, aspect_fix=args.aspect_fix, metadata=metadata,
    )
    log.info("Wczytywanie TEST:")
    test_pf, _ = load_per_file(
        args.keypoints_dir, splits_cfg["splits"]["test"],
        augment_flip=False, aspect_fix=args.aspect_fix, metadata=metadata,
    )

    log.info(f"Liczba cech: {len(feature_cols)}")

    # Zbieramy wszystkie klasy (sortowane alfabetycznie — spójne z sklearn RF.classes_)
    all_labels = sorted({lbl for _, _, y in train_pf + val_pf + test_pf for lbl in y})
    label_to_idx = {l: i for i, l in enumerate(all_labels)}
    log.info(f"Klasy: {all_labels}")

    # Scaler — fit TYLKO na train, transformacja per-plik (bez crossowania)
    X_train_concat = np.concatenate([X for _, X, _ in train_pf])
    if np.isnan(X_train_concat).any():
        raise ValueError("NaN w cechach train — sprawdź compute_engineered_features()")
    scaler = StandardScaler().fit(X_train_concat)
    log.info(
        f"Scaler: mean range [{scaler.mean_.min():.3f}, {scaler.mean_.max():.3f}], "
        f"scale range [{scaler.scale_.min():.3f}, {scaler.scale_.max():.3f}]"
    )

    def scale_pf(pf):
        return [(f, scaler.transform(X).astype(np.float32), y) for f, X, y in pf]

    train_pf = scale_pf(train_pf)
    val_pf = scale_pf(val_pf)
    test_pf = scale_pf(test_pf)

    Xtr, ytr, _ = make_windows(train_pf, args.window_size, label_to_idx)
    Xv, yv, _ = make_windows(val_pf, args.window_size, label_to_idx)
    Xte, yte, src_te = make_windows(test_pf, args.window_size, label_to_idx)

    log.info(f"train windows: {Xtr.shape}  val: {Xv.shape}  test: {Xte.shape}")
    log.info(f"rozkład train: {dict(zip(all_labels, [int(c) for c in np.bincount(ytr, minlength=len(all_labels))]))}")

    # Class weights — balanced (jak w RF)
    cw = compute_class_weight("balanced", classes=np.arange(len(all_labels)), y=ytr)
    log.info(f"class weights: {dict(zip(all_labels, cw.round(3).tolist()))}")

    device = "cpu"
    model = BiLSTMClassifier(
        n_features=Xtr.shape[2],
        hidden_size=args.hidden_size,
        num_layers=args.num_layers,
        dropout=args.dropout,
        n_classes=len(all_labels),
    ).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    log.info(f"Model: BiLSTM(in={Xtr.shape[2]}, hidden={args.hidden_size}, "
             f"layers={args.num_layers}, dropout={args.dropout}, classes={len(all_labels)})")
    log.info(f"Liczba parametrów: {n_params:,}")

    optimizer = torch.optim.Adam(
        model.parameters(), lr=args.lr, weight_decay=args.weight_decay
    )
    criterion = nn.CrossEntropyLoss(weight=torch.tensor(cw, dtype=torch.float32, device=device))

    train_loader = DataLoader(
        TensorDataset(torch.from_numpy(Xtr), torch.from_numpy(ytr)),
        batch_size=args.batch_size,
        shuffle=True,
        drop_last=False,
    )

    log.info("Start treningu z early stopping...")
    best_state, best_epoch, history = train_loop(
        model, train_loader, Xv, yv, criterion, optimizer,
        device, args.epochs, args.patience,
    )
    model.load_state_dict(best_state)
    log.info(f"Załadowano najlepsze wagi z epoki {best_epoch}")

    metrics_val = evaluate(model, Xv, yv, "VAL", device, all_labels)
    metrics_test = evaluate(model, Xte, yte, "TEST", device, all_labels)

    per_file_test: dict[str, dict] = {}
    for fname in np.unique(src_te):
        mask = src_te == fname
        m = evaluate(
            model, Xte[mask], yte[mask], f"TEST[{fname}]", device, all_labels
        )
        per_file_test[fname] = {
            "n": m["n"],
            "accuracy": m["accuracy"],
            "f1_macro": m["f1_macro"],
            "confusion_matrix": m["confusion_matrix"],
        }

    # Zapisy
    args.output_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), args.output_dir / "model.pt")
    joblib.dump(scaler, args.output_dir / "scaler.joblib")

    config = {
        "window_size": args.window_size,
        "hidden_size": args.hidden_size,
        "num_layers": args.num_layers,
        "dropout": args.dropout,
        "lr": args.lr,
        "batch_size": args.batch_size,
        "weight_decay": args.weight_decay,
        "epochs_run": history[-1]["epoch"],
        "best_epoch": best_epoch,
        "patience": args.patience,
        "seed": args.seed,
        "n_features": len(feature_cols),
        "feature_set": "engineered (normalized + angles)",
        "feature_cols": feature_cols,
        "labels": all_labels,
        "n_params": int(n_params),
        "augment_flip": bool(args.augment_flip),
        "aspect_fix": bool(args.aspect_fix),
    }
    (args.output_dir / "config.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    metrics_out = {
        "config": {k: v for k, v in config.items() if k != "feature_cols"},
        "n_train_windows": int(len(Xtr)),
        "n_val_windows": int(len(Xv)),
        "n_test_windows": int(len(Xte)),
        "val": metrics_val,
        "test": metrics_test,
        "per_file_test": per_file_test,
        "history": history,
    }
    (args.output_dir / "metrics.json").write_text(
        json.dumps(metrics_out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log.info(f"Zapisano model.pt + scaler.joblib + config.json + metrics.json → {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
