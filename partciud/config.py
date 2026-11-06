from yarl import URL
from pathlib import Path
from datetime import datetime
import os


# Paths
ROOT = list(Path(__file__).parents)[1]
DATA_FOLDER = ROOT / "data"


data_tree = {
    "input": DATA_FOLDER / "raw",
    "prepare": DATA_FOLDER / "interim",
    "clean": DATA_FOLDER / "processed",
    "guide": DATA_FOLDER / "external"
}

def savepath(step, source, file, datafolder=DATA_FOLDER):
    assert step in data_tree.keys(), "Revisa el nombre"
    folderpath = data_tree[step]
    sourcepath = folderpath / source
    os.makedirs(sourcepath, exist_ok=True)
    filepath = sourcepath / file
    return filepath


# Links
url_ine_maps = "https://pautas.ine.mx/transparencia/mapas"
link_ine_maps = URL(url_ine_maps)

