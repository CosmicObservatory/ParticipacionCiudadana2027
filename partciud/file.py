from partciud.config import ROOT
from datetime import datetime
import requests as r
import os
import logging
import time

# Log File
LOG_FOLDER = ROOT / "logs"
os.makedirs(LOG_FOLDER, exist_ok=True)


def get_logger():
    """Logger que escribe cada descarga en un .txt"""
    logger = logging.getLogger("descargas")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fh = logging.FileHandler(
            LOG_FOLDER / f"descargas_{datetime.now():%Y%m%d}.txt",
            encoding="utf-8",
        )
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger

def download(url, dest, logger):
    start = time.perf_counter()
    try:
        response = r.get(url, timeout=60, stream=True)
        response.raise_for_status()
        content = response.content
        dest.write_bytes(content)
        elapsed = time.perf_counter() - start
        logger.info(
            "OK | url=%s | archivo=%s | %.2f s | %.1f KB",
            url, dest.name, elapsed, len(content) / 1024,
        )
    except Exception as e:
        elapsed = time.perf_counter() - start
        logger.error("FALLO | url=%s | %.2f s | %s", url, elapsed, e)