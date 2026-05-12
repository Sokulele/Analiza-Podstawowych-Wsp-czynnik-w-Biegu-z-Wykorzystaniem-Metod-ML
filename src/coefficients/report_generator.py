"""Generator raportu Markdown per biegacz.

Łączy wyniki z `temporal_metrics`, `spatial_metrics`, `symmetry` z klasyfikacją
względem `reference_values`. Output: 1 plik MD z tabelami + sekcją Wnioski.

Format raportu:
1. Header — meta (wideo, długość, FPS, klatki, model)
2. Temporal — kadencja, GCT L/R, flight, cycle, duty factor (z klasyfikacją)
3. Spatial — kąty stawów @ initial contact, torso lean, vertical osc, foot strike
4. Symmetry — SI per metryka, klasyfikacja
5. Wnioski — lista warningów posortowana priorytetem
6. Surowe dane — pełne wartości (mean ± std, n) jako tabele

Uruchomienie standalone (zwykle wywołane z `analyze.py`):
    .venv/Scripts/python.exe src/coefficients/report_generator.py \\
        --temporal-json data/inference/24-adam-temporal.json \\
        --spatial-json  data/inference/24-adam-spatial.json \\
        --symmetry-json data/inference/24-adam-symmetry.json \\
        --meta-json     data/inference/24-adam-meta.json \\
        --output        data/inference/raporty/24-adam.md
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from reference_values import Classification, classify_value, get_recommendation  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _row(name: str, value: str, classification: Classification, comment: str = "") -> str:
    """Wiersz tabeli MD: | metric | value | classification | warnings | comment |."""
    emoji = classification.status_emoji()
    label = classification.label
    warns = "; ".join(classification.warnings) if classification.warnings else "—"
    return f"| {name} | {value} | {emoji} {label} | {warns} | {comment} |"


def _header_table() -> list[str]:
    return [
        "| Współczynnik | Wartość | Klasyfikacja | Ostrzeżenia | Komentarz |",
        "|---|---|---|---|---|",
    ]


def _section_temporal(temporal: dict) -> tuple[list[str], list[str]]:
    """Sekcja temporal — zwraca (lines, warnings_collected)."""
    lines: list[str] = ["## Temporal — wskaźniki czasowe", ""]
    lines.extend(_header_table())
    warnings_all: list[str] = []

    # Kadencja
    cad = temporal["cadence"]["cadence_spm"]
    cls = classify_value(cad, "cadence_spm")
    lines.append(_row("Kadencja [spm]", f"{cad}", cls,
                      f"n_steps={temporal['cadence']['n_steps_total']}, "
                      f"L/R={temporal['cadence']['n_steps_left']}/{temporal['cadence']['n_steps_right']}"))
    warnings_all.extend(cls.warnings)

    # GCT L/R
    gct_l = temporal["phase_durations"]["gct_left"]
    gct_r = temporal["phase_durations"]["gct_right"]
    if gct_l["mean_ms"] is not None:
        cls = classify_value(gct_l["mean_ms"], "gct_ms")
        lines.append(_row("GCT lewa [ms]", f"{gct_l['mean_ms']:.0f} ± {gct_l['std_ms']:.0f}",
                          cls, f"n={gct_l['n']}"))
        warnings_all.extend(f"GCT lewa: {w}" for w in cls.warnings)
    if gct_r["mean_ms"] is not None:
        cls = classify_value(gct_r["mean_ms"], "gct_ms")
        lines.append(_row("GCT prawa [ms]", f"{gct_r['mean_ms']:.0f} ± {gct_r['std_ms']:.0f}",
                          cls, f"n={gct_r['n']}"))
        warnings_all.extend(f"GCT prawa: {w}" for w in cls.warnings)

    # Flight
    fl = temporal["phase_durations"]["flight"]
    if fl["mean_ms"] is not None:
        cls = classify_value(fl["mean_ms"], "flight_ms")
        lines.append(_row("Flight time [ms]", f"{fl['mean_ms']:.0f} ± {fl['std_ms']:.0f}",
                          cls, f"n={fl['n']}"))
        warnings_all.extend(f"Flight: {w}" for w in cls.warnings)

    # Cycle time (informacyjnie)
    ct = temporal["cycle_time"]
    if ct["cycle_combined"]["mean_ms"] is not None:
        cls_no = Classification(ct["cycle_combined"]["mean_ms"], "—", [], "ms")
        lines.append(_row("Cycle time [ms]",
                          f"{ct['cycle_combined']['mean_ms']:.0f} ± {ct['cycle_combined']['std_ms']:.0f}",
                          cls_no, f"L={ct['cycle_left']['mean_ms']:.0f}, R={ct['cycle_right']['mean_ms']:.0f}"))

    # Duty factor
    df_l = temporal["duty_factor"]["duty_factor_left"]
    df_r = temporal["duty_factor"]["duty_factor_right"]
    if df_l is not None:
        cls = classify_value(df_l, "duty_factor")
        lines.append(_row("Duty factor lewa", f"{df_l}", cls, ""))
        warnings_all.extend(f"Duty factor L: {w}" for w in cls.warnings)
    if df_r is not None:
        cls = classify_value(df_r, "duty_factor")
        lines.append(_row("Duty factor prawa", f"{df_r}", cls, ""))
        warnings_all.extend(f"Duty factor R: {w}" for w in cls.warnings)

    lines.append("")
    rec = get_recommendation("cadence_spm")
    if rec:
        lines.append(f"_Rekomendacja kadencji_: {rec}")
        lines.append("")

    return lines, warnings_all


def _section_spatial(spatial: dict) -> tuple[list[str], list[str]]:
    lines: list[str] = ["## Spatial — wskaźniki kinematyczne", ""]
    lines.extend(_header_table())
    warnings_all: list[str] = []

    # Knee angle at initial contact (preferred over per-phase)
    if "knee_angle_at_contact" in spatial:
        kc = spatial["knee_angle_at_contact"]
        for side, key in (("LEWA", "left_knee"), ("PRAWA", "right_knee")):
            stat = kc[key]
            if stat["mean"] is not None:
                cls = classify_value(stat["mean"], "knee_angle_initial_contact_deg")
                lines.append(_row(f"Kąt kolana @ initial contact {side} [°]",
                                  f"{stat['mean']:.1f} ± {stat['std']:.1f}",
                                  cls, f"n={stat['n']}"))
                warnings_all.extend(f"Knee@contact {side}: {w}" for w in cls.warnings)

    # Torso lean
    tl = spatial["torso_lean"]["overall"]
    if tl["mean"] is not None:
        cls = classify_value(tl["mean"], "torso_lean_deg")
        lines.append(_row("Pochylenie tułowia [°]", f"{tl['mean']:.1f} ± {tl['std']:.1f}",
                          cls, f"n={tl['n']}"))
        warnings_all.extend(f"Tułów: {w}" for w in cls.warnings)

    # Vertical oscillation per torso (raw cm pominięte bo brak kalibracji)
    vo_pt = spatial["vertical_oscillation"]["vertical_oscillation_per_torso"]
    if vo_pt["mean"] is not None:
        cls = classify_value(vo_pt["mean"], "vertical_oscillation_per_torso")
        lines.append(_row("Vertical oscillation (per torso)",
                          f"{vo_pt['mean']:.3f} ± {vo_pt['std']:.3f}",
                          cls,
                          f"n_cycles={spatial['vertical_oscillation']['n_cycles_used']}"))
        warnings_all.extend(f"Vertical osc: {w}" for w in cls.warnings)

    # Foot strike
    fs = spatial["foot_strike"]
    for side, key in (("LEWA", "left_foot"), ("PRAWA", "right_foot")):
        d = fs[key]
        total = d["n_heel"] + d["n_mid"] + d["n_forefoot"]
        if total > 0:
            cls_no = Classification(None, d["dominant"], [], "")
            comment = (f"H/M/F = {d['n_heel']}/{d['n_mid']}/{d['n_forefoot']} "
                       f"({d['n_heel']/total*100:.0f}%/{d['n_mid']/total*100:.0f}%/{d['n_forefoot']/total*100:.0f}%), "
                       f"kąt {d['contact_angle_deg']['mean']:.1f}°")
            lines.append(_row(f"Foot strike {side}", d["dominant"], cls_no, comment))

    lines.append("")
    rec = get_recommendation("vertical_oscillation_per_torso")
    if rec:
        lines.append(f"_Vertical oscillation_: {rec}")
        lines.append("")
    rec = get_recommendation("foot_strike_distribution")
    if rec:
        lines.append(f"_Foot strike_: {rec}")
        lines.append("")

    return lines, warnings_all


def _section_symmetry(symmetry: dict) -> tuple[list[str], list[str]]:
    lines: list[str] = ["## Symetria L/P", ""]
    lines.extend([
        "| Wskaźnik | L | R | Δ | SI [%] | Klasyfikacja |",
        "|---|---|---|---|---|---|",
    ])
    warnings_all: list[str] = []

    def add_row(name: str, key: str, fmt_l: str, fmt_r: str, fmt_d: str) -> None:
        d = symmetry[key]
        si = d.get("symmetry_index_pct")
        cls = classify_value(si, "symmetry_si_pct")
        lines.append(
            f"| {name} | {fmt_l} | {fmt_r} | {fmt_d} | {si if si is not None else '—'} "
            f"| {cls.status_emoji()} {cls.label} |"
        )
        if si is not None and si > 5:
            warnings_all.append(f"{name}: asymetria {cls.label} (SI={si}%)")

    # GCT
    g = symmetry["gct"]
    if g.get("left_ms") is not None:
        add_row("GCT [ms]", "gct",
                f"{g['left_ms']:.0f}", f"{g['right_ms']:.0f}",
                f"{g['delta_ms']:+.1f}")
    # Cycle time
    ct = symmetry["cycle_time"]
    if ct.get("left_ms") is not None:
        add_row("Cycle time [ms]", "cycle_time",
                f"{ct['left_ms']:.0f}", f"{ct['right_ms']:.0f}",
                f"{ct['delta_ms']:+.1f}")
    # Duty factor
    df_ = symmetry["duty_factor"]
    if df_.get("left") is not None:
        add_row("Duty factor", "duty_factor",
                f"{df_['left']}", f"{df_['right']}",
                f"{df_['delta']:+.3f}")
    # Knee angle stance
    k = symmetry["knee_angle_stance"]
    if k.get("left_deg") is not None:
        add_row("Kąt kolana @ stance [°]", "knee_angle_stance",
                f"{k['left_deg']:.1f}", f"{k['right_deg']:.1f}",
                f"{k['delta_deg']:+.2f}")
    # Ankle angle stance
    a = symmetry["ankle_angle_stance"]
    if a.get("left_deg") is not None:
        add_row("Kąt kostki @ stance [°]", "ankle_angle_stance",
                f"{a['left_deg']:.1f}", f"{a['right_deg']:.1f}",
                f"{a['delta_deg']:+.2f}")

    # Foot strike consistency (osobno, nie jako SI)
    fs = symmetry["foot_strike"]
    consistent = "✅ tak" if fs["consistent"] else "🟡 nie"
    lines.append("")
    lines.append(f"**Foot strike consistency**: {consistent} "
                 f"(L={fs['left_dominant']} {fs['left_pct_forefoot']}% forefoot, "
                 f"R={fs['right_dominant']} {fs['right_pct_forefoot']}% forefoot)")
    if not fs["consistent"]:
        warnings_all.append(
            f"Foot strike różny L/R: L={fs['left_dominant']}, R={fs['right_dominant']}"
        )

    if "overall" in symmetry:
        o = symmetry["overall"]
        lines.append("")
        lines.append(f"**Ogólna symetria**: max SI = {o['max_si_pct']}%, mean SI = {o['mean_si_pct']}%")
        if o["max_si_pct"] > 10:
            warnings_all.insert(0, f"⚠️ Największa asymetria {o['max_si_pct']}% > 10% — kandydat do uwagi specjalisty")

    lines.append("")
    return lines, warnings_all


def _section_summary(warnings: list[str]) -> list[str]:
    """Sekcja Wnioski — zebrane wszystkie warningi posortowane."""
    lines: list[str] = ["## Wnioski i ostrzeżenia", ""]
    if not warnings:
        lines.append("✅ **Wszystkie współczynniki w normie referencyjnej.** Brak istotnych ostrzeżeń.")
        lines.append("")
        return lines

    # Sortuj — emoji ⚠️ na początek
    priority = sorted(warnings, key=lambda w: 0 if "⚠️" in w else 1)
    lines.append("**Wykryte odchylenia od wartości referencyjnych:**")
    lines.append("")
    for w in priority:
        lines.append(f"- {w}")
    lines.append("")
    lines.append("_Powyższe odchylenia warto przedyskutować z trenerem / fizjoterapeutą. "
                 "Wartości referencyjne pochodzą z literatury (Novacheck 1998, Heiderscheit 2011, "
                 "Souza 2016, Diaz 2019) i mają charakter ogólny — indywidualna sytuacja biegacza "
                 "może wymagać innych progów._")
    lines.append("")
    return lines


def generate_report(
    meta: dict,
    temporal: dict,
    spatial: dict,
    symmetry: dict,
) -> str:
    """Wygeneruj pełny raport MD."""
    lines: list[str] = []

    # Header
    title = meta.get("title", meta.get("video", "Raport biegowy"))
    lines.append(f"# Raport analizy biegu — {title}")
    lines.append("")
    lines.append(f"- **Wideo**: `{meta.get('video', '?')}`")
    lines.append(f"- **FPS**: {meta.get('fps', '?')}")
    lines.append(f"- **Klatki**: {meta.get('n_frames', '?')}")
    lines.append(f"- **Czas trwania**: {meta.get('duration_s', '?')} s")
    lines.append(f"- **Rozdzielczość**: {meta.get('width', '?')}×{meta.get('height', '?')}")
    lines.append(f"- **Model klasyfikatora**: `{meta.get('model_dir', '?')}` (test acc {meta.get('model_test_acc', '?')})")
    lines.append(f"- **Średnia confidence predykcji**: {meta.get('avg_confidence', '?')}")
    lines.append(f"- **Wygenerowano**: {meta.get('generated', '?')}")
    lines.append("")

    all_warnings: list[str] = []

    # Temporal
    sec_lines, warns = _section_temporal(temporal)
    lines.extend(sec_lines)
    all_warnings.extend(warns)

    # Spatial
    sec_lines, warns = _section_spatial(spatial)
    lines.extend(sec_lines)
    all_warnings.extend(warns)

    # Symmetry
    sec_lines, warns = _section_symmetry(symmetry)
    lines.extend(sec_lines)
    all_warnings.extend(warns)

    # Summary
    lines.extend(_section_summary(all_warnings))

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("_Raport wygenerowany automatycznie. Nie zastępuje konsultacji ze specjalistą "
                 "biomechaniki sportu / fizjoterapeutą._")
    lines.append("")
    lines.append("_Wartości referencyjne: zob. `docs/reference-values.md`._")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generator raportu MD z analiz biegu")
    parser.add_argument("--temporal-json", type=Path, required=True)
    parser.add_argument("--spatial-json", type=Path, required=True)
    parser.add_argument("--symmetry-json", type=Path, required=True)
    parser.add_argument("--meta-json", type=Path, default=None,
                        help="Opcjonalny JSON z metadanymi (video, fps, model itp.)")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    temporal = json.loads(args.temporal_json.read_text(encoding="utf-8"))
    spatial = json.loads(args.spatial_json.read_text(encoding="utf-8"))
    symmetry = json.loads(args.symmetry_json.read_text(encoding="utf-8"))
    meta = json.loads(args.meta_json.read_text(encoding="utf-8")) if args.meta_json else {}

    report = generate_report(meta, temporal, spatial, symmetry)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    log.info(f"Zapisano raport: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
