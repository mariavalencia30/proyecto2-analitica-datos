"""
pengwin_io.py
-------------
Modulo unico de carga y preprocesamiento del dataset PENGWIN.

Centraliza en un solo lugar lo que antes estaba repetido en
build_manifest.py, mip_visualizer.py y hu_windowing_check.py, para que
entrenamiento, inferencia y los tres visualizadores usen exactamente la
misma logica de carga, clip, ventaneo y resize (pipeline identico en
train y en inferencia, como pidio el profesor).

Convenciones del equipo (mismas constantes que el resto del repo):
- Clip previo: [-1024, 3000] HU, neutraliza padding y metal.
- Ventana osea de visualizacion/entrada al modelo: centro 400, ancho 1800.
- Umbral osea (mascara gruesa, sin ML): 250 HU sobre el volumen crudo.

Uso:
    from pengwin_io import load_case, window_hu, resize_slice

    caso = load_case("001")
    corte = window_hu(caso["image"][caso["image"].shape[0] // 2])
    corte_256 = resize_slice(corte, 256)
"""

from pathlib import Path
from dataclasses import dataclass

import numpy as np
import SimpleITK as sitk
from skimage.transform import resize as _sk_resize

# ---------------------------------------------------------------------------
# CONFIGURACION — mismas rutas y constantes que el resto del repo
# ---------------------------------------------------------------------------
DATA_ROOT = Path("data/raw")
IMAGES_DIRS = [
    DATA_ROOT / "PENGWIN_CT_train_images_part1",
    DATA_ROOT / "PENGWIN_CT_train_images_part2",
]
LABELS_DIR = DATA_ROOT / "PENGWIN_CT_train_labels"

CLIP_MIN, CLIP_MAX = -1024, 3000        # neutraliza padding y metal
WINDOW_CENTER, WINDOW_WIDTH = 400, 1800  # ventana osea
BONE_HU_THRESHOLD = 250                  # umbral osea (mascara gruesa, no-ML)

# Fragmento principal por convencion del dataset: la etiqueta que termina en
# 1 (1, 11, 21) es el fragmento mayor de su region. Se usa para la distancia
# de separacion; se valida por separado en el EDA (fragmento_principal.py).
LABEL_TO_REGION = {1: "sacro", 11: "coxal_izq", 21: "coxal_der"}


# ---------------------------------------------------------------------------
# RUTAS
# ---------------------------------------------------------------------------
def find_image_path(case_id: str) -> Path | None:
    """Busca el .mha de imagen de un caso en part1/part2."""
    case_id = str(case_id).zfill(3)
    for img_dir in IMAGES_DIRS:
        candidate = img_dir / f"{case_id}.mha"
        if candidate.exists():
            return candidate
    return None


def find_label_path(case_id: str) -> Path | None:
    """Busca el .mha de label de un caso."""
    case_id = str(case_id).zfill(3)
    candidate = LABELS_DIR / f"{case_id}.mha"
    return candidate if candidate.exists() else None


# ---------------------------------------------------------------------------
# CARGA
# ---------------------------------------------------------------------------
@dataclass
class PengwinCase:
    case_id: str
    image: np.ndarray          # (z, y, x) HU crudo, int
    label: np.ndarray | None   # (z, y, x) etiquetas de fragmento, o None
    spacing_xyz: tuple         # (sx, sy, sz) mm/voxel, del header SimpleITK


def load_case(case_id: str, load_label: bool = True) -> PengwinCase:
    """
    Carga imagen (+ label si existe) de un caso y devuelve el volumen crudo
    en HU junto con el spacing fisico del header. No aplica clip ni ventaneo:
    eso lo hacen clip_hu / window_hu, para poder medir en HU crudo cuando
    haga falta (ej. EDA de intensidades).
    """
    img_path = find_image_path(case_id)
    if img_path is None:
        raise FileNotFoundError(f"No se encontro imagen para el caso {case_id}")

    img = sitk.ReadImage(str(img_path))
    image = sitk.GetArrayFromImage(img)  # (z, y, x)
    spacing_xyz = img.GetSpacing()       # SimpleITK: (x, y, z) en mm

    label = None
    if load_label:
        label_path = find_label_path(case_id)
        if label_path is not None:
            lbl_img = sitk.ReadImage(str(label_path))
            label = sitk.GetArrayFromImage(lbl_img)

    return PengwinCase(case_id=str(case_id).zfill(3), image=image, label=label,
                        spacing_xyz=spacing_xyz)


