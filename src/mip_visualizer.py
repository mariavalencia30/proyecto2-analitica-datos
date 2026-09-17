"""
mip_visualizer.py
------------------
Visualizador 1 — MIP raw.

Aplica un umbral óseo sobre el volumen CRUDO (sin pasar por el modelo, sin
ventaneo de visualización) y calcula la proyección de máxima intensidad
(MIP) en los tres ejes anatómicos: axial, coronal y sagital. Respeta el
aspect ratio real usando el spacing físico de cada caso.

Requisitos:
    pip install SimpleITK numpy matplotlib pandas

Uso:
    python mip_visualizer.py                 # corre sobre CASOS_EJEMPLO
    python mip_visualizer.py 007              # corre sobre un caso puntual
"""

import sys
from pathlib import Path
import SimpleITK as sitk
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------
DATA_ROOT = Path.home() / "Downloads" / "pengwin_data" / "raw"
IMAGES_DIRS = [
    DATA_ROOT / "PENGWIN_CT_train_images_part1",
    DATA_ROOT / "PENGWIN_CT_train_images_part2",
]

OUTPUT_DIR = Path("outputs/figures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MANIFEST_PATH = Path("data/manifest.csv")

# Umbral óseo sobre HU crudo (no es la ventana de visualización, es una
# segmentación gruesa para aislar hueso antes de proyectar)
HU_THRESHOLD = 250

# Casos de ejemplo si no se pasa un case_id por línea de comandos
CASOS_EJEMPLO = ["001", "025", "068"]


def find_image_path(case_id):
    for img_dir in IMAGES_DIRS:
        candidate = img_dir / f"{case_id}.mha"
        if candidate.exists():
            return candidate
    return None


def compute_mip(volume, axis, hu_threshold):
    """
    Aplica umbral óseo y calcula MIP a lo largo del eje dado.
    volume: array (z, y, x) en HU crudo.
    axis: 0 = axial (colapsa z), 1 = coronal (colapsa y), 2 = sagital (colapsa x)
    """
    bone_only = np.where(volume > hu_threshold, volume, volume.min())
    mip = bone_only.max(axis=axis)
    return mip


def mip_visualization(case_id, spacing_xyz=None):
    img_path = find_image_path(case_id)
    if img_path is None:
        print(f"[AVISO] No se encontró el caso {case_id}, se omite.")
        return

    img = sitk.ReadImage(str(img_path))
    volume = sitk.GetArrayFromImage(img)  # (z, y, x)
    sx, sy, sz = img.GetSpacing()  # spacing real (x, y, z) en mm

    # MIP en los 3 ejes anatómicos
    mip_axial = compute_mip(volume, axis=0, hu_threshold=HU_THRESHOLD)     # vista desde arriba (x-y)
    mip_coronal = compute_mip(volume, axis=1, hu_threshold=HU_THRESHOLD)   # vista frontal (x-z)
    mip_sagital = compute_mip(volume, axis=2, hu_threshold=HU_THRESHOLD)   # vista lateral (y-z)

    fig, axes = plt.subplots(1, 3, figsize=(15, 6))

    axes[0].imshow(mip_axial, cmap="gray", aspect=sy / sx)
    axes[0].set_title(f"Caso {case_id} — MIP axial")
    axes[0].axis("off")

    axes[1].imshow(mip_coronal, cmap="gray", aspect=sz / sx, origin="lower")
    axes[1].set_title(f"Caso {case_id} — MIP coronal")
    axes[1].axis("off")

    axes[2].imshow(mip_sagital, cmap="gray", aspect=sz / sy, origin="lower")
    axes[2].set_title(f"Caso {case_id} — MIP sagital")
    axes[2].axis("off")

    plt.tight_layout()
    out_path = OUTPUT_DIR / f"mip_raw_{case_id}.png"
    plt.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Guardado: {out_path}")


def main():
    if len(sys.argv) > 1:
        casos = sys.argv[1:]
    else:
        casos = CASOS_EJEMPLO

    for case_id in casos:
        case_id = case_id.zfill(3)
        mip_visualization(case_id)


if __name__ == "__main__":
    main()