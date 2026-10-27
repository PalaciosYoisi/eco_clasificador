"""CP-IMG-01 a 11 · Preparar la imagen   (F3: clasificar el residuo)

Función probada:  ClasificadorResiduos.clasificar_imagen(ruta) y clasificar_desde_memoria(archivo)
                  en backend/clasificador.py. Antes de llamar al modelo, la imagen se pasa a
                  RGB, se redimensiona y se divide entre 255.
Nivel: unitaria · Tipo: funcional · Caja blanca
Resultado esperado: del Plan de Pruebas (F3: "preparar la imagen") y del README /
                  configuracion_clases.json: el modelo trabaja con imágenes de 160 x 160 píxeles
                  y 3 canales, con valores entre 0 y 1, en el orden rojo, verde, azul.
Precondición: clasificador con modelo falso (definido en este archivo); el modelo guarda lo que
                  recibe para que la prueba lo revise. Las fotos de prueba las crea el propio
                  código en una carpeta temporal.

Ejecutar este archivo:  python -m pytest -v tests/f3_clasificar_residuo/test_preparar_la_imagen.py
Ejecutar un caso:       python -m pytest -v -k cp_img_08
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
# Reemplazo del modelo entrenado
# ----------------------------------------------------------------------
class ModeloFalso:
    """Stub del modelo: devuelve probabilidades fijas y guarda lo que recibe."""

    def __init__(self):
        self.entrada = None

    def predict(self, entrada, verbose=0):
        self.entrada = entrada
        return np.array([[0.1] * 10])


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


def guardar_foto(carpeta, nombre, modo, tamano, color):
    ruta = carpeta / nombre
    Image.new(modo, tamano, color).save(ruta)
    return str(ruta)


# (caso, nombre del archivo, modo de color, tamaño (ancho, alto), color, objetivo)
FOTOS = [
    ("cp_img_01", "foto.png", "RGB", (300, 200), (200, 100, 50), "una foto horizontal"),
    ("cp_img_02", "foto.png", "RGB", (1, 1), (200, 100, 50), "un solo píxel"),
    ("cp_img_03", "foto.png", "RGB", (4000, 3000), (200, 100, 50), "una foto de 12 megapíxeles"),
    ("cp_img_04", "foto.png", "L", (300, 200), 120, "png en escala de grises"),
    ("cp_img_05", "foto.png", "RGBA", (300, 200), (200, 100, 50, 255), "png con transparencia"),
    ("cp_img_06", "foto.jpg", "RGB", (300, 200), (200, 100, 50), "formato jpg"),
]

# (caso, modo de color, color de la foto, [rojo, verde, azul] esperados, objetivo)
PIXELES = [
    ("cp_img_07", "RGB", (255, 255, 255), [1.0, 1.0, 1.0], "blanco: el máximo, 255, pasa a 1"),
    ("cp_img_08", "RGB", (255, 0, 0), [1.0, 0.0, 0.0], "rojo puro: el rojo es el primer canal"),
    ("cp_img_09", "RGBA", (255, 0, 0, 0), [1.0, 0.0, 0.0], "la transparencia se descarta"),
]


@pytest.mark.parametrize("caso, nombre, modo, tamano, color, objetivo", FOTOS)
def test_toda_foto_llega_al_modelo_de_160_x_160_x_3(clasificador, tmp_path, caso, nombre, modo, tamano, color, objetivo):
    ruta = guardar_foto(tmp_path, nombre, modo, tamano, color)      # preparar

    clasificador.clasificar_imagen(ruta)                            # ejecutar

    assert clasificador.model.entrada.shape == (1, 160, 160, 3)     # verificar


@pytest.mark.parametrize("caso, modo, color, esperado, objetivo", PIXELES)
def test_el_primer_pixel_llega_normalizado_en_orden_rojo_verde_azul(clasificador, tmp_path, caso, modo, color, esperado, objetivo):
    ruta = guardar_foto(tmp_path, "color.png", modo, (40, 30), color)

    clasificador.clasificar_imagen(ruta)

    primer_pixel = clasificador.model.entrada[0][0][0]
    assert primer_pixel.tolist() == pytest.approx(esperado)


def test_cp_img_10_una_imagen_en_memoria_se_prepara_igual(clasificador):
    """CP-IMG-10 · Objetivo: la ruta que recibe la imagen en memoria prepara lo mismo."""
    archivo = io.BytesIO()
    Image.new("RGB", (300, 200), (10, 20, 30)).save(archivo, format="PNG")
    archivo.seek(0)

    clasificador.clasificar_desde_memoria(archivo)

    assert clasificador.model.entrada.shape == (1, 160, 160, 3)


def test_cp_img_11_en_memoria_algo_que_no_es_una_imagen_devuelve_error(clasificador):
    """CP-IMG-11 · Objetivo: un texto en lugar de una imagen no se cae: informa el error."""
    resultado = clasificador.clasificar_desde_memoria(io.BytesIO(b"esto no es una imagen"))

    assert resultado["estado"] == "error"
