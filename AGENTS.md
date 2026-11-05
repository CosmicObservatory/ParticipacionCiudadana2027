# AGENTS.md — VotacionHMO / Votación 2026

Análisis electoral y poblacional del estado de Sonora (21 distritos
electorales locales). Pipeline implementado como libretas Jupyter
autocontenidas; `vothmo/` solo contiene utilidades de configuración,
reparación de shapefiles y el dashboard.

## Pipeline de libretas (ejecutar en orden)

| Libreta | Función |
|---|---|
| `notebooks/00_preparacion_datos.ipynb` | Extrae cartografía INE de `data/raw/Mapas`, repara shapefiles, normaliza conteos electorales `data/Censos`, descarga ITER/CONAPO, genera `mun_ine_inegi.csv` y todas las capas `data/processed/` |
| `notebooks/01_distritos_historia.ipynb` | Mapas animados de los 21 distritos 2019–2025, conteos de secciones, transiciones distrito↔distrito (Sankey) |
| `notebooks/02_demografia_electoral.ipynb` | Pirámides sexo/edad, distribución por distrito/municipio/sección, participación (sv/nv/ns) |
| `notebooks/03_escenarios.ipynb` | Escenarios bajo/base/alto de población (CONAPO) y padrón (drivers padronal/demográfico) a horizonte libre; exporta `escenarios_*.csv` |
| `notebooks/04_padron_vs_censo.ipynb` | Razón padrón/población (total y 18+) por municipio y distrito; contraste INEGI 2010/2020 |

## Ejecución

```bash
# ejecutar una libreta de punta a punta (desde la raíz del repo)
uv run --with nbconvert -- jupyter nbconvert --to notebook --execute \
    --inplace notebooks/0X_*.ipynb
```

`nbconvert`/`nbformat` están declarados en `pyproject.toml`; en entornos
donde falten, el prefijo `uv run --with nbconvert` los provee sin
modificar el venv.

## Tableros

Dos frontends equivalentes sobre `vothmo/dashboard/`: `data.py` concentra
cargadores tidy memoizados (`lru_cache`) y `figures.py` las figuras Plotly;
`app.py` (Dash) y `streamlit_app.py` son solo capas de UI. Ambos abren en
una portada-historia (`/`, textos en `narrativa.historia_md`/`fuentes_md`,
en Dash el layout vive en `historia.py`) que cierra con fuentes y un enlace
a la herramienta; las pestañas solo se renderizan en `/herramienta`
(Dash: `dcc.Location` + ruteo; Streamlit: `st.navigation(position="hidden")`).

```bash
uv run python -m vothmo.dashboard.app                                  # Dash → :8050
uv run streamlit run vothmo/dashboard/streamlit_app.py                 # Streamlit → :8501
```

## Datos

- `data/raw/Mapas/{2019..2025}` — cartografía INE (capa `SECCION`);
  campos normalizados: `seccion`, `municipio`, `distrito_l`,
  `distrito_f`, `ln`, `pad`. Proyección origen: LCC/WGS84 → EPSG:4326.
- `data/Censos/` — conteos censales electorales INE 2009–2024
  (`seccion`, `del`, `sexo`, `edad`, `ln`, `sv`, `nv`, `ns`).
- `data/raw/inegi/` — ITER 2010 (nacional) y 2020 (Sonora).
- `data/raw/conapo/` — `pobproy_quinq1.csv` (descarga requiere
  `User-Agent` de navegador).

### Artefactos clave en `data/processed/`

- `secciones_{año}.gpkg` / `secciones_simp_{año}.gpkg` — completas y
  simplificadas (usar siempre `*_simp` en figuras).
- `distritos_{año}.gpkg` / `distritos_simp_{año}.gpkg` — 21 distritos.
- `municipios_sonora.gpkg` / `municipios_simp.gpkg` — disueltos de
  secciones **2024** (`ln_2024`, `pad_2024`).
- `conteos_sonora.csv.gz`, `censo_inegi_municipios.csv`,
  `conapo_sonora.csv`, `seccion_distrito_por_anio.csv`,
  `mun_ine_inegi.csv`, `escenarios_*.csv`.

## Caveats importantes

- **Claves municipales duales**: la cartografía y los conteos del INE
  usan su propio catálogo municipal (`municipio`), distinto del
  `mpiocve` de INEGI. Usa `mun_ine_inegi.csv` para cruzar; las capas
  `secciones_*`/`municipios_*` ya traen `mpiocve` + `nom_mun`.
- **`pad` ≠ `ln`**: `pad` es el padrón electoral (incluye credenciales
  no entregadas); `ln` es la lista nominal. El `ln` del conteo censal
  es un corte electoral, no el padrón cartográfico.
- **Sexo**: 2009–2021 solo 0/1 (hombre/mujer); 2024 añade 2 (no binario).
- **Geometrías**: las capas completas son pesadas; en mapas usa siempre
  `*_simp` y GeoJSON "ligero" (geometría + id). Evita `color` discreto
  en `px.choropleth_map` con muchas categorías: duplica el GeoJSON por
  trace (una libreta llegó a 5.7 GB).
- **Sin censo por sección**: no se halló descarga directa del ECGE de
  INEGI; los denominadores poblacionales llegan solo a municipio y el
  reparto municipal→distrito usa pesos de padrón 2025 (aproximación
  documentada).
- **Fuentes pendientes**: ECGE/INEGI sección e ITER 2015 no tienen URL
  directa funcional (Access Denied); requieren descarga manual.
- `data/` está en `.gitignore`; los artefactos se regeneran corriendo
  la libreta 00.

## Estilo

- Ruff: `line-length = 99`, isort con `vothmo` como first-party.
- Libretas autocontenidas: cada una carga sus propios artefactos; no
  extraer lógica compartida a `vothmo/` salvo indicación expresa.
