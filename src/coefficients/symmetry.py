"""Symetria L/P — różnice między lewą a prawą stroną biegacza.

Wskaźniki symetrii (Symmetry Index, SI):
    SI = 200% × |L - R| / (L + R)   [%]

- SI = 0% → idealna symetria
- SI < 5% → typowa zdrowa biomechanika
- SI > 10% → znacząca asymetria, kandydat do uwagi rehabilitacyjnej

Wymaga wyników z `temporal_metrics` i `spatial_metrics` (JSON lub dict in-memory).

Uruchomienie:
    .venv/Scripts/python.exe src/coefficients/symmetry.py \\
        --temporal-json data/inference/24-adam-temporal.json \\
        --spatial-json  data/inference/24-adam-spatial.json
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def symmetry_index(left: float | None, right: float | None) -> float | None:
    """Symmetry Index [%] = 200 × |L - R| / (L + R). Robert SI (Robinson 1987)."""
    if left is None or right is None:
        return None
    s = left + right
    if abs(s) < 1e-9:
        return None
    return round(200.0 * abs(left - right) / s, 2)


def _classify_si(si: float | None) -> str:
    """Heurystyka: 0-5% normal, 5-10% mild, >10% significant."""
    if si is None:
        return "—"
    if si < 5:
        return "symetria zdrowa"
    if si < 10:
        return "asymetria łagodna"
    return "asymetria znacząca"


def compute_symmetry(temporal: dict, spatial: dict) -> dict:
    """Zbierz wszystkie pary L/P i policz SI dla każdej."""
    out: dict = {}

    # GCT L vs R
    gct_l = temporal["phase_durations"]["gct_left"].get("mean_s")
    gct_r = temporal["phase_durations"]["gct_right"].get("mean_s")
    si_gct = symmetry_index(gct_l, gct_r)
    out["gct"] = {
        "left_ms": (gct_l * 1000 if gct_l else None),
        "right_ms": (gct_r * 1000 if gct_r else None),
        "delta_ms": (round((gct_r - gct_l) * 1000, 1) if gct_l and gct_r else None),
        "symmetry_index_pct": si_gct,
        "classification": _classify_si(si_gct),
    }

    # Czas cyklu L vs R
    ct_l = temporal["cycle_time"]["cycle_left"].get("mean_s")
    ct_r = temporal["cycle_time"]["cycle_right"].get("mean_s")
    si_ct = symmetry_index(ct_l, ct_r)
    out["cycle_time"] = {
        "left_ms": (ct_l * 1000 if ct_l else None),
        "right_ms": (ct_r * 1000 if ct_r else None),
        "delta_ms": (round((ct_r - ct_l) * 1000, 1) if ct_l and ct_r else None),
        "symmetry_index_pct": si_ct,
        "classification": _classify_si(si_ct),
    }

    # Duty factor L vs R
    df_l = temporal["duty_factor"].get("duty_factor_left")
    df_r = temporal["duty_factor"].get("duty_factor_right")
    si_df = symmetry_index(df_l, df_r)
    out["duty_factor"] = {
        "left": df_l,
        "right": df_r,
        "delta": (round(df_r - df_l, 3) if df_l and df_r else None),
        "symmetry_index_pct": si_df,
        "classification": _classify_si(si_df),
    }

    # Kąt kolana w STANCE — porównujemy left_knee@LEFT_STANCE vs right_knee@RIGHT_STANCE
    # (kolano oporowe w stance własnej nogi)
    angles = spatial["joint_angles"]
    left_knee_stance = angles["left_knee"]["LEFT_STANCE"]["mean"]
    right_knee_stance = angles["right_knee"]["RIGHT_STANCE"]["mean"]
    si_knee = symmetry_index(left_knee_stance, right_knee_stance)
    out["knee_angle_stance"] = {
        "left_deg": left_knee_stance,
        "right_deg": right_knee_stance,
        "delta_deg": (round(right_knee_stance - left_knee_stance, 2) if left_knee_stance and right_knee_stance else None),
        "symmetry_index_pct": si_knee,
        "classification": _classify_si(si_knee),
    }

    # Kąt kostki w STANCE
    left_ankle_stance = angles["left_ankle"]["LEFT_STANCE"]["mean"]
    right_ankle_stance = angles["right_ankle"]["RIGHT_STANCE"]["mean"]
    si_ankle = symmetry_index(left_ankle_stance, right_ankle_stance)
    out["ankle_angle_stance"] = {
        "left_deg": left_ankle_stance,
        "right_deg": right_ankle_stance,
        "delta_deg": (round(right_ankle_stance - left_ankle_stance, 2) if left_ankle_stance and right_ankle_stance else None),
        "symmetry_index_pct": si_ankle,
        "classification": _classify_si(si_ankle),
    }

    # Foot strike — porównujemy procent forefoot per noga
    fs = spatial["foot_strike"]
    l_total = fs["left_foot"]["n_heel"] + fs["left_foot"]["n_mid"] + fs["left_foot"]["n_forefoot"]
    r_total = fs["right_foot"]["n_heel"] + fs["right_foot"]["n_mid"] + fs["right_foot"]["n_forefoot"]
    pct_l_fore = (fs["left_foot"]["n_forefoot"] / l_total * 100) if l_total else None
    pct_r_fore = (fs["right_foot"]["n_forefoot"] / r_total * 100) if r_total else None
    out["foot_strike"] = {
        "left_dominant": fs["left_foot"]["dominant"],
        "right_dominant": fs["right_foot"]["dominant"],
        "left_pct_forefoot": (round(pct_l_fore, 1) if pct_l_fore is not None else None),
        "right_pct_forefoot": (round(pct_r_fore, 1) if pct_r_fore is not None else None),
        "consistent": fs["left_foot"]["dominant"] == fs["right_foot"]["dominant"],
    }

    # Globalna ocena
    si_values = [
        out["gct"]["symmetry_index_pct"],
        out["cycle_time"]["symmetry_index_pct"],
        out["duty_factor"]["symmetry_index_pct"],
        out["knee_angle_stance"]["symmetry_index_pct"],
        out["ankle_angle_stance"]["symmetry_index_pct"],
    ]
    si_values = [v for v in si_values if v is not None]
    if si_values:
        out["overall"] = {
            "max_si_pct": round(max(si_values), 2),
            "mean_si_pct": round(sum(si_values) / len(si_values), 2),
        }

    return out


def print_symmetry_report(symmetry: dict) -> None:
    log.info("=" * 60)
    log.info("SYMETRIA L/P (Symmetry Index = 200 × |L−R| / (L+R))")
    log.info("=" * 60)

    g = symmetry["gct"]
    log.info(f"GCT:          L={g['left_ms']:.0f} ms, R={g['right_ms']:.0f} ms, "
             f"Δ={g['delta_ms']:+.1f} ms, SI={g['symmetry_index_pct']}% ({g['classification']})")

    ct = symmetry["cycle_time"]
    log.info(f"Cycle time:   L={ct['left_ms']:.0f} ms, R={ct['right_ms']:.0f} ms, "
             f"Δ={ct['delta_ms']:+.1f} ms, SI={ct['symmetry_index_pct']}% ({ct['classification']})")

    d = symmetry["duty_factor"]
    log.info(f"Duty factor:  L={d['left']}, R={d['right']}, "
             f"Δ={d['delta']:+.3f}, SI={d['symmetry_index_pct']}% ({d['classification']})")

    k = symmetry["knee_angle_stance"]
    log.info(f"Knee@STANCE:  L={k['left_deg']:.1f}°, R={k['right_deg']:.1f}°, "
             f"Δ={k['delta_deg']:+.2f}°, SI={k['symmetry_index_pct']}% ({k['classification']})")

    a = symmetry["ankle_angle_stance"]
    log.info(f"Ankle@STANCE: L={a['left_deg']:.1f}°, R={a['right_deg']:.1f}°, "
             f"Δ={a['delta_deg']:+.2f}°, SI={a['symmetry_index_pct']}% ({a['classification']})")

    fs = symmetry["foot_strike"]
    log.info(f"Foot strike:  L={fs['left_dominant']} ({fs['left_pct_forefoot']}% forefoot), "
             f"R={fs['right_dominant']} ({fs['right_pct_forefoot']}% forefoot), "
             f"consistent={fs['consistent']}")

    if "overall" in symmetry:
        o = symmetry["overall"]
        log.info(f"OGÓLNIE:      max SI = {o['max_si_pct']}%, mean SI = {o['mean_si_pct']}%")
    log.info("=" * 60)


def main() -> int:
    parser = argparse.ArgumentParser(description="Współczynniki symetrii L/P (Etap 6)")
    parser.add_argument("--temporal-json", type=Path, required=True)
    parser.add_argument("--spatial-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args()

    temporal = json.loads(args.temporal_json.read_text(encoding="utf-8"))
    spatial = json.loads(args.spatial_json.read_text(encoding="utf-8"))

    symmetry = compute_symmetry(temporal, spatial)
    print_symmetry_report(symmetry)

    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(symmetry, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info(f"Zapisano JSON: {args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
