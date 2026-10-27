"""CP-CAT-07 a 12 · Errores del clasificador   (F2 y F3)

Función probada:  ClasificadorResiduos  en backend/clasificador.py
                  clasificar_imagen(), clasificar_desde_memoria() y class_names
Nivel: unitaria · Tipo: funcional · Caja blanca
Resultado esperado: del Plan de Pruebas (F2: los archivos "dañados" se rechazan "con un mensaje
                  claro"; sección 7: "si el modelo no carga, el sistema puede dar categorías al
                  azar sin avisar"). Lo esperado es que el clasificador no se caiga y que avise
                  del problema en lugar de inventar un resultado.
Precondición CP-CAT-07 a 09: clasificador con modelo falso (definido en este archivo).
Precondición CP-CAT-10 a 12: el archivo del modelo y el de configuración no existen.

Ejecutar este archivo:  python -m pytest -v tests/f3_clasificar_residuo/test_errores_del_clasificador.py
Ejecutar un caso:       python -m pytest -v -k cp_cat_10
"""
import io
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))   # para importar el código

sys.modules["tensorflow"] = SimpleNamespace()      # tarda en cargar y no hace falta
from clasificador import ClasificadorResiduos      # noqa: E402


# ----------------------------------------------------------------------
# Reemplazos del modelo entrenado
# ----------------------------------------------------------------------
class ModeloFalso:
    """Stub del modelo: devuelve probabilidades fijas."""

    def predict(self, entrada, verbose=0):
        return np.array([[0.1] * 10])


class ModeloQueFalla:
    """Un modelo que siempre se rompe al predecir."""

    def predict(self, entrada, verbose=0):
        raise RuntimeError("modelo roto")


class ClasificadorConModeloFalso(ClasificadorResiduos):
    """Es el ClasificadorResiduos real, pero sin cargar el modelo de verdad."""

    def __init__(self):
        self.class_names = [
            "bolsas_plastico", "botellas_plastico", "envases_plastico", "organic",
            "papel", "recyclable", "residuos_medicos", "tetra_pack", "vasos_papel",
            "vidrio",
        ]
        self.img_width = 160
        self.img_height = 160
        self.model = ModeloFalso()


@pytest.fixture
def clasificador():
    return ClasificadorConModeloFalso()


@pytest.fixture
def sin_modelo():
    """El constructor real, con rutas que no existen: no puede cargar el modelo."""
    return ClasificadorResiduos(modelo_path="no_existe.h5", config_path="no_existe.json")


@pytest.fixture
def foto(tmp_path):
    """Una foto blanca de 300 x 200, creada en una carpeta temporal."""
    ruta = tmp_path / "foto.png"
    Image.new("RGB", (300, 200), (255, 255, 255)).save(ruta)
    return str(ruta)


CATEGORIAS = [
    "bolsas_plastico", "botellas_plastico", "envases_plastico", "organic",
    "papel", "recyclable", "residuos_medicos", "tetra_pack", "vasos_papel",
    "vidrio",
]


def test_cp_cat_07_una_imagen_que_no_existe_devuelve_error(clasificador):
    """CP-CAT-07 · Objetivo: si la ruta no existe, avisar con un mensaje claro."""
    resultado = clasificador.clasificar_imagen("no_existe.png")

    assert resultado["estado"] == "error"
    assert "no existe" in resultado["mensaje"]


def test_cp_cat_08_un_archivo_danado_devuelve_error(clasificador, tmp_path):
    """CP-CAT-08 · Objetivo: un .jpg que en realidad es texto no se puede abrir."""
    archivo_danado = tmp_path / "danado.jpg"
    archivo_danado.write_bytes(b"esto no es una imagen")

    resultado = clasificador.clasificar_imagen(str(archivo_danado))

    assert resultado["estado"] == "error"


def test_cp_cat_09_si_el_modelo_falla_devuelve_error_con_su_mensaje(clasificador, foto):
    """CP-CAT-09 · Objetivo: un fallo del modelo no tumba el sistema."""
    clasificador.model = ModeloQueFalla()

    resultado = clasificador.clasificar_imagen(foto)

    assert resultado["estado"] == "error"
    assert "modelo roto" in resultado["mensaje"]


def test_cp_cat_10_sin_modelo_clasificar_una_imagen_no_responde_exito(sin_modelo, foto):
    """CP-CAT-10 · Objetivo: sin modelo no se inventa una categoría."""
    resultado = sin_modelo.clasificar_imagen(foto)

    assert resultado["estado"] != "éxito"


def test_cp_cat_11_sin_modelo_clasificar_desde_memoria_no_responde_exito(sin_modelo):
    """CP-CAT-11 · Objetivo: lo mismo por el camino de la imagen en memoria."""
    archivo = io.BytesIO()
    Image.new("RGB", (50, 50), (10, 20, 30)).save(archivo, format="PNG")
    archivo.seek(0)

    resultado = sin_modelo.clasificar_desde_memoria(archivo)

    assert resultado["estado"] != "éxito"


def test_cp_cat_12_sin_modelo_las_categorias_siguen_siendo_las_10_del_sistema(sin_modelo):
    """CP-CAT-12 · Objetivo: aunque falle el modelo, las categorías son las del README."""
    assert sorted(sin_modelo.class_names) == sorted(CATEGORIAS)
