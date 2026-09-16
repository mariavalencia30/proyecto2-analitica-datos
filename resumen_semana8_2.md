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

## 4. Diagnóstico de valores HU (`check_hu_outliers.py`)

- Se detectaron 52 casos con valores HU fuera del rango típico de CT (-1100 a 5000 HU).
- **Explicación identificada, no es un error:**
  - Valores mínimos repetidos exactos (ej. -2048, -1023) = **padding** del escáner fuera del campo de reconstrucción.
  - Valores máximos muy altos (hasta 47,685 HU en un caso) = **artefacto de metal**, esperable porque son pacientes candidatos a cirugía de fijación pélvica (ya traen tornillos/placas en algunos casos).
- **Decisión:** al aplicar el ventaneo HU se hará un `clip` agresivo (ej. -1024 a 3000) antes de normalizar, para que el padding y el metal no dañen el contraste del hueso. Esto se documentará como hallazgo del EDA.

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

## 5. Splits fijos (`make_splits.py`)

- Split por `case_id` (nunca por corte, para evitar data leakage).
- Estratificado por número de fragmentos (buckets bajo/medio/alto).
- Semilla fija = 42.

Bucket 'alto': 26 casos -> train=18, val=4, test=4
Bucket 'bajo': 1 casos -> train=1, val=0, test=0
Bucket 'medio': 73 casos -> train=51, val=11, test=11

Total: train=70, val=15, test=15
Splits guardados en: data/splits.json

**Resultado:** train=70, val=15, test=15.

**Limitación conocida (documentada, no es un bug):** solo existe 1 caso en el bucket "bajo" (≤3 fragmentos), así que ese extremo quedó representado únicamente en train y no en val/test. Se deja anotado para el informe final.

## 6. Pendiente para cerrar la Semana 8

- [ ] Loader NIfTI/`.mha` + ventaneo HU (con el clip ya definido), probado visualmente en varios casos.
- [ ] EDA completo de fragmentos (distribución por caso, tamaños en mm³, etc.).
- [ ] Visualizador 1 (MIP raw).
- [ ] Repositorio de GitHub con historial de commits y PRs por integrante.

## Archivos generados hasta ahora
- `src/build_manifest.py`
- `src/check_hu_outliers.py`
- `src/make_splits.py`
- `data/manifest.csv`
- `data/splits.json`


