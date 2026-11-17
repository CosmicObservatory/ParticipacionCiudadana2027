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
## Mapas electorales
url_ine_maps = "https://pautas.ine.mx/transparencia/mapas"
link_ine_maps = URL(url_ine_maps)

## Elecciones Configuración
elecciones = "https://ieesonora.org.mx/resultados/computo/diputaciones"
url_elecciones = URL(elecciones)

## Resultados Elecciones
elec2018 = "https://ieesonora.org.mx/_elecciones/procesos/2018/resultados/basedatos/"
elec2021 = "https://ieesonora.org.mx/_elecciones/procesos/2021/resultados/basedatos/"
elec2024 = "https://www.ieesonora.org.mx/elecciones2024/computo/CDE/"

api_elecciones_2018 = URL(elec2018)
api_elecciones_2021 = URL(elec2021)
api_elecciones_2024 = URL(elec2024)


## Censo INEGI
icensus2005 = "https://www.inegi.org.mx/contenidos/programas/ccpv/2005/datosabiertos/cpv2005_iter_00_csv.zip"
icensus2010 = "https://www.inegi.org.mx/contenidos/programas/ccpv/2010/datosabiertos/iter_nal_2010_csv.zip"
icensus2020 = "https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/iter/iter_00_cpv2020_csv.zip"

api_inegi_census_2005 = URL(icensus2005)
api_inegi_census_2010 = URL(icensus2010)
api_inegi_census_2020 = URL(icensus2020)

