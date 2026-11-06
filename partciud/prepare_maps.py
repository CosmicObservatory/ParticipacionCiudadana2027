"""
    Maps Download Preparation
"""
from partciud.config import link_ine_maps, savepath
from partciud.file import get_logger, download
from datetime import date
import time
from pathlib import Path
import requests as r
from bs4 import BeautifulSoup
import os


# Obtain File Links Guide
year_limit = date.today().year
year_start = 2020
years = list(range(year_start, year_limit + 1))
pages = [f"index_{y}.html" if y != year_limit else "index.html" for y in years]
download_pages = []
for p in pages:
    link = link_ine_maps / p
    response = r.get(link)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "lxml")
    refs = soup.find_all("a")
    useful_links = []
    for l in refs:
        if l.text=="Descargar archivo":
            useful_links.append(l['href'])
    download_pages += [ul for ul in useful_links if not ul.split("/")[1].startswith("Area")]


# Downlaod File Links

logger = get_logger()

logger.info("=== INICIO lote: %d archivos ===", len(download_pages))
t0 = time.perf_counter()
k = 0
for page in download_pages:
        year = page.split("/")[0].split("_")[-1]
        filename = page.split("/")[1]
        down_link = link_ine_maps / page
        dest = savepath("input", f"ine_maps/{year}", down_link.name)
        print(f"Progreso {k} / {len(download_pages)}")
        download(down_link, dest, logger)
        k+= 1 
logger.info("=== FIN lote | total %.1f s ===", time.perf_counter() - t0)
