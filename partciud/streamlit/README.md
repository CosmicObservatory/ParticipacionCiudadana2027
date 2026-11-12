# Tablero Streamlit

Frontend Streamlit **autocontenido** del análisis electoral y
poblacional de Sonora. Incluye su propia copia de la lógica de datos
y figuras junto con los artefactos procesados necesarios.

## Ejecutar localmente

Desde la raíz del repo:

```bash
uv run streamlit run partciud/streamlit/app.py    # → http://localhost:8501
```

La portada-historia vive en `/` y la herramienta interactiva en
`/herramienta` (navegación de páginas oculta).

## Estructura

| Archivo | Rol |
|---|---|
| `app.py` | La aplicación completa: configuración de página, navegación oculta y todas las páginas. |
| `data.py` | Cargadores tidy memoizados (`lru_cache`) y tablas derivadas. |
| `figures.py` | Constructores de figuras Plotly. |
| `narrativa.py` | Textos markdown generados a partir de los datos. |
| `data/` | Artefactos procesados que usa el tablero (~20 MB): `conteos_sonora.csv.gz`, `mun_ine_inegi.csv`, `censo_inegi_municipios.csv`, `conapo_sonora.csv`, `escenarios_*.csv` (4), `municipios_simp.gpkg`, `distritos_simp_{2019..2025}.gpkg` (7) y `secciones_simp_{2019..2025}.gpkg` (7). |

## Dependencias

Las dependencias de Streamlit están declaradas en `pyproject.toml`:

- `streamlit`
- `geopandas`
- `plotly`
- `pandas`

Para desarrollo local se usa `uv`:

```bash
uv sync
```

Para Streamlit Community Cloud se generó `requirements.txt` en la raíz
del repo con:

```bash
uv export --format requirements-txt --no-hashes --no-emit-project --no-dev --output-file requirements.txt
```

Si actualizas `pyproject.toml` o `uv.lock`, vuelve a exportar
`requirements.txt` antes de desplegar.

## Despliegue en Streamlit Community Cloud

1. **Sube el repo a GitHub/GitLab/Bitbucket.** Asegúrate de incluir
   `partciud/streamlit/` y sus datos (~20 MB). El archivo `.gitignore`
   no excluye esta carpeta.

2. Ve a [share.streamlit.io](https://share.streamlit.io) e inicia sesión
   con tu cuenta de GitHub.

3. Selecciona **Create app** → **Deploy a public app from a GitHub repo**.

4. Configura la app:
   - **Repository**: tu repo.
   - **Branch**: la rama principal (por ejemplo `main`).
   - **Main file path**: `partciud/streamlit/app.py`
   - **Python version**: `3.14` (o la versión indicada en `.python-version`).
   - **Requirements file**: `requirements.txt` (en la raíz del repo).

5. Haz clic en **Deploy**. La primera vez puede tardar varios minutos
   mientras Streamlit Cloud instala las dependencias y descarga los datos.

6. Una vez desplegada, la app estará disponible en una URL pública del
   estilo `https://<usuario>-<app>.streamlit.app`.

### Notas sobre Streamlit Cloud

- Los datos se cargan desde `partciud/streamlit/data/` mediante rutas
  relativas al propio `app.py`; no requieren configuración adicional.
- Los mapas usan el estilo `carto-positron` de Plotly, que no necesita
  token de Mapbox.
- Si Streamlit Cloud aún no soporta Python 3.14, cambia
  `requires-python` en `pyproject.toml`, `.python-version` y vuelve a
  generar `requirements.txt` con Python 3.13.
- La app usa `st.navigation` y `st.Page`, por lo que se requiere
  Streamlit >= 1.36; la versión fijada en `requirements.txt` es 1.67.0.

## Caveats

- Streamlit **no recarga módulos importados**: tras editar cualquier
  archivo de este paquete hay que reiniciar el proceso (Ctrl+C y volver
  a ejecutar), no basta con recargar la página.
- Los datos de `data/` son una copia de los artefactos generados por el
  pipeline. Si se regeneran, hay que volver a copiarlos aquí.
