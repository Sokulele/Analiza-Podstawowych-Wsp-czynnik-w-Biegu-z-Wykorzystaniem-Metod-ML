"""CLI Etapu 7 — generator rekomendacji biegowych.

Wczytuje JSON-y wygenerowane przez `src/coefficients/analyze.py` (temporal,
spatial, symmetry, meta) i produkuje:
- `*-recommendations.json` (lista obiektów Recommendation)
- (opcjonalnie) `*-recommendations.md` — sekcję Markdown do dołączenia do raportu

## Użycie

Auto-wykrycie wszystkich JSON-ów po basename:
    .venv/Scripts/python.exe src/recommendations/recommend.py \\
        --inference-dir data/inference \\
        --basename 22-running-analysis-with-physiotherapist

Ręcznie wskazane ścieżki:
    .venv/Scripts/python.exe src/recommendations/recommend.py \\
        --temporal-json data/inference/24-adam-temporal.json \\
        --spatial-json  data/inference/24-adam-spatial.json \\
        --symmetry-json data/inference/24-adam-symmetry.json \\
        --meta-json     data/inference/24-adam-meta.json
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from rules import generate_recommendations, render_markdown  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _resolve_paths(args: argparse.Namespace) -> tuple[Path, Path, Path, Path | None]:
    """Zwraca (temporal, spatial, symmetry, meta_or_None) na podstawie argumentów."""
    if args.basename:
        d = args.inference_dir
        base = args.basename
        temporal = d / f"{base}-temporal.json"
        spatial = d / f"{base}-spatial.json"
        symmetry = d / f"{base}-symmetry.json"
        meta = d / f"{base}-meta.json"
        meta = meta if meta.exists() else None
        return temporal, spatial, symmetry, meta

    missing = [n for n, p in (("--temporal-json", args.temporal_json),
                              ("--spatial-json", args.spatial_json),
                              ("--symmetry-json", args.symmetry_json)) if p is None]
    if missing:
        raise SystemExit(f"Brak argumentów: {missing} (lub użyj --basename)")
    return args.temporal_json, args.spatial_json, args.symmetry_json, args.meta_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Etap 7 — generator rekomendacji biegowych")
    parser.add_argument("--inference-dir", type=Path, default=Path("data/inference"),
                        help="Katalog z JSON-ami (gdy używasz --basename)")
    parser.add_argument("--basename", type=str, default=None,
                        help="Prefix plików (np. '22-running-analysis-with-physiotherapist')")
    parser.add_argument("--temporal-json", type=Path, default=None)
    parser.add_argument("--spatial-json", type=Path, default=None)
    parser.add_argument("--symmetry-json", type=Path, default=None)
    parser.add_argument("--meta-json", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None,
                        help="Gdzie zapisać *-recommendations.json (domyślnie obok temporal-json)")
    parser.add_argument("--output-md", type=Path, default=None,
                        help="Gdzie zapisać *-recommendations.md (domyślnie data/inference/raporty/<basename>-rekomendacje.md)")
    parser.add_argument("--no-md", action="store_true", help="Pomiń generowanie sekcji MD")
    args = parser.parse_args()

    temporal_p, spatial_p, symmetry_p, meta_p = _resolve_paths(args)

    log.info(f"Wczytuję: {temporal_p.name}, {spatial_p.name}, {symmetry_p.name}, "
             f"meta={'(brak)' if meta_p is None else meta_p.name}")

    temporal = json.loads(temporal_p.read_text(encoding="utf-8"))
    spatial = json.loads(spatial_p.read_text(encoding="utf-8"))
    symmetry = json.loads(symmetry_p.read_text(encoding="utf-8"))
    meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p else {}

    result = generate_recommendations(meta, temporal, spatial, symmetry)

    # Output JSON
    out_json = args.output_json
    if out_json is None:
        base = temporal_p.stem.replace("-temporal", "")
        out_json = temporal_p.parent / f"{base}-recommendations.json"
    out_json.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    log.info(f"Zapisano: {out_json}")

    # Output MD
    if not args.no_md:
        out_md = args.output_md
        if out_md is None:
            base = temporal_p.stem.replace("-temporal", "")
            raporty = temporal_p.parent / "raporty"
            raporty.mkdir(exist_ok=True)
            out_md = raporty / f"{base}-rekomendacje.md"
        out_md.write_text(render_markdown(result, meta), encoding="utf-8")
        log.info(f"Zapisano: {out_md}")

    # Konsola — krótkie podsumowanie
    s = result["summary"]
    log.info(f"Podsumowanie: 🔴{s['critical']} 🟠{s['warning']} 🟡{s['watch']} ℹ️{s['info']} "
             f"(łącznie {s['total']})")
    for r in result["recommendations"]:
        log.info(f"  [{r['severity']:8s}] {r['category']:18s} | {r['title']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
