"""Współczynniki temporalne biegu — z sekwencji faz + FPS.

Oblicza:
- **Kadencja** [spm = steps per minute] — liczba kontaktów stóp na minutę
- **GCT (Ground Contact Time)** — czas kontaktu stopy z ziemią, osobno L/R
- **Czas lotu** (flight time)
- **Czas cyklu** (stride duration) — od kontaktu jednej stopy do następnego kontaktu **tej samej** stopy
- **Duty factor** — GCT / cycle_time, frakcja cyklu w kontakcie z ziemią

Algorytm:
1. Wykrywanie segmentów STANCE/FLIGHT z sekwencji faz (run-length encoding)
2. Statystyki per segment: mean ± std, min, max, n

Stride length jest liczone **tylko** gdy podana prędkość bieżni (`treadmill_speed_ms`):
`stride = speed × cycle_time`. Bez tego inputu klucz `stride_length` jest pomijany,
a pozostałe metryki są niezależne od prędkości.

Uruchomienie standalone:
    .venv/Scripts/python.exe src/coefficients/temporal_metrics.py \\
        --phases data/inference/24-adam-phases.csv
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


@dataclass
class Segment:
    """Jeden segment fazy (np. LEFT_STANCE od klatki 10 do 20)."""
    phase: str
    start: int   # frame index
    end: int     # frame index (exclusive)
    n_frames: int
    duration_s: float


def find_segments(phases: np.ndarray, fps: float) -> list[Segment]:
    """Run-length encoding sekwencji etykiet → lista segmentów."""
    if len(phases) == 0:
        return []
    segments: list[Segment] = []
    cur = phases[0]
    start = 0
    for i in range(1, len(phases)):
        if phases[i] != cur:
            n = i - start
            segments.append(Segment(cur, start, i, n, n / fps))
            cur = phases[i]
            start = i
    n = len(phases) - start
    segments.append(Segment(cur, start, len(phases), n, n / fps))
    return segments


def _stats(durations_s: list[float]) -> dict:
    """Mean / std / min / max / n / mean_ms (do raportowania)."""
    if not durations_s:
        return {"n": 0, "mean_s": None, "std_s": None, "min_s": None, "max_s": None}
    arr = np.array(durations_s)
    return {
        "n": len(durations_s),
        "mean_s": round(float(arr.mean()), 4),
        "std_s": round(float(arr.std()), 4),
        "min_s": round(float(arr.min()), 4),
        "max_s": round(float(arr.max()), 4),
        "mean_ms": round(float(arr.mean() * 1000), 1),
        "std_ms": round(float(arr.std() * 1000), 1),
    }


def compute_cadence(phases: np.ndarray, fps: float) -> dict:
    """Kadencja [spm] = liczba kontaktów stóp / minutę.

    Krok = wejście w STANCE (LEFT lub RIGHT). Liczymy transitions FLIGHT → STANCE.
    """
    n = len(phases)
    duration_s = n / fps if fps > 0 else 0.0
    if duration_s <= 0:
        return {"cadence_spm": 0.0, "n_steps": 0, "duration_s": 0.0}

    n_steps = 0
    n_left = 0
    n_right = 0
    for i in range(1, n):
        # entry into stance: previous != stance, current == stance
        prev_is_stance = phases[i - 1] in ("LEFT_STANCE", "RIGHT_STANCE")
        curr = phases[i]
        if curr in ("LEFT_STANCE", "RIGHT_STANCE") and not prev_is_stance:
            n_steps += 1
            if curr == "LEFT_STANCE":
                n_left += 1
            else:
                n_right += 1
    # +1 jeśli pierwsza klatka jest STANCE (pierwszy krok już zaczęty)
    if n > 0 and phases[0] in ("LEFT_STANCE", "RIGHT_STANCE"):
        n_steps += 1
        if phases[0] == "LEFT_STANCE":
            n_left += 1
        else:
            n_right += 1

    cadence_spm = (n_steps / duration_s) * 60.0
    return {
        "cadence_spm": round(cadence_spm, 1),
        "n_steps_total": n_steps,
        "n_steps_left": n_left,
        "n_steps_right": n_right,
        "duration_s": round(duration_s, 2),
    }


def compute_phase_durations(phases: np.ndarray, fps: float) -> dict:
    """Czasy segmentów per faza (GCT L/R, flight) — mean ± std."""
    segments = find_segments(phases, fps)

    durations_left = [s.duration_s for s in segments if s.phase == "LEFT_STANCE"]
    durations_right = [s.duration_s for s in segments if s.phase == "RIGHT_STANCE"]
    durations_flight = [s.duration_s for s in segments if s.phase == "FLIGHT"]

    return {
        "gct_left": _stats(durations_left),
        "gct_right": _stats(durations_right),
        "flight": _stats(durations_flight),
    }


def compute_cycle_time(phases: np.ndarray, fps: float) -> dict:
    """Czas cyklu (stride duration) = od jednego kontaktu nogi do następnego kontaktu **tej samej** nogi.

    Cykl L: klatka i (entry into LEFT_STANCE) → klatka j (next entry into LEFT_STANCE).
    Analogicznie R. Mean ± std per noga, łącznie.
    """
    # Znajdź indeksy entry-into-stance per noga
    n = len(phases)
    left_entries: list[int] = []
    right_entries: list[int] = []
    if n > 0:
        if phases[0] == "LEFT_STANCE":
            left_entries.append(0)
        elif phases[0] == "RIGHT_STANCE":
            right_entries.append(0)
    for i in range(1, n):
        prev_is_left = phases[i - 1] == "LEFT_STANCE"
        prev_is_right = phases[i - 1] == "RIGHT_STANCE"
        if phases[i] == "LEFT_STANCE" and not prev_is_left:
            left_entries.append(i)
        elif phases[i] == "RIGHT_STANCE" and not prev_is_right:
            right_entries.append(i)

    # Cykle = różnice kolejnych entries (w klatkach → sekundy)
    cycles_left = [(left_entries[i + 1] - left_entries[i]) / fps for i in range(len(left_entries) - 1)]
    cycles_right = [(right_entries[i + 1] - right_entries[i]) / fps for i in range(len(right_entries) - 1)]

    return {
        "cycle_left": _stats(cycles_left),
        "cycle_right": _stats(cycles_right),
        "cycle_combined": _stats(cycles_left + cycles_right),
    }


def compute_stride_length(cycle_time: dict, treadmill_speed_ms: float) -> dict:
    """Stride length [m] = treadmill_speed × cycle_time.

    Cycle = od kontaktu nogi do następnego kontaktu **tej samej** nogi (czyli pełny
    cykl ruchu, 2 step length w klasycznej terminologii biomechanicznej).
    """
    out: dict = {"treadmill_speed_ms": round(float(treadmill_speed_ms), 3)}
    for side_key, out_key in (
        ("cycle_left", "stride_left"),
        ("cycle_right", "stride_right"),
        ("cycle_combined", "stride_combined"),
    ):
        ct = cycle_time.get(side_key, {})
        mean_s = ct.get("mean_s")
        std_s = ct.get("std_s")
        n = ct.get("n", 0)
        if mean_s is None or n == 0:
            out[out_key] = {"n": 0, "mean_m": None, "std_m": None}
            continue
        out[out_key] = {
            "n": int(n),
            "mean_m": round(mean_s * treadmill_speed_ms, 3),
            "std_m": round((std_s or 0.0) * treadmill_speed_ms, 3),
        }
    return out


def compute_duty_factor(phase_durations: dict, cycle_time: dict) -> dict:
    """Duty factor = GCT / cycle_time, osobno L/R i kombinowany.

    Przyjmujemy że cycle_time_left odpowiada GCT_left (nie jest to ideal:
    1 cykl L zawiera 1 stance L i jeden bezpośrednio po L, ale takie uproszczenie
    jest powszechne w literaturze).
    """
    df_left = None
    df_right = None
    if phase_durations["gct_left"]["n"] > 0 and cycle_time["cycle_left"]["n"] > 0:
        df_left = round(phase_durations["gct_left"]["mean_s"] / cycle_time["cycle_left"]["mean_s"], 3)
    if phase_durations["gct_right"]["n"] > 0 and cycle_time["cycle_right"]["n"] > 0:
        df_right = round(phase_durations["gct_right"]["mean_s"] / cycle_time["cycle_right"]["mean_s"], 3)

    return {
        "duty_factor_left": df_left,
        "duty_factor_right": df_right,
    }


def compute_temporal_metrics(
    phases: np.ndarray,
    fps: float,
    treadmill_speed_ms: float | None = None,
) -> dict:
    """Wszystkie współczynniki temporalne w jednym dictie.

    Args:
        phases: sekwencja etykiet faz (LEFT_STANCE / RIGHT_STANCE / FLIGHT / DOUBLE_SUPPORT)
        fps: częstotliwość klatek wideo
        treadmill_speed_ms: prędkość bieżni [m/s]; jeśli podana, dodawany jest klucz
            `stride_length`. Wymagany input od użytkownika — nie da się wyliczyć z samego wideo.
    """
    cadence = compute_cadence(phases, fps)
    phase_durations = compute_phase_durations(phases, fps)
    cycle_time = compute_cycle_time(phases, fps)
    duty_factor = compute_duty_factor(phase_durations, cycle_time)

    result = {
        "fps": round(fps, 2),
        "n_frames": int(len(phases)),
        "cadence": cadence,
        "phase_durations": phase_durations,
        "cycle_time": cycle_time,
        "duty_factor": duty_factor,
    }

    if treadmill_speed_ms is not None and treadmill_speed_ms > 0:
        result["stride_length"] = compute_stride_length(cycle_time, treadmill_speed_ms)

    return result


def print_temporal_report(metrics: dict) -> None:
    """Czytelny raport tekstowy."""
    log.info("=" * 60)
    log.info("WSPÓŁCZYNNIKI TEMPORALNE")
    log.info("=" * 60)
    c = metrics["cadence"]
    log.info(f"Kadencja:        {c['cadence_spm']:.1f} spm "
             f"(n={c['n_steps_total']}, L={c['n_steps_left']}, R={c['n_steps_right']}, czas {c['duration_s']:.1f}s)")

    pd_ = metrics["phase_durations"]
    log.info(f"GCT lewa noga:   {pd_['gct_left']['mean_ms']:.0f} ± {pd_['gct_left']['std_ms']:.0f} ms "
             f"(n={pd_['gct_left']['n']}, range [{pd_['gct_left']['min_s']*1000:.0f}, {pd_['gct_left']['max_s']*1000:.0f}] ms)")
    log.info(f"GCT prawa noga:  {pd_['gct_right']['mean_ms']:.0f} ± {pd_['gct_right']['std_ms']:.0f} ms "
             f"(n={pd_['gct_right']['n']}, range [{pd_['gct_right']['min_s']*1000:.0f}, {pd_['gct_right']['max_s']*1000:.0f}] ms)")
    log.info(f"Flight time:     {pd_['flight']['mean_ms']:.0f} ± {pd_['flight']['std_ms']:.0f} ms "
             f"(n={pd_['flight']['n']}, range [{pd_['flight']['min_s']*1000:.0f}, {pd_['flight']['max_s']*1000:.0f}] ms)")

    ct = metrics["cycle_time"]
    log.info(f"Czas cyklu L:    {ct['cycle_left']['mean_ms']:.0f} ± {ct['cycle_left']['std_ms']:.0f} ms (n={ct['cycle_left']['n']})")
    log.info(f"Czas cyklu R:    {ct['cycle_right']['mean_ms']:.0f} ± {ct['cycle_right']['std_ms']:.0f} ms (n={ct['cycle_right']['n']})")

    df = metrics["duty_factor"]
    log.info(f"Duty factor L:   {df['duty_factor_left']}")
    log.info(f"Duty factor R:   {df['duty_factor_right']}")

    sl = metrics.get("stride_length")
    if sl:
        combined = sl["stride_combined"]
        log.info(f"Stride length:   {combined['mean_m']:.2f} ± {combined['std_m']:.2f} m "
                 f"(speed {sl['treadmill_speed_ms']:.2f} m/s, n={combined['n']})")
    log.info("=" * 60)


def main() -> int:
    parser = argparse.ArgumentParser(description="Współczynniki temporalne biegu (Etap 6)")
    parser.add_argument("--phases", type=Path, required=True,
                        help="CSV z kolumnami frame, timestamp, phase_predicted (z run_inference.py)")
    parser.add_argument("--fps", type=float, default=None,
                        help="FPS wideo (default: estymacja z timestamp[1]-timestamp[0])")
    parser.add_argument("--treadmill-speed-ms", type=float, default=None,
                        help="Prędkość bieżni [m/s]; jeśli podane, doda klucz stride_length do JSON")
    parser.add_argument("--output-json", type=Path, default=None,
                        help="Zapisz metryki do JSON (opcjonalnie)")
    args = parser.parse_args()

    df = pd.read_csv(args.phases)
    if "phase_predicted" not in df.columns:
        raise KeyError("CSV nie ma kolumny phase_predicted. Czy to wyjście run_inference.py?")

    phases = df["phase_predicted"].to_numpy()

    if args.fps is None:
        if len(df) >= 2:
            dt = df["timestamp"].iloc[1] - df["timestamp"].iloc[0]
            fps = 1.0 / dt if dt > 0 else 30.0
        else:
            fps = 30.0
    else:
        fps = args.fps
    log.info(f"FPS: {fps:.2f} (estymacja z timestamp)")

    metrics = compute_temporal_metrics(phases, fps, treadmill_speed_ms=args.treadmill_speed_ms)
    print_temporal_report(metrics)

    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info(f"Zapisano JSON: {args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
