"""Textos narrativos (markdown) compartidos por los tableros Dash y Streamlit.

Las cifras se calculan sobre los datos tidy en cada render, de modo que el
texto siga siendo correcto si los artefactos se regeneran.
"""

import numpy as np

from vothmo.dashboard import data


def diccionario_md() -> str:
    """Diccionario de los datos tidy que alimentan el tablero."""
    n_conteos = len(data.conteos())
    n_sec = data.conteos()["seccion"].nunique()
    return f"""## Diccionario de datos

### Conjuntos de datos (`data/processed/`)

| Archivo | Contenido | Llave |
|---|---|---|
| `conteos_sonora.csv.gz` | Conteo censal electoral INE: {n_conteos:,} filas, una por elección × sección × sexo × edad ({n_sec:,} secciones, elecciones {", ".join(map(str, data.anios_elec()))}) | `aelec, seccion, sexo, edad` |
| `seccion_distrito_por_anio.csv` | Pivote sección → distrito local/federal por año de cartografía (2019–2025) | `anio, seccion` |
| `secciones_{{simp_}}<anio>.gpkg` | Capas seccionales INE con `ln`, `pad`, `distrito_l`, `distrito_f`, `mpiocve`, `nom_mun` | `seccion` |
| `distritos_{{simp_}}<anio>.gpkg` | 21 distritos electorales locales | `distrito_l` |
| `municipios_{{simp}}.gpkg` | 72 municipios (disueltos de secciones 2024) | `mpiocve` |
| `mun_ine_inegi.csv` | Puente entre el catálogo municipal del INE (`mun_ine`) y el de INEGI (`mpiocve`) | — |
| `censo_inegi_municipios.csv` | Población INEGI 2010/2020 por municipio (`pobtot`, `p_18ymas`, …) | `anio, mpiocve` |
| `conapo_sonora.csv` | Proyección CONAPO municipal por sexo y edad quinquenal, 1990–2040 | `anio, mpiocve, sexo` |
| `escenarios_poblacion_*.csv` | Población proyectada a 2040 por escenario (bajo/base/alto), municipal y distrital | `anio, escenario` |
| `escenarios_padron_*.csv` | Padrón proyectado a 2040 por escenario y *driver* (`padronal`/`demografico`) | `anio, driver, escenario` |

### Glosario de variables

| Variable | Significado |
|---|---|
| `pad` | Padrón electoral de la cartografía INE (incluye credenciales no entregadas y registros sin depurar) |
| `ln` | Lista nominal: ciudadanos con credencial vigente al corte del conteo |
| `sv` | Personas de la lista nominal que **sí votaron** en esa elección |
| `nv` | Personas de la lista nominal que **no votaron** |
| `ns` | Sin dato de votación (`ln = sv + nv + ns`) |
| `lns` | Lista nominal con dato: `sv + nv`; `ln − ns` |
| `pc` | Participación: `sv / lns` |
| `razon_18` | `pad / pob_18mas` (CONAPO): padrón sobre población residente mayor de edad |
| `razon_total` | `pad / pob_total` |
| `del` / `distrito_l` | Distrito electoral local (1–21) |
| `def` / `distrito_f` | Distrito electoral federal (1–7) |
| `sexo` | 0 = hombres, 1 = mujeres, 2 = no binario (solo 2024) |
| `mpiocve` | Clave municipal **INEGI**; en `conteos_*` la columna homónima es la clave **INE** (`mun_ine`) |
"""


