# Resumen de avance — Semana 8
**Proyecto 2 Analítica de Datos — PENGWIN (fracturas pélvicas)**

## 1. Dataset descargado

- Fuente: Task 1 (CT) del challenge PENGWIN, vía Zenodo (https://doi.org/10.5281/zenodo.10927452).
- Archivos: `PENGWIN_CT_train_images_part1`, `PENGWIN_CT_train_images_part2`, `PENGWIN_CT_train_labels`.
- **Total: 100 casos** (imagen + máscara de fragmentos, uno por paciente).

## 2. Hallazgo importante: formato de archivo

- El dataset viene en formato **`.mha`**, no en NIfTI como asumía el enunciado del proyecto.
- Se ajustó el pipeline para usar **SimpleITK** en vez de `nibabel`. El spacing físico (mm/vóxel) sigue obteniéndose correctamente del header, así que el requisito de la rúbrica se cumple igual.
- Se notificó al profesor por escrito, dejando constancia de la decisión.

## 3. Manifest del dataset (`build_manifest.py`)

Script que recorre los 100 casos y extrae metadatos completos (shape, spacing, rango HU, número de fragmentos, y validación de que cada imagen tenga su máscara correspondiente).

**Resultado:**
- **100/100 casos válidos** (ningún caso huérfano ni corrupto).
- Spacing: entre 0.625 y 1.25 mm/vóxel según el eje (rango normal para CT clínico).
- Fragmentos por caso: entre 3 y 9, promedio 5.75.

```text
============================================================
RESUMEN DEL MANIFEST
============================================================
Total de casos encontrados : 100
Casos válidos               : 100
Casos inválidos/incompletos : 0

Rango de spacing (mm/vóxel) en casos válidos:
  spacing_x: 0.658 - 1.220
  spacing_y: 0.658 - 1.220
  spacing_z: 0.625 - 1.250

Rango HU global: -6211.0 a 47685.0

Fragmentos únicos por caso (excluyendo fondo):
  min: 3, max: 9, promedio: 5.75

Manifest guardado en: /Users/mariavalencia/Downloads/pengwin_data/data/manifest.csv
```

## 4. Diagnóstico de valores HU (`check_hu_outliers.py`)

- Se detectaron 52 casos con valores HU fuera del rango típico de CT (-1100 a 5000 HU).
- **Explicación identificada, no es un error:**
  - Valores mínimos repetidos exactos (ej. -2048, -1023) = **padding** del escáner fuera del campo de reconstrucción.
  - Valores máximos muy altos (hasta 47,685 HU en un caso) = **artefacto de metal**, pero casi nunca está en el hueso pélvico: el EDA de intensidades (notebook 02) muestra que proviene de implantes femorales y de objetos externos al paciente.
- **Decisión:** al aplicar el ventaneo HU se hará un `clip` agresivo (ej. -1024 a 3000) antes de normalizar, para que el padding y el metal no dañen el contraste del hueso. Esto se documentará como hallazgo del EDA.

```text
Total casos válidos: 100

Top 5 casos con HU máximo más alto:
 case_id  hu_min  hu_max     hu_mean
      80 -1023.0 47685.0 -600.436101
      68 -6211.0 30445.0 -757.690200
     100 -6152.0 24970.0 -936.068190
      55 -1023.0 23354.0 -668.465611
      84 -1023.0 19419.0 -546.270047

Top 5 casos con HU mínimo más bajo:
 case_id  hu_min  hu_max      hu_mean
      68 -6211.0 30445.0  -757.690200
     100 -6152.0 24970.0  -936.068190
      51 -3376.0  9741.0  -949.747885
      96 -3193.0 13843.0  -708.974439
      74 -2913.0 15467.0 -1004.721474

Casos con valores fuera del rango esperado (-1100 a 5000 HU): 52
 case_id  hu_min  hu_max      hu_mean
       3 -1023.0 16709.0  -427.226756
       4 -1418.0  4961.0  -187.163303
       7 -1023.0 19380.0  -610.517546
      10 -2048.0  7573.0  -909.534589
      11 -2285.0  1677.0  -945.008948
      13 -1023.0 16941.0  -669.545505
      19 -2048.0  1727.0  -813.558878
      20 -2048.0  3321.0  -848.485221
      21 -2048.0  1677.0  -691.015887
      22 -1023.0  5327.0  -547.394570
      24 -2048.0  5237.0  -805.412518
      25 -1023.0 12939.0  -433.262051
      27 -1024.0 10827.0  -677.896896
      29 -1023.0  9989.0  -566.968421
      32 -2048.0  5754.0  -817.513973
      35 -2048.0  3549.0  -527.518973
      37 -1023.0 12340.0  -646.803353
      38 -2048.0  1736.0  -786.168491
      40 -2048.0  1753.0  -868.233099
      41 -2076.0  1655.0  -472.923524
      42 -2048.0  1739.0  -939.439844
      46 -1023.0 11480.0  -664.185156
      50 -1023.0  6916.0  -266.191004
      51 -3376.0  9741.0  -949.747885
      52 -2048.0  1703.0  -873.728869
      54 -1023.0  9015.0  -596.495610
      55 -1023.0 23354.0  -668.465611
      57 -1023.0 16749.0  -442.228584
      60 -2048.0  2352.0  -200.028130
      61 -2048.0  1620.0  -927.562912
      63 -1166.0  1530.0   -99.571106
      64 -2048.0  1791.0  -780.405319
      65 -2602.0 11341.0  -810.555367
      67 -2048.0  3156.0  -543.084253
      68 -6211.0 30445.0  -757.690200
      69 -2048.0  3077.0 -1004.433639
      70 -2048.0  1775.0  -790.217641
      72 -1479.0  7697.0  -210.649178
      73 -1023.0  6153.0  -663.556772
      74 -2913.0 15467.0 -1004.721474
      76 -2048.0  1695.0  -874.844786
      77 -2048.0  1749.0  -827.060723
      78 -2359.0  1782.0  -400.412043
      80 -1023.0 47685.0  -600.436101
      81 -2048.0  1872.0  -171.194516
      84 -1023.0 19419.0  -546.270047
      87 -1023.0  9618.0  -401.300658
      90 -2048.0  1756.0 -1001.211786
      94 -2048.0  1779.0 -1034.751606
      96 -3193.0 13843.0  -708.974439
      98 -2048.0  1924.0  -804.574777
     100 -6152.0 24970.0  -936.068190
```

## 5. Splits fijos (`make_splits.py`)

- Split por `case_id` (nunca por corte, para evitar data leakage).
- Estratificado por número de fragmentos (buckets bajo/medio/alto).
- Semilla fija = 42.

```text
Bucket 'alto': 26 casos -> train=18, val=4, test=4
Bucket 'bajo': 1 casos -> train=1, val=0, test=0
Bucket 'medio': 73 casos -> train=51, val=11, test=11

Total: train=70, val=15, test=15
Splits guardados en: data/splits.json
```

**Resultado:** train=70, val=15, test=15.

**Limitación conocida (documentada, no es un bug):** solo existe 1 caso en el bucket "bajo" (≤3 fragmentos), así que ese extremo quedó representado únicamente en train y no en val/test. Se deja anotado para el informe final.

## 6. Carga de volúmenes y ventaneo HU (`hu windowing check.py`)

- Carga de `.mha` con SimpleITK → array `(z, y, x)` en HU crudo; el spacing sale de `img.GetSpacing()` (orden `x, y, z`).
- Función `apply_hu_window`: primero `clip` a **[-1024, 3000] HU** (neutraliza padding y metal, ver sección 4) y luego ventana ósea **C=400 / W=1800**, normalizada a `[0, 1]`.
- Verificado visualmente en 3 casos: `001` (normal), `080` (HU máx. 47 685, metal) y `068` (HU mín. -6 211, padding). Salida: `outputs/figures/hu_window_check_{001,068,080}.png`.

## 7. EDA de fragmentos (`eda_fragments.py`)

Usa la convención oficial de etiquetas de PENGWIN: `0` fondo, `1–10` sacro, `11–20` coxal izquierdo, `21–30` coxal derecho. No apareció ningún label fuera de esa convención (`n_labels_desconocidos = 0` en los 100 casos). El volumen se calcula con el spacing real de cada caso (mm³, no vóxeles).

```text
============================================================
RESUMEN EDA DE FRAGMENTOS
============================================================
                                   metrica        valor
                                   n_casos 1.000000e+02
                      fragmentos_total_min 3.000000e+00
                      fragmentos_total_max 9.000000e+00
                    fragmentos_total_media 5.750000e+00
                    fragmentos_sacro_media 1.530000e+00
                fragmentos_coxal_izq_media 2.150000e+00
                fragmentos_coxal_der_media 2.070000e+00
    casos_sin_fractura_sacro (1 fragmento) 5.500000e+01
casos_sin_fractura_coxal_izq (1 fragmento) 3.400000e+01
casos_sin_fractura_coxal_der (1 fragmento) 3.600000e+01
                     volumen_hueso_mm3_min 5.511926e+05
                     volumen_hueso_mm3_max 1.095226e+06
                   volumen_hueso_mm3_media 7.810584e+05
```

La misma tabla, legible:

| Métrica | Valor |
|---|---|
| Casos analizados | 100 |
| Fragmentos totales por caso | mín 3 · máx 9 · media 5.75 |
| Fragmentos promedio — sacro | 1.53 |
| Fragmentos promedio — coxal izquierdo | 2.15 |
| Fragmentos promedio — coxal derecho | 2.07 |
| Casos con sacro sin fractura (1 fragmento) | 55 |
| Casos con coxal izquierdo sin fractura | 34 |
| Casos con coxal derecho sin fractura | 36 |
| Volumen de hueso por caso | 551 193 – 1 095 226 mm³ · media 781 058 mm³ (≈ 0.55 – 1.10 L) |

Distribución de fragmentos totales por caso (de `data/eda_fragments_detalle.csv`):

| Fragmentos | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|
| Casos | 1 | 13 | 32 | 28 | 18 | 6 | 2 |

**Lectura de los resultados:**

- Las tres regiones están presentes en los 100 casos (mínimo = 3 fragmentos = una pelvis con un fragmento por hueso). La cabeza de clasificación no tendrá clases ausentes a nivel de volumen; el desbalance aparecerá a nivel de corte (muchos cortes sin sacro o sin alguno de los coxales).
- El sacro es el hueso que menos se fractura (55 % intacto, máximo 4 fragmentos); los coxales se fracturan en ~65 % de los casos y son simétricos entre sí (2.15 vs 2.07). Máximo observado: 6 fragmentos en un coxal izquierdo, así que el límite de 10 por región del dataset queda holgado.
- Solo 1 caso no tiene ninguna fractura (3 fragmentos); es el mismo caso único del bucket "bajo" de los splits.
- Los splits quedaron balanceados en dificultad: media de fragmentos por caso train 5.76 / val 5.73 / test 5.73.
- El volumen de hueso varía ~2× entre casos (tamaño del paciente + campo de visión del CT). Es una razón más para medir siempre en mm con el spacing del header y no en vóxeles.

Salidas: `data/eda_fragments_detalle.csv`, `outputs/eda/resumen_estadistico.csv`, `outputs/eda/hist_fragmentos_totales.png`, `outputs/eda/barras_fragmentos_por_region.png`, `outputs/eda/boxplot_volumen_hueso_mm3.png`.

## 8. Visualizador 1 — MIP raw (`mip_visualizer.py`)

- Umbral óseo de **250 HU sobre el volumen crudo** (sin modelo y sin ventaneo), y proyección de máxima intensidad en los tres ejes: axial, coronal y sagital.
- El aspect ratio de cada vista usa el spacing físico del caso, así que las proporciones son reales.
- Acepta `case_id` por línea de comandos. Generado para `001`, `025`, `042` y `068` → `outputs/figures/mip_raw_<id>.png`.
- **Limitación detectada:** en casos con metal (ej. `068`) los picos de HU saturan la escala de grises y el hueso se ve muy oscuro; además se cuelan la camilla y cables. Pendiente fijar `vmin/vmax` en el `imshow` (ej. 250–2000 HU).

## 9. Mini-resumen: qué se hizo y con qué comando

Todos los comandos se corren **desde la raíz del repo** (los scripts usan rutas relativas `data/` y `outputs/`).

| # | Paso | Comando | Qué produce |
|---|---|---|---|
| 1 | Manifest del dataset | `python src/build_manifest.py` | `data/manifest.csv` (100/100 válidos, spacing, HU, nº fragmentos) |
| 2 | Diagnóstico de HU | `python src/check_hu_outliers.py` | Consola: 52 casos con padding/metal → decisión de clip [-1024, 3000] |
| 3 | Splits fijos | `python src/make_splits.py` | `data/splits.json` (70/15/15, seed 42, por `case_id`, estratificado) |
| 4 | Ventaneo HU | `python "src/hu windowing check.py"` | `outputs/figures/hu_window_check_*.png` |
| 5 | EDA de fragmentos | `python src/eda_fragments.py` | `data/eda_fragments_detalle.csv` + `outputs/eda/*` |
| 6 | Visualizador 1 (MIP) | `python src/mip_visualizer.py` o `python src/mip_visualizer.py 042` | `outputs/figures/mip_raw_<id>.png` |

Orden obligatorio: el paso 1 va primero (2, 3 y 5 leen `data/manifest.csv`). Los pasos 4 y 6 solo necesitan los datos crudos.

## 10. Cómo ejecutarlo desde cero

**1. Clonar el repo**

```bash
git clone https://github.com/mariavalencia30/proyecto2-analitica-datos.git
cd proyecto2-analitica-datos
```

**2. Entorno virtual e instalación**

```bash
python3 -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install SimpleITK numpy pandas matplotlib tqdm
pip freeze > requirements.txt       # solo la primera vez; luego basta: pip install -r requirements.txt
```

Versiones con las que se desarrolló (Python 3.14, macOS): SimpleITK 2.5.6 · numpy 2.5.3 · pandas 3.0.5 · matplotlib 3.11.2 · tqdm 4.70.1.

**3. Descargar los datos** desde Zenodo (https://doi.org/10.5281/zenodo.10927452), descomprimir y dejarlos exactamente así (los scripts buscan en `~/Downloads/pengwin_data/raw`):

```text
~/Downloads/pengwin_data/raw/
├── PENGWIN_CT_train_images_part1/   001.mha … 
├── PENGWIN_CT_train_images_part2/   … 100.mha
└── PENGWIN_CT_train_labels/         001.mha … 100.mha
```

Si los datos están en otra ruta, cambiar la constante `DATA_ROOT` (y `LABELS_DIR` en `eda_fragments.py`) al inicio de cada script.

**4. Correr el pipeline completo**

```bash
python src/build_manifest.py
python src/check_hu_outliers.py
python src/make_splits.py
python "src/hu windowing check.py"
python src/eda_fragments.py
python src/mip_visualizer.py
```

**5. Verificar:** el manifest debe reportar 100/100 válidos, los splits 70/15/15, y el EDA debe imprimir la tabla de la sección 7. Como la semilla es fija (42), `data/splits.json` debe salir idéntico al versionado.

## 11. Estado de la Semana 8 y pendientes

- [x] Dataset curado con splits fijos.
- [x] Carga de `.mha` + ventaneo HU con clip, probado visualmente en 3 casos.
- [x] EDA de fragmentos por caso.
- [x] Visualizador 1 (MIP raw) operativo.
- [ ] Hacer commit de lo nuevo (`eda_fragments.py`, `mip_visualizer.py`, `outputs/eda/`, `mip_raw_*.png`, `eda_fragments_detalle.csv`) — hoy está sin versionar.
- [ ] Llenar `README.md`, `requirements.txt` e `IA_USAGE.md` (los tres están vacíos).
- [ ] Mover la carga + ventaneo a un módulo reutilizable (ej. `src/pengwin_io.py`) para que el `Dataset` de PyTorch de la semana 9 lo importe.
- [ ] Renombrar `src/hu windowing check.py` → `src/hu_windowing_check.py` (`git mv`).
- [ ] Corregir escala de grises del MIP en casos con metal.
- [ ] Trabajo por ramas + Pull Requests por integrante y protección de `main`.

## Archivos generados hasta ahora

- `src/`: `build_manifest.py`, `check_hu_outliers.py`, `make_splits.py`, `hu windowing check.py`, `eda_fragments.py`, `mip_visualizer.py`
- `data/`: `manifest.csv`, `splits.json`, `eda_fragments_detalle.csv`
- `outputs/figures/`: `hu_window_check_{001,068,080}.png`, `mip_raw_{001,025,042,068}.png`
- `outputs/eda/`: `resumen_estadistico.csv`, `hist_fragmentos_totales.png`, `barras_fragmentos_por_region.png`, `boxplot_volumen_hueso_mm3.png`
