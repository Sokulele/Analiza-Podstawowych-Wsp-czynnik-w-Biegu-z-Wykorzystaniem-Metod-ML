"""Sonduje metadane filmików: FPS, rozdzielczość, liczba klatek, czas trwania."""
import argparse
import logging
import sys
from pathlib import Path

import cv2
import pandas as pd

# Wymuszamy UTF-8 na stdout — nazwy plików mogą zawierać Unicode (np. ⧸)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def probe_video(path: Path) -> dict:
    """Odczytuje podstawowe metadane z pliku wideo."""
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        log.warning("Nie udało się otworzyć: %s", path.name)
        return {"file": path.name, "error": "cannot open"}

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
    fourcc = "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)])
    cap.release()

    duration_s = frame_count / fps if fps > 0 else 0.0
    size_mb = path.stat().st_size / (1024 * 1024)

    return {
        "file": path.name,
        "fps": round(fps, 3),
        "width": width,
        "height": height,
        "frames": frame_count,
        "duration_s": round(duration_s, 2),
        "size_mb": round(size_mb, 2),
        "codec": fourcc,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Sonduje metadane filmików w katalogu.")
    parser.add_argument("--videos-dir", default="data/videos", help="Katalog z filmikami")
    parser.add_argument("--output", default="data/videos_metadata.csv", help="Plik wyjściowy CSV")
    args = parser.parse_args()

    videos_dir = Path(args.videos_dir)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    videos = sorted(videos_dir.glob("*.mp4"))
    log.info("Znaleziono %d filmików w %s", len(videos), videos_dir)

    rows = [probe_video(v) for v in videos]
    df = pd.DataFrame(rows)
    df.to_csv(output, index=False, encoding="utf-8")
    log.info("Zapisano metadane do %s", output)

    with pd.option_context("display.max_columns", None, "display.width", 200):
        print(df.to_string(index=False))


if __name__ == "__main__":
    main()