def conclusiones_md() -> str:
    """Conclusiones numeradas con las cifras calculadas del proyecto."""
    rm = data.razon_mun(2025)
    re_ = data.razon_estado().set_index("anio")
    top3 = rm.nlargest(3, "razon_18")
    n_alta = int((rm["razon_18"] > 1).sum())
    corr = np.corrcoef(np.log10(rm["pob"].clip(lower=1)), rm["razon_18"])[0, 1]
    pad21, pad22 = re_.loc[2021, "pad"], re_.loc[2022, "pad"]
    top_txt = ", ".join(f"{r.nom_mun} ({r.razon_18:.1f}×)" for r in top3.itertuples())

    r = data.resumen_anual()
    pc_min = r.loc[r["pc"].idxmin()]
    pc_max = r.loc[r["pc"].idxmax()]
    ln0, ln1 = r["ln"].iloc[0], r["ln"].iloc[-1]

    pc24 = data.participacion_edad(2024)
    d = pc24[pc24["sexo"].isin([0, 1])]
    joven = d[d["edad"] <= 24]["sv"].sum() / d[d["edad"] <= 24]["lns"].sum() * 100
    mayor = d[d["edad"] >= 60]["sv"].sum() / d[d["edad"] >= 60]["lns"].sum() * 100

    pad, _ = data.padron_anual()
    pad_g = pad["pad"].iloc[-1] / pad["pad"].iloc[0] - 1

    pob_e, pad_e = data.escenarios_estado()
    pob40 = pob_e[pob_e["anio"] == 2040].set_index("escenario")["pob"]
    pad40_p = pad_e[(pad_e["anio"] == 2040) & (pad_e["driver"] == "padronal")].set_index(
        "escenario"
    )["pad"]
    pad40_d = pad_e[(pad_e["anio"] == 2040) & (pad_e["driver"] == "demografico")].set_index(
        "escenario"
    )["pad"]

    return f"""## Conclusiones

### 1. ¿Por qué el padrón / población 18+ supera el 100 %?

A nivel estatal la razón es **{re_.loc[2025, "razon_18"]:.0%}** (2025) y
**{n_alta} de 72 municipios** superan el 100 %, así que no es ruido de pueblos
pequeños: el numerador y el denominador miden **universos distintos**.

- **`pad` cuenta registrados, no residentes.** El padrón lista a los ciudadanos
  con credencial registrada en la sección; quien emigró (al interior de México o
  a EE. UU.) conserva su registro en su último domicilio, mientras que CONAPO
  proyecta *residentes*. En municipios rurales con alta emigración el efecto se
  dispara: {top_txt} son los casos extremos, y la razón crece al decrecer el
  tamaño municipal (correlación con log₁₀(población) = **{corr:.2f}**).
- **Registros sin depurar.** Entre 2021 y 2022 el padrón estatal *cayó*
  ~{pad21 - pad22:,.0f} personas —la depuración periódica que retira fallecidos
  y duplicados— y la razón bajó de {re_.loc[2021, "razon_18"]:.1%} a
  {re_.loc[2022, "razon_18"]:.1%}: evidencia directa de que el padrón arrastra
  "peso muerto" entre depuraciones.
- **`pad` incluye credenciales no entregadas** y el denominador es una
  *proyección* suavizada de CONAPO, no un conteo: el error relativo crece en
  municipios pequeños.

**Lectura correcta:** la razón no es "cobertura electoral"; vale como
comparativo entre municipios/años, pero no debe leerse como un porcentaje
acotado en 100 %.

### 2. La participación se concentra en adultos mayores

En 2024 votaron **{joven:.0f} %** de los empadronados de 18–24 años contra
**{mayor:.0f} %** de los de 60+. La curva por edad sube de forma casi monótona:
el electorado joven es el segmento con mayor margen de crecimiento.

### 3. La elección intermedia castiga la participación

El mínimo histórico del periodo es {int(pc_min["aelec"])} (**{pc_min["pc"]:.1f} %**,
intermedia y en pandemia) contra un pico de {pc_max["pc"]:.1f} % en
{int(pc_max["aelec"])}. La lista nominal creció de {ln0 / 1e6:.2f} a
{ln1 / 1e6:.2f} millones entre 2009 y 2024.

### 4. El padrón crece más rápido que la población

El padrón cartográfico aumentó **{pad_g:.0%}** entre 2019 y 2025 mientras la
población estatal crecía menos — parte del "crecimiento" es rezago sin depurar.
A 2040 los escenarios proyectan población de {pob40["bajo"] / 1e6:.2f}–
{pob40["alto"] / 1e6:.2f} M (base {pob40["base"] / 1e6:.2f} M) y padrón base de
**{pad40_p["base"] / 1e6:.2f} M** con driver padronal contra
**{pad40_d["base"] / 1e6:.2f} M** con driver demográfico: extrapolar la historia
del padrón infla el futuro por el mismo fenómeno de la conclusión 1.

### 5. Limitaciones

- Sin censo por sección: los denominadores poblacionales llegan solo a
  municipio; el reparto municipal → distrito usa pesos de padrón 2025.
- `ln` (conteo censal) y `pad` (cartografía) son cortes administrativos
  distintos; no son intercambiables.
"""


