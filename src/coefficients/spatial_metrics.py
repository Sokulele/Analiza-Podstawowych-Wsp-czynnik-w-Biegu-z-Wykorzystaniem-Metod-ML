"""Współczynniki przestrzenne (kinematyczne) biegu — z keypointów + faz.

Oblicza:
- **Kąty stawów per faza**: kolana (L/R), biodra (L/R), kostki (L/R)
- **Pochylenie tułowia** (torso lean)
- **Vertical oscillation** — Δy hip per cykl, w jednostkach torso_length (znormalizowane)
- **Foot strike pattern** — kąt stopy względem podłoża w momencie initial contact (heel/mid/forefoot)

Wszystkie kąty są w stopniach. Jednostki długościowe — w `torso_length` (normalized to body),
chyba że oznaczono inaczej. Foot strike: kąt > 5° = heel strike, < −5° = forefoot, środek = mid.

Wymaga DataFrame'u z keypointami (smoothed) + kolumną `phase_predicted` (z run_inference.py).

Uruchomienie standalone:
    .venv/Scripts/python.exe src/coefficients/spatial_metrics.py \\
        --phases data/inference/24-adam-phases.csv \\
        --output-json data/inference/24-adam-spatial.json
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Z src/training importujemy funkcje pomocnicze do kątów (już istnieją w features.py)
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "training"))
from features import _angle_deg, _midpoint, _xyz  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

PHASE_LABELS = ("LEFT_STANCE", "RIGHT_STANCE", "FLIGHT")


def _stats_arr(values: np.ndarray) -> dict:
    """Mean / std / min / max / n dla pojedynczej tablicy wartości."""
    if len(values) == 0:
        return {"n": 0, "mean": None, "std": None, "min": None, "max": None}
    return {
        "n": int(len(values)),
        "mean": round(float(np.mean(values)), 2),
        "std": round(float(np.std(values)), 2),
        "min": round(float(np.min(values)), 2),
        "max": round(float(np.max(values)), 2),
    }


def compute_joint_angles_per_phase(df: pd.DataFrame, phases: np.ndarray) -> dict:
    """Kąty stawów (kolana, biodra, kostki — L/R) — mean ± std per faza.

    Kąty:
    - Kolano: biodro → kolano → kostka (mniejszy kąt = mocniejsze zgięcie)
    - Biodro: ramię → biodro → kolano
    - Kostka: kolano → kostka → palce stopy
    """
    # Pre-compute wszystkie kąty per klatka
    angles = {
        "left_knee": _angle_deg(_xyz(df, "LEFT_HIP"), _xyz(df, "LEFT_KNEE"), _xyz(df, "LEFT_ANKLE")),
        "right_knee": _angle_deg(_xyz(df, "RIGHT_HIP"), _xyz(df, "RIGHT_KNEE"), _xyz(df, "RIGHT_ANKLE")),
        "left_hip": _angle_deg(_xyz(df, "LEFT_SHOULDER"), _xyz(df, "LEFT_HIP"), _xyz(df, "LEFT_KNEE")),
        "right_hip": _angle_deg(_xyz(df, "RIGHT_SHOULDER"), _xyz(df, "RIGHT_HIP"), _xyz(df, "RIGHT_KNEE")),
        "left_ankle": _angle_deg(_xyz(df, "LEFT_KNEE"), _xyz(df, "LEFT_ANKLE"), _xyz(df, "LEFT_FOOT_INDEX")),
        "right_ankle": _angle_deg(_xyz(df, "RIGHT_KNEE"), _xyz(df, "RIGHT_ANKLE"), _xyz(df, "RIGHT_FOOT_INDEX")),
    }

    out: dict = {}
    for joint, vals in angles.items():
        out[joint] = {"overall": _stats_arr(vals)}
        for phase in PHASE_LABELS:
            mask = phases == phase
            out[joint][phase] = _stats_arr(vals[mask])
    return out


def compute_torso_lean(df: pd.DataFrame, phases: np.ndarray) -> dict:
    """Pochylenie tułowia względem pionu — kąt linii (mid_hip → mid_shoulder) vs (0, -1, 0).

    Wartości > 0 = pochylenie do przodu (typowe dla biegu).
    """
    mid_hip = _midpoint(df, "LEFT_HIP", "RIGHT_HIP")
    mid_shoulder = _midpoint(df, "LEFT_SHOULDER", "RIGHT_SHOULDER")
    torso_vec = mid_shoulder - mid_hip
    # MediaPipe Y rośnie w dół, więc "do góry" to (0, -1, 0). Używamy x, y (płaszczyzna obrazu)
    torso_2d = torso_vec[:, :2]
    vertical_2d = np.array([0.0, -1.0])
    norms = np.linalg.norm(torso_2d, axis=1)
    norms = np.where(norms < 1e-9, 1.0, norms)
    cos_theta = np.clip((torso_2d @ vertical_2d) / norms, -1.0, 1.0)
    angles = np.degrees(np.arccos(cos_theta))

    out = {"overall": _stats_arr(angles)}
    for phase in PHASE_LABELS:
        mask = phases == phase
        out[phase] = _stats_arr(angles[mask])
    return out


def compute_vertical_oscillation(df: pd.DataFrame, phases: np.ndarray, fps: float) -> dict:
    """Vertical oscillation — Δy mid_hip per cykl biegu.

    Cykl = od jednego kontaktu LEFT_STANCE do następnego LEFT_STANCE (lub R→R).
    Mierzymy max(Y_hip) - min(Y_hip) wewnątrz cyklu, potem mean ± std.

    Jednostka: surowa wartość Y (znormalizowana 0-1 jeśli dane MediaPipe lub pikselowa
    jeśli aspect fix był aplikowany). Plus znormalizowana przez `torso_length`.
    """
    mid_hip = _midpoint(df, "LEFT_HIP", "RIGHT_HIP")
    mid_shoulder = _midpoint(df, "LEFT_SHOULDER", "RIGHT_SHOULDER")
    torso_length = np.linalg.norm(mid_shoulder - mid_hip, axis=1)
    hip_y = mid_hip[:, 1]

    # Znajdź entry-into-LEFT_STANCE (granice cykli)
    n = len(phases)
    left_entries: list[int] = []
    if n > 0 and phases[0] == "LEFT_STANCE":
        left_entries.append(0)
    for i in range(1, n):
        if phases[i] == "LEFT_STANCE" and phases[i - 1] != "LEFT_STANCE":
            left_entries.append(i)

    oscillations_raw: list[float] = []
    oscillations_norm: list[float] = []
    for i in range(len(left_entries) - 1):
        s, e = left_entries[i], left_entries[i + 1]
        if e - s < 3:
            continue
        cycle_y = hip_y[s:e]
        delta = float(cycle_y.max() - cycle_y.min())
        oscillations_raw.append(delta)
        # Normalizuj długością tułowia w tym samym cyklu (mean torso w cyklu)
        torso_mean = float(np.mean(torso_length[s:e]))
        if torso_mean > 1e-9:
            oscillations_norm.append(delta / torso_mean)

    return {
        "vertical_oscillation_raw": _stats_arr(np.array(oscillations_raw)),
        "vertical_oscillation_per_torso": _stats_arr(np.array(oscillations_norm)),
        "n_cycles_used": len(oscillations_raw),
    }


def compute_foot_strike_pattern(df: pd.DataFrame, phases: np.ndarray) -> dict:
    """Foot strike pattern — kąt stopy w momencie kontaktu (entry into STANCE).

    Kąt stopy = wektor (HEEL → FOOT_INDEX) względem osi poziomej (X).
    - heel strike: HEEL niżej niż FOOT_INDEX → kąt > 0 (palce do góry)
    - forefoot:    FOOT_INDEX niżej niż HEEL → kąt < 0
    - midfoot:     ~0

    Konwencja MediaPipe: Y rośnie w dół, więc "niżej" = większe Y.
    Kąt = atan2(Δy, Δx) gdzie Δ = FOOT_INDEX - HEEL.
    Jeśli FOOT_INDEX_y > HEEL_y (palce niżej) → forefoot (kąt > 0 w MediaPipe Y-down).
    Konwertuję żeby intuicyjnie: heel strike → kąt > 0 (jak w fizjologii).
    """
    out: dict = {}
    for side in ("LEFT", "RIGHT"):
        heel = _xyz(df, f"{side}_HEEL")
        foot_idx = _xyz(df, f"{side}_FOOT_INDEX")
        # Wektor heel→foot_index w 2D (płaszczyzna obrazu)
        dx = foot_idx[:, 0] - heel[:, 0]
        dy = foot_idx[:, 1] - heel[:, 1]
        # Konwencja: heel strike = pięta na ziemi pierwsza = palce wyżej =
        # FOOT_INDEX_y < HEEL_y (mniejsze Y to wyżej w MediaPipe) → dy < 0
        # Konwersja na intuicyjny kąt: kąt > 0 = heel strike
        # arctan2(-dy, dx) — odwracamy y (bo MediaPipe Y-down)
        angles = np.degrees(np.arctan2(-dy, dx))

        # Dla jednoznaczności: bierzemy wartość bezwzględną odchylenia od linii poziomej
        # Heel strike: ~+10 do +30°, mid ~0°, forefoot ~−10 do −30°

        # Znajdź klatki wejścia w STANCE tej nogi
        target_stance = f"{side}_STANCE"
        n = len(phases)
        entries: list[int] = []
        if n > 0 and phases[0] == target_stance:
            entries.append(0)
        for i in range(1, n):
            if phases[i] == target_stance and phases[i - 1] != target_stance:
                entries.append(i)

        # Kąt w klatce kontaktu (entry frame)
        if entries:
            contact_angles = angles[entries]
            n_heel = int(np.sum(contact_angles > 5))
            n_mid = int(np.sum((contact_angles >= -5) & (contact_angles <= 5)))
            n_forefoot = int(np.sum(contact_angles < -5))
            stats = _stats_arr(contact_angles)
        else:
            contact_angles = np.array([])
            n_heel = n_mid = n_forefoot = 0
            stats = _stats_arr(contact_angles)

        # Klasyfikacja dominująca
        max_count = max(n_heel, n_mid, n_forefoot)
        if max_count == 0:
            dominant = "unknown"
        elif n_heel == max_count:
            dominant = "heel strike"
        elif n_forefoot == max_count:
            dominant = "forefoot strike"
        else:
            dominant = "midfoot strike"

        out[f"{side.lower()}_foot"] = {
            "contact_angle_deg": stats,
            "n_heel": n_heel,
            "n_mid": n_mid,
            "n_forefoot": n_forefoot,
            "dominant": dominant,
        }
    return out


def compute_knee_angle_at_initial_contact(df: pd.DataFrame, phases: np.ndarray) -> dict:
    """Kąt kolana w momencie kontaktu (entry into STANCE) per noga.

    Referencja: 160-175° = prawidłowy, >175° = overstriding, <155° = "siedzący" bieg.
    Używamy kąta kolana **tej nogi która właśnie uderza** (LEFT_KNEE w entry-into-LEFT_STANCE
    i RIGHT_KNEE w entry-into-RIGHT_STANCE).
    """
    angles = {
        "LEFT": _angle_deg(_xyz(df, "LEFT_HIP"), _xyz(df, "LEFT_KNEE"), _xyz(df, "LEFT_ANKLE")),
        "RIGHT": _angle_deg(_xyz(df, "RIGHT_HIP"), _xyz(df, "RIGHT_KNEE"), _xyz(df, "RIGHT_ANKLE")),
    }

    out: dict = {}
    n = len(phases)
    for side in ("LEFT", "RIGHT"):
        target = f"{side}_STANCE"
        entries: list[int] = []
        if n > 0 and phases[0] == target:
            entries.append(0)
        for i in range(1, n):
            if phases[i] == target and phases[i - 1] != target:
                entries.append(i)

        if entries:
            contact_knee_angles = angles[side][entries]
            out[f"{side.lower()}_knee"] = _stats_arr(contact_knee_angles)
        else:
            out[f"{side.lower()}_knee"] = _stats_arr(np.array([]))
    return out


def compute_spatial_metrics(df: pd.DataFrame, phases: np.ndarray, fps: float) -> dict:
    """Wszystkie współczynniki przestrzenne w jednym dictie."""
    return {
        "joint_angles": compute_joint_angles_per_phase(df, phases),
        "knee_angle_at_contact": compute_knee_angle_at_initial_contact(df, phases),
        "torso_lean": compute_torso_lean(df, phases),
        "vertical_oscillation": compute_vertical_oscillation(df, phases, fps),
        "foot_strike": compute_foot_strike_pattern(df, phases),
    }


def print_spatial_report(metrics: dict) -> None:
    """Czytelny raport tekstowy."""
    log.info("=" * 60)
    log.info("WSPÓŁCZYNNIKI PRZESTRZENNE (KINEMATYCZNE)")
    log.info("=" * 60)

    log.info("Kąty stawów [stopnie] (mean ± std per faza):")
    angles = metrics["joint_angles"]
    for joint in ("left_knee", "right_knee", "left_hip", "right_hip", "left_ankle", "right_ankle"):
        a = angles[joint]
        log.info(f"  {joint:<14} overall: {a['overall']['mean']:.1f} ± {a['overall']['std']:.1f} "
                 f"| L_STANCE: {a['LEFT_STANCE']['mean']}±{a['LEFT_STANCE']['std']} "
                 f"| R_STANCE: {a['RIGHT_STANCE']['mean']}±{a['RIGHT_STANCE']['std']} "
                 f"| FLIGHT: {a['FLIGHT']['mean']}±{a['FLIGHT']['std']}")

    if "knee_angle_at_contact" in metrics:
        kc = metrics["knee_angle_at_contact"]
        log.info(f"Kąt kolana @ initial contact: "
                 f"LEWA {kc['left_knee']['mean']}° ± {kc['left_knee']['std']} (n={kc['left_knee']['n']}), "
                 f"PRAWA {kc['right_knee']['mean']}° ± {kc['right_knee']['std']} (n={kc['right_knee']['n']})")

    tl = metrics["torso_lean"]
    log.info(f"Pochylenie tułowia: {tl['overall']['mean']:.1f}° ± {tl['overall']['std']:.1f} "
             f"(L_STANCE {tl['LEFT_STANCE']['mean']}, R_STANCE {tl['RIGHT_STANCE']['mean']}, FLIGHT {tl['FLIGHT']['mean']})")

    vo = metrics["vertical_oscillation"]
    log.info(f"Vertical oscillation (raw): {vo['vertical_oscillation_raw']['mean']:.4f} ± {vo['vertical_oscillation_raw']['std']:.4f} "
             f"(n_cycles={vo['n_cycles_used']})")
    log.info(f"Vertical oscillation (per torso): {vo['vertical_oscillation_per_torso']['mean']:.3f} ± {vo['vertical_oscillation_per_torso']['std']:.3f}")

    fs = metrics["foot_strike"]
    log.info(f"Foot strike LEWA:  {fs['left_foot']['dominant']} "
             f"(heel/mid/fore = {fs['left_foot']['n_heel']}/{fs['left_foot']['n_mid']}/{fs['left_foot']['n_forefoot']}, "
             f"kąt {fs['left_foot']['contact_angle_deg']['mean']:.1f}° ± {fs['left_foot']['contact_angle_deg']['std']:.1f}°)")
    log.info(f"Foot strike PRAWA: {fs['right_foot']['dominant']} "
             f"(heel/mid/fore = {fs['right_foot']['n_heel']}/{fs['right_foot']['n_mid']}/{fs['right_foot']['n_forefoot']}, "
             f"kąt {fs['right_foot']['contact_angle_deg']['mean']:.1f}° ± {fs['right_foot']['contact_angle_deg']['std']:.1f}°)")
    log.info("=" * 60)


def main() -> int:
    parser = argparse.ArgumentParser(description="Współczynniki przestrzenne biegu (Etap 6)")
    parser.add_argument("--phases", type=Path, required=True,
                        help="CSV z phases + keypointami (z run_inference.py --include-keypoints)")
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args()

    df = pd.read_csv(args.phases)
    if "phase_predicted" not in df.columns:
        raise KeyError("CSV nie ma kolumny phase_predicted. Czy to wyjście run_inference.py?")
    if "LEFT_HIP_x" not in df.columns:
        raise KeyError("CSV nie ma keypointów. Uruchom run_inference.py z --include-keypoints.")

    phases = df["phase_predicted"].to_numpy()
    if len(df) >= 2:
        dt = df["timestamp"].iloc[1] - df["timestamp"].iloc[0]
        fps = 1.0 / dt if dt > 0 else 30.0
    else:
        fps = 30.0
    log.info(f"FPS: {fps:.2f}, klatek: {len(df)}")

    metrics = compute_spatial_metrics(df, phases, fps)
    print_spatial_report(metrics)

    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info(f"Zapisano JSON: {args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
