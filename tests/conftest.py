"""Preparacion comun de las pruebas unitarias de EcoClasificador.

Las pruebas son unitarias: no usan MySQL, ni el modelo real, ni TensorFlow.
Todo lo que estorba se reemplaza por un doble de prueba (como FechaFija en
la clase 03) y los datos de entrada se escriben a mano (datos quemados).
"""
import importlib
import sys
import types
from pathlib import Path

import numpy as np
import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

# Datos quemados: las 10 clases de models/configuracion_clases.json
CLASES = [
    "bolsas_plastico", "botellas_plastico", "envases_plastico", "organic",
    "papel", "recyclable", "residuos_medicos", "tetra_pack", "vasos_papel",
    "vidrio",
]

RESULTADO_EXITO = {
    "estado": "éxito",
    "categoria": "papel",
    "confianza": 0.9,
    "clase_idx": 4,
    "tiempo_prediccion": 0.1,
    "todas_las_clases": {"papel": 0.9, "organic": 0.1},
    "tamano_original": "10x10",
    "tamano_procesado": "160x160",
}


class ClasificadorFalso:
    """Reemplaza a ClasificadorResiduos: devuelve lo que la prueba le diga."""

    def __init__(self):
        self.resultado = dict(RESULTADO_EXITO)
        self.rutas_recibidas = []

    def clasificar_imagen(self, ruta):
        self.rutas_recibidas.append(ruta)
        return self.resultado


class BaseDeDatosFalsa:
    """Reemplaza a DatabaseManager: nunca abre una conexion real."""

    def is_connected(self):
        return False

    def guardar_clasificacion(self, *args, **kwargs):
        return 1

    def obtener_guia_residuo(self, categoria):
        return {"categoria": categoria}


class ModeloFalso:
    """Reemplaza al modelo de Keras: devuelve probabilidades fijas."""

    def __init__(self, probabilidades):
        self.probabilidades = probabilidades
        self.entrada_recibida = None

    def predict(self, entrada, verbose=0):
        self.entrada_recibida = entrada
        return np.array([self.probabilidades])


@pytest.fixture(scope="module")
def app_modulo(tmp_path_factory):
    """app.py importado con clasificador y base de datos falsos."""
    with pytest.MonkeyPatch.context() as mp:
        falso_clasificador = types.ModuleType("clasificador")
        falso_clasificador.ClasificadorResiduos = ClasificadorFalso
        falso_database = types.ModuleType("database")
        falso_database.DatabaseManager = BaseDeDatosFalsa
        mp.setitem(sys.modules, "clasificador", falso_clasificador)
        mp.setitem(sys.modules, "database", falso_database)
        mp.delitem(sys.modules, "app", raising=False)

        modulo = importlib.import_module("app")
        modulo.app.config["TESTING"] = True
        modulo.app.config["UPLOAD_FOLDER"] = str(tmp_path_factory.mktemp("uploads"))
        yield modulo
        sys.modules.pop("app", None)


@pytest.fixture
def cliente(app_modulo):
    """Cliente HTTP de Flask; el clasificador vuelve a su respuesta de exito."""
    app_modulo.clasificador.resultado = dict(RESULTADO_EXITO)
    app_modulo.clasificador.rutas_recibidas = []
    return app_modulo.app.test_client()


@pytest.fixture(scope="module")
def modulo_clasificador():
    """clasificador.py real, con TensorFlow reemplazado por un modulo vacio."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(sys.modules, "tensorflow", types.ModuleType("tensorflow"))
        mp.delitem(sys.modules, "clasificador", raising=False)
        modulo = importlib.import_module("clasificador")
        yield modulo
        sys.modules.pop("clasificador", None)


@pytest.fixture
def crear_clasificador(modulo_clasificador):
    """Fabrica un clasificador con modelo falso, sin cargar el .h5 real."""
    def _crear(probabilidades):
        clasificador = modulo_clasificador.ClasificadorResiduos.__new__(
            modulo_clasificador.ClasificadorResiduos
        )
        clasificador.class_names = list(CLASES)
        clasificador.img_height = 160
        clasificador.img_width = 160
        clasificador.model = ModeloFalso(probabilidades)
        return clasificador
    return _crear
