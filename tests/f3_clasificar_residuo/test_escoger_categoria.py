"""CP-CAT-01 a 06 · Escoger la categoría   (F3: clasificar el residuo)

Función probada:  ClasificadorResiduos.clasificar_imagen(ruta)  en backend/clasificador.py
                  Entre las 10 categorías gana la de mayor probabilidad.
Nivel: unitaria · Tipo: funcional · Caja blanca
Resultado esperado: del Plan de Pruebas (F3: "devuelve una de las 10 categorías y el porcentaje
                  de confianza") y del README (las 10 categorías y su orden).
Precondición: clasificador con modelo falso (definido en este archivo); cada caso le indica al
                  modelo qué probabilidades devolver, así que la categoría que debe salir se
                  conoce de antemano.

Ejecutar este archivo:  python -m pytest -v tests/f3_clasificar_residuo/test_escoger_categoria.py
Ejecutar un caso:       python -m pytest -v -k cp_cat_03
"""
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
    """Stub del modelo: devuelve las probabilidades que la prueba le indique."""

    def __init__(self):
        self.probabilidades = [0.1] * 10

    def predict(self, entrada, verbose=0):
        return np.array([self.probabilidades])


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
def foto(tmp_path):
    """Una foto blanca de 300 x 200, creada en una carpeta temporal."""
    ruta = tmp_path / "foto.png"
    Image.new("RGB", (300, 200), (255, 255, 255)).save(ruta)
    return str(ruta)


# Probabilidades escritas a mano, una por cada una de las 10 categorías (suman 1)
PROBABILIDADES_MEZCLADAS = [0.03, 0.12, 0.05, 0.30, 0.08, 0.02, 0.25, 0.07, 0.03, 0.05]

CAMPOS_QUE_USA_LA_API = [
    "estado", "categoria", "confianza", "clase_idx", "todas_las_clases",
    "tiempo_prediccion", "tamano_original", "tamano_procesado",
]

# (caso, probabilidades, categoría esperada, confianza esperada, objetivo)
GANADORAS = [
    ("cp_cat_01", [0.91, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01],
     "bolsas_plastico", 0.91, "gana la primera categoría de la lista"),
    ("cp_cat_02", [0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.82, 0.02, 0.02, 0.02],
     "residuos_medicos", 0.82, "gana una categoría del medio: la de residuos médicos"),
    ("cp_cat_03", [0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.91],
     "vidrio", 0.91, "gana la última categoría de la lista"),
    ("cp_cat_04", [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
     "recyclable", 1.0, "certeza total: la confianza es 1"),
]


@pytest.mark.parametrize("caso, probabilidades, categoria_esperada, confianza_esperada, objetivo", GANADORAS)
def test_gana_la_categoria_de_mayor_probabilidad(
        clasificador, foto, caso, probabilidades, categoria_esperada, confianza_esperada, objetivo):
    clasificador.model.probabilidades = probabilidades              # preparar

    resultado = clasificador.clasificar_imagen(foto)                # ejecutar

    assert resultado["categoria"] == categoria_esperada             # verificar
    assert resultado["confianza"] == pytest.approx(confianza_esperada)


def test_cp_cat_05_todas_las_clases_vienen_ordenadas_de_mayor_a_menor(clasificador, foto):
    """CP-CAT-05 · Objetivo: la página muestra primero la categoría más probable."""
    clasificador.model.probabilidades = PROBABILIDADES_MEZCLADAS

    resultado = clasificador.clasificar_imagen(foto)

    confianzas = list(resultado["todas_las_clases"].values())
    assert confianzas == sorted(confianzas, reverse=True)


def test_cp_cat_06_el_resultado_trae_todos_los_campos_que_usa_la_api(clasificador, foto):
    """CP-CAT-06 · Objetivo: si falta un campo, la API falla al armar su respuesta."""
    resultado = clasificador.clasificar_imagen(foto)

    assert set(CAMPOS_QUE_USA_LA_API) <= set(resultado)