def glosario_md() -> str:
    """Glosario de conceptos que aparecen en las gráficas del tablero."""
    return r"""## Glosario

### Geografía electoral

- **Sección electoral.** Unidad mínima de la cartografía del INE: agrupa a los
  electores que votan en las mismas casillas. Sonora tiene ~1,600 secciones.
- **Distrito electoral local (`distrito_l` / `del`).** Circunscripción que elige
  un diputado al Congreso del Estado; Sonora tiene 21. Aparece en los mapas y
  barras de "distrito local".
- **Distrito electoral federal (`distrito_f` / `def`).** Circunscripción que
  elige un diputado federal; Sonora tiene 7.
- **Cartografía electoral.** Capas geográficas del INE (secciones, distritos)
  publicadas anualmente; aquí se usan los cortes 2019–2025. El `pad` y el `ln`
  de estas capas son cortes administrativos al año de publicación.
- **`mun_ine` vs `mpiocve`.** El INE y el INEGI usan catálogos municipales
  distintos; `mun_ine_inegi.csv` traduce entre ellos. En `conteos_*` la columna
  `mpiocve` es en realidad la clave INE.

### Datos electorales

- **Padrón electoral (`pad`).** Total de ciudadanos con credencial de elector
  tramitada y registrados en la sección — incluye credenciales no entregadas y
  registros aún no depurados (fallecidos, duplicados, emigrantes). Por eso puede
  rebasar a la población residente mayor de edad.
- **Lista nominal (`ln`).** Subconjunto del padrón con credencial vigente al
  corte del conteo: el universo real de quienes podían votar en esa elección.
- **Conteo censal electoral.** Estadística del INE que cruza la lista nominal
  contra los resultados: para cada sección × sexo × edad indica cuántos
  votaron (`sv`), no votaron (`nv`) o no tienen dato (`ns`).
- **`sv` / `nv` / `ns`.** Sí votaron / no votaron / sin dato;
  $$ln = sv + nv + ns$$
- **`lns`.** Lista nominal *con dato*; es el denominador de la
  participación porque excluye a quienes no se sabe si votaron:
  $$lns = sv + nv = ln - ns$$
- **Participación (`pc`).** Fracción de empadronados con dato que
  sí emitió voto. No es abstención sobre población: mide la lista nominal.
  $$pc = \frac{sv}{lns}$$
- **Depuración del padrón.** Proceso periódico del INE que retira fallecidos,
  duplicados y bajas; explica las caídas puntuales del padrón (p. ej. 2022).
- **Sexo (0/1/2).** En los conteos: 0 = hombres, 1 = mujeres; 2 = no binario,
  categoría que solo aparece en 2024.

### Demografía

- **INEGI / ITER.** Instituto de estadística y su base de población por
  localidad; aquí se usa agregada a municipio para 2010 y 2020.
- **CONAPO.** Consejo Nacional de Población; fuente de las proyecciones
  municipales por sexo y edad quinquenal (1990–2040).
- **Población 18+ (`pob_18mas` / `p_18ymas`).** Residentes en edad de votar
  según la proyección o el censo — el denominador "oficial" para comparar
  contra el padrón.
- **Razón padrón/población (`razon_18`, `razon_total`).** Lee comparativas,
  no cobertura: puede pasar de 100 % por emigrantes registrados, rezago de
  depuración y error de proyección.
  $$\mathrm{razon}_{18} = \frac{pad}{pob_{18+}}, \qquad \mathrm{razon}_{total} = \frac{pad}{pob_{total}}$$
- **Pirámide (edad × sexo).** Barras horizontales espejo: hombres a la
  izquierda (valores negativos), mujeres a la derecha; muestra la estructura
  por edad de la lista nominal.
- **Mapa coroplético.** Polígonos coloreados por el valor de una variable
  (lista nominal, participación o razón) — más oscuro = mayor valor.

### Escenarios y proyección

- **Escenario bajo / base / alto.** Tres trayectorias a 2040: la *base* repite
  el crecimiento observado; *bajo* y *alto* lo modulan −25 % y +25 % por
  defecto (factor ajustable por escenario en *Crecimiento*).
- **CAGR** (*Compound Annual Growth Rate*). Tasa anual compuesta que resume
  en una sola tasa el crecimiento entre dos puntos; es el motor de todas las
  proyecciones:
  $$\mathrm{CAGR} = \left(\frac{V_f}{V_0}\right)^{\frac{1}{n}} - 1$$
- **Driver padronal.** Proyecta el padrón futuro con el CAGR del propio padrón
  cartográfico 2019–2025; como el padrón crece más rápido que la población
  (acumula rezago), arroja cifras más altas.
- **Driver demográfico.** Proyecta el padrón futuro con el CAGR de la
  población 18+ de CONAPO 2015–2025; supone que el empadronamiento seguirá a
  la demografía — trayectoria más conservadora.
- **Horizonte de proyección.** Año final de los escenarios (2040).
- **Año base.** Último año observado desde el que se extrapola: 2025 para
  población (CONAPO) y 2025 para padrón (cartografía).
- **Proyección escenarizada.** Cada serie proyecta el valor base con el CAGR
  modulado por el factor de su escenario ($f_{bajo}$, $f_{base}$, $f_{alto}$,
  editables en *Crecimiento*):
  $$pad_{a} = pad_{a_0} \times (1 + f \times \mathrm{CAGR})^{a - a_0}, \qquad f \in \{0.75,\; 1,\; 1.25\}\ \text{por defecto}$$
- **Reparto municipal → distrito.** Los escenarios se calculan por municipio;
  para pasarlos a distrito local se reparte cada municipio con los **pesos de
  padrón 2025** (fracción del padrón municipal que vive en cada distrito) —
  aproximación necesaria porque no hay censo por sección.
  $$w_{m,d} = \frac{pad_{m,d}}{pad_{m}}, \qquad pob_{d} = \sum_{m} w_{m,d} \times pob_{m}$$
"""


