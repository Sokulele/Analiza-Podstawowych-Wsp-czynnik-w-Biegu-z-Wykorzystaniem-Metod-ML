"""Analiza porównawcza klasyfikatorów faz biegu (Etap 5.4).

Wczytuje metrics.json z czterech katalogów modeli i generuje materiał do
rozdziału 5.4 pracy magisterskiej:

- comparison_table.md / comparison_summary.json — tabela zbiorcza acc/F1/luka
- per_file_test.md — accuracy per filmik testowy × model
- error_breakdown.md — typologia błędów (L↔R vs FLIGHT↔STANCE)
- confusion_matrices_test.png — 4 macierze pomyłek na teście (heatmapy)
- learning_curves_lstm.png — krzywe uczenia obu runów LSTM
- feature_importances_rf.png — TOP-15 cech dla RF v1 i RF v2

Skrypt jest standalone — nie trenuje, nie odczytuje keypointów.
Operuje wyłącznie na zapisanych artefaktach (`models/{*}/metrics.json`).

Uruchomienie:
    .venv/Scripts/python.exe src/training/compare_models.py
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


# Definicja porównywanych modeli — kolejność = kolejność w tabelach i panelach
MODEL_SPECS: list[dict] = [
    {
        "id": "rf_v1",
        "label": "RF v1 (raw)",
        "short": "RF v1",
        "dir": "rf_baseline",
        "kind": "rf",
    },
    {
        "id": "rf_v2",
        "label": "RF v2 (engineered)",
        "short": "RF v2",
        "dir": "rf_engineered",
        "kind": "rf",
    },
    {
        "id": "lstm_run1",
        "label": "LSTM run 1 (h=128, overfit)",
        "short": "LSTM run 1",
        "dir": "lstm_run1_overfit",
        "kind": "lstm",
    },
    {
        "id": "lstm_run2",
        "label": "LSTM run 2 (primary)",
        "short": "LSTM run 2",
        "dir": "lstm_primary",
        "kind": "lstm",
    },
]

CLASS_LABELS = ["FLIGHT", "LEFT_STANCE", "RIGHT_STANCE"]


def load_all_metrics(models_dir: Path) -> list[dict]:
    """Wczytaj metrics.json dla wszystkich modeli z MODEL_SPECS, dołącz do specs."""
    out: list[dict] = []
    for spec in MODEL_SPECS:
        path = models_dir / spec["dir"] / "metrics.json"
        if not path.exists():
            raise FileNotFoundError(f"Brak {path}")
        spec = {**spec, "metrics": json.loads(path.read_text(encoding="utf-8"))}
        log.info(f"  wczytano {path}")
        out.append(spec)
    return out


def off_diagonal_errors(cm: list[list[int]]) -> dict[str, int]:
    """Z macierzy 3×3 (FLIGHT/LEFT_STANCE/RIGHT_STANCE) policz typowe pomyłki.

    cm[i][j] = klatek z true=i sklasyfikowanych jako pred=j.
    Indeksy: 0=FLIGHT, 1=LEFT_STANCE, 2=RIGHT_STANCE.
    """
    cm_a = np.array(cm, dtype=int)
    n = int(cm_a.sum())
    correct = int(np.trace(cm_a))
    lr = int(cm_a[1, 2] + cm_a[2, 1])  # L↔R
    flight_stance = int(
        cm_a[0, 1] + cm_a[0, 2] + cm_a[1, 0] + cm_a[2, 0]
    )  # FLIGHT↔STANCE w obie strony
    return {
        "n_total": n,
        "n_correct": correct,
        "n_errors": n - correct,
        "lr_confusion": lr,
        "flight_stance_confusion": flight_stance,
    }


def build_summary_table(models: list[dict]) -> tuple[str, list[dict]]:
    """Tabela zbiorcza acc/F1/luka val→test dla 4 modeli (Markdown + lista dictów)."""
    rows: list[dict] = []
    for m in models:
        met = m["metrics"]
        val = met["val"]
        test = met["test"]
        cfg = met["config"]
        n_features = cfg.get("n_features")
        gap = val["accuracy"] - test["accuracy"]
        rows.append(
            {
                "model_id": m["id"],
                "label": m["label"],
                "n_features": n_features,
                "n_train": met.get("n_train") or met.get("n_train_windows"),
                "n_val": met.get("n_val") or met.get("n_val_windows"),
                "n_test": met.get("n_test") or met.get("n_test_windows"),
                "val_accuracy": val["accuracy"],
                "val_f1_macro": val["f1_macro"],
                "test_accuracy": test["accuracy"],
                "test_f1_macro": test["f1_macro"],
                "gap_val_test_pp": gap * 100,
            }
        )

    md = ["# Porównanie modeli — metryki globalne", ""]
    md.append(
        "| Model | Cechy | n train / val / test | Val acc | Val F1 | Test acc | Test F1 | Luka val→test |"
    )
    md.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in rows:
        md.append(
            f"| {r['label']} "
            f"| {r['n_features']} "
            f"| {r['n_train']} / {r['n_val']} / {r['n_test']} "
            f"| {r['val_accuracy']*100:.1f}% "
            f"| {r['val_f1_macro']:.3f} "
            f"| **{r['test_accuracy']*100:.1f}%** "
            f"| **{r['test_f1_macro']:.3f}** "
            f"| {r['gap_val_test_pp']:.1f} p.p. |"
        )
    md.append("")
    md.append(
        "Uwaga: LSTM ma mniej okien niż RF ma klatek (po 7 z każdej strony pliku "
        "odpada — krawędzie okna 15). Test RF n=1490 vs test LSTM n=1448 (Δ 42)."
    )
    md.append("")
    return "\n".join(md), rows


def build_per_file_table(models: list[dict]) -> str:
    """Tabela accuracy per-film × model. Filmy: 02, 20, 22."""
    # Zbiór nazw plików — z każdego modelu
    file_keys = sorted(
        {fname for m in models for fname in m["metrics"]["per_file_test"].keys()}
    )

    # Krótki opis filmu z testu
    file_descriptions: dict[str, str] = {
        "02": "Running at 13 km/h — boczne ujęcie",
        "20": "Walk → run, 0.8–3.5 m/s",
        "22": "Physiotherapist demo — pionowe wideo",
    }

    def short(fname: str) -> str:
        # Numer filmu = pierwszy token przed " - " ("02 - Running..." → "02")
        return fname.split(" - ")[0].strip()

    md = ["# Porównanie modeli — accuracy per filmik testowy", ""]
    header = "| Film | n RF / LSTM | " + " | ".join(m["short"] for m in models) + " |"
    sep = "| --- | --- |" + " --- |" * len(models)
    md.append(header)
    md.append(sep)

    for fname in file_keys:
        num = short(fname)
        desc = file_descriptions.get(num, "")
        # n może być różne między RF (klatki) a LSTM (okna 15)
        ns = []
        for m in models:
            entry = m["metrics"]["per_file_test"].get(fname)
            ns.append((m["kind"], entry["n"] if entry else None))
        n_rf = next((n for kind, n in ns if kind == "rf" and n is not None), None)
        n_lstm = next((n for kind, n in ns if kind == "lstm" and n is not None), None)
        n_cell = f"{n_rf or '—'} / {n_lstm or '—'}"

        row_parts = [f"| **{num}** — {desc}", f" {n_cell}"]
        for m in models:
            entry = m["metrics"]["per_file_test"].get(fname)
            if entry is None:
                row_parts.append(" — ")
                continue
            row_parts.append(f" {entry['accuracy']*100:.1f}%")
        md.append("|".join(row_parts) + " |")
    md.append("")

    # Druga tabela — F1 macro per-film
    md.append("## F1 macro per-film")
    md.append("")
    header_f1 = "| Film | " + " | ".join(m["short"] for m in models) + " |"
    sep_f1 = "| --- |" + " --- |" * len(models)
    md.append(header_f1)
    md.append(sep_f1)
    for fname in file_keys:
        num = short(fname)
        desc = file_descriptions.get(num, "")
        row_parts = [f"| **{num}** — {desc}"]
        for m in models:
            entry = m["metrics"]["per_file_test"].get(fname)
            if entry is None:
                row_parts.append(" — ")
                continue
            row_parts.append(f" {entry['f1_macro']:.3f}")
        md.append("|".join(row_parts) + " |")
    md.append("")
    return "\n".join(md)


def build_error_breakdown(models: list[dict]) -> str:
    """Tabela typów błędów: L↔R vs FLIGHT↔STANCE na test."""
    md = ["# Analiza typów błędów na test", ""]
    md.append(
        "Z macierzy pomyłek 3×3 (FLIGHT / LEFT_STANCE / RIGHT_STANCE) "
        "wyróżniamy dwie kategorie błędów:"
    )
    md.append("")
    md.append("- **L↔R**: pomyłki między LEFT_STANCE a RIGHT_STANCE — najgorszy typ błędu, "
              "bo bezpośrednio rujnuje współczynnik symetrii L/R w produkcji")
    md.append("- **FLIGHT↔STANCE**: pomyłki o moment kontaktu z ziemią — przesunięcie "
              "GCT/flight time o 1-2 klatki, znacznie mniej dotkliwe")
    md.append("")
    md.append(
        "| Model | n test | poprawne | błędy razem | L↔R | FLIGHT↔STANCE | "
        "% L↔R w błędach |"
    )
    md.append("| --- | --- | --- | --- | --- | --- | --- |")
    for m in models:
        cm = m["metrics"]["test"]["confusion_matrix"]
        st = off_diagonal_errors(cm)
        share_lr = st["lr_confusion"] / st["n_errors"] * 100 if st["n_errors"] else 0.0
        md.append(
            f"| {m['label']} "
            f"| {st['n_total']} "
            f"| {st['n_correct']} "
            f"| {st['n_errors']} "
            f"| {st['lr_confusion']} "
            f"| {st['flight_stance_confusion']} "
            f"| {share_lr:.1f}% |"
        )
    md.append("")
    md.append(
        "Dla 3 klas (FLIGHT/L_STANCE/R_STANCE) suma `L↔R` + `FLIGHT↔STANCE` "
        "pokrywa wszystkie 6 pól off-diagonal — czyli sumę błędów."
    )
    md.append("")
    return "\n".join(md)


def plot_confusion_matrices_test(models: list[dict], out_path: Path) -> None:
    """4 macierze pomyłek (test) jako heatmapy znormalizowane wierszami (recall)."""
    fig, axes = plt.subplots(2, 2, figsize=(11, 10))
    axes_flat = axes.flatten()
    for ax, m in zip(axes_flat, models):
        cm = np.array(m["metrics"]["test"]["confusion_matrix"], dtype=float)
        # Normalizacja per-row (recall) — porównywalna mimo różnego n
        cm_norm = cm / cm.sum(axis=1, keepdims=True)
        im = ax.imshow(cm_norm, cmap="Blues", vmin=0, vmax=1, aspect="auto")
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                color = "white" if cm_norm[i, j] > 0.5 else "black"
                ax.text(
                    j, i,
                    f"{int(cm[i, j])}\n({cm_norm[i, j]*100:.0f}%)",
                    ha="center", va="center",
                    color=color, fontsize=9,
                )
        n_total = int(cm.sum())
        acc = m["metrics"]["test"]["accuracy"] * 100
        ax.set_title(f"{m['label']}  —  acc {acc:.1f}%  (n={n_total})", fontsize=10)
        ax.set_xticks(range(len(CLASS_LABELS)))
        ax.set_yticks(range(len(CLASS_LABELS)))
        ax.set_xticklabels(CLASS_LABELS, rotation=20, ha="right", fontsize=9)
        ax.set_yticklabels(CLASS_LABELS, fontsize=9)
        ax.set_xlabel("predicted")
        ax.set_ylabel("true")
    fig.suptitle(
        "Macierze pomyłek na zbiorze test — wartości znormalizowane wierszami (recall)",
        fontsize=12, y=0.99,
    )
    fig.subplots_adjust(left=0.08, right=0.88, top=0.93, bottom=0.07,
                        wspace=0.25, hspace=0.45)
    cax = fig.add_axes([0.91, 0.15, 0.02, 0.7])
    fig.colorbar(im, cax=cax, label="recall")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    log.info(f"  zapisano {out_path}")


def plot_learning_curves_lstm(models: list[dict], out_path: Path) -> None:
    """Krzywe uczenia LSTM run 1 i run 2 — train/val loss + val_acc na osi prawej."""
    lstm_models = [m for m in models if m["kind"] == "lstm"]
    fig, axes = plt.subplots(1, len(lstm_models), figsize=(13, 5), sharey=False)
    if len(lstm_models) == 1:
        axes = [axes]

    for ax, m in zip(axes, lstm_models):
        hist = m["metrics"].get("history", [])
        epochs = [h["epoch"] for h in hist]
        train_loss = [h["train_loss"] for h in hist]
        val_loss = [h["val_loss"] for h in hist]
        val_acc = [h["val_acc"] for h in hist]
        best_epoch = m["metrics"]["config"].get("best_epoch")

        ax.plot(epochs, train_loss, label="train_loss", color="C0", linewidth=2)
        ax.plot(epochs, val_loss, label="val_loss", color="C3", linewidth=2)
        if best_epoch is not None:
            ax.axvline(
                best_epoch, color="black", linestyle="--", alpha=0.5,
                label=f"best epoch ({best_epoch})",
            )
        ax.set_xlabel("epoka")
        ax.set_ylabel("loss")
        ax.set_title(m["label"], fontsize=10)
        ax.grid(True, alpha=0.3)

        ax2 = ax.twinx()
        ax2.plot(epochs, val_acc, label="val_acc", color="C2", linewidth=1.5,
                 linestyle=":")
        ax2.set_ylabel("val_acc")
        ax2.set_ylim(0.5, 1.0)

        # Legendy z dwóch osi
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=8)

    fig.suptitle("Krzywe uczenia LSTM — porównanie dwóch konfiguracji", fontsize=12)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    log.info(f"  zapisano {out_path}")


def plot_feature_importances_rf(models: list[dict], out_path: Path, top_n: int = 15) -> None:
    """TOP-N feature importances obu RF w jednej figurze (poziome słupki)."""
    rf_models = [m for m in models if m["kind"] == "rf"]
    fig, axes = plt.subplots(1, len(rf_models), figsize=(13, 6), sharey=False)
    if len(rf_models) == 1:
        axes = [axes]

    for ax, m in zip(axes, rf_models):
        top = m["metrics"].get("top_features", [])[:top_n]
        # JSON: lista par [name, importance]
        names = [t[0] for t in top]
        imps = [t[1] for t in top]
        # Odwracamy żeby najważniejsze były na górze
        names = names[::-1]
        imps = imps[::-1]

        # Kolorowanie: kąty stawów / inne — wizualizacja "co dominuje"
        colors = []
        for n in names:
            ln = n.lower()
            if "angle" in ln or "lean" in ln:
                colors.append("C2")  # zielony — kąty
            elif "visibility" in ln:
                colors.append("C3")  # czerwony — visibility (artefakty kadrowania)
            else:
                colors.append("C0")  # niebieski — surowe / znormalizowane współrzędne

        ax.barh(range(len(names)), imps, color=colors)
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, fontsize=8)
        ax.set_xlabel("feature importance")
        ax.set_title(f"{m['label']} (TOP-{top_n})", fontsize=10)
        ax.grid(True, alpha=0.3, axis="x")

    # Legenda kolorów u góry figury
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="C2", label="kąt stawu / pochylenie"),
        Patch(facecolor="C0", label="współrzędna keypointu"),
        Patch(facecolor="C3", label="visibility (artefakt)"),
    ]
    fig.legend(handles=legend_elements, loc="upper center", ncol=3,
               bbox_to_anchor=(0.5, 1.02), fontsize=9)
    fig.suptitle(
        "Najważniejsze cechy w obu wariantach Random Forest",
        fontsize=12, y=1.05,
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    log.info(f"  zapisano {out_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analiza porównawcza klasyfikatorów (Etap 5.4)")
    parser.add_argument("--models-dir", type=Path, default=Path("models"))
    parser.add_argument("--output-dir", type=Path,
                        default=Path("docs/thesis-notes/figures"))
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    log.info(f"Wczytuję metryki z {args.models_dir}")
    models = load_all_metrics(args.models_dir)

    # Tabele Markdown + JSON
    log.info("Generuję comparison_table.md i comparison_summary.json")
    md_summary, rows_summary = build_summary_table(models)
    (args.output_dir / "comparison_table.md").write_text(md_summary, encoding="utf-8")
    (args.output_dir / "comparison_summary.json").write_text(
        json.dumps(rows_summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    log.info("Generuję per_file_test.md")
    md_perfile = build_per_file_table(models)
    (args.output_dir / "per_file_test.md").write_text(md_perfile, encoding="utf-8")

    log.info("Generuję error_breakdown.md")
    md_errors = build_error_breakdown(models)
    (args.output_dir / "error_breakdown.md").write_text(md_errors, encoding="utf-8")

    # Wykresy PNG
    log.info("Generuję wykresy:")
    plot_confusion_matrices_test(models, args.output_dir / "confusion_matrices_test.png")
    plot_learning_curves_lstm(models, args.output_dir / "learning_curves_lstm.png")
    plot_feature_importances_rf(models, args.output_dir / "feature_importances_rf.png")

    log.info(f"Gotowe. Artefakty w {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