# ---------------------------------------------------------------------------
# PREPROCESAMIENTO: clip, ventaneo, resize
# ---------------------------------------------------------------------------
def clip_hu(volume: np.ndarray, clip_min: int = CLIP_MIN, clip_max: int = CLIP_MAX) -> np.ndarray:
    """Clip previo en HU crudo. Neutraliza padding (-2048/-1023) y metal (picos >5000 HU)."""
    return np.clip(volume, clip_min, clip_max)


def window_hu(volume: np.ndarray, center: int = WINDOW_CENTER, width: int = WINDOW_WIDTH,
              clip_min: int = CLIP_MIN, clip_max: int = CLIP_MAX) -> np.ndarray:
    """
    Ventaneo HU -> [0, 1] float32. Aplica clip_hu internamente, asi que se
    puede llamar directo sobre el volumen crudo de load_case().
    Misma formula que hu_windowing_check.py, para que el chequeo visual
    y el pipeline real produzcan exactamente lo mismo.
    """
    volume = clip_hu(volume, clip_min, clip_max)
    low, high = center - width / 2, center + width / 2
    windowed = np.clip(volume, low, high)
    windowed = (windowed - low) / (high - low)
    return windowed.astype(np.float32)


def bone_mask(volume_hu_crudo: np.ndarray, threshold: int = BONE_HU_THRESHOLD) -> np.ndarray:
    """
    Mascara gruesa de hueso por umbral de intensidad (preprocesamiento
    clasico, no interviene el modelo). Se usa en el visualizador 1 (MIP/3D
    del volumen crudo) y para limpiar estructuras que no son hueso
    (camilla, cables) antes de reconstruir.
    """
    return volume_hu_crudo > threshold


def resize_slice(slice_2d: np.ndarray, size: int = 256, order: int = 1) -> np.ndarray:
    """
    Redimensiona un corte 2D (y, x) a (size, size). order=1 (bilineal) para
    imagenes en ventana [0,1]; usar order=0 (vecino mas cercano) para
    mascaras de etiquetas, pasando is_label=True para conservar valores
    enteros exactos.
    """
    return _sk_resize(
        slice_2d, (size, size),
        order=order, preserve_range=True, anti_aliasing=(order != 0),
    ).astype(slice_2d.dtype if order == 0 else np.float32)


def resize_label_slice(slice_2d: np.ndarray, size: int = 256) -> np.ndarray:
    """Resize de una mascara de fragmentos: vecino mas cercano, sin promediar etiquetas."""
    out = _sk_resize(
        slice_2d, (size, size),
        order=0, preserve_range=True, anti_aliasing=False,
    )
    return np.round(out).astype(slice_2d.dtype)


# ---------------------------------------------------------------------------
# PRUEBA DE HUMO
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    case_id = sys.argv[1] if len(sys.argv) > 1 else "001"

    caso = load_case(case_id)
    print(f"Caso {caso.case_id}: image {caso.image.shape}, "
          f"label {None if caso.label is None else caso.label.shape}, "
          f"spacing_xyz={caso.spacing_xyz}")

    corte_central = caso.image[caso.image.shape[0] // 2]
    ventaneado = window_hu(corte_central)
    print(f"Corte central ventaneado: min={ventaneado.min():.3f}, "
          f"max={ventaneado.max():.3f}, dtype={ventaneado.dtype}")

    corte_256 = resize_slice(ventaneado, 256)
    print(f"Resize a 256: shape={corte_256.shape}")

    if caso.label is not None:
        label_256 = resize_label_slice(caso.label[caso.image.shape[0] // 2], 256)
        print(f"Resize label a 256: shape={label_256.shape}, "
              f"valores unicos={sorted(np.unique(label_256).tolist())}")

    mascara = bone_mask(caso.image)
    print(f"Bone mask: {mascara.sum()} voxeles de hueso de {mascara.size} totales")

    print("\nOK: pengwin_io.py funciona correctamente.")