def escenarios_md() -> str:
    """Descripción de los escenarios bajo/base/alto para la pestaña de inicio."""
    return r"""## Escenarios de crecimiento

Los escenarios proyectan cada serie desde el año base (2025) hasta 2040
repitiendo el crecimiento observado (CAGR), modulado por un factor $f$:

$$valor_{a} = valor_{a_0} \times (1 + f \times \mathrm{CAGR})^{a - a_0}$$

- **Base** ($f = 1$ por defecto): replica el crecimiento observado — CONAPO
  para la población y, para el padrón, el *driver* elegido.
- **Bajo** ($f = 0.75$ por defecto): crecimiento atenuado.
- **Alto** ($f = 1.25$ por defecto): crecimiento acelerado.

Cada escenario tiene su propio factor $f$ editable. En la pestaña
*Crecimiento*, el radio bajo/base/alto posiciona los deslizadores en el
factor guardado de ese escenario (por defecto $f \in \{0.75, 1, 1.25\}$, es
decir, ∓25 % del CAGR) y puedes ajustarlos **de forma independiente** para
la población y para el padrón electoral.
"""


def fuentes_md() -> str:
    """Fuentes consultadas para los datos y la cartografía del proyecto."""
    return """## Fuentes consultadas

- **INE** — Instituto Nacional Electoral: conteos censales de la lista
  nominal 2009–2024 (`data/Censos`) y cartografía electoral seccional y
  distrital 2019–2025 (`data/raw/Mapas`).
- **INEGI** — Instituto Nacional de Estadística y Geografía: ITER/censo de
  población 2010 y 2020, agregados a municipio.
- **CONAPO** — Consejo Nacional de Población: proyecciones de población
  municipal por sexo y edad quinquenal, 1990–2040.
- **IEE Sonora** — Instituto Estatal Electoral: resultados electorales
  (pendiente de integrar).

*Caveats: `pad` (padrón cartográfico) ≠ `ln` (lista nominal del conteo);
la clave municipal del INE difiere de la de INEGI (`mun_ine_inegi.csv`);
sin censo por sección, el reparto municipal → distrito usa pesos de
padrón 2025.*
"""


def historia_md() -> dict[str, str]:
    """Bloques narrativos de la portada-historia, en orden de lectura.

    Las cifras se calculan sobre los datos tidy en cada render; cada frontend
    intercala las figuras correspondientes entre bloque y bloque.
    """
    r = data.resumen_anual()
    pc_min = r.loc[r["pc"].idxmin()]
    pc_max = r.loc[r["pc"].idxmax()]
    ln0, ln1 = r["ln"].iloc[0], r["ln"].iloc[-1]

    pc24 = data.participacion_edad(2024)
    d = pc24[pc24["sexo"].isin([0, 1])]
    joven = d[d["edad"] <= 24]["sv"].sum() / d[d["edad"] <= 24]["lns"].sum() * 100
    mayor = d[d["edad"] >= 60]["sv"].sum() / d[d["edad"] >= 60]["lns"].sum() * 100

    n_sec = len(data.secciones_geo(2025))
    t = data.transiciones_distrito(2019, 2025)
    mov = t[t["dl0"] != t["dl1"]]["n"].sum()
    tot = t["n"].sum()

    re_ = data.razon_estado().set_index("anio")
    rm = data.razon_mun(2025)
    n_alta = int((rm["razon_18"] > 1).sum())
    pad21, pad22 = re_.loc[2021, "pad"], re_.loc[2022, "pad"]
    pad, _ = data.padron_anual()
    pad_g = pad["pad"].iloc[-1] / pad["pad"].iloc[0] - 1

    pob_e, pad_e = data.escenarios_estado()
    pob40 = pob_e[pob_e["anio"] == 2040].set_index("escenario")["pob"]
    pad40_p = pad_e[(pad_e["anio"] == 2040) & (pad_e["driver"] == "padronal")].set_index(
        "escenario"
    )["pad"]
    pad40_d = pad_e[(pad_e["anio"] == 2040) & (pad_e["driver"] == "demografico")].set_index(
        "escenario"
    )["pad"]

    return {
        "intro": f"""Sonora vota en **21 distritos electorales locales** repartidos en
~{n_sec:,} secciones. Entre 2009 y 2024 su lista nominal —los ciudadanos con
credencial vigente al corte de cada elección— pasó de **{ln0 / 1e6:.2f} a
{ln1 / 1e6:.2f} millones**. La participación oscila con el tipo de elección:
el mínimo del periodo fue {int(pc_min["aelec"])} (**{pc_min["pc"]:.1f} %**,
intermedia y en pandemia) y el pico {pc_max["pc"]:.1f} % en
{int(pc_max["aelec"])}.
""",
        "demografia": f"""## Quiénes salen a votar

La participación se concentra en los adultos mayores: en 2024 votó el
**{joven:.0f} %** de la lista nominal de 18–24 años contra el **{mayor:.0f} %**
de los de 60+. La curva por edad sube de forma casi monótona — el electorado
joven es el segmento con mayor margen de crecimiento.
""",
        "distritos": f"""## Una geografía que se redibuja

Las secciones no son fijas: el INE republica la cartografía cada año y los
distritos se reacomodan. Entre 2019 y 2025, **{mov:,} de {tot:,} secciones
compartidas cambiaron de distrito local**. El Sankey muestra los flujos entre
distritos y las barras finales cuánto padrón ganó o perdió cada uno solo por
reacomodo — no por crecimiento real.
""",
        "padron": f"""## Más padrón que habitantes

El padrón cartográfico creció **{pad_g:.0%}** entre 2019 y 2025, más rápido
que la población. En 2025 la razón padrón / población 18+ estatal es
**{re_.loc[2025, "razon_18"]:.0%}** y **{n_alta} de 72 municipios** superan
el 100 %: el padrón cuenta *registrados* —incluye a quien emigró y a
credenciales no entregadas— mientras la proyección cuenta *residentes*.
Entre 2021 y 2022 la depuración del padrón retiró ~{pad21 - pad22:,.0f}
registros: evidencia del rezago que acumula entre depuraciones.
""",
        "escenarios": f"""## Hacia 2040

Repitiendo el crecimiento observado, la población llegaría a
**{pob40["base"] / 1e6:.2f} M** (rango {pob40["bajo"] / 1e6:.2f}–
{pob40["alto"] / 1e6:.2f} M entre escenarios) y el padrón a
**{pad40_p["base"] / 1e6:.2f} M** extrapolando su propia historia —driver
padronal— contra **{pad40_d["base"] / 1e6:.2f} M** si siguiera a la
demografía: el rezago del padrón vuelve a inflar la primera trayectoria.
""",
    }
